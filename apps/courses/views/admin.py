"""
Admin Views - عروض المسؤولين
S-ACM - Smart Academic Content Management System

This module contains all admin-facing views for course management.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.db.models import Q

from ..models import Course, CourseMajor, InstructorCourse
from ..forms import CourseForm, CourseMajorFormSet
from apps.accounts.views import AdminRequiredMixin
from apps.accounts.models import User, Major, Level, Semester
from apps.core.models import AuditLog


class AdminCourseListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """قائمة المقررات للأدمن"""
    model = Course
    template_name = 'admin_panel/courses/list.html'
    context_object_name = 'courses'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Course.objects.select_related('level', 'semester')
        
        # فلترة
        level = self.request.GET.get('level')
        semester = self.request.GET.get('semester')
        search = self.request.GET.get('search')
        
        if level:
            queryset = queryset.filter(level_id=level)
        if semester:
            queryset = queryset.filter(semester_id=semester)
        if search:
            queryset = queryset.filter(
                Q(course_name__icontains=search) |
                Q(course_code__icontains=search)
            )
        
        return queryset.order_by('course_code')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['levels'] = Level.objects.all()
        context['semesters'] = Semester.objects.all()
        return context


class AdminCourseCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """إنشاء مقرر جديد"""
    model = Course
    form_class = CourseForm
    template_name = 'admin_panel/courses/create.html'
    success_url = reverse_lazy('courses:admin_course_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        AuditLog.log(
            user=self.request.user,
            action='create',
            model_name='Course',
            object_id=self.object.id,
            object_repr=str(self.object),
            request=self.request
        )
        
        messages.success(self.request, f'تم إنشاء المقرر "{self.object.course_name}" بنجاح.')
        return response


class AdminCourseUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    """تحديث مقرر"""
    model = Course
    form_class = CourseForm
    template_name = 'admin_panel/courses/edit.html'
    success_url = reverse_lazy('courses:admin_course_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        AuditLog.log(
            user=self.request.user,
            action='update',
            model_name='Course',
            object_id=self.object.id,
            object_repr=str(self.object),
            request=self.request
        )
        
        messages.success(self.request, f'تم تحديث المقرر "{self.object.course_name}" بنجاح.')
        return response


class AdminCourseDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    """تفاصيل المقرر للأدمن"""
    model = Course
    template_name = 'admin_panel/courses/detail.html'
    context_object_name = 'course'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object
        
        context['files'] = course.files.filter(is_deleted=False)
        context['instructors'] = course.instructor_courses.select_related('instructor')
        context['majors'] = course.course_majors.select_related('major')
        
        # عدد الطلاب
        from apps.accounts.models import Role
        context['students_count'] = User.objects.filter(
            role__code=Role.STUDENT,
            major__in=course.course_majors.values_list('major', flat=True),
            level=course.level,
            account_status='active'
        ).count()
        
        return context


class AdminInstructorAssignView(LoginRequiredMixin, AdminRequiredMixin, View):
    """تعيين مدرس لمقرر"""
    template_name = 'admin_panel/courses/assign_instructor.html'
    
    def get(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        from apps.accounts.models import Role
        instructors = User.objects.filter(role__code=Role.INSTRUCTOR, account_status='active')
        assigned = course.instructor_courses.values_list('instructor_id', flat=True)
        
        context = {
            'course': course,
            'instructors': instructors,
            'assigned': list(assigned)
        }
        return render(request, self.template_name, context)
    
    def post(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        instructor_ids = request.POST.getlist('instructors')
        
        # حذف التعيينات القديمة
        InstructorCourse.objects.filter(course=course).delete()
        
        # إنشاء التعيينات الجديدة
        for idx, instructor_id in enumerate(instructor_ids):
            InstructorCourse.objects.create(
                course=course,
                instructor_id=instructor_id,
                is_primary=(idx == 0)  # الأول هو الرئيسي
            )
        
        AuditLog.log(
            user=request.user,
            action='update',
            model_name='InstructorCourse',
            object_id=course.id,
            object_repr=f'تعيين مدرسين لـ {course}',
            changes={'instructors': instructor_ids},
            request=request
        )
        
        messages.success(request, f'تم تحديث المدرسين للمقرر "{course.course_name}" بنجاح.')
        return redirect('courses:admin_course_detail', pk=course.pk)


class AdminCourseMajorView(LoginRequiredMixin, AdminRequiredMixin, View):
    """ربط المقرر بالتخصصات"""
    template_name = 'admin_panel/courses/assign_majors.html'
    
    def get(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        majors = Major.objects.filter(is_active=True)
        assigned = course.course_majors.values_list('major_id', flat=True)
        
        context = {
            'course': course,
            'majors': majors,
            'assigned': list(assigned)
        }
        return render(request, self.template_name, context)
    
    def post(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        major_ids = request.POST.getlist('majors')
        
        # حذف الربط القديم
        CourseMajor.objects.filter(course=course).delete()
        
        # إنشاء الربط الجديد
        for major_id in major_ids:
            CourseMajor.objects.create(course=course, major_id=major_id)
        
        AuditLog.log(
            user=request.user,
            action='update',
            model_name='CourseMajor',
            object_id=course.id,
            object_repr=f'ربط تخصصات لـ {course}',
            changes={'majors': major_ids},
            request=request
        )
        
        messages.success(request, f'تم تحديث التخصصات للمقرر "{course.course_name}" بنجاح.')
        return redirect('courses:admin_course_detail', pk=course.pk)
