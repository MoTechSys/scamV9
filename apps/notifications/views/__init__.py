"""
Views Package - نظام الإشعارات v2
S-ACM - Smart Academic Content Management System
"""

from .common import (
    NotificationListView,
    NotificationDetailView,
    NotificationTrashView,
    MarkAsReadView,
    MarkAllAsReadView,
    DeleteNotificationView,
    RestoreNotificationView,
    EmptyTrashView,
    ArchiveNotificationView,
    UnreadCountView,
    PreferencesView,
)

from .composer import (
    ComposerView,
    SentNotificationsView,
)

from .htmx import (
    HtmxLevelsForMajor,
    HtmxStudentsCount,
    HtmxBellUpdate,
    HtmxSearchStudents,
)

__all__ = [
    # Common
    'NotificationListView',
    'NotificationDetailView',
    'NotificationTrashView',
    'MarkAsReadView',
    'MarkAllAsReadView',
    'DeleteNotificationView',
    'RestoreNotificationView',
    'EmptyTrashView',
    'ArchiveNotificationView',
    'UnreadCountView',
    'PreferencesView',
    # Composer
    'ComposerView',
    'SentNotificationsView',
    # HTMX
    'HtmxLevelsForMajor',
    'HtmxStudentsCount',
    'HtmxBellUpdate',
    'HtmxSearchStudents',
]
