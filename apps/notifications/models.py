"""
نماذج نظام الإشعارات - النسخة الجديدة v2
S-ACM - Smart Academic Content Management System

=== Architecture ===
- Notification: الإشعار الأصلي مع GenericForeignKey للربط بأي كائن
- NotificationRecipient: مستلم الإشعار مع حالة القراءة والحذف والأرشفة
- NotificationPreference: تفضيلات إشعارات المستخدم (البريد الإلكتروني)
"""

from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone


class Notification(models.Model):
    """
    جدول الإشعارات الرئيسي
    يدعم GenericForeignKey للربط بأي كائن في النظام
    """
    # === أنواع الإشعارات ===
    NOTIFICATION_TYPES = [
        ('general', 'إشعار عام'),
        ('course', 'إشعار مقرر'),
        ('file_upload', 'رفع ملف جديد'),
        ('assignment', 'واجب'),
        ('exam', 'اختبار'),
        ('grade', 'درجة'),
        ('announcement', 'إعلان'),
        ('system', 'إشعار نظام'),
        ('welcome', 'ترحيب'),
    ]

    # === مستويات الأولوية مع ألوان Badge ===
    PRIORITY_CHOICES = [
        ('low', 'منخفضة'),
        ('normal', 'عادية'),
        ('high', 'عالية'),
        ('urgent', 'عاجلة'),
    ]

    PRIORITY_COLORS = {
        'low': 'secondary',
        'normal': 'info',
        'high': 'warning',
        'urgent': 'danger',
    }

    # === الحقول الأساسية ===
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
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

    # === GenericForeignKey - الربط الذكي بأي كائن ===
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='نوع الكائن المرتبط'
    )
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='معرف الكائن المرتبط'
    )
    related_object = GenericForeignKey('content_type', 'object_id')

    # === ربط مباشر بالمقرر (للاستعلامات السريعة) ===
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name='المقرر المرتبط'
    )

    # === التواريخ والحالة ===
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
            models.Index(fields=['notification_type', 'created_at'], name='idx_notif_type_date'),
            models.Index(fields=['course', 'created_at'], name='idx_notif_course_date'),
            models.Index(fields=['sender', 'created_at'], name='idx_notif_sender_date'),
            models.Index(fields=['content_type', 'object_id'], name='idx_notif_generic'),
            models.Index(fields=['is_active', 'created_at'], name='idx_notif_active_date'),
        ]

    def __str__(self):
        return self.title

    @property
    def priority_color(self):
        """إرجاع لون Bootstrap للأولوية"""
        return self.PRIORITY_COLORS.get(self.priority, 'info')

    @property
    def is_expired(self):
        """هل انتهت صلاحية الإشعار؟"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    def get_recipients_count(self):
        """عدد المستلمين"""
        return self.recipients.count()

    def get_read_count(self):
        """عدد من قرأ الإشعار"""
        return self.recipients.filter(is_read=True).count()

    def get_related_url(self):
        """
        إرجاع الرابط الذكي للكائن المرتبط بالإشعار
        يستخدم للانتقال المباشر عند النقر
        """
        if not self.content_type or not self.object_id:
            return None

        model_name = self.content_type.model
        try:
            from django.urls import reverse
            if model_name == 'lecturefile':
                obj = self.content_type.get_object_for_this_type(pk=self.object_id)
                return reverse('student:study_room', kwargs={'file_pk': obj.pk})
            elif model_name == 'course':
                return reverse('student:course_detail', kwargs={'pk': self.object_id})
        except Exception:
            pass
        return None


class NotificationRecipient(models.Model):
    """
    جدول مستلمي الإشعارات
    كل صف يمثل علاقة إشعار-مستلم مع حالة القراءة والحذف
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
        help_text='حذف ناعم - الإشعار لا يظهر لكنه موجود'
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='وقت الحذف'
    )
    is_archived = models.BooleanField(
        default=False,
        verbose_name='مؤرشف'
    )

    class Meta:
        db_table = 'notification_recipients'
        unique_together = ('notification', 'user')
        verbose_name = 'مستلم إشعار'
        verbose_name_plural = 'مستلمو الإشعارات'
        indexes = [
            models.Index(fields=['user', 'is_read', 'is_deleted'], name='idx_nr_user_read_del'),
            models.Index(fields=['user', 'is_deleted', 'is_archived'], name='idx_nr_user_del_arch'),
            models.Index(fields=['user', 'is_read'], name='idx_nr_user_read'),
        ]

    def __str__(self):
        return f"{self.notification.title} -> {self.user.full_name}"

    def mark_as_read(self):
        """تحديد الإشعار كمقروء"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    def soft_delete(self):
        """حذف ناعم - نقل إلى سلة المهملات"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def restore(self):
        """استعادة من سلة المهملات"""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def archive(self):
        """أرشفة الإشعار"""
        self.is_archived = True
        self.save(update_fields=['is_archived'])

    def unarchive(self):
        """إلغاء الأرشفة"""
        self.is_archived = False
        self.save(update_fields=['is_archived'])


class NotificationPreference(models.Model):
    """
    تفضيلات إشعارات المستخدم
    تفعيل/تعطيل الإشعارات عبر البريد الإلكتروني حسب النوع
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
        verbose_name='المستخدم'
    )
    email_enabled = models.BooleanField(
        default=True,
        verbose_name='تفعيل إشعارات البريد الإلكتروني'
    )
    email_file_upload = models.BooleanField(
        default=True,
        verbose_name='إشعار رفع ملف جديد'
    )
    email_announcement = models.BooleanField(
        default=True,
        verbose_name='إشعار إعلان'
    )
    email_assignment = models.BooleanField(
        default=True,
        verbose_name='إشعار واجب'
    )
    email_exam = models.BooleanField(
        default=True,
        verbose_name='إشعار اختبار'
    )
    email_grade = models.BooleanField(
        default=True,
        verbose_name='إشعار درجة'
    )
    email_system = models.BooleanField(
        default=True,
        verbose_name='إشعار نظام'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث'
    )

    class Meta:
        db_table = 'notification_preferences'
        verbose_name = 'تفضيلات إشعارات'
        verbose_name_plural = 'تفضيلات الإشعارات'

    def __str__(self):
        return f"تفضيلات إشعارات {self.user.full_name}"

    @classmethod
    def get_or_create_for_user(cls, user):
        """الحصول على تفضيلات المستخدم أو إنشائها"""
        obj, _ = cls.objects.get_or_create(user=user)
        return obj
