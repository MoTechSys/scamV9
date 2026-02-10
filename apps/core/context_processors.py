"""
Context Processors للمتغيرات العامة في القوالب
S-ACM - Smart Academic Content Management System
"""

import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def site_settings(request):
    """إضافة إعدادات الموقع للقوالب"""
    try:
        return {
            'SITE_NAME': 'S-ACM',
            'SITE_FULL_NAME': 'نظام إدارة المحتوى الأكاديمي الذكي',
            'SITE_VERSION': '1.0.0',
            'DEBUG': settings.DEBUG,
        }
    except Exception as e:
        logger.error(f"site_settings context processor error: {e}")
        return {'SITE_NAME': 'S-ACM', 'DEBUG': False}


def user_notifications(request):
    """إضافة عدد الإشعارات غير المقروءة + آخر 5 إشعارات للـ Navbar dropdown"""
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
        except Exception as e:
            logger.error(f"user_notifications context processor error: {e}")
    return {'unread_count': 0, 'recent_notifications': []}


def user_role_info(request):
    """إضافة معلومات دور المستخدم والصلاحيات والقائمة الديناميكية"""
    if request.user.is_authenticated:
        try:
            role = request.user.role
            menu_items = getattr(request, 'menu_items', [])
            user_permissions = getattr(request, 'user_permissions', set())

            return {
                'user_role': role.display_name if role else None,
                'user_role_code': role.code if role else None,
                'is_admin': request.user.is_admin(),
                'is_instructor': request.user.is_instructor(),
                'is_student': request.user.is_student(),
                'menu_items': menu_items,
                'user_permissions': user_permissions,
                'has_perm': lambda p: '__all__' in user_permissions or p in user_permissions,
            }
        except Exception as e:
            logger.error(f"user_role_info context processor error: {e}")
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
    """إضافة الفصل الدراسي الحالي - مع Caching لتحسين الأداء"""
    try:
        from django.core.cache import cache
        from apps.accounts.models import Semester

        cache_key = 'current_semester_obj'
        semester = cache.get(cache_key)

        if semester is None:
            semester = Semester.objects.filter(is_current=True).first()
            cache.set(cache_key, semester, 300)

        return {'current_semester': semester}
    except Exception as e:
        logger.error(f"current_semester context processor error: {e}")
        return {'current_semester': None}
