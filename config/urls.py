"""
URL configuration for S-ACM project - Enterprise Edition.
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

    # Accounts App (Authentication, Profile)
    path('accounts/', include('apps.accounts.urls')),

    # NEW: Instructor App (Enterprise)
    path('instructor/', include('apps.instructor.urls')),

    # NEW: Student App (Enterprise)
    path('student/', include('apps.student.urls')),

    # Streaming Engine
    path('stream/', include('apps.core.streaming_urls')),

    # Courses App (Legacy admin routes + file download/view)
    path('courses/', include('apps.courses.urls')),

    # Notifications App
    path('notifications/', include('apps.notifications.urls')),

    # AI Features App (Legacy compatibility)
    path('ai/', include('apps.ai_features.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

# Admin site customization
admin.site.site_header = "إدارة S-ACM"
admin.site.site_title = "لوحة تحكم S-ACM"
admin.site.index_title = "مرحباً بك في نظام إدارة المحتوى الأكاديمي الذكي"

# Custom error handlers
handler400 = 'apps.core.views.custom_400'
handler403 = 'apps.core.views.custom_403'
handler404 = 'apps.core.views.custom_404'
handler500 = 'apps.core.views.custom_500'
