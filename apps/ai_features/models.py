"""
نماذج وظائف الذكاء الاصطناعي - Enterprise Edition
S-ACM - Smart Academic Content Management System

== التحديثات ==
- إضافة md_file_path لكل من AISummary (لتخزين مسار ملف .md)
- إضافة AIGenerationJob لتتبع عمليات التوليد للمدرسين
- إضافة StudentProgress لتتبع تقدم الطلاب
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


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
        one_hour_ago = timezone.now() - timedelta(hours=1)
        recent = cls.objects.filter(
            user=user, request_time__gte=one_hour_ago, was_cached=False
        ).count()
        limit = getattr(settings, 'AI_RATE_LIMIT_PER_HOUR', 10)
        return recent < limit

    @classmethod
    def get_remaining_requests(cls, user):
        one_hour_ago = timezone.now() - timedelta(hours=1)
        recent = cls.objects.filter(
            user=user, request_time__gte=one_hour_ago, was_cached=False
        ).count()
        limit = getattr(settings, 'AI_RATE_LIMIT_PER_HOUR', 10)
        return max(0, limit - recent)

    @classmethod
    def log_request(cls, user, request_type, file=None, tokens_used=0,
                    was_cached=False, success=True, error_message=None):
        return cls.objects.create(
            user=user, request_type=request_type, file=file,
            tokens_used=tokens_used, was_cached=was_cached,
            success=success, error_message=error_message
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
