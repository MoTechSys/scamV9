"""
URLs لتطبيق ai_features
S-ACM - Smart Academic Content Management System
"""

from django.urls import path
from . import views

app_name = 'ai_features'

urlpatterns = [
    # AI Features
    path('summarize/<int:file_id>/', views.SummarizeView.as_view(), name='summarize'),
    path('questions/<int:file_id>/', views.GenerateQuestionsView.as_view(), name='questions'),
    path('ask/<int:file_id>/', views.AskDocumentView.as_view(), name='ask_document'),
    path('ask/<int:file_id>/clear/', views.ClearChatHistoryView.as_view(), name='clear_chat'),
    
    # Usage Stats
    path('usage/', views.AIUsageStatsView.as_view(), name='usage_stats'),
]
