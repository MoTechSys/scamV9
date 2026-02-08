"""
Middleware للتحكم في الجلسات والأمان
S-ACM - Smart Academic Content Management System
"""

from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages


class ActiveAccountMiddleware:
    """
    Middleware للتحقق من أن الحساب مفعّل
    """
    
    # الصفحات المستثناة من التحقق
    EXEMPT_URLS = [
        '/accounts/login/',
        '/accounts/logout/',
        '/accounts/activation/',
        '/admin/',
        '/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # تجاهل الصفحات المستثناة
        path = request.path
        
        for exempt_url in self.EXEMPT_URLS:
            if path.startswith(exempt_url):
                return self.get_response(request)
        
        # التحقق من المستخدم المسجل
        if request.user.is_authenticated:
            if hasattr(request.user, 'account_status'):
                if request.user.account_status != 'active':
                    messages.warning(request, 'يجب تفعيل حسابك أولاً')
                    return redirect('accounts:activation_step1')
        
        return self.get_response(request)


class RoleBasedRedirectMiddleware:
    """
    Middleware لتوجيه المستخدمين حسب أدوارهم
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    @staticmethod
    def get_dashboard_url(user):
        """الحصول على رابط لوحة التحكم حسب الدور"""
        from .models import Role
        
        if not user.is_authenticated:
            return reverse('accounts:login')
        
        role_code = user.role.code if user.role else None
        
        if role_code == Role.ADMIN:
            return reverse('accounts:admin_dashboard')
        elif role_code == Role.INSTRUCTOR:
            return reverse('courses:instructor_dashboard')
        elif role_code == Role.STUDENT:
            return reverse('courses:student_dashboard')
        else:
            return reverse('core:home')


class SecurityHeadersMiddleware:
    """
    Middleware لإضافة رؤوس الأمان
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # إضافة رؤوس الأمان
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response
