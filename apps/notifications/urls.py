"""
URLs لتطبيق notifications
S-ACM - Smart Academic Content Management System
"""

from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # User Notifications
    path('', views.NotificationListView.as_view(), name='list'),
    path('<int:pk>/', views.NotificationDetailView.as_view(), name='detail'),
    path('<int:pk>/read/', views.MarkAsReadView.as_view(), name='mark_read'),
    path('mark-all-read/', views.MarkAllAsReadView.as_view(), name='mark_all_read'),
    path('<int:pk>/delete/', views.DeleteNotificationView.as_view(), name='delete'),
    path('unread-count/', views.UnreadCountView.as_view(), name='unread_count'),
    
    # Instructor Notifications
    path('instructor/create/', views.InstructorNotificationCreateView.as_view(), name='instructor_create'),
    path('instructor/', views.InstructorNotificationListView.as_view(), name='instructor_list'),
    
    # Admin Notifications
    path('admin/create/', views.AdminNotificationCreateView.as_view(), name='admin_create'),
    path('admin/', views.AdminNotificationListView.as_view(), name='admin_list'),
]
