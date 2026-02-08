"""
URLs لتطبيق accounts
S-ACM - Smart Academic Content Management System
"""

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    
    # Account Activation
    path('activate/', views.ActivationStep1View.as_view(), name='activation_step1'),
    path('activate/email/', views.ActivationStep2View.as_view(), name='activation_step2'),
    path('activate/verify/', views.ActivationVerifyOTPView.as_view(), name='activation_verify_otp'),
    path('activate/password/', views.ActivationSetPasswordView.as_view(), name='activation_set_password'),
    
    # Password Reset
    path('password-reset/', views.PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset/<str:token>/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # Profile
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/update/', views.ProfileUpdateView.as_view(), name='profile_update'),
    path('profile/change-password/', views.ChangePasswordView.as_view(), name='change_password'),
]
