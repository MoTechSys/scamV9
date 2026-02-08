"""
Instructor App URLs
S-ACM Enterprise Edition
"""
from django.urls import path
from . import views

app_name = 'instructor'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.InstructorDashboardView.as_view(), name='dashboard'),

    # Courses
    path('courses/', views.InstructorCourseListView.as_view(), name='course_list'),
    path('courses/<int:pk>/', views.InstructorCourseDetailView.as_view(), name='course_detail'),

    # File Operations
    path('files/upload/', views.FileUploadView.as_view(), name='file_upload'),
    path('files/<int:pk>/update/', views.FileUpdateView.as_view(), name='file_update'),
    path('files/<int:pk>/delete/', views.FileDeleteView.as_view(), name='file_delete'),
    path('files/<int:pk>/toggle/', views.FileToggleVisibilityView.as_view(), name='file_toggle_visibility'),
    path('files/bulk-action/', views.FileBulkActionView.as_view(), name='file_bulk_action'),

    # Recycle Bin
    path('trash/', views.TrashListView.as_view(), name='trash_list'),
    path('trash/<int:pk>/restore/', views.TrashRestoreView.as_view(), name='trash_restore'),
    path('trash/<int:pk>/destroy/', views.TrashDestroyView.as_view(), name='trash_destroy'),
    path('trash/empty/', views.TrashEmptyView.as_view(), name='trash_empty'),

    # AI Hub
    path('ai/', views.AIHubView.as_view(), name='ai_hub'),
    path('ai/generate/', views.AIGenerateView.as_view(), name='ai_generate'),
    path('ai/archives/', views.AIArchivesView.as_view(), name='ai_archives'),
    path('ai/archives/<int:pk>/delete/', views.AIArchiveDeleteView.as_view(), name='ai_archive_delete'),

    # Student Roster
    path('roster/<int:course_pk>/', views.StudentRosterView.as_view(), name='student_roster'),
    path('roster/<int:course_pk>/export/', views.RosterExportExcelView.as_view(), name='roster_export_excel'),

    # AJAX
    path('api/course-files/', views.CourseFilesAjaxView.as_view(), name='course_files_ajax'),
]
