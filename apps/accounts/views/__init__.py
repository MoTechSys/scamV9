"""
Views Package - حزمة العروض
S-ACM - Smart Academic Content Management System

هذا الملف يصدّر جميع الـ Views من الحزمة.
تم تنظيم الـ Views حسب الوظيفة:
- mixins.py: أدوات التحقق من الصلاحيات
- auth.py: المصادقة والتفعيل وإعادة كلمة المرور
- profile.py: الملف الشخصي
"""

# Mixins - أدوات التحقق من الصلاحيات
from .mixins import (
    AdminRequiredMixin,
    InstructorRequiredMixin,
    StudentRequiredMixin,
)

# Authentication Views - المصادقة
from .auth import (
    LoginView,
    LogoutView,
    ActivationStep1View,
    ActivationStep2View,
    ActivationVerifyOTPView,
    ActivationSetPasswordView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
)

# Profile Views - الملف الشخصي
from .profile import (
    ProfileView,
    ProfileUpdateView,
    ChangePasswordView,
)

# قائمة التصدير للتوافق
__all__ = [
    # Mixins
    'AdminRequiredMixin',
    'InstructorRequiredMixin',
    'StudentRequiredMixin',
    # Auth
    'LoginView',
    'LogoutView',
    'ActivationStep1View',
    'ActivationStep2View',
    'ActivationVerifyOTPView',
    'ActivationSetPasswordView',
    'PasswordResetRequestView',
    'PasswordResetConfirmView',
    # Profile
    'ProfileView',
    'ProfileUpdateView',
    'ChangePasswordView',
]

