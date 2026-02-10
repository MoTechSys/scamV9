"""
Django settings for S-ACM (Smart Academic Content Management) project.
Configured for: Supabase PostgreSQL + Supabase Storage + Railway Deployment
"""

import os
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
# Allow sandbox and Railway URLs
CSRF_TRUSTED_ORIGINS += [
    'https://*.sandbox.novita.ai',
    'https://*.e2b.dev',
    'https://*.railway.app',
    'https://*.up.railway.app',
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'storages',
    # Project Apps (located in apps/ directory)
    'apps.core.apps.CoreConfig',
    'apps.accounts.apps.AccountsConfig',
    'apps.courses.apps.CoursesConfig',
    'apps.notifications.apps.NotificationsConfig',
    'apps.ai_features.apps.AiFeaturesConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
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

# =============================================================================
# Database Configuration
# =============================================================================
# Supabase PostgreSQL via Transaction Pooler (port 6543)
# Switch to PostgreSQL by setting USE_POSTGRES=True in .env

USE_POSTGRES = os.getenv('USE_POSTGRES', 'False').lower() == 'true'

if USE_POSTGRES:
    # Support DATABASE_URL (Railway auto-injects this)
    _database_url = os.getenv('DATABASE_URL', '')
    if _database_url:
        import dj_database_url
        DATABASES = {
            'default': dj_database_url.parse(
                _database_url,
                conn_max_age=600,
                conn_health_checks=True,
            )
        }
        # Add options for Transaction Pooler compatibility
        DATABASES['default']['OPTIONS'] = {
            'connect_timeout': 5,
        }
        # Disable server-side cursors for Transaction Pooler (PgBouncer)
        DATABASES['default']['DISABLE_SERVER_SIDE_CURSORS'] = True
    else:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': os.getenv('DB_NAME', 'postgres'),
                'USER': os.getenv('DB_USER', 'postgres'),
                'PASSWORD': os.getenv('DB_PASSWORD', ''),
                'HOST': os.getenv('DB_HOST', 'localhost'),
                'PORT': os.getenv('DB_PORT', '5432'),
                'OPTIONS': {
                    'connect_timeout': 5,
                },
                'DISABLE_SERVER_SIDE_CURSORS': True,
                'CONN_MAX_AGE': 600,
                'CONN_HEALTH_CHECKS': True,
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

# =============================================================================
# Static files (CSS, JavaScript, Images)
# =============================================================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise for static files in production
if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
else:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# =============================================================================
# Media files (User uploads) - Supabase Storage (S3-Compatible)
# =============================================================================
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Supabase S3 Storage Configuration
_supabase_s3_endpoint = os.getenv('SUPABASE_S3_ENDPOINT', '')
_supabase_s3_access_key = os.getenv('SUPABASE_S3_ACCESS_KEY', '')
_supabase_s3_secret_key = os.getenv('SUPABASE_S3_SECRET_KEY', '')

if _supabase_s3_access_key and _supabase_s3_secret_key and 'placeholder' not in _supabase_s3_access_key:
    # Use Supabase S3 for media storage
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_STORAGE_BUCKET_NAME = os.getenv('SUPABASE_S3_BUCKET', 'media')
    AWS_S3_REGION_NAME = os.getenv('SUPABASE_S3_REGION', 'ap-south-1')
    AWS_S3_ENDPOINT_URL = _supabase_s3_endpoint
    AWS_ACCESS_KEY_ID = _supabase_s3_access_key
    AWS_SECRET_ACCESS_KEY = _supabase_s3_secret_key
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = True
    AWS_S3_SIGNATURE_VERSION = 's3v4'

# Supabase Public API
SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY', '')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login/Logout URLs
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'core:dashboard_redirect'
LOGOUT_REDIRECT_URL = 'accounts:login'

# =============================================================================
# Email Configuration
# =============================================================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('EMAIL_HOST_USER', 'noreply@s-acm.com')

# =============================================================================
# Manus API Proxy (OpenAI-compatible)
# =============================================================================
MANUS_API_KEY = os.getenv('MANUS_API_KEY', '')
MANUS_BASE_URL = os.getenv('MANUS_BASE_URL', 'https://api.manus.im/api/llm-proxy/v1')
AI_MODEL_NAME = os.getenv('AI_MODEL_NAME', 'gpt-4.1-mini')

# Legacy keys (kept for backward compat)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

# AI Rate Limiting - disabled by default (unlimited usage)
AI_RATE_LIMIT_PER_HOUR = int(os.getenv('AI_RATE_LIMIT_PER_HOUR', 9999))

# =============================================================================
# File Upload Settings
# =============================================================================
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_FILE_EXTENSIONS = ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.txt', '.md']
ALLOWED_VIDEO_EXTENSIONS = ['.mp4', '.webm', '.avi', '.mov']
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']

# =============================================================================
# Session Settings
# =============================================================================
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# =============================================================================
# Security Hardening (Always-on)
# =============================================================================
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'SAMEORIGIN'

# Production security (auto-enabled when DEBUG=False)
if not DEBUG:
    SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'True').lower() == 'true'
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# =============================================================================
# Logging Configuration
# =============================================================================
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': LOGS_DIR / 'django.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
