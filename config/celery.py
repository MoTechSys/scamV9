"""
Celery Configuration
S-ACM - Smart Academic Content Management System

هذا الملف يحتوي على تكوين Celery للمهام غير المتزامنة
"""

import os
from celery import Celery
from django.conf import settings

# تعيين إعدادات Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# إنشاء تطبيق Celery
app = Celery('scam')

# تحميل الإعدادات من Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# اكتشاف المهام تلقائياً من التطبيقات
app.autodiscover_tasks()


# ========== إعدادات Celery الافتراضية ==========

app.conf.update(
    # Broker (Redis)
    broker_url=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    
    # Result Backend
    result_backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    
    # Serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Timezone
    timezone='Asia/Riyadh',
    enable_utc=True,
    
    # Task Settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Retry Settings
    task_default_retry_delay=60,
    task_max_retries=3,
    
    # Rate Limiting
    task_annotations={
        'apps.ai_features.services.generate_summary_async': {
            'rate_limit': '10/m'  # 10 مهام في الدقيقة
        },
        'apps.ai_features.services.generate_questions_async': {
            'rate_limit': '5/m'  # 5 مهام في الدقيقة
        },
    },
    
    # Worker Settings
    worker_prefetch_multiplier=1,
    worker_concurrency=4,
    
    # Task Time Limits
    task_soft_time_limit=300,  # 5 دقائق
    task_time_limit=600,  # 10 دقائق
    
    # Result Expiration
    result_expires=3600,  # ساعة واحدة
)


# ========== Beat Schedule (المهام المجدولة) ==========

app.conf.beat_schedule = {
    # تنظيف الكاش القديم
    'cleanup-old-cache': {
        'task': 'apps.core.tasks.cleanup_old_cache',
        'schedule': 3600.0,  # كل ساعة
    },
    # تنظيف الملفات المحذوفة
    'cleanup-deleted-files': {
        'task': 'apps.courses.tasks.cleanup_deleted_files',
        'schedule': 86400.0,  # كل يوم
    },
    # إرسال تقرير يومي
    'send-daily-report': {
        'task': 'apps.core.tasks.send_daily_report',
        'schedule': 86400.0,  # كل يوم
        'options': {'expires': 3600}
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """مهمة للاختبار"""
    print(f'Request: {self.request!r}')
