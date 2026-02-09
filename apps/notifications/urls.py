"""
URLs لنظام الإشعارات v2
S-ACM - Smart Academic Content Management System
"""

from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # === User Notifications (مشترك) ===
    path('', views.NotificationListView.as_view(), name='list'),
    path('<int:pk>/', views.NotificationDetailView.as_view(), name='detail'),
    path('<int:pk>/read/', views.MarkAsReadView.as_view(), name='mark_read'),
    path('mark-all-read/', views.MarkAllAsReadView.as_view(), name='mark_all_read'),
    path('<int:pk>/delete/', views.DeleteNotificationView.as_view(), name='delete'),
    path('<int:pk>/restore/', views.RestoreNotificationView.as_view(), name='restore'),
    path('<int:pk>/archive/', views.ArchiveNotificationView.as_view(), name='archive'),
    path('unread-count/', views.UnreadCountView.as_view(), name='unread_count'),
    path('preferences/', views.PreferencesView.as_view(), name='preferences'),

    # === Trash (سلة المهملات) ===
    path('trash/', views.NotificationTrashView.as_view(), name='trash'),
    path('trash/empty/', views.EmptyTrashView.as_view(), name='empty_trash'),

    # === Composer (إنشاء إشعار - دكتور/أدمن) ===
    path('compose/', views.ComposerView.as_view(), name='compose'),
    path('sent/', views.SentNotificationsView.as_view(), name='sent'),

    # === Backward Compatibility (التوافق الخلفي) ===
    path('instructor/create/', views.ComposerView.as_view(), name='instructor_create'),
    path('instructor/sent/', views.SentNotificationsView.as_view(), name='instructor_sent'),
    path('admin/create/', views.ComposerView.as_view(), name='admin_create'),
    path('admin/', views.SentNotificationsView.as_view(), name='admin_list'),

    # === HTMX Endpoints ===
    path('htmx/levels/', views.HtmxLevelsForMajor.as_view(), name='htmx_levels'),
    path('htmx/students-count/', views.HtmxStudentsCount.as_view(), name='htmx_students_count'),
    path('htmx/bell/', views.HtmxBellUpdate.as_view(), name='htmx_bell'),
    path('htmx/search-students/', views.HtmxSearchStudents.as_view(), name='htmx_search_students'),
]
