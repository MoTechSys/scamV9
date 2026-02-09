"""
Context Processors للمتغيرات العامة في القوالب
S-ACM - Smart Academic Content Management System
"""

from django.conf import settings


def site_settings(request):
    """
    إضافة إعدادات الموقع للقوالب
    """
    return {
        'SITE_NAME': 'S-ACM',
        'SITE_FULL_NAME': 'نظام إدارة المحتوى الأكاديمي الذكي',
        'SITE_VERSION': '1.0.0',
        'DEBUG': settings.DEBUG,
    }


def user_notifications(request):
    """
    إضافة عدد الإشعارات غير المقروءة + آخر 5 إشعارات للـ Navbar dropdown
    يستخدم NotificationService المركزي
    """
    if request.user.is_authenticated:
        try:
            from apps.notifications.services import NotificationService
            unread_count = NotificationService.get_unread_count(request.user)
            recent_notifications = NotificationService.get_recent_notifications(
                request.user, limit=5
            )
            return {
                'unread_count': unread_count,
                'recent_notifications': recent_notifications,
            }
        except Exception:
            pass
    return {'unread_count': 0, 'recent_notifications': []}



def user_role_info(request):
    """
    إضافة معلومات دور المستخدم والصلاحيات والقائمة الديناميكية
    """
    if request.user.is_authenticated:
        role = request.user.role
        
        # الحصول على القائمة والصلاحيات من الـ middleware
        menu_items = getattr(request, 'menu_items', [])
        user_permissions = getattr(request, 'user_permissions', set())
        
        return {
            'user_role': role.display_name if role else None,
            'user_role_code': role.code if role else None,
            'is_admin': request.user.is_admin(),
            'is_instructor': request.user.is_instructor(),
            'is_student': request.user.is_student(),
            # القائمة الديناميكية
            'menu_items': menu_items,
            'user_permissions': user_permissions,
            # دالة للتحقق من الصلاحية في القوالب
            'has_perm': lambda p: '__all__' in user_permissions or p in user_permissions,
        }
    return {
        'user_role': None,
        'user_role_code': None,
        'is_admin': False,
        'is_instructor': False,
        'is_student': False,
        'menu_items': [],
        'user_permissions': set(),
        'has_perm': lambda p: False,
    }


def current_semester(request):
    """
    إضافة الفصل الدراسي الحالي - مع Caching لتحسين الأداء
    """
    from django.core.cache import cache
    from apps.accounts.models import Semester
    
    cache_key = 'current_semester_obj'
    semester = cache.get(cache_key)
    
    if semester is None:
        try:
            semester = Semester.objects.filter(is_current=True).first()
            # Cache for 5 minutes
            cache.set(cache_key, semester, 300)
        except:
            semester = None
    
    return {'current_semester': semester}

