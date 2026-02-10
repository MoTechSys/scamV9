"""
نماذج وظائف الذكاء الاصطناعي - Enterprise Edition v2 (Dynamic Governance)
S-ACM - Smart Academic Content Management System

=== Phase 2: TANK AI Engine ===
- AIConfiguration: Singleton model for AI settings (replaces .env hardcodes)
- APIKey: Encrypted key storage with health tracking & cooldown
- All existing models preserved and enhanced

== التحديثات ==
- إضافة AIConfiguration (Singleton) للتحكم من لوحة الأدمن
- إضافة APIKey مع تشفير المفتاح + حالة الصحة + معدل الطلبات
- إضافة md_file_path لكل من AISummary (لتخزين مسار ملف .md)
- إضافة AIGenerationJob لتتبع عمليات التوليد للمدرسين
- إضافة StudentProgress لتتبع تقدم الطلاب
"""

import base64
import hashlib
import logging
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

logger = logging.getLogger('ai_features')


# ========================================================================
# Phase 2: Dynamic AI Governance Models
# ========================================================================

class AIConfiguration(models.Model):
    """
    Singleton Model: إعدادات محرك الذكاء الاصطناعي.

    تتيح للأدمن التحكم الكامل في سلوك AI من لوحة التحكم:
    - النموذج النشط (gemini-1.5-flash, gemini-1.5-pro, gemini-2.0-flash)
    - حجم التقطيع (chunk_size) للنصوص الكبيرة
    - الحد الأقصى لتوكنات الإخراج
    - معدل الطلبات المسموح للمستخدم
    - تفعيل/تعطيل الخدمة بالكامل

    Pattern: Singleton via overriding save() and custom manager.
    Usage: AIConfiguration.get_config()
    """

    MODEL_CHOICES = [
        ('gpt-4.1-mini', 'GPT-4.1 Mini (افتراضي - مُوصى به)'),
        ('gpt-4.1-nano', 'GPT-4.1 Nano (خفيف وسريع)'),
        ('gemini-2.5-flash', 'Gemini 2.5 Flash (عبر Manus Proxy)'),
        ('gemini-2.5-pro', 'Gemini 2.5 Pro (متقدم - عبر Manus)'),
        ('gpt-4o', 'GPT-4o (متقدم)'),
        ('gpt-4o-mini', 'GPT-4o Mini (سريع)'),
    ]

    # --- Model Selection ---
    active_model = models.CharField(
        max_length=50,
        choices=MODEL_CHOICES,
        default='gpt-4.1-mini',
        verbose_name='النموذج النشط',
        help_text='نموذج AI المستخدم لجميع العمليات (عبر Manus API Proxy)'
    )

    # --- Chunking Configuration ---
    chunk_size = models.PositiveIntegerField(
        default=30000,
        validators=[MinValueValidator(1000), MaxValueValidator(100000)],
        verbose_name='حجم التقطيع (حرف)',
        help_text='الحد الأقصى لحجم كل جزء من النص قبل الإرسال لـ AI (1000-100000)'
    )
    chunk_overlap = models.PositiveIntegerField(
        default=500,
        validators=[MinValueValidator(0), MaxValueValidator(5000)],
        verbose_name='تداخل الأجزاء (حرف)',
        help_text='عدد الأحرف المتداخلة بين الأجزاء للحفاظ على السياق'
    )

    # --- Output Configuration ---
    max_output_tokens = models.PositiveIntegerField(
        default=8192,
        validators=[MinValueValidator(100), MaxValueValidator(65536)],
        verbose_name='حد التوكنات للإخراج',
        help_text='الحد الأقصى لعدد التوكنات في استجابة AI (100-65536)'
    )
    temperature = models.FloatField(
        default=0.3,
        validators=[MinValueValidator(0.0), MaxValueValidator(2.0)],
        verbose_name='درجة الإبداع (Temperature)',
        help_text='0.0 = محافظ ودقيق | 1.0 = متوازن | 2.0 = إبداعي'
    )

    # --- Rate Limiting ---
    user_rate_limit_per_hour = models.PositiveIntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(1000)],
        verbose_name='حد الطلبات/ساعة للمستخدم',
        help_text='الحد الأقصى لطلبات AI لكل مستخدم في الساعة'
    )

    # --- Service Toggle ---
    is_service_enabled = models.BooleanField(
        default=True,
        verbose_name='خدمة AI مفعلة',
        help_text='إيقاف هذا الخيار يعطّل جميع خدمات AI في النظام'
    )
    maintenance_message = models.CharField(
        max_length=500,
        blank=True,
        default='خدمة الذكاء الاصطناعي متوقفة مؤقتاً للصيانة.',
        verbose_name='رسالة الصيانة',
        help_text='الرسالة التي تظهر للمستخدمين عند تعطيل الخدمة'
    )

    # --- Metadata ---
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخر تحديث')
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='آخر تعديل بواسطة',
        related_name='ai_config_updates'
    )

    class Meta:
        db_table = 'ai_configuration'
        verbose_name = 'إعدادات الذكاء الاصطناعي'
        verbose_name_plural = 'إعدادات الذكاء الاصطناعي'

    def __str__(self):
        status = '🟢 مفعل' if self.is_service_enabled else '🔴 معطل'
        return f'إعدادات AI ({self.active_model}) - {status}'

    def save(self, *args, **kwargs):
        """Singleton pattern: Only one instance allowed."""
        self.pk = 1
        super().save(*args, **kwargs)
        # Invalidate cache on save
        cache.delete('ai_configuration')

    def delete(self, *args, **kwargs):
        """Prevent deletion of singleton."""
        pass

    @classmethod
    def get_config(cls):
        """
        Get the singleton configuration instance (cached).

        Returns:
            AIConfiguration: The configuration instance, creating default if needed.
        """
        config = cache.get('ai_configuration')
        if config is None:
            config, _ = cls.objects.get_or_create(pk=1)
            cache.set('ai_configuration', config, timeout=300)  # 5 min cache
        return config

    @classmethod
    def invalidate_cache(cls):
        """Force cache invalidation."""
        cache.delete('ai_configuration')


