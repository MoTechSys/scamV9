"""
خدمات الإشعارات
S-ACM - Smart Academic Content Management System
"""

from django.db.models import Q
from .models import Notification


class NotificationService:
    """خدمة إدارة الإشعارات"""
    
    @classmethod
    def create_notification(cls, user, title, body, notification_type='info', related_course=None, related_file=None):
        """
        إنشاء إشعار جديد
        """
        return Notification.objects.create(
            user=user,
            title=title,
            body=body,
            notification_type=notification_type,
            related_course=related_course,
            related_file=related_file
        )
    
    @classmethod
    def bulk_create_notifications(cls, users, title, body, notification_type='info', related_course=None):
        """
        إنشاء إشعارات متعددة لمجموعة من المستخدمين
        """
        notifications = [
            Notification(
                user=user,
                title=title,
                body=body,
                notification_type=notification_type,
                related_course=related_course
            )
            for user in users
        ]
        
        if notifications:
            Notification.objects.bulk_create(notifications)
        
        return len(notifications)
    
    @classmethod
    def notify_new_file(cls, file_obj):
        """
        إرسال إشعار عند رفع ملف جديد
        """
        from apps.accounts.models import User
        
        course = file_obj.course
        
        # الحصول على جميع الطلاب المسجلين في التخصصات المرتبطة بالمقرر
        majors = course.course_majors.values_list('major_id', flat=True)
        students = User.objects.filter(
            role__role_name='student',
            major_id__in=majors,
            level=course.level,
            account_status='active'
        )
        
        return cls.bulk_create_notifications(
            users=students,
            title=f"ملف جديد في {course.course_name}",
            body=f"تم رفع ملف جديد: {file_obj.title}",
            notification_type='new_file',
            related_course=course
        )
    
    @classmethod
    def notify_announcement(cls, title, body, course=None, target_role=None, target_major=None, target_level=None):
        """
        إرسال إعلان عام
        """
        from apps.accounts.models import User
        
        users = User.objects.filter(account_status='active')
        
        if target_role:
            users = users.filter(role__role_name=target_role)
        
        if target_major:
            users = users.filter(major=target_major)
        
        if target_level:
            users = users.filter(level=target_level)
        
        if course:
            majors = course.course_majors.values_list('major_id', flat=True)
            users = users.filter(
                Q(major_id__in=majors) | Q(role__role_name__in=['admin', 'instructor'])
            )
        
        return cls.bulk_create_notifications(
            users=users.distinct(),
            title=title,
            body=body,
            notification_type='info',
            related_course=course
        )
    
    @classmethod
    def get_user_notifications(cls, user, unread_only=False, limit=None):
        """
        الحصول على إشعارات المستخدم
        """
        notifications = Notification.objects.filter(user=user).order_by('-created_at')
        
        if unread_only:
            notifications = notifications.filter(is_read=False)
        
        if limit:
            notifications = notifications[:limit]
        
        return notifications
    
    @classmethod
    def get_unread_count(cls, user):
        """
        الحصول على عدد الإشعارات غير المقروءة
        """
        return Notification.objects.filter(user=user, is_read=False).count()
    
    @classmethod
    def mark_as_read(cls, notification_id, user):
        """
        تحديد إشعار كمقروء
        """
        return Notification.objects.filter(
            pk=notification_id,
            user=user
        ).update(is_read=True)
    
    @classmethod
    def mark_all_as_read(cls, user):
        """
        تحديد جميع الإشعارات كمقروءة
        """
        return Notification.objects.filter(
            user=user,
            is_read=False
        ).update(is_read=True)
    
    @classmethod
    def delete_notification(cls, notification_id, user):
        """
        حذف إشعار
        """
        return Notification.objects.filter(
            pk=notification_id,
            user=user
        ).delete()
    
    @classmethod
    def delete_old_notifications(cls, days=30):
        """
        حذف الإشعارات القديمة
        """
        from datetime import timedelta
        from django.utils import timezone
        
        cutoff_date = timezone.now() - timedelta(days=days)
        return Notification.objects.filter(
            created_at__lt=cutoff_date,
            is_read=True
        ).delete()
