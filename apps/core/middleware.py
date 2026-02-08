"""
Middleware للأمان والأداء
S-ACM - Smart Academic Content Management System

هذا الملف يحتوي على Middleware للـ:
1. Rate Limiting لمنع هجمات DoS
2. Security Headers
3. Request Logging
"""

import time
import logging
from collections import defaultdict
from threading import Lock
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger('security')


class RateLimitMiddleware:
    """
    Rate Limiting Middleware لمنع هجمات DoS
    
    يحد من عدد الطلبات لكل IP خلال فترة زمنية محددة
    
    الإعدادات (في settings.py):
    - RATE_LIMIT_REQUESTS: عدد الطلبات المسموحة (افتراضي: 100)
    - RATE_LIMIT_WINDOW: الفترة الزمنية بالثواني (افتراضي: 60)
    - RATE_LIMIT_ENABLED: تفعيل/تعطيل (افتراضي: True)
    
    Security Fix: DoS Prevention
    - يمنع المستخدمين من إرسال عدد كبير من الطلبات
    - يحمي endpoints الحساسة مثل Login و CSV Import
    """
    
    # الحدود الافتراضية
    DEFAULT_REQUESTS = 100
    DEFAULT_WINDOW = 60  # ثانية
    
    # حدود خاصة لـ endpoints معينة
    ENDPOINT_LIMITS = {
        '/accounts/login/': {'requests': 5, 'window': 60},  # 5 محاولات/دقيقة
        '/accounts/activate/': {'requests': 10, 'window': 60},
        '/accounts/password-reset/': {'requests': 3, 'window': 60},
        '/admin/users/import/': {'requests': 2, 'window': 60},  # CSV Import
        '/api/ai/': {'requests': 10, 'window': 60},  # AI endpoints
    }
    
    def __init__(self, get_response):
        self.get_response = get_response
        self._lock = Lock()
        
        # التحقق من تفعيل Rate Limiting
        self.enabled = getattr(settings, 'RATE_LIMIT_ENABLED', True)
        self.default_requests = getattr(settings, 'RATE_LIMIT_REQUESTS', self.DEFAULT_REQUESTS)
        self.default_window = getattr(settings, 'RATE_LIMIT_WINDOW', self.DEFAULT_WINDOW)
    
    def __call__(self, request):
        if not self.enabled:
            return self.get_response(request)
        
        # الحصول على IP العميل
        client_ip = self._get_client_ip(request)
        
        # الحصول على الحدود لهذا الـ endpoint
        limits = self._get_limits_for_path(request.path)
        
        # التحقق من Rate Limit
        if not self._check_rate_limit(client_ip, request.path, limits):
            logger.warning(
                f"Rate limit exceeded for IP {client_ip} on {request.path}"
            )
            return self._rate_limit_response(request)
        
        return self.get_response(request)
    
    def _get_client_ip(self, request) -> str:
        """الحصول على IP العميل الحقيقي"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')
    
    def _get_limits_for_path(self, path: str) -> dict:
        """الحصول على الحدود المناسبة للمسار"""
        for endpoint, limits in self.ENDPOINT_LIMITS.items():
            if path.startswith(endpoint):
                return limits
        return {'requests': self.default_requests, 'window': self.default_window}
    
    def _check_rate_limit(self, client_ip: str, path: str, limits: dict) -> bool:
        """
        التحقق من Rate Limit باستخدام Cache
        
        Returns:
            bool: True إذا كان الطلب مسموحاً
        """
        cache_key = f"rate_limit:{client_ip}:{path}"
        
        with self._lock:
            # الحصول على البيانات من الكاش
            data = cache.get(cache_key, {'count': 0, 'start_time': time.time()})
            
            current_time = time.time()
            
            # إعادة تعيين إذا انتهت الفترة
            if current_time - data['start_time'] > limits['window']:
                data = {'count': 1, 'start_time': current_time}
                cache.set(cache_key, data, limits['window'])
                return True
            
            # زيادة العداد
            data['count'] += 1
            
            # التحقق من تجاوز الحد
            if data['count'] > limits['requests']:
                return False
            
            cache.set(cache_key, data, limits['window'])
            return True
    
    def _rate_limit_response(self, request):
        """إنشاء استجابة Rate Limit"""
        if request.headers.get('Accept', '').find('application/json') != -1:
            return JsonResponse(
                {'error': 'تم تجاوز الحد المسموح من الطلبات. يرجى المحاولة لاحقاً.'},
                status=429
            )
        return HttpResponse(
            'تم تجاوز الحد المسموح من الطلبات. يرجى المحاولة لاحقاً.',
            status=429
        )


class SecurityHeadersMiddleware:
    """
    Middleware لإضافة Security Headers
    
    يضيف headers أمنية مهمة لكل استجابة
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Content Security Policy
        if not response.has_header('Content-Security-Policy'):
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https://generativelanguage.googleapis.com;"
            )
        
        # X-Content-Type-Options
        response['X-Content-Type-Options'] = 'nosniff'
        
        # X-Frame-Options
        if not response.has_header('X-Frame-Options'):
            response['X-Frame-Options'] = 'SAMEORIGIN'
        
        # Referrer-Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions-Policy
        response['Permissions-Policy'] = (
            'accelerometer=(), camera=(), geolocation=(), gyroscope=(), '
            'magnetometer=(), microphone=(), payment=(), usb=()'
        )
        
        return response


