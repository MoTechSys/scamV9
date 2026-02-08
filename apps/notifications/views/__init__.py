"""
Views Package - حزمة عروض الإشعارات
S-ACM - Smart Academic Content Management System

تصدير جميع الـ Views للتوافق مع urls.py
"""

# Common Views - العمليات المشتركة
from .common import (
    NotificationListView,
    NotificationDetailView,
    MarkAsReadView,
    MarkAllAsReadView,
    DeleteNotificationView,
    UnreadCountView,
)

# Instructor Views - عروض المدرس
from .instructor import (
    InstructorNotificationCreateView,
    InstructorNotificationListView,
)

# Admin Views - عروض الأدمن
from .admin import (
    AdminNotificationCreateView,
    AdminNotificationListView,
)

__all__ = [
    # Common
    'NotificationListView',
    'NotificationDetailView',
    'MarkAsReadView',
    'MarkAllAsReadView',
    'DeleteNotificationView',
    'UnreadCountView',
    # Instructor
    'InstructorNotificationCreateView',
    'InstructorNotificationListView',
    # Admin
    'AdminNotificationCreateView',
    'AdminNotificationListView',
]