class APIKey(models.Model):
    """
    مفتاح API مع تشفير وتتبع الصحة.

    Features:
    - Base64 encrypted key storage (not plaintext in DB)
    - Health tracking: error_count, last_error, latency
    - Automatic cooldown on 429 (Rate Limit) errors
    - RPM (Requests Per Minute) limit per key
    - Admin can test connection directly
    """

    PROVIDER_CHOICES = [
        ('manus', 'Manus API Proxy (OpenAI Compatible)'),
        ('openai', 'OpenAI Direct'),
    ]

    STATUS_CHOICES = [
        ('active', '🟢 نشط'),
        ('cooldown', '🟡 في فترة راحة'),
        ('disabled', '🔴 معطل'),
        ('error', '⚠️ خطأ'),
    ]

    # --- Identity ---
    label = models.CharField(
        max_length=100,
        verbose_name='اسم المفتاح',
        help_text='اسم وصفي للتمييز (مثال: مفتاح المشروع الرئيسي)',
        default='مفتاح API'
    )
    provider = models.CharField(
        max_length=20,
        choices=PROVIDER_CHOICES,
        default='manus',
        verbose_name='المزود'
    )

    # --- Encrypted Key ---
    _encrypted_key = models.TextField(
        db_column='encrypted_key',
        verbose_name='المفتاح المشفر',
        help_text='يتم التشفير تلقائياً عند الحفظ'
    )
    key_hint = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='تلميح المفتاح',
        help_text='آخر 4 أحرف من المفتاح (للتعرف)'
    )

    # --- Status & Health ---
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='الحالة'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='مفعّل',
        help_text='يمكن تعطيله يدوياً من الأدمن'
    )
    error_count = models.PositiveIntegerField(
        default=0,
        verbose_name='عدد الأخطاء'
    )
    total_requests = models.PositiveIntegerField(
        default=0,
        verbose_name='إجمالي الطلبات'
    )
    last_error = models.TextField(
        blank=True, null=True,
        verbose_name='آخر خطأ'
    )
    last_error_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name='وقت آخر خطأ'
    )
    last_success_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name='وقت آخر نجاح'
    )
    last_latency_ms = models.PositiveIntegerField(
        default=0,
        verbose_name='زمن الاستجابة (مللي ثانية)'
    )

    # --- Rate Limiting ---
    rpm_limit = models.PositiveIntegerField(
        default=15,
        validators=[MinValueValidator(1), MaxValueValidator(1000)],
        verbose_name='حد الطلبات/دقيقة (RPM)',
        help_text='الحد الأقصى للطلبات في الدقيقة حسب خطة Google Cloud'
    )
    cooldown_until = models.DateTimeField(
        null=True, blank=True,
        verbose_name='فترة الراحة حتى',
        help_text='المفتاح لن يُستخدم حتى هذا الوقت'
    )

    # --- Tokens Tracking ---
    tokens_used_today = models.PositiveIntegerField(
        default=0,
        verbose_name='التوكنات المستخدمة اليوم'
    )
    tokens_reset_date = models.DateField(
        null=True, blank=True,
        verbose_name='تاريخ آخر إعادة تعيين'
    )

    # --- Metadata ---
    priority = models.PositiveIntegerField(
        default=0,
        verbose_name='الأولوية',
        help_text='أقل رقم = أولوية أعلى. يُستخدم لترتيب التدوير'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخر تحديث')

    class Meta:
        db_table = 'ai_api_keys'
        verbose_name = 'مفتاح API'
        verbose_name_plural = 'مفاتيح API'
        ordering = ['priority', '-is_active', 'created_at']
        indexes = [
            models.Index(fields=['provider', 'is_active', 'status']),
            models.Index(fields=['cooldown_until']),
        ]

    def __str__(self):
        return f'{self.label} ({self.get_status_display()}) ...{self.key_hint}'

    # --- Encryption / Decryption ---
    @staticmethod
    def _get_encryption_key():
        """Derive encryption key from Django SECRET_KEY."""
        secret = settings.SECRET_KEY.encode('utf-8')
        return hashlib.sha256(secret).digest()

    def set_key(self, raw_key: str):
        """Encrypt and store the API key."""
        if not raw_key:
            return
        # Simple XOR + Base64 encryption (suitable for DB storage)
        enc_key = self._get_encryption_key()
        encrypted = bytes(
            a ^ b for a, b in zip(
                raw_key.encode('utf-8'),
                (enc_key * ((len(raw_key) // len(enc_key)) + 1))[:len(raw_key)]
            )
        )
        self._encrypted_key = base64.b64encode(encrypted).decode('utf-8')
        self.key_hint = raw_key[-4:] if len(raw_key) >= 4 else raw_key

    def get_key(self) -> str:
        """Decrypt and return the API key."""
        if not self._encrypted_key:
            return ''
        try:
            enc_key = self._get_encryption_key()
            encrypted = base64.b64decode(self._encrypted_key.encode('utf-8'))
            decrypted = bytes(
                a ^ b for a, b in zip(
                    encrypted,
                    (enc_key * ((len(encrypted) // len(enc_key)) + 1))[:len(encrypted)]
                )
            )
            return decrypted.decode('utf-8')
        except Exception as e:
            logger.error(f'APIKey decryption failed for {self.label}: {e}')
            return ''

    # --- Health Management ---
    def mark_success(self, latency_ms: int = 0):
        """Mark a successful API call."""
        now = timezone.now()
        self.last_success_at = now
        self.last_latency_ms = latency_ms
        self.total_requests += 1
        self.error_count = 0  # Reset error streak
        self.status = 'active'
        self._update_daily_tokens()
        self.save(update_fields=[
            'last_success_at', 'last_latency_ms', 'total_requests',
            'error_count', 'status', 'tokens_used_today',
            'tokens_reset_date', 'updated_at'
        ])

    def mark_error(self, error_message: str, is_rate_limit: bool = False):
        """Mark a failed API call."""
        now = timezone.now()
        self.last_error = error_message[:500]
        self.last_error_at = now
        self.error_count += 1
        self.total_requests += 1

        if is_rate_limit:
            # Cooldown for 60 seconds on rate limit
            self.cooldown_until = now + timedelta(seconds=60)
            self.status = 'cooldown'
            logger.warning(f'APIKey {self.label}: Rate limited, cooldown until {self.cooldown_until}')
        elif self.error_count >= 5:
            # Disable after 5 consecutive errors
            self.status = 'error'
            self.is_active = False
            logger.error(f'APIKey {self.label}: Disabled after {self.error_count} errors')
        else:
            self.status = 'active'

        self.save(update_fields=[
            'last_error', 'last_error_at', 'error_count',
            'total_requests', 'cooldown_until', 'status',
            'is_active', 'updated_at'
        ])

    def is_available(self) -> bool:
        """Check if key is available for use."""
        if not self.is_active:
            return False
        if self.status in ('disabled', 'error'):
            return False
        if self.cooldown_until and timezone.now() < self.cooldown_until:
            return False
        return True

    def check_rpm_limit(self) -> bool:
        """Check if RPM limit allows another request (uses Django cache)."""
        cache_key = f'api_key_rpm_{self.pk}'
        current_count = cache.get(cache_key, 0)
        if current_count >= self.rpm_limit:
            return False
        # Increment with 60-second TTL
        cache.set(cache_key, current_count + 1, timeout=60)
        return True

    def _update_daily_tokens(self):
        """Reset daily token counter if needed."""
        today = timezone.now().date()
        if self.tokens_reset_date != today:
            self.tokens_used_today = 0
            self.tokens_reset_date = today

    def clean(self):
        """Validate the model."""
        if not self._encrypted_key:
            raise ValidationError({'_encrypted_key': 'مفتاح API مطلوب.'})


# ========================================================================
# Existing Models (Preserved & Enhanced)
# ========================================================================

class AISummary(models.Model):
    """ملخصات الذكاء الاصطناعي - المخرجات تُحفظ كملفات .md"""
    file = models.OneToOneField(
        'courses.LectureFile',
        on_delete=models.CASCADE,
        related_name='ai_summary',
        verbose_name='الملف'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='requested_summaries',
        verbose_name='المستخدم'
    )
    summary_text = models.TextField(
        verbose_name='نص الملخص',
        help_text='ملخص مختصر - النص الكامل في ملف .md',
        default='',
        blank=True,
    )
    md_file_path = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='مسار ملف Markdown',
        help_text='المسار النسبي لملف الملخص في media/'
    )
    language = models.CharField(max_length=10, default='ar', verbose_name='لغة الملخص')
    word_count = models.PositiveIntegerField(default=0, verbose_name='عدد الكلمات')
    generated_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ التوليد')
    generation_time = models.FloatField(default=0, verbose_name='وقت التوليد (ثانية)')
    model_used = models.CharField(max_length=100, default='gemini-2.0-flash', verbose_name='النموذج المستخدم')
    is_cached = models.BooleanField(default=True, verbose_name='مخزن مؤقتاً')

    class Meta:
        db_table = 'ai_summaries'
        verbose_name = 'ملخص AI'
        verbose_name_plural = 'ملخصات AI'
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['file']),
            models.Index(fields=['generated_at']),
        ]

    def __str__(self):
        return f"Summary for {self.file.title}"

    @classmethod
    def get_cached_summary(cls, file):
        return cls.objects.filter(file=file, is_cached=True).first()


class AIGeneratedQuestion(models.Model):
    """أسئلة مولدة بالذكاء الاصطناعي"""
    QUESTION_TYPES = [
        ('mcq', 'اختيار من متعدد'),
        ('true_false', 'صح وخطأ'),
        ('short_answer', 'إجابة قصيرة'),
        ('mixed', 'مختلط'),
    ]

    file = models.ForeignKey(
        'courses.LectureFile',
        on_delete=models.CASCADE,
        related_name='ai_questions',
        verbose_name='الملف'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='requested_questions',
        verbose_name='المستخدم'
    )
    question_text = models.TextField(verbose_name='نص السؤال')
    question_type = models.CharField(
        max_length=50, choices=QUESTION_TYPES,
        default='short_answer', verbose_name='نوع السؤال'
    )
    options = models.JSONField(null=True, blank=True, help_text='خيارات MCQ')
    correct_answer = models.TextField(verbose_name='الإجابة الصحيحة')
    explanation = models.TextField(null=True, blank=True, verbose_name='الشرح')
    score = models.FloatField(default=1.0, verbose_name='الدرجة')
    difficulty_level = models.CharField(max_length=20, default='medium', verbose_name='مستوى الصعوبة')
    generated_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ التوليد')
    is_cached = models.BooleanField(default=True, verbose_name='مخزن مؤقتاً')

    class Meta:
        db_table = 'ai_generated_questions'
        verbose_name = 'سؤال AI'
        verbose_name_plural = 'أسئلة AI'
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['file']),
            models.Index(fields=['question_type']),
        ]

    def __str__(self):
        return self.question_text[:50]

    @classmethod
    def get_cached_questions(cls, file, question_type='mixed'):
        if question_type == 'mixed':
            return cls.objects.filter(file=file, is_cached=True)
        return cls.objects.filter(file=file, question_type=question_type, is_cached=True)


class AIChat(models.Model):
    """محادثات الذكاء الاصطناعي (اسأل المستند)"""
    file = models.ForeignKey(
        'courses.LectureFile', on_delete=models.CASCADE,
        related_name='ai_chats', verbose_name='الملف'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='ai_chats', verbose_name='المستخدم'
    )
    question = models.TextField(verbose_name='السؤال')
    answer = models.TextField(verbose_name='الإجابة')
    is_helpful = models.BooleanField(null=True, blank=True, verbose_name='مفيد')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ السؤال')
    response_time = models.FloatField(default=0, verbose_name='وقت الاستجابة (ثانية)')

    class Meta:
        db_table = 'ai_chats'
        verbose_name = 'محادثة AI'
        verbose_name_plural = 'محادثات AI'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['file', 'user']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Chat: {self.question[:50]}..."


class AIUsageLog(models.Model):
    """سجل استخدام الذكاء الاصطناعي - Rate Limiting"""
    REQUEST_TYPES = [
        ('summary', 'تلخيص'),
        ('questions', 'توليد أسئلة'),
        ('chat', 'محادثة'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='ai_usage_logs', verbose_name='المستخدم'
    )
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES, verbose_name='نوع الطلب')
    file = models.ForeignKey(
        'courses.LectureFile', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='ai_usage_logs', verbose_name='الملف'
    )
    tokens_used = models.PositiveIntegerField(default=0, verbose_name='التوكنات المستخدمة')
    request_time = models.DateTimeField(auto_now_add=True, verbose_name='وقت الطلب')
    was_cached = models.BooleanField(default=False, verbose_name='من الذاكرة المؤقتة')
    success = models.BooleanField(default=True, verbose_name='ناجح')
    error_message = models.TextField(blank=True, null=True, verbose_name='رسالة الخطأ')
    api_key_used = models.ForeignKey(
        APIKey, on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='مفتاح API المستخدم',
        related_name='usage_logs'
    )

    class Meta:
        db_table = 'ai_usage_logs'
        verbose_name = 'سجل استخدام AI'
        verbose_name_plural = 'سجلات استخدام AI'
        ordering = ['-request_time']
        indexes = [
            models.Index(fields=['user', 'request_time']),
            models.Index(fields=['request_type']),
            models.Index(fields=['request_time']),
        ]

    def __str__(self):
        return f"{self.user.academic_id} - {self.get_request_type_display()}"

    @classmethod
    def check_rate_limit(cls, user):
        """Check rate limit using dynamic config from DB."""
        one_hour_ago = timezone.now() - timedelta(hours=1)
        recent = cls.objects.filter(
            user=user, request_time__gte=one_hour_ago, was_cached=False
        ).count()
        # Get limit from DB configuration (fallback to settings)
        try:
            config = AIConfiguration.get_config()
            limit = config.user_rate_limit_per_hour
        except Exception:
            limit = getattr(settings, 'AI_RATE_LIMIT_PER_HOUR', 10)
        return recent < limit

    @classmethod
    def get_remaining_requests(cls, user):
        one_hour_ago = timezone.now() - timedelta(hours=1)
        recent = cls.objects.filter(
            user=user, request_time__gte=one_hour_ago, was_cached=False
        ).count()
        try:
            config = AIConfiguration.get_config()
            limit = config.user_rate_limit_per_hour
        except Exception:
            limit = getattr(settings, 'AI_RATE_LIMIT_PER_HOUR', 10)
        return max(0, limit - recent)

    @classmethod
    def log_request(cls, user, request_type, file=None, tokens_used=0,
                    was_cached=False, success=True, error_message=None,
                    api_key=None):
        return cls.objects.create(
            user=user, request_type=request_type, file=file,
            tokens_used=tokens_used, was_cached=was_cached,
            success=success, error_message=error_message,
            api_key_used=api_key
        )


class AIGenerationJob(models.Model):
    """
    سجل عمليات التوليد بالذكاء الاصطناعي (للمدرسين).
    يتتبع كل عملية توليد (ملخص/أسئلة) مع التكوين والنتائج.
    """
    JOB_TYPES = [
        ('summary', 'تلخيص'),
        ('questions', 'أسئلة'),
        ('mixed', 'ملخص + أسئلة'),
    ]
    STATUS_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('processing', 'قيد المعالجة'),
        ('completed', 'مكتمل'),
        ('failed', 'فشل'),
    ]

    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='ai_generation_jobs', verbose_name='المدرس'
    )
    file = models.ForeignKey(
        'courses.LectureFile', on_delete=models.CASCADE,
        related_name='ai_generation_jobs', verbose_name='الملف'
    )
    job_type = models.CharField(max_length=20, choices=JOB_TYPES, verbose_name='نوع العملية')
    config = models.JSONField(
        default=dict, blank=True,
        verbose_name='التكوين',
        help_text='تكوين المصفوفة: عدد MCQ, TF, SA مع الدرجات'
    )
    user_notes = models.TextField(blank=True, default='', verbose_name='ملاحظات المدرس')
    md_file_path = models.CharField(
        max_length=500, blank=True, null=True,
        verbose_name='مسار ملف النتيجة'
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default='pending', verbose_name='الحالة'
    )
    error_message = models.TextField(blank=True, null=True, verbose_name='رسالة الخطأ')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ الاكتمال')

    class Meta:
        db_table = 'ai_generation_jobs'
        verbose_name = 'عملية توليد AI'
        verbose_name_plural = 'عمليات توليد AI'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['instructor', 'created_at']),
            models.Index(fields=['file']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.get_job_type_display()} - {self.file.title} ({self.get_status_display()})"


class StudentProgress(models.Model):
    """تتبع تقدم الطالب في استعراض الملفات"""
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='study_progress', verbose_name='الطالب'
    )
    file = models.ForeignKey(
        'courses.LectureFile', on_delete=models.CASCADE,
        related_name='student_progress', verbose_name='الملف'
    )
    progress = models.PositiveIntegerField(
        default=0, verbose_name='نسبة التقدم',
        help_text='0-100'
    )
    last_position = models.CharField(
        max_length=100, blank=True, default='',
        verbose_name='آخر موقع',
        help_text='رقم الصفحة أو وقت الفيديو'
    )
    last_accessed = models.DateTimeField(auto_now=True, verbose_name='آخر وصول')
    total_time_seconds = models.PositiveIntegerField(
        default=0, verbose_name='إجمالي وقت الدراسة (ثانية)'
    )

    class Meta:
        db_table = 'student_progress'
        verbose_name = 'تقدم طالب'
        verbose_name_plural = 'تقدم الطلاب'
        unique_together = ('student', 'file')
        ordering = ['-last_accessed']
        indexes = [
            models.Index(fields=['student', 'last_accessed']),
        ]

    def __str__(self):
        return f"{self.student.full_name} - {self.file.title} ({self.progress}%)"
