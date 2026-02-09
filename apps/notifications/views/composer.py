"""
Composer Views - واجهة إنشاء وإرسال الإشعارات
S-ACM - Smart Academic Content Management System

Views:
- ComposerView: إنشاء إشعار جديد (للدكتور والأدمن)
- SentNotificationsView: قائمة الإشعارات المرسلة
"""

from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from django.views.generic import ListView

from ..models import Notification
from ..services import NotificationService
from ..forms import ComposerForm
from apps.accounts.views import AdminRequiredMixin, InstructorRequiredMixin


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
            return redirect('notifications:list')

        form = ComposerForm(
            user=request.user,
            is_admin=request.user.is_admin(),
        )
        return render(request, self.template_name, {
            'form': form,
            'active_page': 'notification_create',
        })

    def post(self, request):
        if not self._check_permission(request):
            messages.error(request, 'ليس لديك صلاحية لإرسال إشعارات.')
            return redirect('notifications:list')

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
                    'active_page': 'notification_create',
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
            return redirect('notifications:sent')

        return render(request, self.template_name, {
            'form': form,
            'active_page': 'notification_create',
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
        context['active_page'] = 'notification_sent'
        return context
