"""
نماذج نظام الإشعارات
S-ACM - Smart Academic Content Management System
"""

from django.db import models
from django.conf import settings


class Notification(models.Model):
    """
    جدول الإشعارات (Notifications)
    """
    NOTIFICATION_TYPES = [
        ('general', 'إشعار عام'),
        ('course', 'إشعار مقرر'),
        ('file_upload', 'رفع ملف جديد'),
        ('announcement', 'إعلان'),
        ('system', 'إشعار نظام'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'منخفضة'),
        ('normal', 'عادية'),
        ('high', 'عالية'),
        ('urgent', 'عاجلة'),
    ]
    
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_notifications',
        verbose_name='المرسل'
    )
    title = models.CharField(
        max_length=255,
        verbose_name='عنوان الإشعار'
    )
    body = models.TextField(
        verbose_name='محتوى الإشعار'
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='general',
        verbose_name='نوع الإشعار'
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='normal',
        verbose_name='الأولوية'
    )
    # ربط اختياري بمقرر
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name='المقرر المرتبط'
    )
    # ربط اختياري بملف
    file = models.ForeignKey(
        'courses.LectureFile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name='الملف المرتبط'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء'
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ انتهاء الصلاحية'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط'
    )
    
    class Meta:
        db_table = 'notifications'
        verbose_name = 'إشعار'
        verbose_name_plural = 'الإشعارات'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['notification_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['course']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_recipients_count(self):
        """الحصول على عدد المستلمين"""
        return self.recipients.count()
    
    def get_read_count(self):
        """الحصول على عدد من قرأ الإشعار"""
        return self.recipients.filter(is_read=True).count()


class NotificationRecipient(models.Model):
    """
    جدول مستلمي الإشعارات (Notification_Recipients)
    """
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name='recipients',
        verbose_name='الإشعار'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_notifications',
        verbose_name='المستلم'
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name='مقروء'
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='وقت القراءة'
    )
    is_deleted = models.BooleanField(
        default=False,
        verbose_name='محذوف',
        help_text='حذف الإشعار من قائمة المستخدم فقط'
    )
    
    class Meta:
        db_table = 'notification_recipients'
        unique_together = ('notification', 'user')
        verbose_name = 'مستلم إشعار'
        verbose_name_plural = 'مستلمو الإشعارات'
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', 'is_deleted']),
        ]
    
    def __str__(self):
        return f"{self.notification.title} -> {self.user.full_name}"
    
    def mark_as_read(self):
        """تحديد الإشعار كمقروء"""
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class NotificationManager:
    """
    مدير لإنشاء وإرسال الإشعارات
    """
    
    @staticmethod
    def create_file_upload_notification(file_obj, course):
        """
        إنشاء إشعار عند رفع ملف جديد
        يرسل إلى جميع طلاب المقرر
        """
        from apps.accounts.models import User
        
        notification = Notification.objects.create(
            sender=file_obj.uploader,
            title=f"ملف جديد في {course.course_name}",
            body=f"تم رفع ملف جديد: {file_obj.title}",
            notification_type='file_upload',
            course=course,
            file=file_obj
        )
        
        # الحصول على جميع طلاب المقرر
        students = User.objects.filter(
            role__role_name='Student',
            major__in=course.course_majors.values_list('major', flat=True),
            level=course.level,
            account_status='active'
        )
        
        # إنشاء سجلات المستلمين
        recipients = [
            NotificationRecipient(notification=notification, user=student)
            for student in students
        ]
        NotificationRecipient.objects.bulk_create(recipients)
        
        return notification
    
    @staticmethod
    def create_course_notification(sender, course, title, body, send_to_all_department=False):
        """
        إنشاء إشعار للمقرر
        """
        from apps.accounts.models import User
        
        notification = Notification.objects.create(
            sender=sender,
            title=title,
            body=body,
            notification_type='course',
            course=course
        )
        
        # تحديد المستلمين
        if send_to_all_department:
            # إرسال لجميع طلاب القسم والمستوى
            students = User.objects.filter(
                role__role_name='Student',
                major__in=course.course_majors.values_list('major', flat=True),
                account_status='active'
            )
        else:
            # إرسال لطلاب المقرر فقط
            students = User.objects.filter(
                role__role_name='Student',
                major__in=course.course_majors.values_list('major', flat=True),
                level=course.level,
                account_status='active'
            )
        
        # إنشاء سجلات المستلمين
        recipients = [
            NotificationRecipient(notification=notification, user=student)
            for student in students
        ]
        NotificationRecipient.objects.bulk_create(recipients)
        
        return notification
    
    @staticmethod
    def create_system_notification(title, body, users=None):
        """
        إنشاء إشعار نظام
        """
        from apps.accounts.models import User
        
        notification = Notification.objects.create(
            sender=None,
            title=title,
            body=body,
            notification_type='system',
            priority='high'
        )
        
        if users is None:
            # إرسال لجميع المستخدمين النشطين
            users = User.objects.filter(account_status='active')
        
        # إنشاء سجلات المستلمين
        recipients = [
            NotificationRecipient(notification=notification, user=user)
            for user in users
        ]
        NotificationRecipient.objects.bulk_create(recipients)
        
        return notification
    
    @staticmethod
    def get_unread_count(user):
        """
        الحصول على عدد الإشعارات غير المقروءة للمستخدم
        """
        return NotificationRecipient.objects.filter(
            user=user,
            is_read=False,
            is_deleted=False,
            notification__is_active=True
        ).count()
    
    @staticmethod
    def get_user_notifications(user, include_read=True, limit=None):
        """
        الحصول على إشعارات المستخدم
        """
        queryset = NotificationRecipient.objects.filter(
            user=user,
            is_deleted=False,
            notification__is_active=True
        ).select_related('notification', 'notification__sender', 'notification__course')
        
        if not include_read:
            queryset = queryset.filter(is_read=False)
        
        queryset = queryset.order_by('-notification__created_at')
        
        if limit:
            queryset = queryset[:limit]
        
        return queryset
