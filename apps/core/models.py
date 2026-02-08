"""
نماذج أساسية للنظام
S-ACM - Smart Academic Content Management System
"""

from django.db import models


class SystemSetting(models.Model):
    """
    جدول إعدادات النظام
    لتخزين الإعدادات القابلة للتعديل
    """
    key = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='المفتاح'
    )
    value = models.TextField(
        verbose_name='القيمة'
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='الوصف'
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name='عام',
        help_text='هل يمكن للمستخدمين العاديين رؤية هذا الإعداد'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث'
    )
    
    class Meta:
        db_table = 'system_settings'
        verbose_name = 'إعداد نظام'
        verbose_name_plural = 'إعدادات النظام'
    
    def __str__(self):
        return self.key
    
    @classmethod
    def get_setting(cls, key, default=None):
        """الحصول على قيمة إعداد معين"""
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return default
    
    @classmethod
    def set_setting(cls, key, value, description=None):
        """تعيين قيمة إعداد معين"""
        obj, created = cls.objects.update_or_create(
            key=key,
            defaults={'value': value, 'description': description}
        )
        return obj


class AuditLog(models.Model):
    """
    جدول سجل التدقيق
    لتتبع التغييرات الهامة في النظام
    """
    ACTION_TYPES = [
        ('create', 'إنشاء'),
        ('update', 'تحديث'),
        ('delete', 'حذف'),
        ('login', 'تسجيل دخول'),
        ('logout', 'تسجيل خروج'),
        ('export', 'تصدير'),
        ('import', 'استيراد'),
        ('promote', 'ترقية'),
    ]
    
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs',
        verbose_name='المستخدم'
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_TYPES,
        verbose_name='الإجراء'
    )
    model_name = models.CharField(
        max_length=100,
        verbose_name='اسم النموذج'
    )
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='معرف الكائن'
    )
    object_repr = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='تمثيل الكائن'
    )
    changes = models.JSONField(
        blank=True,
        null=True,
        verbose_name='التغييرات'
    )
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name='عنوان IP'
    )
    user_agent = models.TextField(
        blank=True,
        null=True,
        verbose_name='معلومات المتصفح'
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name='الوقت'
    )
    
    class Meta:
        db_table = 'audit_logs'
        verbose_name = 'سجل تدقيق'
        verbose_name_plural = 'سجلات التدقيق'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'action']),
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user} - {self.get_action_display()} - {self.model_name}"
    
    @classmethod
    def log(cls, user, action, model_name, object_id=None, object_repr=None, 
            changes=None, request=None):
        """تسجيل إجراء في سجل التدقيق"""
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = cls.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        return cls.objects.create(
            user=user,
            action=action,
            model_name=model_name,
            object_id=object_id,
            object_repr=object_repr,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @staticmethod
    def get_client_ip(request):
        """الحصول على عنوان IP للعميل"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
