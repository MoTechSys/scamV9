"""
Views Package - نظام الإشعارات v3
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
    NotificationManagementView,
)

from .composer import (
    ComposerView,
    SentNotificationsView,
    HideSentNotificationView,
    UnhideSentNotificationView,
    DeleteSentNotificationView,
    RestoreSentNotificationView,
)

from .htmx import (
    HtmxLevelsForMajor,
    HtmxStudentsCount,
    HtmxBellUpdate,
    HtmxSearchStudents,
    HtmxSearchInstructors,
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
    'NotificationManagementView',
    # Composer
    'ComposerView',
    'SentNotificationsView',
    'HideSentNotificationView',
    'UnhideSentNotificationView',
    'DeleteSentNotificationView',
    'RestoreSentNotificationView',
    # HTMX
    'HtmxLevelsForMajor',
    'HtmxStudentsCount',
    'HtmxBellUpdate',
    'HtmxSearchStudents',
    'HtmxSearchInstructors',
]
