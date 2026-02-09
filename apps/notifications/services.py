"""
خدمات نظام الإشعارات v2 - Service Layer
S-ACM - Smart Academic Content Management System

=== Architecture ===
NotificationService: الخدمة المركزية لإنشاء وإدارة الإشعارات
- إنشاء إشعارات مع bulk_create للأداء
- منطق الاستهداف الذكي (Smart Targeting)
- دعم GenericForeignKey
- دعم فلاتر ديناميكية (التخصص -> المستوى)
"""

import logging
from django.db import transaction
from django.db.models import Q, Count
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from .models import Notification, NotificationRecipient, NotificationPreference

logger = logging.getLogger('notifications')


class NotificationService:
    """
    الخدمة المركزية لنظام الإشعارات
    كل العمليات تمر من هنا - Single Source of Truth
    """

    # ============================================================
    # 1) إنشاء الإشعارات
    # ============================================================

    @classmethod
    @transaction.atomic
    def create_notification(cls, title, body, notification_type='general',
                            priority='normal', sender=None, course=None,
                            related_object=None, recipients=None,
                            expires_at=None):
        """
        إنشاء إشعار جديد وتوزيعه على المستلمين

        Args:
            title: عنوان الإشعار
            body: محتوى الإشعار
            notification_type: نوع الإشعار
            priority: الأولوية
            sender: المرسل (User أو None للنظام)
            course: المقرر المرتبط (اختياري)
            related_object: الكائن المرتبط (أي Django Model)
            recipients: QuerySet أو list من المستخدمين المستلمين
            expires_at: تاريخ انتهاء الصلاحية

        Returns:
            Notification: الإشعار المنشأ
        """
        # بناء حقول GenericForeignKey
        content_type = None
        object_id = None
        if related_object is not None:
            content_type = ContentType.objects.get_for_model(related_object)
            object_id = related_object.pk

        notification = Notification.objects.create(
            sender=sender,
            title=title,
            body=body,
            notification_type=notification_type,
            priority=priority,
            course=course,
            content_type=content_type,
            object_id=object_id,
            expires_at=expires_at,
            is_active=True,
        )

        # إنشاء سجلات المستلمين بالجملة
        if recipients:
            recipient_objects = [
                NotificationRecipient(notification=notification, user=user)
                for user in recipients
            ]
            if recipient_objects:
                NotificationRecipient.objects.bulk_create(
                    recipient_objects,
                    ignore_conflicts=True  # تجنب الأخطاء عند التكرار
                )

        logger.info(
            f"Notification created: '{title}' type={notification_type} "
            f"recipients={len(recipient_objects) if recipients else 0}"
        )

        return notification

    # ============================================================
    # 2) إشعارات تلقائية (Triggers)
    # ============================================================

    @classmethod
    def notify_file_upload(cls, file_obj, course):
        """
        إشعار رفع ملف جديد -> جميع طلاب المقرر
        """
        from apps.accounts.models import User, Role

        students = User.objects.filter(
            role__code=Role.STUDENT,
            major__in=course.course_majors.values_list('major', flat=True),
            level=course.level,
            account_status='active',
        )

        return cls.create_notification(
            title=f"ملف جديد في {course.course_name}",
            body=f"تم رفع ملف جديد: {file_obj.title}",
            notification_type='file_upload',
            priority='normal',
            sender=file_obj.uploader,
            course=course,
            related_object=file_obj,
            recipients=students,
        )

    @classmethod
    def notify_new_user(cls, user):
        """
        إشعار ترحيب بمستخدم جديد
        """
        return cls.create_notification(
            title="مرحباً بك في S-ACM!",
            body=f"أهلاً {user.full_name}، تم تفعيل حسابك بنجاح. "
                 f"يمكنك الآن استخدام جميع خدمات النظام.",
            notification_type='welcome',
            priority='normal',
            sender=None,
            recipients=[user],
        )

    @classmethod
    def notify_assignment(cls, assignment_obj, course, sender):
        """
        إشعار واجب جديد -> طلاب المقرر
        """
        from apps.accounts.models import User, Role

        students = User.objects.filter(
            role__code=Role.STUDENT,
            major__in=course.course_majors.values_list('major', flat=True),
            level=course.level,
            account_status='active',
        )

        return cls.create_notification(
            title=f"واجب جديد في {course.course_name}",
            body=f"تم نشر واجب جديد: {assignment_obj.title}",
            notification_type='assignment',
            priority='high',
            sender=sender,
            course=course,
            related_object=assignment_obj,
            recipients=students,
        )

    @classmethod
    def notify_exam(cls, exam_obj, course, sender):
        """
        إشعار اختبار -> طلاب المقرر
        """
        from apps.accounts.models import User, Role

        students = User.objects.filter(
            role__code=Role.STUDENT,
            major__in=course.course_majors.values_list('major', flat=True),
            level=course.level,
            account_status='active',
        )

        return cls.create_notification(
            title=f"اختبار في {course.course_name}",
            body=f"تم نشر اختبار جديد: {exam_obj.title}",
            notification_type='exam',
            priority='urgent',
            sender=sender,
            course=course,
            related_object=exam_obj,
            recipients=students,
        )

    @classmethod
    def notify_grade(cls, student, course, message, sender=None):
        """
        إشعار درجة -> طالب محدد
        """
        return cls.create_notification(
            title=f"درجة جديدة في {course.course_name}",
            body=message,
            notification_type='grade',
            priority='high',
            sender=sender,
            course=course,
            recipients=[student],
        )

    @classmethod
    def notify_system(cls, title, body, users=None):
        """
        إشعار نظام -> جميع المستخدمين أو مجموعة محددة
        """
        from apps.accounts.models import User

        if users is None:
            users = User.objects.filter(account_status='active')

        return cls.create_notification(
            title=title,
            body=body,
            notification_type='system',
            priority='high',
            sender=None,
            recipients=users,
        )

    # ============================================================
    # 3) منطق الاستهداف الذكي (Smart Targeting)
    # ============================================================

    @classmethod
    def get_targeted_users(cls, target_type, major=None, level=None,
                           course=None, specific_user_id=None):
        """
        الحصول على المستخدمين المستهدفين بناءً على الفلاتر

        Args:
            target_type: نوع الاستهداف
                - 'all_students': جميع الطلاب
                - 'all_instructors': جميع المدرسين
                - 'everyone': الجميع
                - 'course_students': طلاب مقرر محدد
                - 'major_students': طلاب تخصص محدد
                - 'specific_student': طالب محدد
                - 'specific_instructor': مدرس محدد
            major: التخصص (اختياري)
            level: المستوى (اختياري)
            course: المقرر (اختياري)
            specific_user_id: معرف مستخدم محدد

        Returns:
            QuerySet: المستخدمين المستهدفين
        """
        from apps.accounts.models import User, Role

        base_qs = User.objects.filter(account_status='active')

        if target_type == 'everyone':
            return base_qs

        elif target_type == 'all_students':
            qs = base_qs.filter(role__code=Role.STUDENT)
            if major:
                qs = qs.filter(major=major)
            if level:
                qs = qs.filter(level=level)
            return qs

        elif target_type == 'all_instructors':
            return base_qs.filter(role__code=Role.INSTRUCTOR)

        elif target_type == 'course_students':
            if not course:
                return User.objects.none()
            return base_qs.filter(
                role__code=Role.STUDENT,
                major__in=course.course_majors.values_list('major', flat=True),
                level=course.level,
            )

        elif target_type == 'major_students':
            if not major:
                return User.objects.none()
            qs = base_qs.filter(role__code=Role.STUDENT, major=major)
            if level:
                qs = qs.filter(level=level)
            return qs

        elif target_type == 'specific_student':
            if not specific_user_id:
                return User.objects.none()
            return base_qs.filter(
                pk=specific_user_id,
                role__code=Role.STUDENT,
            )

        elif target_type == 'specific_instructor':
            if not specific_user_id:
                return User.objects.none()
            return base_qs.filter(
                pk=specific_user_id,
                role__code=Role.INSTRUCTOR,
            )

        elif target_type == 'major_instructors':
            if not major:
                return User.objects.none()
            # الدكاترة الذين يدرّسون مقررات في هذا التخصص
            from apps.courses.models import Course
            course_ids = Course.objects.filter(
                course_majors__major=major,
                is_active=True,
            ).values_list('pk', flat=True)
            instructor_ids = Course.objects.filter(
                pk__in=course_ids,
            ).values_list('instructor_courses__instructor', flat=True).distinct()
            return base_qs.filter(
                pk__in=instructor_ids,
                role__code=Role.INSTRUCTOR,
            )

        return User.objects.none()

    # ============================================================
    # 4) استعلامات القراءة
    # ============================================================

    @classmethod
    def get_unread_count(cls, user):
        """عدد الإشعارات غير المقروءة"""
        return NotificationRecipient.objects.filter(
            user=user,
            is_read=False,
            is_deleted=False,
            notification__is_active=True,
        ).count()

    @classmethod
    def get_user_notifications(cls, user, filter_type='all',
                               include_read=True, limit=None):
        """
        جلب إشعارات المستخدم مع فلاتر

        Args:
            user: المستخدم
            filter_type: 'all', 'unread', 'archived', 'trash'
            include_read: تضمين المقروءة
            limit: الحد الأقصى

        Returns:
            QuerySet
        """
        qs = NotificationRecipient.objects.filter(
            user=user,
            notification__is_active=True,
        ).select_related(
            'notification',
            'notification__sender',
            'notification__course',
            'notification__content_type',
        )

        if filter_type == 'unread':
            qs = qs.filter(is_read=False, is_deleted=False, is_archived=False)
        elif filter_type == 'archived':
            qs = qs.filter(is_archived=True, is_deleted=False)
        elif filter_type == 'trash':
            qs = qs.filter(is_deleted=True)
        else:
            # all = غير محذوفة وغير مؤرشفة
            qs = qs.filter(is_deleted=False, is_archived=False)
            if not include_read:
                qs = qs.filter(is_read=False)

        qs = qs.order_by('-notification__created_at')

        if limit:
            qs = qs[:limit]

        return qs

    @classmethod
    def get_recent_notifications(cls, user, limit=5):
        """آخر 5 إشعارات غير مقروءة للـ Navbar dropdown"""
        return cls.get_user_notifications(
            user, filter_type='unread', limit=limit
        )

    @classmethod
    def get_sent_notifications(cls, user, include_hidden=False):
        """جلب الإشعارات المرسلة من المستخدم"""
        qs = Notification.objects.filter(
            sender=user,
            is_deleted_by_sender=False,
        )
        if not include_hidden:
            qs = qs.filter(is_hidden_by_sender=False)
        return qs.annotate(
            recipients_count=Count('recipients'),
            read_count=Count('recipients', filter=Q(recipients__is_read=True)),
        ).order_by('-created_at')

    @classmethod
    def get_sender_trash(cls, user):
        """جلب الإشعارات المرسلة المحذوفة (في سلة المهملات)"""
        return Notification.objects.filter(
            sender=user,
            is_deleted_by_sender=True,
        ).annotate(
            recipients_count=Count('recipients'),
            read_count=Count('recipients', filter=Q(recipients__is_read=True)),
        ).order_by('-sender_deleted_at')

    @classmethod
    def hide_sent_notification(cls, notification_id, user):
        """إخفاء إشعار مرسل من القائمة"""
        try:
            notification = Notification.objects.get(pk=notification_id, sender=user)
            notification.is_hidden_by_sender = True
            notification.save(update_fields=['is_hidden_by_sender'])
            return True
        except Notification.DoesNotExist:
            return False

    @classmethod
    def unhide_sent_notification(cls, notification_id, user):
        """إظهار إشعار مرسل مخفي"""
        try:
            notification = Notification.objects.get(pk=notification_id, sender=user)
            notification.is_hidden_by_sender = False
            notification.save(update_fields=['is_hidden_by_sender'])
            return True
        except Notification.DoesNotExist:
            return False

    @classmethod
    def soft_delete_sent(cls, notification_id, user):
        """نقل إشعار مرسل إلى سلة المهملات"""
        try:
            notification = Notification.objects.get(pk=notification_id, sender=user)
            notification.is_deleted_by_sender = True
            notification.sender_deleted_at = timezone.now()
            notification.save(update_fields=['is_deleted_by_sender', 'sender_deleted_at'])
            return True
        except Notification.DoesNotExist:
            return False

    @classmethod
    def restore_sent_from_trash(cls, notification_id, user):
        """استعادة إشعار مرسل من سلة المهملات"""
        try:
            notification = Notification.objects.get(
                pk=notification_id, sender=user, is_deleted_by_sender=True
            )
            notification.is_deleted_by_sender = False
            notification.sender_deleted_at = None
            notification.is_hidden_by_sender = False
            notification.save(update_fields=['is_deleted_by_sender', 'sender_deleted_at', 'is_hidden_by_sender'])
            return True
        except Notification.DoesNotExist:
            return False

    @classmethod
    def empty_sender_trash(cls, user):
        """إفراغ سلة مهملات المرسل (حذف نهائي)"""
        return Notification.objects.filter(
            sender=user,
            is_deleted_by_sender=True,
        ).update(is_active=False)

    # ============================================================
    # 5) عمليات التحديث
    # ============================================================

    @classmethod
    def mark_as_read(cls, notification_id, user):
        """تحديد إشعار كمقروء"""
        try:
            recipient = NotificationRecipient.objects.get(
                notification_id=notification_id,
                user=user,
            )
            recipient.mark_as_read()
            return True
        except NotificationRecipient.DoesNotExist:
            return False

    @classmethod
    def mark_all_as_read(cls, user):
        """تحديد جميع الإشعارات كمقروءة"""
        return NotificationRecipient.objects.filter(
            user=user,
            is_read=False,
            is_deleted=False,
        ).update(is_read=True, read_at=timezone.now())

    @classmethod
    def soft_delete(cls, notification_id, user):
        """نقل إشعار إلى سلة المهملات"""
        try:
            recipient = NotificationRecipient.objects.get(
                notification_id=notification_id,
                user=user,
            )
            recipient.soft_delete()
            return True
        except NotificationRecipient.DoesNotExist:
            return False

    @classmethod
    def restore_from_trash(cls, notification_id, user):
        """استعادة إشعار من سلة المهملات"""
        try:
            recipient = NotificationRecipient.objects.get(
                notification_id=notification_id,
                user=user,
                is_deleted=True,
            )
            recipient.restore()
            return True
        except NotificationRecipient.DoesNotExist:
            return False

    @classmethod
    def permanent_delete(cls, notification_id, user):
        """حذف نهائي للإشعار"""
        return NotificationRecipient.objects.filter(
            notification_id=notification_id,
            user=user,
        ).delete()

    @classmethod
    def empty_trash(cls, user):
        """إفراغ سلة المهملات"""
        return NotificationRecipient.objects.filter(
            user=user,
            is_deleted=True,
        ).delete()

    @classmethod
    def archive_notification(cls, notification_id, user):
        """أرشفة إشعار"""
        try:
            recipient = NotificationRecipient.objects.get(
                notification_id=notification_id,
                user=user,
            )
            recipient.archive()
            return True
        except NotificationRecipient.DoesNotExist:
            return False

    # ============================================================
    # 6) HTMX Helpers - Cascading Dropdowns
    # ============================================================

    @classmethod
    def get_majors_for_targeting(cls):
        """جلب التخصصات المتاحة للفلترة"""
        from apps.accounts.models import Major
        return Major.objects.filter(is_active=True).order_by('major_name')

    @classmethod
    def get_levels_for_major(cls, major_id):
        """جلب المستويات المتاحة لتخصص معين"""
        from apps.accounts.models import User, Level, Role
        level_ids = User.objects.filter(
            role__code=Role.STUDENT,
            major_id=major_id,
            account_status='active',
        ).values_list('level_id', flat=True).distinct()
        return Level.objects.filter(pk__in=level_ids).order_by('level_number')

    @classmethod
    def get_students_count(cls, major_id=None, level_id=None, course_id=None):
        """عدد الطلاب المستهدفين بناءً على الفلاتر"""
        from apps.accounts.models import User, Role

        qs = User.objects.filter(
            role__code=Role.STUDENT,
            account_status='active',
        )
        if course_id:
            from apps.courses.models import Course
            try:
                course = Course.objects.get(pk=course_id)
                qs = qs.filter(
                    major__in=course.course_majors.values_list('major', flat=True),
                    level=course.level,
                )
            except Course.DoesNotExist:
                return 0
        else:
            if major_id:
                qs = qs.filter(major_id=major_id)
            if level_id:
                qs = qs.filter(level_id=level_id)

        return qs.count()

    # ============================================================
    # 7) الصيانة
    # ============================================================

    @classmethod
    def cleanup_old_notifications(cls, days=90):
        """حذف الإشعارات القديمة المقروءة"""
        cutoff = timezone.now() - timezone.timedelta(days=days)
        deleted_count, _ = NotificationRecipient.objects.filter(
            is_read=True,
            notification__created_at__lt=cutoff,
        ).delete()
        logger.info(f"Cleaned up {deleted_count} old notification recipients")
        return deleted_count


# ============================================================
# Backward Compatibility Alias (للتوافق مع الكود القديم)
# ============================================================
class NotificationManager:
    """
    واجهة التوافق الخلفي - تُعيد التوجيه إلى NotificationService
    """
    create_file_upload_notification = NotificationService.notify_file_upload
    create_course_notification = staticmethod(
        lambda sender, course, title, body, **kwargs:
            NotificationService.create_notification(
                title=title, body=body, notification_type='course',
                sender=sender, course=course,
                recipients=NotificationService.get_targeted_users(
                    'course_students', course=course
                ),
            )
    )
    create_system_notification = NotificationService.notify_system
    get_unread_count = NotificationService.get_unread_count
    get_user_notifications = NotificationService.get_user_notifications
    get_recent_notifications = NotificationService.get_recent_notifications
