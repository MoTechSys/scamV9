"""
Profile Views - عروض الملف الشخصي
S-ACM - Smart Academic Content Management System

هذا الملف يحتوي على Views المتعلقة بالملف الشخصي للمستخدم:
- عرض الملف الشخصي
- تحديث البيانات الشخصية
- تغيير كلمة المرور
"""

from django.shortcuts import render, redirect
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from django.views.generic import TemplateView

from ..models import UserActivity
from ..forms import ProfileUpdateForm, ChangePasswordForm


class ProfileView(LoginRequiredMixin, TemplateView):
    """
    عرض الملف الشخصي للمستخدم.
    
    يعرض معلومات المستخدم الأساسية وآخر النشاطات.
    
    السياق (Context):
        - user: بيانات المستخدم الحالي
        - recent_activities: آخر 10 نشاطات للمستخدم
    """
    template_name = 'accounts/profile.html'
    
    def get_context_data(self, **kwargs):
        """إضافة بيانات المستخدم ونشاطاته للسياق."""
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        context['recent_activities'] = UserActivity.objects.filter(
            user=self.request.user
        )[:10]
        return context


class ProfileUpdateView(LoginRequiredMixin, View):
    """
    تحديث الملف الشخصي للمستخدم.
    
    يتيح للمستخدم تحديث بياناته الشخصية مثل:
    - البريد الإلكتروني
    - الصورة الشخصية
    - معلومات إضافية
    """
    template_name = 'accounts/profile_update.html'
    
    def get(self, request):
        """عرض نموذج تحديث الملف الشخصي."""
        form = ProfileUpdateForm(instance=request.user)
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        """معالجة تحديث الملف الشخصي."""
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            
            # تسجيل النشاط
            UserActivity.objects.create(
                user=request.user,
                activity_type='profile_update',
                description='تم تحديث الملف الشخصي',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, 'تم تحديث الملف الشخصي بنجاح.')
            return redirect('accounts:profile')
        
        return render(request, self.template_name, {'form': form})


class ChangePasswordView(LoginRequiredMixin, View):
    """
    تغيير كلمة المرور للمستخدم.
    
    يتيح للمستخدم تغيير كلمة مروره مع الحفاظ على جلسته النشطة.
    
    الميزات:
        - التحقق من كلمة المرور الحالية
        - التحقق من تطابق كلمة المرور الجديدة
        - الحفاظ على الجلسة بعد التغيير
    """
    template_name = 'accounts/change_password.html'
    
    def get(self, request):
        """عرض نموذج تغيير كلمة المرور."""
        form = ChangePasswordForm(request.user)
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        """معالجة تغيير كلمة المرور."""
        form = ChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            request.user.set_password(form.cleaned_data['new_password1'])
            request.user.save()
            
            # الحفاظ على الجلسة - مهم جداً لعدم تسجيل خروج المستخدم
            update_session_auth_hash(request, request.user)
            
            # تسجيل النشاط
            UserActivity.objects.create(
                user=request.user,
                activity_type='password_change',
                description='تم تغيير كلمة المرور',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, 'تم تغيير كلمة المرور بنجاح.')
            return redirect('accounts:profile')
        
        return render(request, self.template_name, {'form': form})
