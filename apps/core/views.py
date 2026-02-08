"""
Views لتطبيق core
S-ACM - Smart Academic Content Management System
"""

from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
import logging

logger = logging.getLogger(__name__)


class HomeView(TemplateView):
    """الصفحة الرئيسية"""
    template_name = 'core/home.html'
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('core:dashboard_redirect')
        return super().get(request, *args, **kwargs)


@login_required
def dashboard_redirect(request):
    """
    توجيه المستخدم إلى لوحة التحكم المناسبة حسب دوره
    """
    user = request.user
    
    # الأدمن أو السوبر يوزر يروح للوحة Django Admin
    if user.is_superuser or user.is_admin():
        return redirect('/scam-admin/')
    elif user.is_instructor():
        return redirect('instructor:dashboard')
    elif user.is_student():
        return redirect('student:dashboard')
    else:
        # إذا لم يكن له دور محدد
        return redirect('accounts:profile')


class AboutView(TemplateView):
    """صفحة عن النظام"""
    template_name = 'core/about.html'


class ContactView(TemplateView):
    """صفحة التواصل"""
    template_name = 'core/contact.html'


# =============================================================================
# Custom Error Handlers
# =============================================================================

def custom_404(request, exception=None):
    """
    صفحة خطأ 404 مخصصة
    Page Not Found
    """
    logger.warning(
        f"404 Error: {request.path} - User: {request.user if request.user.is_authenticated else 'Anonymous'}"
    )
    return render(request, 'errors/404.html', status=404)


def custom_500(request):
    """
    صفحة خطأ 500 مخصصة
    Internal Server Error
    """
    logger.error(
        f"500 Error: {request.path} - User: {request.user if hasattr(request, 'user') and request.user.is_authenticated else 'Anonymous'}"
    )
    return render(request, 'errors/500.html', status=500)


def custom_403(request, exception=None):
    """
    صفحة خطأ 403 مخصصة
    Permission Denied
    """
    logger.warning(
        f"403 Error: {request.path} - User: {request.user if request.user.is_authenticated else 'Anonymous'}"
    )
    return render(request, 'errors/403.html', status=403)


def custom_400(request, exception=None):
    """
    صفحة خطأ 400 مخصصة
    Bad Request
    """
    logger.warning(
        f"400 Error: {request.path} - User: {request.user if request.user.is_authenticated else 'Anonymous'}"
    )
    return render(request, 'errors/400.html', status=400)


# =============================================================================
# Health Check Endpoint
# =============================================================================

def health_check(request):
    """
    نقطة نهاية للتحقق من صحة التطبيق
    Used by Docker, Kubernetes, and load balancers
    """
    from django.http import JsonResponse
    from django.db import connection
    
    health_status = {
        'status': 'healthy',
        'database': 'connected',
    }
    
    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['database'] = f'error: {str(e)}'
        logger.error(f"Health check failed - Database error: {e}")
        return JsonResponse(health_status, status=503)
    
    return JsonResponse(health_status, status=200)


# =============================================================================
# Legacy Class-Based Views (for backwards compatibility)
# =============================================================================

class Error404View(TemplateView):
    """صفحة خطأ 404"""
    template_name = 'errors/404.html'


class Error500View(TemplateView):
    """صفحة خطأ 500"""
    template_name = 'errors/500.html'
