"""
Profile Views - عروض الملف الشخصي
S-ACM - Smart Academic Content Management System

هذا الملف يحتوي على Views المتعلقة بالملف الشخصي للمستخدم:
- عرض وتحديث الملف الشخصي (مدمج)
- تغيير كلمة المرور
"""

from django.shortcuts import render, redirect
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View

from ..models import UserActivity
from ..forms import ProfileUpdateForm, ChangePasswordForm


class ProfileView(LoginRequiredMixin, View):
    """
    عرض وتحديث الملف الشخصي للمستخدم (مدمج).
    
    GET: يعرض معلومات المستخدم مع نموذج التعديل.
    POST: يحفظ التعديلات على الملف الشخصي.
    
    يستخدم dashboard_base.html لعرض Sidebar.
    """
    template_name = 'accounts/profile.html'
    
    def get(self, request):
        form = ProfileUpdateForm(instance=request.user)
        recent_activities = UserActivity.objects.filter(user=request.user)[:10]
        return render(request, self.template_name, {
            'form': form,
            'recent_activities': recent_activities,
            'active_page': 'profile',
        })
    
    def post(self, request):
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            UserActivity.objects.create(
                user=request.user,
                activity_type='profile_update',
                description='تم تحديث الملف الشخصي',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            messages.success(request, 'تم تحديث الملف الشخصي بنجاح.')
            return redirect('accounts:profile')
        
        recent_activities = UserActivity.objects.filter(user=request.user)[:10]
        return render(request, self.template_name, {
            'form': form,
            'recent_activities': recent_activities,
            'active_page': 'profile',
        })


class ProfileUpdateView(LoginRequiredMixin, View):
    """
    Redirect إلى ProfileView الموحد (للتوافق مع الروابط القديمة).
    """
    def get(self, request):
        return redirect('accounts:profile')
    
    def post(self, request):
        return redirect('accounts:profile')


class ChangePasswordView(LoginRequiredMixin, View):
    """
    تغيير كلمة المرور للمستخدم.
    
    يتيح للمستخدم تغيير كلمة مروره مع الحفاظ على جلسته النشطة.
    يستخدم dashboard_base.html لعرض Sidebar.
    """
    template_name = 'accounts/change_password.html'
    
    def get(self, request):
        form = ChangePasswordForm(request.user)
        return render(request, self.template_name, {
            'form': form,
            'active_page': 'change_password',
        })
    
    def post(self, request):
        form = ChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            request.user.set_password(form.cleaned_data['new_password1'])
            request.user.save()
            update_session_auth_hash(request, request.user)
            UserActivity.objects.create(
                user=request.user,
                activity_type='password_change',
                description='تم تغيير كلمة المرور',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            messages.success(request, 'تم تغيير كلمة المرور بنجاح.')
            return redirect('accounts:profile')
        
        return render(request, self.template_name, {
            'form': form,
            'active_page': 'change_password',
        })
