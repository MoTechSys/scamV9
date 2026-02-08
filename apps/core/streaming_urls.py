"""Streaming Engine URLs"""
from django.urls import path
from .streaming import StreamFileView, StreamMarkdownView

app_name = 'streaming'

urlpatterns = [
    path('file/<int:pk>/', StreamFileView.as_view(), name='stream_file'),
    path('markdown/<path:path>/', StreamMarkdownView.as_view(), name='stream_markdown'),
]
