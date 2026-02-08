"""
محرك البث (Streaming Engine) - خدمة ملفات بدعم Range Headers
S-ACM Enterprise Edition

يدعم:
- بث الفيديو مع Range Headers (تسريع التحميل والتشغيل)
- عرض PDF مع Content-Disposition inline
- عرض ملفات Markdown مع تحويل إلى HTML
- حماية IDOR كاملة عبر SecureFileDownloadMixin
"""

import mimetypes
import os
import re
from pathlib import Path

from django.conf import settings
from django.http import (
    FileResponse, HttpResponse, HttpResponseNotFound,
    StreamingHttpResponse, Http404
)
from django.shortcuts import get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.encoding import smart_str

from apps.courses.models import LectureFile
from apps.courses.mixins import SecureFileDownloadMixin
from apps.accounts.models import UserActivity

import logging

logger = logging.getLogger('courses')


class RangeFileIterator:
    """
    مُكرّر للملفات مع دعم Range Headers.
    يُمكّن من بث أجزاء محددة من الملف بكفاءة.
    """
    def __init__(self, file_obj, start: int = 0, end: int = None, chunk_size: int = 8192):
        self.file_obj = file_obj
        self.start = start
        self.end = end
        self.chunk_size = chunk_size

    def __iter__(self):
        self.file_obj.seek(self.start)
        remaining = (self.end - self.start + 1) if self.end else None
        while True:
            if remaining is not None:
                read_size = min(self.chunk_size, remaining)
            else:
                read_size = self.chunk_size

            data = self.file_obj.read(read_size)
            if not data:
                break
            if remaining is not None:
                remaining -= len(data)
            yield data
            if remaining is not None and remaining <= 0:
                break

    def close(self):
        self.file_obj.close()


class StreamFileView(SecureFileDownloadMixin, View):
    """
    بث الملفات مع دعم Range Headers الكامل.
    يُستخدم لبث الفيديو والـ PDF والمحتوى الآخر.
    """

    def get(self, request, pk):
        user = request.user
        require_visible = user.is_student()

        try:
            file_obj = self.get_secure_file(pk, require_visible=require_visible)
        except Exception:
            raise Http404("الملف غير موجود أو لا تملك صلاحية الوصول.")

        # تسجيل المشاهدة
        file_obj.increment_view()
        UserActivity.objects.create(
            user=user,
            activity_type='view',
            description=f'بث ملف: {file_obj.title}',
            file_id=file_obj.id,
            ip_address=request.META.get('REMOTE_ADDR')
        )

        # رابط خارجي
        if file_obj.content_type == 'external_link':
            from django.shortcuts import redirect
            return redirect(file_obj.external_link)

        # ملف محلي
        if not file_obj.local_file:
            raise Http404("الملف غير موجود على الخادم.")

        file_path = file_obj.local_file.path
        if not os.path.exists(file_path):
            raise Http404("الملف غير موجود على الخادم.")

        file_size = os.path.getsize(file_path)
        content_type, _ = mimetypes.guess_type(file_path)
        content_type = content_type or 'application/octet-stream'

        # التحقق من Range Header
        range_header = request.META.get('HTTP_RANGE', '')

        if range_header and file_obj.is_video():
            return self._serve_range_response(file_path, file_size, content_type, range_header)

        # للـ PDF والملفات الأخرى - عرض inline
        response = FileResponse(
            open(file_path, 'rb'),
            content_type=content_type,
        )
        response['Content-Length'] = file_size
        response['Accept-Ranges'] = 'bytes'

        # PDF و الصور inline، الباقي attachment
        if file_obj.is_pdf() or file_obj.is_image():
            response['Content-Disposition'] = f'inline; filename="{smart_str(Path(file_path).name)}"'
        else:
            response['Content-Disposition'] = f'inline; filename="{smart_str(Path(file_path).name)}"'

        return response

    def _serve_range_response(self, file_path, file_size, content_type, range_header):
        """خدمة استجابة Range (206 Partial Content)."""
        range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)
        if not range_match:
            response = HttpResponse(status=416)
            response['Content-Range'] = f'bytes */{file_size}'
            return response

        start = int(range_match.group(1))
        end_str = range_match.group(2)
        end = int(end_str) if end_str else file_size - 1

        if start >= file_size:
            response = HttpResponse(status=416)
            response['Content-Range'] = f'bytes */{file_size}'
            return response

        end = min(end, file_size - 1)
        content_length = end - start + 1

        file_handle = open(file_path, 'rb')
        iterator = RangeFileIterator(file_handle, start=start, end=end)

        response = StreamingHttpResponse(
            iterator,
            status=206,
            content_type=content_type,
        )
        response['Content-Length'] = content_length
        response['Content-Range'] = f'bytes {start}-{end}/{file_size}'
        response['Accept-Ranges'] = 'bytes'
        response['Cache-Control'] = 'no-cache'

        return response


class StreamMarkdownView(LoginRequiredMixin, View):
    """
    عرض ملفات Markdown المُولّدة بالـ AI.
    يُحوّل Markdown إلى HTML مع تنسيق RTL.
    """

    def get(self, request, path):
        """عرض ملف Markdown من media/ai_generated/."""
        # تنظيف المسار لمنع directory traversal
        clean_path = path.replace('..', '').strip('/')
        full_path = Path(settings.MEDIA_ROOT) / clean_path

        if not full_path.exists() or not full_path.is_file():
            raise Http404("الملف غير موجود.")

        # التأكد أن الملف داخل ai_generated
        ai_dir = Path(settings.MEDIA_ROOT) / 'ai_generated'
        try:
            full_path.resolve().relative_to(ai_dir.resolve())
        except ValueError:
            raise Http404("مسار غير مسموح.")

        content = full_path.read_text(encoding='utf-8')

        # إزالة الـ frontmatter إذا وُجد
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                content = parts[2].strip()

        # تحويل Markdown إلى HTML
        try:
            import markdown
            html_content = markdown.markdown(
                content,
                extensions=['tables', 'fenced_code', 'toc', 'nl2br']
            )
        except ImportError:
            # Fallback: إرجاع Markdown خام
            html_content = f'<pre dir="rtl" style="white-space: pre-wrap;">{content}</pre>'

        return HttpResponse(html_content, content_type='text/html; charset=utf-8')
