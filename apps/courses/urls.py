"""
URL Configuration for Courses App
S-ACM - Smart Academic Content Management System

Cleaned: Only shared file operations remain.
Legacy student/instructor/admin URLs have been removed.
- Students → apps.student (student:*)
- Instructors → apps.instructor (instructor:*)
- Admin → Django Admin (/scam-admin/)
"""

from django.urls import path
from .views.common import FileDownloadView, FileViewView

app_name = 'courses'

urlpatterns = [
    # ==============================
    # File Operations (العمليات المشتركة على الملفات)
    # ==============================
    # تم تأمين هذه الروابط ضد ثغرات IDOR
    path('files/<int:pk>/download/', FileDownloadView.as_view(), name='file_download'),
    path('files/<int:pk>/view/', FileViewView.as_view(), name='file_view'),
]
