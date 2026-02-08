"""
Common Notification Views - العمليات المشتركة للإشعارات
S-ACM - Smart Academic Content Management System

هذا الملف يحتوي على Views مشتركة لجميع المستخدمين:
- عرض قائمة الإشعارات
- عرض تفاصيل الإشعار
- تحديد كمقروء / حذف
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from django.views.generic import ListView
from django.http import JsonResponse
from django.utils import timezone

from ..models import Notification, NotificationRecipient, NotificationManager


class NotificationListView(LoginRequiredMixin, ListView):
    """
    قائمة إشعارات المستخدم الحالي.
    
    تعرض جميع الإشعارات (المقروءة وغير المقروءة) مع إمكانية الترقيم.
    
    السياق (Context):
        - notifications: قائمة الإشعارات
        - unread_count: عدد الإشعارات غير المقروءة
    """
    template_name = 'notifications/list.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        """جلب جميع إشعارات المستخدم."""
        return NotificationManager.get_user_notifications(
            self.request.user,
            include_read=True
        )
    
    def get_context_data(self, **kwargs):
        """إضافة عدد الإشعارات غير المقروءة."""
        context = super().get_context_data(**kwargs)
        context['unread_count'] = NotificationManager.get_unread_count(self.request.user)
        return context


class NotificationDetailView(LoginRequiredMixin, View):
    """
    عرض تفاصيل إشعار محدد.
    
    عند فتح الإشعار، يتم تحديده كمقروء تلقائياً.
    """
    template_name = 'notifications/detail.html'
    
    def get(self, request, pk):
        """عرض الإشعار وتحديده كمقروء."""
        recipient = get_object_or_404(
            NotificationRecipient,
            notification_id=pk,
            user=request.user,
            is_deleted=False
        )
        
        # تحديد كمقروء
        recipient.mark_as_read()
        
        return render(request, self.template_name, {
            'notification': recipient.notification,
            'recipient': recipient
        })


class MarkAsReadView(LoginRequiredMixin, View):
    """
    تحديد إشعار واحد كمقروء.
    
    يدعم طلبات AJAX ويُرجع JSON في هذه الحالة.
    """
    
    def post(self, request, pk):
        """تحديد الإشعار كمقروء."""
        recipient = get_object_or_404(
            NotificationRecipient,
            notification_id=pk,
            user=request.user
        )
        recipient.mark_as_read()
        
        # دعم AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        return redirect('notifications:list')


class MarkAllAsReadView(LoginRequiredMixin, View):
    """
    تحديد جميع إشعارات المستخدم كمقروءة.
    
    عملية جماعية تستخدم update() للأداء المحسّن.
    """
    
    def post(self, request):
        """تحديد الكل كمقروء."""
        NotificationRecipient.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
        
        # دعم AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        messages.success(request, 'تم تحديد جميع الإشعارات كمقروءة.')
        return redirect('notifications:list')


class DeleteNotificationView(LoginRequiredMixin, View):
    """
    حذف إشعار من قائمة المستخدم (Soft Delete).
    
    لا يحذف الإشعار الأصلي، فقط يخفيه من قائمة المستخدم.
    """
    
    def post(self, request, pk):
        """حذف الإشعار (إخفاء)."""
        recipient = get_object_or_404(
            NotificationRecipient,
            notification_id=pk,
            user=request.user
        )
        recipient.is_deleted = True
        recipient.save(update_fields=['is_deleted'])
        
        # دعم AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        messages.success(request, 'تم حذف الإشعار.')
        return redirect('notifications:list')


class UnreadCountView(LoginRequiredMixin, View):
    """
    API للحصول على عدد الإشعارات غير المقروءة.
    
    يُستخدم مع AJAX لتحديث العداد في الـ Navbar.
    
    الاستجابة:
        {"count": N}
    """
    
    def get(self, request):
        """إرجاع عدد الإشعارات غير المقروءة."""
        count = NotificationManager.get_unread_count(request.user)
        return JsonResponse({'count': count})