class RequestLoggingMiddleware:
    """
    Middleware لتسجيل الطلبات
    
    يسجل معلومات مهمة عن كل طلب للمراقبة والتحليل
    """
    
    # المسارات التي لا يتم تسجيلها
    EXCLUDED_PATHS = ['/static/', '/media/', '/favicon.ico']
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # تخطي المسارات المستثناة
        if any(request.path.startswith(p) for p in self.EXCLUDED_PATHS):
            return self.get_response(request)
        
        start_time = time.time()
        
        response = self.get_response(request)
        
        # حساب وقت المعالجة
        duration = time.time() - start_time
        
        # تسجيل الطلب
        self._log_request(request, response, duration)
        
        return response
    
    def _log_request(self, request, response, duration: float):
        """تسجيل معلومات الطلب"""
        user = getattr(request, 'user', None)
        user_id = user.academic_id if user and user.is_authenticated else 'anonymous'
        
        log_data = {
            'method': request.method,
            'path': request.path,
            'status': response.status_code,
            'duration_ms': round(duration * 1000, 2),
            'user': user_id,
            'ip': self._get_client_ip(request),
        }
        
        # تسجيل الطلبات البطيئة كتحذير
        if duration > 1.0:  # أكثر من ثانية
            logger.warning(f"Slow request: {log_data}")
        elif response.status_code >= 400:
            logger.warning(f"Error response: {log_data}")
        else:
            logger.debug(f"Request: {log_data}")
    
    def _get_client_ip(self, request) -> str:
        """الحصول على IP العميل"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')


class FileUploadSecurityMiddleware:
    """
    Middleware لأمان رفع الملفات
    
    يتحقق من:
    1. حجم الملف
    2. نوع الملف
    3. امتداد الملف
    """
    
    # الحد الأقصى لحجم الملف (50MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024
    
    # الامتدادات المسموحة
    ALLOWED_EXTENSIONS = {
        '.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx',
        '.txt', '.md', '.csv',
        '.jpg', '.jpeg', '.png', '.gif', '.webp',
        '.mp4', '.webm', '.mp3', '.wav',
        '.zip', '.rar', '.7z'
    }
    
    # MIME types المسموحة
    ALLOWED_MIME_TYPES = {
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-powerpoint',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/plain',
        'text/markdown',
        'text/csv',
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/webp',
        'video/mp4',
        'video/webm',
        'audio/mpeg',
        'audio/wav',
        'application/zip',
        'application/x-rar-compressed',
        'application/x-7z-compressed',
    }
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # التحقق فقط من طلبات POST مع ملفات
        if request.method == 'POST' and request.FILES:
            error = self._validate_files(request.FILES)
            if error:
                logger.warning(f"File upload blocked: {error}")
                return JsonResponse({'error': error}, status=400)
        
        return self.get_response(request)
    
    def _validate_files(self, files) -> str:
        """
        التحقق من صحة الملفات المرفوعة
        
        Returns:
            str: رسالة خطأ أو None إذا كانت الملفات صالحة
        """
        import os
        
        for field_name, file in files.items():
            # التحقق من الحجم
            if file.size > self.MAX_FILE_SIZE:
                return f'حجم الملف {file.name} يتجاوز الحد المسموح ({self.MAX_FILE_SIZE / 1024 / 1024:.0f}MB)'
            
            # التحقق من الامتداد
            _, ext = os.path.splitext(file.name)
            if ext.lower() not in self.ALLOWED_EXTENSIONS:
                return f'امتداد الملف {ext} غير مسموح'
            
            # التحقق من MIME type
            content_type = file.content_type
            if content_type not in self.ALLOWED_MIME_TYPES:
                # السماح بـ application/octet-stream للملفات غير المعروفة
                if content_type != 'application/octet-stream':
                    return f'نوع الملف {content_type} غير مسموح'
        
        return None


# ========== Permission Middleware ==========

from django.utils.functional import SimpleLazyObject


def get_user_permissions(request):
    """الحصول على صلاحيات المستخدم (lazy loading)"""
    if not hasattr(request, '_cached_permissions'):
        if request.user.is_authenticated:
            if request.user.is_superuser or request.user.is_admin():
                request._cached_permissions = {'__all__'}
            else:
                request._cached_permissions = request.user.get_permissions()
        else:
            request._cached_permissions = set()
    return request._cached_permissions


def get_user_menu(request):
    """الحصول على قائمة المستخدم (lazy loading)"""
    if not hasattr(request, '_cached_menu'):
        from .menu import get_menu_for_user
        if request.user.is_authenticated:
            request._cached_menu = get_menu_for_user(request.user)
        else:
            request._cached_menu = []
    return request._cached_menu


class PermissionMiddleware:
    """
    Middleware لتحميل الصلاحيات والقائمة تلقائياً
    
    يضيف للـ request:
        - request.user_permissions: مجموعة صلاحيات المستخدم
        - request.menu_items: قائمة العناصر المرئية للمستخدم
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # استخدام SimpleLazyObject لتحميل البيانات عند الحاجة فقط
        request.user_permissions = SimpleLazyObject(lambda: get_user_permissions(request))
        request.menu_items = SimpleLazyObject(lambda: get_user_menu(request))
        
        return self.get_response(request)

