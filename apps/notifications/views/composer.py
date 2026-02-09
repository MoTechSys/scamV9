"""
Composer Views - واجهة إنشاء وإرسال الإشعارات v3
S-ACM - Smart Academic Content Management System

Views:
- ComposerView: إنشاء إشعار جديد (للدكتور والأدمن)
- SentNotificationsView: قائمة الإشعارات المرسلة
- HideSentNotificationView: إخفاء إشعار مرسل
- UnhideSentNotificationView: إظهار إشعار مرسل
- DeleteSentNotificationView: حذف إشعار مرسل (سلة المهملات)
- RestoreSentNotificationView: استعادة إشعار مرسل من سلة المهملات
"""

from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from django.views.generic import ListView
from django.http import HttpResponse

from ..models import Notification
from ..services import NotificationService
from ..forms import ComposerForm


class ComposerView(LoginRequiredMixin, View):
    """
    Composer View - إنشاء وإرسال إشعار جديد
    متاح للدكاترة والأدمن
    يدعم الاستهداف الذكي عبر HTMX
    """
    template_name = 'notifications/composer.html'

    def _check_permission(self, request):
        """التحقق من صلاحية المستخدم (Admin أو Instructor)"""
        user = request.user
        return user.is_admin() or user.is_instructor()

    def get(self, request):
        if not self._check_permission(request):
            messages.error(request, 'ليس لديك صلاحية لإرسال إشعارات.')
            return redirect('notifications:management')

        form = ComposerForm(
            user=request.user,
            is_admin=request.user.is_admin(),
        )
        return render(request, self.template_name, {
            'form': form,
            'active_page': 'notifications',
            'active_section': 'compose',
        })

    def post(self, request):
        if not self._check_permission(request):
            messages.error(request, 'ليس لديك صلاحية لإرسال إشعارات.')
            return redirect('notifications:management')

        form = ComposerForm(
            request.POST,
            user=request.user,
            is_admin=request.user.is_admin(),
        )

        if form.is_valid():
            data = form.cleaned_data
            target_type = data['target_type']

            # الحصول على المستلمين
            recipients = NotificationService.get_targeted_users(
                target_type=target_type,
                major=data.get('major'),
                level=data.get('level'),
                course=data.get('course'),
                specific_user_id=data.get('specific_user_id'),
            )

            if not recipients.exists():
                messages.warning(request, 'لم يتم العثور على مستلمين بناءً على الفلاتر المحددة.')
                return render(request, self.template_name, {
                    'form': form,
                    'active_page': 'notifications',
                    'active_section': 'compose',
                })

            # إنشاء الإشعار
            notification = NotificationService.create_notification(
                title=data['title'],
                body=data['body'],
                notification_type=data['notification_type'],
                priority=data['priority'],
                sender=request.user,
                course=data.get('course'),
                recipients=recipients,
            )

            recipient_count = recipients.count()
            messages.success(
                request,
                f'تم إرسال الإشعار "{data["title"]}" إلى {recipient_count} مستلم.'
            )
            return redirect('notifications:management')

        return render(request, self.template_name, {
            'form': form,
            'active_page': 'notifications',
            'active_section': 'compose',
        })


class SentNotificationsView(LoginRequiredMixin, ListView):
    """
    قائمة الإشعارات المرسلة من المستخدم الحالي
    متاح للدكاترة والأدمن
    """
    template_name = 'notifications/sent.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        return NotificationService.get_sent_notifications(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'notifications'
        context['active_section'] = 'sent'
        return context


class HideSentNotificationView(LoginRequiredMixin, View):
    """إخفاء إشعار مرسل"""

    def post(self, request, pk):
        NotificationService.hide_sent_notification(pk, request.user)

        if request.headers.get('HX-Request'):
            return HttpResponse(status=204, headers={
                'HX-Trigger': 'notificationsUpdated'
            })

        messages.success(request, 'تم إخفاء الإشعار.')
        return redirect('notifications:management')


class UnhideSentNotificationView(LoginRequiredMixin, View):
    """إظهار إشعار مرسل"""

    def post(self, request, pk):
        NotificationService.unhide_sent_notification(pk, request.user)

        if request.headers.get('HX-Request'):
            return HttpResponse(status=204, headers={
                'HX-Trigger': 'notificationsUpdated'
            })

        messages.success(request, 'تم إظهار الإشعار.')
        return redirect('notifications:management')


class DeleteSentNotificationView(LoginRequiredMixin, View):
    """حذف إشعار مرسل - نقل إلى سلة المهملات"""

    def post(self, request, pk):
        NotificationService.soft_delete_sent(pk, request.user)

        if request.headers.get('HX-Request'):
            return HttpResponse(status=204, headers={
                'HX-Trigger': 'notificationsUpdated'
            })

        messages.success(request, 'تم نقل الإشعار المرسل إلى سلة المهملات.')
        return redirect('notifications:management')


class RestoreSentNotificationView(LoginRequiredMixin, View):
    """استعادة إشعار مرسل من سلة المهملات"""

    def post(self, request, pk):
        NotificationService.restore_sent_from_trash(pk, request.user)

        if request.headers.get('HX-Request'):
            return HttpResponse(status=204, headers={
                'HX-Trigger': 'notificationsUpdated'
            })

        messages.success(request, 'تم استعادة الإشعار المرسل.')
        return redirect('notifications:management')
