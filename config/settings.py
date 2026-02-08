"""
Django settings for S-ACM (Smart Academic Content Management) project.
"""

import os
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-default-key')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') + ['*']

# CSRF Trusted Origins for external access
_csrf_env = os.getenv('CSRF_TRUSTED_ORIGINS', '')
CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_env.split(',') if o.strip()] if _csrf_env else []
# Allow sandbox URLs
CSRF_TRUSTED_ORIGINS += ['https://*.sandbox.novita.ai', 'https://*.e2b.dev']

# Application definition
INSTALLED_APPS = [
    # Unfold - Modern Admin Theme (must be before django.contrib.admin)
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Project Apps (located in apps/ directory)
    'apps.core.apps.CoreConfig',
    'apps.accounts.apps.AccountsConfig',
    'apps.courses.apps.CoursesConfig',
    'apps.notifications.apps.NotificationsConfig',
    'apps.ai_features.apps.AiFeaturesConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.core.middleware.PermissionMiddleware',  # Dynamic permissions & menu
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Custom context processors
                'apps.core.context_processors.site_settings',
                'apps.core.context_processors.user_notifications',
                'apps.core.context_processors.user_role_info',
                'apps.core.context_processors.current_semester',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
# Using SQLite for development (easy setup and fast testing)
# Switch to PostgreSQL for production by setting USE_POSTGRES=True in .env
USE_POSTGRES = os.getenv('USE_POSTGRES', 'False').lower() == 'true'

if USE_POSTGRES:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 's_acm_db'),
            'USER': os.getenv('DB_USER', 'postgres'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
        }
    }
else:
    # SQLite for development (default)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'ar'
TIME_ZONE = 'Asia/Riyadh'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (User uploads)
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login/Logout URLs
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'core:dashboard_redirect'
LOGOUT_REDIRECT_URL = 'accounts:login'

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('EMAIL_HOST_USER', 'noreply@s-acm.com')

# Google Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

# AI Rate Limiting (requests per hour per user)
AI_RATE_LIMIT_PER_HOUR = int(os.getenv('AI_RATE_LIMIT_PER_HOUR', 10))

# File Upload Settings
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_FILE_EXTENSIONS = ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.txt', '.md']
ALLOWED_VIDEO_EXTENSIONS = ['.mp4', '.webm', '.avi', '.mov']
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']

