"""
Student Views - عروض الطلاب
S-ACM - Smart Academic Content Management System

This module contains all student-facing views.
"""

from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView

from ..models import Course, LectureFile
from ..mixins import CourseEnrollmentMixin
from apps.accounts.views import StudentRequiredMixin
from apps.notifications.models import NotificationManager


class StudentDashboardView(LoginRequiredMixin, StudentRequiredMixin, TemplateView):
    """لوحة تحكم الطالب"""
    template_name = 'student_panel/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.request.user
        
        # المقررات الحالية
        context['current_courses'] = Course.objects.get_current_courses_for_student(student)
        
        # المقررات المؤرشفة
        context['archived_courses'] = Course.objects.get_archived_courses_for_student(student)
        
        # الإشعارات غير المقروءة
        context['unread_notifications'] = NotificationManager.get_unread_count(student)
        
        # آخر الملفات المرفوعة
        context['recent_files'] = LectureFile.objects.filter(
            course__in=context['current_courses'],
            is_visible=True,
            is_deleted=False
        ).order_by('-upload_date')[:5]
        
        return context


class StudentCourseListView(LoginRequiredMixin, StudentRequiredMixin, ListView):
    """قائمة مقررات الطالب"""
    template_name = 'student_panel/courses/list.html'
    context_object_name = 'courses'
    
    def get_queryset(self):
        student = self.request.user
        view_type = self.request.GET.get('view', 'current')
        
        if view_type == 'archived':
            return Course.objects.get_archived_courses_for_student(student)
        return Course.objects.get_current_courses_for_student(student)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['view_type'] = self.request.GET.get('view', 'current')
        return context


class StudentCourseDetailView(LoginRequiredMixin, StudentRequiredMixin, CourseEnrollmentMixin, DetailView):
    """تفاصيل المقرر للطالب - مع التحقق من التسجيل"""
    model = Course
    template_name = 'student_panel/courses/detail.html'
    context_object_name = 'course'
    
    def get_object(self, queryset=None):
        """التحقق من صلاحية الوصول للمقرر"""
        course = super().get_object(queryset)
        # التحقق من تسجيل الطالب في المقرر
        self.check_course_access(self.request.user, course)
        return course
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object
        
        # الملفات حسب النوع
        files = course.files.filter(is_visible=True, is_deleted=False)
        context['lectures'] = files.filter(file_type='Lecture')
        context['summaries'] = files.filter(file_type='Summary')
        context['exams'] = files.filter(file_type='Exam')
        context['assignments'] = files.filter(file_type='Assignment')
        context['references'] = files.filter(file_type='Reference')
        context['others'] = files.filter(file_type='Other')
        
        # المدرسين
        context['instructors'] = course.instructor_courses.select_related('instructor')
        
        return context
