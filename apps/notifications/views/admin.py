"""
Admin Notification Views - عروض إشعارات الأدمن
S-ACM - Smart Academic Content Management System

هذا الملف يحتوي على Views إشعارات الأدمن:
- إنشاء إشعار عام (لجميع المستخدمين أو فئة معينة)
- عرض قائمة جميع الإشعارات
"""

from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy

from ..models import Notification, NotificationRecipient
from ..forms import NotificationForm
from apps.accounts.views import AdminRequiredMixin


class AdminNotificationCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """
    إنشاء إشعار عام من لوحة تحكم الأدمن.
    
    يتيح للأدمن إرسال إشعار لفئة محددة من المستخدمين:
    - الكل (all)
    - الطلاب فقط (students)
    - المدرسين فقط (instructors)
    
    يستخدم bulk_create لإنشاء سجلات المستلمين بكفاءة.
    """
    model = Notification
    form_class = NotificationForm
    template_name = 'admin_panel/notifications/create.html'
    success_url = reverse_lazy('notifications:admin_list')
    
    def form_valid(self, form):
        """حفظ الإشعار وإنشاء سجلات المستلمين."""
        notification = form.save(commit=False)
        notification.sender = self.request.user
        notification.save()
        
        # تحديد المستلمين حسب الفئة المختارة
        target = form.cleaned_data.get('target')
        
        from apps.accounts.models import User, Role
        
        if target == 'all':
            users = User.objects.filter(account_status='active')
        elif target == 'students':
            users = User.objects.filter(role__code=Role.STUDENT, account_status='active')
        elif target == 'instructors':
            users = User.objects.filter(role__code=Role.INSTRUCTOR, account_status='active')
        else:
            users = User.objects.filter(account_status='active')
        
        # إنشاء سجلات المستلمين بالجملة
        recipients = [
            NotificationRecipient(notification=notification, user=user)
            for user in users
        ]
        NotificationRecipient.objects.bulk_create(recipients)
        
        messages.success(self.request, f'تم إرسال الإشعار إلى {len(recipients)} مستخدم.')
        return redirect(self.success_url)


class AdminNotificationListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """
    قائمة جميع الإشعارات في النظام.
    
    تعرض جميع الإشعارات للأدمن مع إمكانية الترقيم.
    """
    model = Notification
    template_name = 'admin_panel/notifications/list.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        """جلب جميع الإشعارات مرتبة بالأحدث."""
        return Notification.objects.all().order_by('-created_at')
