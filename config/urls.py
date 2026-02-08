"""
URL configuration for S-ACM project.
S-ACM - Smart Academic Content Management System
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django Admin
    path('scam-admin/', admin.site.urls),
    
    # Core App (Home, Dashboard redirect)
    path('', include('apps.core.urls')),
    
    # Accounts App (Authentication, Profile, User Management)
    path('accounts/', include('apps.accounts.urls')),
    
    # Courses App (Courses, Files, Student/Instructor panels)
    path('courses/', include('apps.courses.urls')),
    
    # Notifications App
    path('notifications/', include('apps.notifications.urls')),
    
    # AI Features App
    path('ai/', include('apps.ai_features.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
# تخصيص نصوص لوحة الإدارة لمشروع S-ACM
admin.site.site_header = "إدارة S-ACM"
admin.site.site_title = "لوحة تحكم S-ACM"
admin.site.index_title = "مرحباً بك في نظام إدارة المحتوى الأكاديمي الذكي"