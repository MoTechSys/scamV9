"""
نماذج وظائف الذكاء الاصطناعي
S-ACM - Smart Academic Content Management System
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class AISummary(models.Model):
    """
    جدول ملخصات الذكاء الاصطناعي (AI_Summaries)
    يخزن الملخصات المولدة بصيغة Markdown
    """
    file = models.OneToOneField(  # تم التعديل إلى OneToOne لمنع تكرار الملخص لنفس الملف
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
        verbose_name='المستخدم الطالب'
    )
    summary_text = models.TextField(
        verbose_name='نص الملخص',
        help_text='الملخص بصيغة Markdown'
    )
    language = models.CharField(
        max_length=10,
        default='ar',
        verbose_name='لغة الملخص'
    )
    word_count = models.PositiveIntegerField(
        default=0,
        verbose_name='عدد الكلمات'
    )
    generated_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ التوليد'
    )
    generation_time = models.FloatField(
        default=0,
        verbose_name='وقت التوليد (ثانية)'
    )
    model_used = models.CharField(
        max_length=100,
        default='gemini-2.0-flash', # تم تحديث الموديل
        verbose_name='النموذج المستخدم'
    )
    is_cached = models.BooleanField(
        default=True,
        verbose_name='مخزن مؤقتاً',
        help_text='يمكن إعادة استخدامه للمستخدمين الآخرين'
    )
    
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
        """
        الحصول على ملخص مخزن مؤقتاً للملف
        """
        return cls.objects.filter(
            file=file,
            is_cached=True
        ).first()


class AIGeneratedQuestion(models.Model):
    """
    جدول الأسئلة المولدة بالذكاء الاصطناعي (تم تحديث الاسم والهيكل ليتوافق مع Services)
    يخزن كل سؤال كسجل مستقل لسهولة التعامل معه في الاختبارات وبنوك الأسئلة
    """
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
    # المستخدم اختياري هنا لأن الأسئلة قد تكون عامة للمقرر
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requested_questions',
        verbose_name='المستخدم الطالب'
    )
    
    question_text = models.TextField(verbose_name='نص السؤال')
    
    question_type = models.CharField(
        max_length=50,
        choices=QUESTION_TYPES,
        default='short_answer',
        verbose_name='نوع السؤال'
    )
    
    options = models.JSONField(
        null=True, 
        blank=True, 
        help_text='قائمة الخيارات للأسئلة متعددة الاختيار'
    )
    
    correct_answer = models.TextField(verbose_name='الإجابة الصحيحة')
    
    explanation = models.TextField(
        null=True, 
        blank=True, 
        verbose_name='الشرح / التفسير'
    )
    
    difficulty_level = models.CharField(
        max_length=20,
        default='medium',
        verbose_name='مستوى الصعوبة'
    )
    
    generated_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ التوليد'
    )
    
    is_cached = models.BooleanField(
        default=True,
        verbose_name='مخزن مؤقتاً'
    )
    
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
        """
        الحصول على أسئلة مخزنة مؤقتاً للملف
        """
        if question_type == 'mixed':
            return cls.objects.filter(file=file, is_cached=True)
        return cls.objects.filter(
            file=file,
            question_type=question_type,
            is_cached=True
        )


class AIChat(models.Model):
    """
    جدول محادثات الذكاء الاصطناعي (اسأل المستند)
    """
    file = models.ForeignKey(
        'courses.LectureFile',
        on_delete=models.CASCADE,
        related_name='ai_chats',
        verbose_name='الملف'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_chats',
        verbose_name='المستخدم'
    )
    question = models.TextField(
        verbose_name='السؤال'
    )
    answer = models.TextField(
        verbose_name='الإجابة'
    )
    is_helpful = models.BooleanField(
        null=True,
        blank=True,
        verbose_name='مفيد',
        help_text='تقييم المستخدم لجودة الإجابة'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ السؤال'
    )
    response_time = models.FloatField(
        default=0,
        verbose_name='وقت الاستجابة (ثانية)'
    )
    
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
    """
    جدول سجل استخدام الذكاء الاصطناعي
    للتحكم في Rate Limiting
    """
    REQUEST_TYPES = [
        ('summary', 'تلخيص'),
        ('questions', 'توليد أسئلة'),
        ('chat', 'محادثة'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_usage_logs',
        verbose_name='المستخدم'
    )
    request_type = models.CharField(
        max_length=20,
        choices=REQUEST_TYPES,
        verbose_name='نوع الطلب'
    )
    file = models.ForeignKey(
        'courses.LectureFile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_usage_logs',
        verbose_name='الملف'
    )
    tokens_used = models.PositiveIntegerField(
        default=0,
        verbose_name='التوكنات المستخدمة'
    )
    request_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name='وقت الطلب'
    )
    was_cached = models.BooleanField(
        default=False,
        verbose_name='من الذاكرة المؤقتة'
    )
    success = models.BooleanField(
        default=True,
        verbose_name='ناجح'
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        verbose_name='رسالة الخطأ'
    )
    
    class Meta:
        db_table = 'ai_usage_logs'
        verbose_name = 'سجل استخدام AI'
        verbose_name_plural = 'سجلات استخدام AI'
        ordering = ['-request_time']
        indexes = [
            models.Index(fields=['user', 'request_time']),
            models.Index(fields=['request_type']),
        ]
    
    def __str__(self):
        return f"{self.user.academic_id} - {self.get_request_type_display()}"
    
    @classmethod
    def check_rate_limit(cls, user):
        """
        التحقق من حد الاستخدام للمستخدم
        يسمح بـ 10 طلبات في الساعة
        """
        one_hour_ago = timezone.now() - timedelta(hours=1)
        recent_requests = cls.objects.filter(
            user=user,
            request_time__gte=one_hour_ago,
            was_cached=False  # لا نحسب الطلبات من الذاكرة المؤقتة
        ).count()
        
        limit = getattr(settings, 'AI_RATE_LIMIT_PER_HOUR', 10)
        return recent_requests < limit
    
    @classmethod
    def get_remaining_requests(cls, user):
        """
        الحصول على عدد الطلبات المتبقية للمستخدم
        """
        one_hour_ago = timezone.now() - timedelta(hours=1)
        recent_requests = cls.objects.filter(
            user=user,
            request_time__gte=one_hour_ago,
            was_cached=False
        ).count()
        
        limit = getattr(settings, 'AI_RATE_LIMIT_PER_HOUR', 10)
        return max(0, limit - recent_requests)
    
    @classmethod
    def log_request(cls, user, request_type, file=None, tokens_used=0, 
                    was_cached=False, success=True, error_message=None):
        """
        تسجيل طلب AI جديد
        """
        return cls.objects.create(
            user=user,
            request_type=request_type,
            file=file,
            tokens_used=tokens_used,
            was_cached=was_cached,
            success=success,
            error_message=error_message
        )