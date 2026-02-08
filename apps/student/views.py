"""
Student App - غرفة الدراسة الذكية (Enterprise Edition)
S-ACM - Smart Academic Content Management System

يحتوي على:
- Gamified Dashboard (تقدم، استئناف، إحصائيات)
- Split-Screen Study Room
- Context-Aware AI Chat
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Avg, Sum, Q
import time
import logging

from apps.courses.models import Course, LectureFile
from apps.courses.mixins import CourseEnrollmentMixin
from apps.accounts.views import StudentRequiredMixin
from apps.accounts.models import UserActivity
from apps.notifications.models import NotificationManager
from apps.ai_features.models import (
    AISummary, AIGeneratedQuestion, AIChat,
    AIUsageLog, StudentProgress
)

logger = logging.getLogger('courses')


# ========== Gamified Dashboard ==========

class StudentDashboardView(LoginRequiredMixin, StudentRequiredMixin, TemplateView):
    """لوحة تحكم الطالب - Gamified"""
    template_name = 'student/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'dashboard'
        student = self.request.user

        # المقررات الحالية
        current_courses = Course.objects.get_current_courses_for_student(student)
        context['current_courses'] = current_courses
        context['archived_courses'] = Course.objects.get_archived_courses_for_student(student)

        # حساب تقدم كل مقرر
        course_progress = []
        for course in current_courses:
            total_files = course.files.filter(is_visible=True, is_deleted=False).count()
            if total_files > 0:
                viewed_files = StudentProgress.objects.filter(
                    student=student,
                    file__course=course,
                    progress__gt=0
                ).count()
                progress_pct = min(100, int((viewed_files / total_files) * 100))
            else:
                progress_pct = 0
                viewed_files = 0

            instructors = course.instructor_courses.select_related('instructor')
            instructor_name = instructors.first().instructor.full_name if instructors.exists() else '-'

            course_progress.append({
                'course': course,
                'progress': progress_pct,
                'total_files': total_files,
                'viewed_files': viewed_files,
                'instructor': instructor_name,
            })
        context['course_progress'] = course_progress

        # استئناف التعلم - آخر ملف تم الوصول إليه
        last_progress = StudentProgress.objects.filter(
            student=student, progress__lt=100
        ).select_related('file', 'file__course').order_by('-last_accessed').first()
        context['resume_item'] = last_progress

        # الإشعارات
        context['unread_notifications'] = NotificationManager.get_unread_count(student)

        # آخر الملفات
        context['recent_files'] = LectureFile.objects.filter(
            course__in=current_courses,
            is_visible=True, is_deleted=False
        ).select_related('course').order_by('-upload_date')[:5]

        # إحصائيات سريعة
        context['stats'] = {
            'total_courses': current_courses.count(),
            'files_viewed': StudentProgress.objects.filter(student=student, progress__gt=0).count(),
            'ai_used_today': AIUsageLog.objects.filter(
                user=student,
                request_time__date=timezone.now().date()
            ).count(),
            'ai_remaining': AIUsageLog.get_remaining_requests(student),
            'total_summaries': AISummary.objects.filter(user=student).count(),
            'total_questions': AIGeneratedQuestion.objects.filter(user=student).count(),
        }

        return context


# ========== Courses ==========

class StudentCourseListView(LoginRequiredMixin, StudentRequiredMixin, ListView):
    template_name = 'student/course_list.html'
    context_object_name = 'courses'

    def get_queryset(self):
        student = self.request.user
        view_type = self.request.GET.get('view', 'current')
        if view_type == 'archived':
            return Course.objects.get_archived_courses_for_student(student)
        return Course.objects.get_current_courses_for_student(student)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'courses'
        context['view_type'] = self.request.GET.get('view', 'current')
        return context


class StudentCourseDetailView(LoginRequiredMixin, StudentRequiredMixin, CourseEnrollmentMixin, DetailView):
    model = Course
    template_name = 'student/course_detail.html'
    context_object_name = 'course'

    def get_object(self, queryset=None):
        course = super().get_object(queryset)
        self.check_course_access(self.request.user, course)
        return course

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'courses'
        course = self.object
        files = course.files.filter(is_visible=True, is_deleted=False)

        context['lectures'] = files.filter(file_type='Lecture')
        context['summaries'] = files.filter(file_type='Summary')
        context['exams'] = files.filter(file_type='Exam')
        context['assignments'] = files.filter(file_type='Assignment')
        context['references'] = files.filter(file_type='Reference')
        context['others'] = files.filter(file_type='Other')
        context['instructors'] = course.instructor_courses.select_related('instructor')
        context['all_files'] = files

        return context


# ========== Split-Screen Study Room ==========

class StudyRoomView(LoginRequiredMixin, StudentRequiredMixin, View):
    """غرفة الدراسة - شاشة مقسومة: عارض المحتوى + مساعد AI"""
    template_name = 'student/study_room.html'

    def get(self, request, file_pk):
        file_obj = get_object_or_404(LectureFile, pk=file_pk, is_deleted=False, is_visible=True)

        # التحقق من الصلاحية
        mixin = CourseEnrollmentMixin()
        mixin.check_course_access(request.user, file_obj.course)

        # تسجيل المشاهدة
        file_obj.increment_view()
        UserActivity.objects.create(
            user=request.user, activity_type='view',
            description=f'غرفة الدراسة: {file_obj.title}',
            file_id=file_obj.id,
            ip_address=request.META.get('REMOTE_ADDR')
        )

        # تحديث/إنشاء تقدم الطالب
        progress, created = StudentProgress.objects.get_or_create(
            student=request.user, file=file_obj,
            defaults={'progress': 10}
        )
        if not created and progress.progress < 100:
            progress.progress = min(100, progress.progress + 10)
            progress.save(update_fields=['progress', 'last_accessed'])

        # محادثات AI السابقة
        chat_history = AIChat.objects.filter(
            file=file_obj, user=request.user
        ).order_by('created_at')[:50]

        # ملخص موجود
        existing_summary = AISummary.objects.filter(file=file_obj).first()

        # ملفات المقرر (للتنقل)
        course_files = file_obj.course.files.filter(
            is_visible=True, is_deleted=False
        ).order_by('upload_date')
        file_list = list(course_files)
        current_index = next((i for i, f in enumerate(file_list) if f.id == file_obj.id), 0)
        prev_file = file_list[current_index - 1] if current_index > 0 else None
        next_file = file_list[current_index + 1] if current_index < len(file_list) - 1 else None

        context = {
            'file': file_obj,
            'course': file_obj.course,
            'progress': progress,
            'chat_history': chat_history,
            'existing_summary': existing_summary,
            'prev_file': prev_file,
            'next_file': next_file,
            'remaining_requests': AIUsageLog.get_remaining_requests(request.user),
            'active_page': 'study_room',
        }

        return render(request, self.template_name, context)


# ========== AI Chat for Study Room ==========

class AIChatView(LoginRequiredMixin, StudentRequiredMixin, View):
    """محادثة AI سياقية في غرفة الدراسة"""

    def post(self, request, file_pk):
        file_obj = get_object_or_404(LectureFile, pk=file_pk, is_deleted=False)
        question = request.POST.get('question', '').strip()
        action = request.POST.get('action', 'ask')

        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        if not question and action == 'ask':
            if is_ajax:
                return JsonResponse({'success': False, 'error': 'يرجى إدخال سؤال.'})
            messages.error(request, 'يرجى إدخال سؤال.')
            return redirect('student:study_room', file_pk=file_pk)

        # Rate limit check
        if not AIUsageLog.check_rate_limit(request.user):
            error = 'تجاوزت الحد المسموح. حاول بعد ساعة.'
            if is_ajax:
                return JsonResponse({'success': False, 'error': error})
            messages.error(request, error)
            return redirect('student:study_room', file_pk=file_pk)

        try:
            from apps.ai_features.services import GeminiService
            service = GeminiService()
            text = service.extract_text_from_file(file_obj)

            if not text:
                error = 'لا يمكن استخراج النص من هذا الملف.'
                if is_ajax:
                    return JsonResponse({'success': False, 'error': error})
                messages.error(request, error)
                return redirect('student:study_room', file_pk=file_pk)

            # تحديد نوع الطلب
            if action == 'summarize':
                question = 'قم بتلخيص هذا المحتوى بشكل مفصل ومنظم'
            elif action == 'quiz':
                question = 'أنشئ 5 أسئلة اختبارية متنوعة من هذا المحتوى مع الإجابات'
            elif action == 'explain':
                question = 'اشرح المفاهيم الرئيسية في هذا المحتوى بطريقة مبسطة'

            start_time = time.time()
            answer = service.ask_document(text, question)
            response_time = time.time() - start_time

            chat = AIChat.objects.create(
                file=file_obj, user=request.user,
                question=question, answer=answer,
                response_time=response_time,
            )

            AIUsageLog.log_request(
                user=request.user, request_type='chat',
                file=file_obj, success=True,
                tokens_used=len(question.split()) + len(answer.split())
            )

            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'question': question,
                    'answer': answer,
                    'created_at': chat.created_at.strftime('%Y-%m-%d %H:%M'),
                    'remaining': AIUsageLog.get_remaining_requests(request.user),
                })

            messages.success(request, 'تم الحصول على الإجابة!')

        except Exception as e:
            error_str = str(e).lower()
            # Check for rate limit / quota errors
            if 'quota' in error_str or '429' in error_str or 'rate' in error_str or 'resource_exhausted' in error_str:
                error = '⏳ تجاوزت الحد المسموح من الطلبات. انتظر دقيقة ثم حاول مرة أخرى.'
            else:
                error = f'⚠️ حدث خطأ: {str(e)[:100]}'
            if is_ajax:
                return JsonResponse({'success': False, 'error': error})
            messages.error(request, error)

        return redirect('student:study_room', file_pk=file_pk)


class AIChatClearView(LoginRequiredMixin, StudentRequiredMixin, View):
    """مسح سجل المحادثة"""
    def post(self, request, file_pk):
        AIChat.objects.filter(file_id=file_pk, user=request.user).delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        messages.success(request, 'تم مسح المحادثة.')
        return redirect('student:study_room', file_pk=file_pk)


class UpdateProgressView(LoginRequiredMixin, StudentRequiredMixin, View):
    """تحديث تقدم الطالب (AJAX)"""
    def post(self, request, file_pk):
        progress_val = request.POST.get('progress', 0)
        position = request.POST.get('position', '')

        try:
            progress_val = min(100, max(0, int(progress_val)))
        except (ValueError, TypeError):
            progress_val = 0

        prog, _ = StudentProgress.objects.get_or_create(
            student=request.user,
            file_id=file_pk,
            defaults={'progress': progress_val, 'last_position': position}
        )
        if prog.progress < progress_val:
            prog.progress = progress_val
        if position:
            prog.last_position = position
        prog.save()

        return JsonResponse({'success': True, 'progress': prog.progress})
