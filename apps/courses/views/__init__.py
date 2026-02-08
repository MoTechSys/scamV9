"""
Views Package - حزمة العروض
S-ACM - Smart Academic Content Management System

This package contains all views for the courses app, organized by role:
- student.py: Student-facing views
- instructor.py: Instructor-facing views
- admin.py: Admin-facing views
- common.py: Shared views (file download/view)
- htmx.py: HTMX partial views

All views are exported from this __init__.py for backward compatibility.
"""

# Student views
from .student import (
    StudentDashboardView,
    StudentCourseListView,
    StudentCourseDetailView,
)

# Common views (used by both students and instructors)
from .common import (
    FileDownloadView,
    FileViewView,
)

# Instructor views
from .instructor import (
    InstructorDashboardView,
    InstructorCourseListView,
    InstructorCourseDetailView,
    FileUploadView,
    InstructorAIGenerationView,
    FileUpdateView,
    FileDeleteView,
    FileToggleVisibilityView,
)

# Admin views
from .admin import (
    AdminCourseListView,
    AdminCourseCreateView,
    AdminCourseUpdateView,
    AdminCourseDetailView,
    AdminInstructorAssignView,
    AdminCourseMajorView,
)

# HTMX views are imported as a module (function-based views)
from . import htmx

# Export all views for backward compatibility
__all__ = [
    # Student
    'StudentDashboardView',
    'StudentCourseListView',
    'StudentCourseDetailView',
    # Common
    'FileDownloadView',
    'FileViewView',
    # Instructor
    'InstructorDashboardView',
    'InstructorCourseListView',
    'InstructorCourseDetailView',
    'FileUploadView',
    'InstructorAIGenerationView',
    'FileUpdateView',
    'FileDeleteView',
    'FileToggleVisibilityView',
    # Admin
    'AdminCourseListView',
    'AdminCourseCreateView',
    'AdminCourseUpdateView',
    'AdminCourseDetailView',
    'AdminInstructorAssignView',
    'AdminCourseMajorView',
    # HTMX module
    'htmx',
]
