"""
Common Notification Views - العمليات المشتركة لجميع المستخدمين
S-ACM - Smart Academic Content Management System

Views:
- NotificationListView: قائمة الإشعارات (غير مقروءة، الكل، الأرشيف)
- NotificationDetailView: تفاصيل إشعار + تحديد كمقروء + انتقال ذكي
- NotificationTrashView: سلة المهملات
- MarkAsReadView / MarkAllAsReadView
- DeleteNotificationView / RestoreNotificationView / EmptyTrashView
- ArchiveNotificationView
- UnreadCountView: API لتحديث Bell عبر HTMX
- PreferencesView: إعدادات تفضيلات الإشعارات
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from django.views.generic import ListView
from django.http import JsonResponse, HttpResponse
from django.utils import timezone

from ..models import Notification, NotificationRecipient, NotificationPreference
from ..services import NotificationService
from ..forms import NotificationPreferenceForm


class NotificationListView(LoginRequiredMixin, ListView):
    """
    قائمة إشعارات المستخدم مع فلاتر (غير مقروءة، الكل، الأرشيف)
    """
    template_name = 'notifications/list.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        filter_type = self.request.GET.get('filter', 'all')
        return NotificationService.get_user_notifications(
            self.request.user,
            filter_type=filter_type,
            include_read=True,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unread_count'] = NotificationService.get_unread_count(self.request.user)
        context['active_filter'] = self.request.GET.get('filter', 'all')
        context['active_page'] = 'notifications'
        context['trash_count'] = NotificationRecipient.objects.filter(
            user=self.request.user, is_deleted=True
        ).count()
        return context


class NotificationDetailView(LoginRequiredMixin, View):
    """
    تفاصيل إشعار - يحدد كمقروء تلقائياً
    إذا كان الإشعار مرتبطاً بكائن (ملف، مقرر) يتم الانتقال إليه
    """
    template_name = 'notifications/detail.html'

    def get(self, request, pk):
        recipient = get_object_or_404(
            NotificationRecipient.objects.select_related(
                'notification', 'notification__sender',
                'notification__course', 'notification__content_type',
            ),
            notification_id=pk,
            user=request.user,
            is_deleted=False,
        )

        # تحديد كمقروء
        recipient.mark_as_read()

        # محاولة الحصول على رابط الكائن المرتبط
        related_url = recipient.notification.get_related_url()

        return render(request, self.template_name, {
            'notification': recipient.notification,
            'recipient': recipient,
            'related_url': related_url,
            'active_page': 'notifications',
        })


class NotificationTrashView(LoginRequiredMixin, ListView):
    """
    سلة المهملات - الإشعارات المحذوفة (ناعمياً)
    """
    template_name = 'notifications/trash.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        return NotificationService.get_user_notifications(
            self.request.user,
            filter_type='trash',
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'notifications'
        return context


class MarkAsReadView(LoginRequiredMixin, View):
    """تحديد إشعار كمقروء (يدعم AJAX/HTMX)"""

    def post(self, request, pk):
        NotificationService.mark_as_read(pk, request.user)

        if request.headers.get('HX-Request'):
            return HttpResponse(status=204)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})

        return redirect('notifications:list')


class MarkAllAsReadView(LoginRequiredMixin, View):
    """تحديد جميع الإشعارات كمقروءة"""

    def post(self, request):
        count = NotificationService.mark_all_as_read(request.user)

        if request.headers.get('HX-Request'):
            return HttpResponse(status=204, headers={
                'HX-Trigger': 'notificationsUpdated'
            })
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'count': count})

        messages.success(request, 'تم تحديد جميع الإشعارات كمقروءة.')
        return redirect('notifications:list')


class DeleteNotificationView(LoginRequiredMixin, View):
    """حذف ناعم - نقل إلى سلة المهملات"""

    def post(self, request, pk):
        NotificationService.soft_delete(pk, request.user)

        if request.headers.get('HX-Request'):
            return HttpResponse(status=204, headers={
                'HX-Trigger': 'notificationsUpdated'
            })
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})

        messages.success(request, 'تم نقل الإشعار إلى سلة المهملات.')
        return redirect('notifications:list')


class RestoreNotificationView(LoginRequiredMixin, View):
    """استعادة إشعار من سلة المهملات"""

    def post(self, request, pk):
        NotificationService.restore_from_trash(pk, request.user)

        if request.headers.get('HX-Request'):
            return HttpResponse(status=204, headers={
                'HX-Trigger': 'notificationsUpdated'
            })

        messages.success(request, 'تم استعادة الإشعار.')
        return redirect('notifications:trash')


class EmptyTrashView(LoginRequiredMixin, View):
    """إفراغ سلة المهملات"""

    def post(self, request):
        NotificationService.empty_trash(request.user)

        if request.headers.get('HX-Request'):
            return HttpResponse(status=204, headers={
                'HX-Trigger': 'notificationsUpdated'
            })

        messages.success(request, 'تم إفراغ سلة المهملات.')
        return redirect('notifications:trash')


class ArchiveNotificationView(LoginRequiredMixin, View):
    """أرشفة إشعار"""

    def post(self, request, pk):
        NotificationService.archive_notification(pk, request.user)

        if request.headers.get('HX-Request'):
            return HttpResponse(status=204, headers={
                'HX-Trigger': 'notificationsUpdated'
            })

        messages.success(request, 'تم أرشفة الإشعار.')
        return redirect('notifications:list')


class UnreadCountView(LoginRequiredMixin, View):
    """
    API: عدد الإشعارات غير المقروءة
    يُستخدم مع HTMX polling لتحديث Bell Icon
    """

    def get(self, request):
        count = NotificationService.get_unread_count(request.user)
        return JsonResponse({'count': count})


class PreferencesView(LoginRequiredMixin, View):
    """إعدادات تفضيلات الإشعارات"""
    template_name = 'notifications/preferences.html'

    def get(self, request):
        prefs = NotificationPreference.get_or_create_for_user(request.user)
        form = NotificationPreferenceForm(instance=prefs)
        return render(request, self.template_name, {
            'form': form,
            'active_page': 'notifications',
        })

    def post(self, request):
        prefs = NotificationPreference.get_or_create_for_user(request.user)
        form = NotificationPreferenceForm(request.POST, instance=prefs)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم حفظ تفضيلات الإشعارات.')
            return redirect('notifications:preferences')
        return render(request, self.template_name, {
            'form': form,
            'active_page': 'notifications',
        })
