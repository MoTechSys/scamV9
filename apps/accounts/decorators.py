"""
Decorators للتحكم في الصلاحيات
S-ACM - Smart Academic Content Management System
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden


def role_required(allowed_roles):
    """
    Decorator للتحقق من دور المستخدم
    
    Usage:
        @role_required(['admin'])
        def admin_view(request):
            ...
        
        @role_required(['admin', 'instructor'])
        def instructor_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'يجب تسجيل الدخول أولاً')
                return redirect('accounts:login')
            
            user_role = request.user.role.code if request.user.role else None
            
            if user_role not in allowed_roles:
                messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
                return redirect('core:home')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def admin_required(view_func):
    """Decorator للتحقق من صلاحية الأدمن"""
    return role_required(['admin'])(view_func)


def instructor_required(view_func):
    """Decorator للتحقق من صلاحية المدرس"""
    return role_required(['instructor', 'admin'])(view_func)


def student_required(view_func):
    """Decorator للتحقق من صلاحية الطالب"""
    return role_required(['student'])(view_func)


def active_account_required(view_func):
    """
    Decorator للتحقق من أن الحساب مفعّل
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'يجب تسجيل الدخول أولاً')
            return redirect('accounts:login')
        
        if request.user.account_status != 'active':
            messages.error(request, 'حسابك غير مفعّل. يرجى تفعيل الحساب أولاً.')
            return redirect('accounts:activation_step1')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def permission_required(permission_name):
    """
    Decorator للتحقق من صلاحية معينة
    
    Usage:
        @permission_required('can_upload_files')
        def upload_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'يجب تسجيل الدخول أولاً')
                return redirect('accounts:login')
            
            # التحقق من الصلاحية
            if not request.user.has_permission(permission_name):
                messages.error(request, 'ليس لديك الصلاحية المطلوبة')
                return redirect('core:home')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def course_access_required(view_func):
    """
    Decorator للتحقق من صلاحية الوصول للمقرر
    يتوقع وجود course_id في kwargs
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        from apps.courses.models import Course
        from .models import Role
        
        if not request.user.is_authenticated:
            messages.error(request, 'يجب تسجيل الدخول أولاً')
            return redirect('accounts:login')
        
        course_id = kwargs.get('course_id') or kwargs.get('pk')
        
        if not course_id:
            return HttpResponseForbidden('معرف المقرر غير موجود')
        
        try:
            course = Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            messages.error(request, 'المقرر غير موجود')
            return redirect('core:home')
        
        user_role = request.user.role.code if request.user.role else None
        
        # الأدمن لديه وصول كامل
        if user_role == Role.ADMIN:
            return view_func(request, *args, **kwargs)
        
        # المدرس يجب أن يكون معيناً للمقرر
        if user_role == Role.INSTRUCTOR:
            if course.instructor_courses.filter(instructor=request.user).exists():
                return view_func(request, *args, **kwargs)
            messages.error(request, 'لست معيناً لهذا المقرر')
            return redirect('courses:instructor_dashboard')
        
        # الطالب يجب أن يكون في التخصص والمستوى المناسب
        if user_role == Role.STUDENT:
            if course.course_majors.filter(major=request.user.major).exists():
                return view_func(request, *args, **kwargs)
            messages.error(request, 'هذا المقرر ليس ضمن تخصصك')
            return redirect('courses:student_dashboard')
        
        return HttpResponseForbidden('ليس لديك صلاحية الوصول')
    
    return wrapper
