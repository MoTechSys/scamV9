"""
Instructor Notification Views - عروض إشعارات المدرس
S-ACM - Smart Academic Content Management System

هذا الملف يحتوي على Views إشعارات المدرس:
- إنشاء إشعار لمقرر معين
- عرض قائمة الإشعارات المرسلة
"""

from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView

from ..models import Notification, NotificationManager
from ..forms import CourseNotificationForm
from apps.accounts.views import InstructorRequiredMixin


class InstructorNotificationCreateView(LoginRequiredMixin, InstructorRequiredMixin, CreateView):
    """
    إنشاء إشعار جديد لمقرر معين.
    
    يتيح للمدرس إرسال إشعار لجميع طلاب المقرر المعيّن له.
    
    المتطلبات:
        - يجب أن يكون المدرس معيّناً للمقرر
    """
    model = Notification
    form_class = CourseNotificationForm
    template_name = 'notifications/instructor_create.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'notifications'
        return context
    
    def get_form_kwargs(self):
        """تمرير المستخدم للـ Form لتحديد المقررات المتاحة."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        """إنشاء الإشعار وإرساله لطلاب المقرر."""
        course = form.cleaned_data['course']
        title = form.cleaned_data['title']
        body = form.cleaned_data['body']
        
        notification = NotificationManager.create_course_notification(
            sender=self.request.user,
            course=course,
            title=title,
            body=body
        )
        
        messages.success(self.request, 'تم إرسال الإشعار بنجاح.')
        return redirect('instructor:course_detail', pk=course.pk)


class InstructorNotificationListView(LoginRequiredMixin, InstructorRequiredMixin, ListView):
    """
    قائمة الإشعارات المرسلة من المدرس.
    
    تعرض جميع الإشعارات التي أنشأها المدرس الحالي.
    """
    template_name = 'notifications/instructor_sent.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'notifications'
        return context
    
    def get_queryset(self):
        """جلب الإشعارات المرسلة من المدرس الحالي."""
        return Notification.objects.filter(
            sender=self.request.user
        ).order_by('-created_at')
