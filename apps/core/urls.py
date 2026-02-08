"""
URLs لتطبيق core
S-ACM - Smart Academic Content Management System
"""

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    
    # Health check endpoint (for Docker, Kubernetes, load balancers)
    path('health/', views.health_check, name='health_check'),
]
