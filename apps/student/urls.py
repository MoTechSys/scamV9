"""Student App URLs - S-ACM Enterprise"""
from django.urls import path
from . import views

app_name = 'student'

urlpatterns = [
    path('dashboard/', views.StudentDashboardView.as_view(), name='dashboard'),
    path('courses/', views.StudentCourseListView.as_view(), name='course_list'),
    path('courses/<int:pk>/', views.StudentCourseDetailView.as_view(), name='course_detail'),
    path('study-room/<int:file_pk>/', views.StudyRoomView.as_view(), name='study_room'),
    path('ai/chat/<int:file_pk>/', views.AIChatView.as_view(), name='ai_chat'),
    path('ai/chat/<int:file_pk>/clear/', views.AIChatClearView.as_view(), name='ai_chat_clear'),
    path('api/progress/<int:file_pk>/', views.UpdateProgressView.as_view(), name='update_progress'),
]
