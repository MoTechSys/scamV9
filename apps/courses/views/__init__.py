"""
Views Package - حزمة العروض
S-ACM - Smart Academic Content Management System

Cleaned: Only shared file operations remain.
Legacy student/instructor/admin views have been moved to dedicated apps.
"""

# Common views (shared: file download/view)
from .common import (
    FileDownloadView,
    FileViewView,
)

__all__ = [
    'FileDownloadView',
    'FileViewView',
]
