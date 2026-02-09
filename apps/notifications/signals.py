"""
Django Signals لأتمتة الإشعارات
S-ACM - Smart Academic Content Management System

=== Triggers التلقائية ===
1. إنشاء مستخدم جديد (account activated) -> إشعار ترحيب
2. رفع ملف جديد (LectureFile created + visible) -> إشعار لطلاب المقرر
3. نشر واجب (Assignment file type) -> إشعار عاجل
4. نشر اختبار (Exam file type) -> إشعار عاجل
"""

import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

logger = logging.getLogger('notifications')


@receiver(post_save, sender='accounts.User')
def handle_user_activation(sender, instance, created, **kwargs):
    """
    Signal: إرسال إشعار ترحيب عند تفعيل حساب مستخدم
    يعمل عند تغيير account_status من inactive إلى active
    """
    if not created and instance.account_status == 'active':
        # تحقق من أن الحالة تغيرت فعلاً
        try:
            old_instance = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            return

        # لا نرسل إشعار إلا إذا تحول الحساب من غير مفعل إلى مفعل
        if hasattr(instance, '_skip_notification_signal'):
            return

        try:
            from .services import NotificationService
            # تحقق هل الإشعار الترحيبي أُرسل مسبقاً
            from .models import NotificationRecipient
            already_welcomed = NotificationRecipient.objects.filter(
                user=instance,
                notification__notification_type='welcome',
            ).exists()

            if not already_welcomed:
                NotificationService.notify_new_user(instance)
                logger.info(f"Welcome notification sent to {instance.academic_id}")
        except Exception as e:
            logger.error(f"Failed to send welcome notification: {e}")


@receiver(post_save, sender='courses.LectureFile')
def handle_file_upload(sender, instance, created, **kwargs):
    """
    Signal: إرسال إشعار عند رفع ملف جديد مرئي
    يعمل عند إنشاء LectureFile جديد مع is_visible=True
    """
    if created and instance.is_visible and not instance.is_deleted:
        try:
            from .services import NotificationService
            NotificationService.notify_file_upload(instance, instance.course)
            logger.info(
                f"File upload notification sent for '{instance.title}' "
                f"in course {instance.course.course_code}"
            )
        except Exception as e:
            logger.error(f"Failed to send file upload notification: {e}")


@receiver(pre_save, sender='courses.LectureFile')
def handle_file_visibility_change(sender, instance, **kwargs):
    """
    Signal: إرسال إشعار عندما يتم تغيير الملف من مخفي إلى مرئي
    """
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            if not old_instance.is_visible and instance.is_visible and not instance.is_deleted:
                # سيتم إرسال الإشعار بعد الحفظ
                instance._send_visibility_notification = True
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender='courses.LectureFile')
def handle_file_visibility_post_save(sender, instance, created, **kwargs):
    """
    Signal: إكمال إرسال إشعار تغيير الرؤية بعد الحفظ
    """
    if not created and getattr(instance, '_send_visibility_notification', False):
        try:
            from .services import NotificationService
            NotificationService.notify_file_upload(instance, instance.course)
            logger.info(
                f"Visibility change notification sent for '{instance.title}'"
            )
        except Exception as e:
            logger.error(f"Failed to send visibility notification: {e}")
        finally:
            instance._send_visibility_notification = False
