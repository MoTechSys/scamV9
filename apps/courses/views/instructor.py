"""
Instructor Views - عروض المدرسين
S-ACM - Smart Academic Content Management System

This module contains all instructor-facing views including file management
and AI integration features.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy, reverse
from django.db.models import Count
from django.utils import timezone
import logging

from ..models import Course, LectureFile
from ..forms import LectureFileForm
from apps.accounts.views import InstructorRequiredMixin
from apps.accounts.models import User, UserActivity
from apps.notifications.models import NotificationManager
from apps.core.models import AuditLog

# استيراد خدمات الذكاء الاصطناعي (تأكد من وجود Celery أو استدعاء الدالة مباشرة)
try:
    from apps.ai_features.services import generate_summary_async, generate_questions_async
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    logging.warning("AI Services or Celery tasks not found. AI features will be disabled.")

logger = logging.getLogger('courses')


class InstructorDashboardView(LoginRequiredMixin, InstructorRequiredMixin, TemplateView):
    """لوحة تحكم المدرس"""
    template_name = 'instructor_panel/dashboard_new.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'dashboard'
        instructor = self.request.user
        
        # المقررات المعينة - مع prefetch للملفات
        context['my_courses'] = Course.objects.get_courses_for_instructor(instructor).prefetch_related(
            'files'
        ).select_related('level')
        
        # الملفات - Query واحد فقط مع كل البيانات
        instructor_files = LectureFile.objects.filter(
            uploader=instructor,
            is_deleted=False
        ).select_related('course')
        
        # إحصائيات من الـ Query الموجود (بدون queries إضافية)
        files_list = list(instructor_files)
        context['total_files'] = len(files_list)
        context['total_downloads'] = sum(f.download_count for f in files_list)
        context['total_views'] = sum(f.view_count for f in files_list)
        
        # آخر الملفات والأكثر تفاعلاً (من نفس القائمة)
        context['recent_uploads'] = sorted(files_list, key=lambda x: x.upload_date, reverse=True)[:5]
        context['top_files'] = sorted(files_list, key=lambda x: x.download_count, reverse=True)[:5]
        
        return context


class InstructorCourseListView(LoginRequiredMixin, InstructorRequiredMixin, ListView):
    """قائمة مقررات المدرس"""
    template_name = 'instructor_panel/courses/list.html'
    context_object_name = 'courses'
    
    def get_queryset(self):
        return Course.objects.get_courses_for_instructor(self.request.user).prefetch_related('files').select_related('level')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'courses'
        return context


class InstructorCourseDetailView(LoginRequiredMixin, InstructorRequiredMixin, DetailView):
    """تفاصيل المقرر للمدرس"""
    model = Course
    template_name = 'instructor_panel/courses/detail.html'
    context_object_name = 'course'
    
    def get_queryset(self):
        return Course.objects.get_courses_for_instructor(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'courses'
        course = self.object
        
        # جميع الملفات (بما فيها المخفية)
        files = course.files.filter(is_deleted=False)
        context['all_files'] = files
        context['visible_files'] = files.filter(is_visible=True)
        context['hidden_files'] = files.filter(is_visible=False)
        
        # إحصائيات
        context['total_downloads'] = sum(f.download_count for f in files)
        context['total_views'] = sum(f.view_count for f in files)
        
        # عدد الطلاب
        from apps.accounts.models import Role
        context['students_count'] = User.objects.filter(
            role__code=Role.STUDENT,
            major__in=course.course_majors.values_list('major', flat=True),
            level=course.level,
            account_status='active'
        ).count()
        
        # [جديد] التحقق من حالة AI
        context['ai_available'] = AI_AVAILABLE
        
        return context


class FileUploadView(LoginRequiredMixin, InstructorRequiredMixin, CreateView):
    """
    رفع ملف جديد مع تكامل الذكاء الاصطناعي
    """
    model = LectureFile
    form_class = LectureFileForm
    template_name = 'instructor_panel/files/upload.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'files'
        course_id = self.request.GET.get('course')
        if course_id:
            context['selected_course'] = get_object_or_404(Course, pk=course_id)
        return context
    
    def form_valid(self, form):
        form.instance.uploader = self.request.user
        response = super().form_valid(form)
        file_obj = self.object
        
        # تسجيل النشاط
        UserActivity.objects.create(
            user=self.request.user,
            activity_type='upload',
            description=f'رفع ملف: {file_obj.title}',
            file_id=file_obj.id,
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
        
        # إرسال إشعار للطلاب
        if file_obj.is_visible:
            NotificationManager.create_file_upload_notification(
                file_obj,
                file_obj.course
            )
        
        # [جديد] تشغيل الذكاء الاصطناعي إذا طُلب ذلك
        # ملاحظة: نفترض وجود checkbox في الـ HTML اسمه 'auto_generate_ai'
        if AI_AVAILABLE and self.request.POST.get('auto_generate_ai') == 'on':
            try:
                # إرسال مهمة التلخيص (Async)
                generate_summary_async.delay(file_obj.id)
                messages.info(self.request, 'جاري توليد ملخص ذكي للملف في الخلفية...')
            except Exception as e:
                logger.error(f"Failed to trigger AI summary: {e}")
        
        messages.success(self.request, f'تم رفع الملف "{file_obj.title}" بنجاح.')
        return response
    
    def get_success_url(self):
        return reverse('courses:instructor_course_detail', kwargs={'pk': self.object.course.pk})


class InstructorAIGenerationView(LoginRequiredMixin, InstructorRequiredMixin, View):
    """
    [جديد] View لمعالجة طلبات الذكاء الاصطناعي يدوياً من المدرس
    (توليد ملخص / توليد أسئلة)
    """
    def post(self, request, pk):
        file_obj = get_object_or_404(LectureFile, pk=pk, uploader=request.user, is_deleted=False)
        action = request.POST.get('action') # 'summary' or 'questions'
        
        if not AI_AVAILABLE:
            messages.error(request, 'خدمة الذكاء الاصطناعي غير مفعلة حالياً.')
            return redirect('courses:instructor_course_detail', pk=file_obj.course.pk)

        try:
            if action == 'summary':
                generate_summary_async.delay(file_obj.id)
                messages.success(request, 'تم إرسال طلب توليد الملخص. سيظهر قريباً.')
            
            elif action == 'questions':
                num_questions = int(request.POST.get('num_questions', 5))
                q_type = request.POST.get('question_type', 'mixed')
                generate_questions_async.delay(file_obj.id, question_type=q_type, num_questions=num_questions)
                messages.success(request, 'تم إرسال طلب توليد الأسئلة.')
                
            else:
                messages.warning(request, 'إجراء غير معروف.')
                
        except Exception as e:
            logger.error(f"AI Trigger Error: {e}")
            messages.error(request, 'حدث خطأ أثناء الاتصال بخدمة الذكاء الاصطناعي.')

        return redirect('courses:instructor_course_detail', pk=file_obj.course.pk)


class FileUpdateView(LoginRequiredMixin, InstructorRequiredMixin, UpdateView):
    """تحديث ملف"""
    model = LectureFile
    form_class = LectureFileForm
    template_name = 'instructor_panel/files/edit.html'
    
    def get_queryset(self):
        # المدرس يمكنه تعديل ملفاته فقط
        return LectureFile.objects.filter(uploader=self.request.user, is_deleted=False)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'تم تحديث الملف "{self.object.title}" بنجاح.')
        return response
    
    def get_success_url(self):
        return reverse('courses:instructor_course_detail', kwargs={'pk': self.object.course.pk})


class FileDeleteView(LoginRequiredMixin, InstructorRequiredMixin, View):
    """حذف ملف (Soft Delete)"""
    
    def post(self, request, pk):
        file_obj = get_object_or_404(LectureFile, pk=pk, uploader=request.user, is_deleted=False)
        
        # Soft delete
        file_obj.is_deleted = True
        file_obj.deleted_at = timezone.now()
        file_obj.save()
        
        # تسجيل في سجل التدقيق
        AuditLog.log(
            user=request.user,
            action='delete',
            model_name='LectureFile',
            object_id=file_obj.id,
            object_repr=str(file_obj),
            request=request
        )
        
        messages.success(request, f'تم حذف الملف "{file_obj.title}" بنجاح.')
        return redirect('courses:instructor_course_detail', pk=file_obj.course.pk)


class FileToggleVisibilityView(LoginRequiredMixin, InstructorRequiredMixin, View):
    """تبديل ظهور الملف"""
    
    def post(self, request, pk):
        file_obj = get_object_or_404(LectureFile, pk=pk, uploader=request.user, is_deleted=False)
        
        file_obj.is_visible = not file_obj.is_visible
        file_obj.save()
        
        status = 'مرئي' if file_obj.is_visible else 'مخفي'
        messages.success(request, f'تم تغيير حالة الملف "{file_obj.title}" إلى {status}.')
        
        # إرسال إشعار إذا تم جعل الملف مرئياً
        if file_obj.is_visible:
            NotificationManager.create_file_upload_notification(
                file_obj,
                file_obj.course
            )
        
        return redirect('courses:instructor_course_detail', pk=file_obj.course.pk)