# Session Settings
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# =============================================================================
# Logging Configuration
# =============================================================================
# Create logs directory if it doesn't exist
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'detailed': {
            'format': '[{asctime}] {levelname} [{name}:{lineno}] {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'django.log',
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 5,
            'formatter': 'detailed',
            'encoding': 'utf-8',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'errors.log',
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 10,
            'formatter': 'detailed',
            'encoding': 'utf-8',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'security.log',
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 10,
            'formatter': 'detailed',
            'encoding': 'utf-8',
        },
        'ai_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'ai_features.log',
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 5,
            'formatter': 'detailed',
            'encoding': 'utf-8',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['error_file', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'accounts': {
            'handlers': ['console', 'file', 'security_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'courses': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'ai_features': {
            'handlers': ['console', 'ai_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'notifications': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# =============================================================================
# Custom Error Pages
# =============================================================================
# These handlers are used when DEBUG=False
handler404 = 'apps.core.views.custom_404'
handler500 = 'apps.core.views.custom_500'
handler403 = 'apps.core.views.custom_403'

# =============================================================================
# Security Settings (for production)
# =============================================================================
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True



    # HSTS Settings (uncomment for HTTPS)
    # SECURE_HSTS_SECONDS = 31536000  # 1 year
    # SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    # SECURE_HSTS_PRELOAD = True
    # SECURE_SSL_REDIRECT = True

# =============================================================================
# Django Unfold Admin Theme Settings
# =============================================================================
from django.templatetags.static import static
from django.urls import reverse_lazy

UNFOLD = {
    "SITE_TITLE": "S-ACM",
    "SITE_HEADER": "S-ACM",
    "SITE_URL": "/",
    "SITE_SYMBOL": "school",  # Material icon
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    
    # Colors - Primary theme
    "COLORS": {
        "primary": {
            "50": "250 245 255",
            "100": "243 232 255",
            "200": "233 213 255",
            "300": "216 180 254",
            "400": "192 132 252",
            "500": "168 85 247",
            "600": "147 51 234",
            "700": "126 34 206",
            "800": "107 33 168",
            "900": "88 28 135",
            "950": "59 7 100",
        },
    },
    
    # Sidebar Navigation
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": "إدارة الحسابات",
                "separator": True,
                "items": [
                    {
                        "title": "المستخدمين",
                        "icon": "person",
                        "link": reverse_lazy("admin:accounts_user_changelist"),
                    },
                    {
                        "title": "الأدوار",
                        "icon": "badge",
                        "link": reverse_lazy("admin:accounts_role_changelist"),
                    },
                    {
                        "title": "الصلاحيات",
                        "icon": "key",
                        "link": reverse_lazy("admin:accounts_permission_changelist"),
                    },
                    {
                        "title": "التخصصات",
                        "icon": "school",
                        "link": reverse_lazy("admin:accounts_major_changelist"),
                    },
                    {
                        "title": "المستويات",
                        "icon": "layers",
                        "link": reverse_lazy("admin:accounts_level_changelist"),
                    },
                    {
                        "title": "الفصول الدراسية",
                        "icon": "calendar_month",
                        "link": reverse_lazy("admin:accounts_semester_changelist"),
                    },
                ],
            },
            {
                "title": "إدارة المقررات",
                "separator": True,
                "items": [
                    {
                        "title": "المقررات",
                        "icon": "book",
                        "link": reverse_lazy("admin:courses_course_changelist"),
                    },
                    {
                        "title": "الملفات",
                        "icon": "description",
                        "link": reverse_lazy("admin:courses_lecturefile_changelist"),
                    },
                ],
            },
            {
                "title": "محرك الذكاء الاصطناعي",
                "separator": True,
                "items": [
                    {
                        "title": "لوحة مراقبة AI",
                        "icon": "monitoring",
                        "link": "/scam-admin/ai_features/apikey/ai-dashboard/",
                    },
                    {
                        "title": "إعدادات AI",
                        "icon": "tune",
                        "link": reverse_lazy("admin:ai_features_aiconfiguration_changelist"),
                    },
                    {
                        "title": "مفاتيح API",
                        "icon": "vpn_key",
                        "link": reverse_lazy("admin:ai_features_apikey_changelist"),
                    },
                    {
                        "title": "الملخصات",
                        "icon": "summarize",
                        "link": reverse_lazy("admin:ai_features_aisummary_changelist"),
                    },
                    {
                        "title": "الأسئلة المولدة",
                        "icon": "quiz",
                        "link": reverse_lazy("admin:ai_features_aigeneratedquestion_changelist"),
                    },
                    {
                        "title": "المحادثات",
                        "icon": "chat",
                        "link": reverse_lazy("admin:ai_features_aichat_changelist"),
                    },
                    {
                        "title": "سجل الاستخدام",
                        "icon": "analytics",
                        "link": reverse_lazy("admin:ai_features_aiusagelog_changelist"),
                    },
                ],
            },
            {
                "title": "الإشعارات",
                "separator": True,
                "items": [
                    {
                        "title": "الإشعارات",
                        "icon": "notifications",
                        "link": reverse_lazy("admin:notifications_notification_changelist"),
                    },
                ],
            },
            {
                "title": "النظام",
                "separator": True,
                "items": [
                    {
                        "title": "إعدادات النظام",
                        "icon": "settings",
                        "link": reverse_lazy("admin:core_systemsetting_changelist"),
                    },
                    {
                        "title": "سجلات التدقيق",
                        "icon": "history",
                        "link": reverse_lazy("admin:core_auditlog_changelist"),
                    },
                ],
            },
        ],
    },
}
