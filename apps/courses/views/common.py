"""
Common Views - العروض المشتركة
S-ACM - Smart Academic Content Management System

This module contains views shared across student and instructor roles,
such as file download and file viewing.
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.views import View
from django.http import FileResponse
from django.core.exceptions import PermissionDenied
from pathlib import Path
import mimetypes
import logging

from ..models import LectureFile
from ..mixins import SecureFileDownloadMixin
from apps.accounts.models import UserActivity

logger = logging.getLogger('courses')


class FileDownloadView(SecureFileDownloadMixin, View):
    """
    تحميل الملفات بشكل آمن (محمي ضد IDOR)
    """
    
    def get(self, request, pk):
        user = request.user
        
        try:
            require_visible = user.is_student()
            file_obj = self.get_secure_file(pk, require_visible=require_visible)
        except PermissionDenied as e:
            logger.warning(
                f"IDOR attempt blocked: User {user.academic_id} tried to access file {pk}. "
                f"Reason: {str(e)}"
            )
            messages.error(request, str(e) if str(e) else 'ليس لديك صلاحية الوصول لهذا الملف.')
            if user.is_student():
                return redirect('courses:student_dashboard')
            elif user.is_instructor():
                return redirect('courses:instructor_dashboard')
            return redirect('core:dashboard_redirect')
        
        # زيادة عداد التحميل
        file_obj.increment_download()
        
        # تسجيل النشاط
        UserActivity.objects.create(
            user=user,
            activity_type='download',
            description=f'تحميل ملف: {file_obj.title}',
            file_id=file_obj.id,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        # إذا كان رابط خارجي
        if file_obj.content_type == 'external_link':
            return redirect(file_obj.external_link)
        
        # إذا كان ملف محلي
        if file_obj.local_file:
            file_path = file_obj.local_file.path
            content_type, _ = mimetypes.guess_type(file_path)
            response = FileResponse(
                open(file_path, 'rb'),
                content_type=content_type or 'application/octet-stream'
            )
            response['Content-Disposition'] = f'attachment; filename="{Path(file_path).name}"'
            return response
        
        messages.error(request, 'الملف غير موجود.')
        return redirect('courses:student_dashboard')


class FileViewView(SecureFileDownloadMixin, View):
    """
    عرض الملفات (للـ PDF والفيديو) بشكل آمن
    """
    
    def get(self, request, pk):
        user = request.user
        
        try:
            require_visible = user.is_student()
            file_obj = self.get_secure_file(pk, require_visible=require_visible)
        except PermissionDenied as e:
            logger.warning(
                f"IDOR attempt blocked: User {user.academic_id} tried to view file {pk}. "
                f"Reason: {str(e)}"
            )
            messages.error(request, str(e) if str(e) else 'ليس لديك صلاحية الوصول لهذا الملف.')
            return redirect('courses:student_dashboard')
        
        # زيادة عداد المشاهدة
        file_obj.increment_view()
        
        # تسجيل النشاط
        UserActivity.objects.create(
            user=request.user,
            activity_type='view',
            description=f'عرض ملف: {file_obj.title}',
            file_id=file_obj.id,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        context = {
            'file': file_obj,
            'course': file_obj.course
        }
        
        return render(request, 'courses/file_viewer.html', context)
