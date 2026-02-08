"""
Authentication Views - عروض المصادقة
S-ACM - Smart Academic Content Management System

هذا الملف يحتوي على جميع Views المتعلقة بـ:
- تسجيل الدخول والخروج
- تفعيل الحساب (4 خطوات)
- إعادة تعيين كلمة المرور
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib import messages
from django.views import View
from django.urls import reverse
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator

from ..models import User, VerificationCode, PasswordResetToken, UserActivity
from ..forms import (
    LoginForm, ActivationStep1Form, ActivationStep2Form,
    OTPVerificationForm, SetPasswordActivationForm, PasswordResetRequestForm
)
from apps.core.models import AuditLog


# ========== Login / Logout ==========

@method_decorator(ensure_csrf_cookie, name='dispatch')
class LoginView(View):
    """
    عرض تسجيل الدخول.
    
    يتيح للمستخدمين تسجيل الدخول باستخدام الرقم الأكاديمي وكلمة المرور.
    
    الوظائف:
        - التحقق من حالة الحساب (يجب أن يكون active)
        - تسجيل نشاط الدخول
        - دعم خيار "تذكرني"
        - إعادة التوجيه حسب دور المستخدم
    """
    template_name = 'accounts/login.html'
    
    def get(self, request):
        """عرض نموذج تسجيل الدخول."""
        if request.user.is_authenticated:
            return redirect('core:dashboard_redirect')
        form = LoginForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        """معالجة طلب تسجيل الدخول."""
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            
            # التحقق من حالة الحساب
            if user.account_status != 'active':
                messages.error(request, 'هذا الحساب غير مفعّل.')
                return render(request, self.template_name, {'form': form})
            
            login(request, user)
            
            # تسجيل النشاط
            UserActivity.objects.create(
                user=user,
                activity_type='login',
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # تذكرني - إذا لم يختر المستخدم، تنتهي الجلسة عند إغلاق المتصفح
            if not form.cleaned_data.get('remember_me'):
                request.session.set_expiry(0)
            
            messages.success(request, f'مرحباً {user.full_name}!')
            
            # التوجيه حسب الدور أو URL المحدد
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('core:dashboard_redirect')
        
        return render(request, self.template_name, {'form': form})
    
    def _get_client_ip(self, request):
        """استخراج عنوان IP الحقيقي للمستخدم."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class LogoutView(View):
    """
    عرض تسجيل الخروج.
    
    يقوم بتسجيل خروج المستخدم وتسجيل نشاط الخروج.
    """
    
    def get(self, request):
        """معالجة طلب تسجيل الخروج."""
        if request.user.is_authenticated:
            # تسجيل النشاط قبل الخروج
            UserActivity.objects.create(
                user=request.user,
                activity_type='logout',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            logout(request)
            messages.success(request, 'تم تسجيل الخروج بنجاح.')
        return redirect('accounts:login')


# ========== Account Activation (4 Steps) ==========

class ActivationStep1View(View):
    """
    الخطوة الأولى من تفعيل الحساب: التحقق من الهوية.
    
    يُدخل المستخدم الرقم الأكاديمي ورقم الهوية للتحقق.
    """
    template_name = 'accounts/activation/step1.html'
    
    def get(self, request):
        """عرض نموذج التحقق من الهوية."""
        if request.user.is_authenticated:
            return redirect('core:dashboard_redirect')
        form = ActivationStep1Form()
        return render(request, self.template_name, {'form': form, 'step': 1})
    
    def post(self, request):
        """معالجة التحقق من الهوية."""
        form = ActivationStep1Form(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            # حفظ معرف المستخدم في الجلسة للخطوات القادمة
            request.session['activation_user_id'] = user.id
            return redirect('accounts:activation_step2')
        return render(request, self.template_name, {'form': form, 'step': 1})


class ActivationStep2View(View):
    """
    الخطوة الثانية من تفعيل الحساب: إدخال البريد الإلكتروني.
    
    يُدخل المستخدم بريده الإلكتروني ويتم إرسال رمز OTP إليه.
    """
    template_name = 'accounts/activation/step2.html'
    
    def get(self, request):
        """عرض نموذج إدخال البريد الإلكتروني."""
        user_id = request.session.get('activation_user_id')
        if not user_id:
            return redirect('accounts:activation_step1')
        
        form = ActivationStep2Form()
        return render(request, self.template_name, {'form': form, 'step': 2})
    
    def post(self, request):
        """معالجة إرسال رمز OTP."""
        user_id = request.session.get('activation_user_id')
        if not user_id:
            return redirect('accounts:activation_step1')
        
        form = ActivationStep2Form(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = get_object_or_404(User, id=user_id)
            
            # إنشاء رمز OTP صالح لـ 10 دقائق
            otp_code = VerificationCode.generate_code()
            VerificationCode.objects.create(
                user=user,
                code=otp_code,
                email=email,
                expires_at=timezone.now() + timedelta(minutes=10)
            )
            
            # إرسال البريد الإلكتروني
            try:
                send_mail(
                    subject='رمز تفعيل حسابك في S-ACM',
                    message=f'رمز التفعيل الخاص بك هو: {otp_code}\n\nهذا الرمز صالح لمدة 10 دقائق.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
            except Exception as e:
                # في بيئة التطوير، نعرض الرمز مباشرة
                messages.info(request, f'رمز التحقق (للتطوير): {otp_code}')
            
            request.session['activation_email'] = email
            messages.success(request, 'تم إرسال رمز التحقق إلى بريدك الإلكتروني.')
            return redirect('accounts:activation_verify_otp')
        
        return render(request, self.template_name, {'form': form, 'step': 2})


class ActivationVerifyOTPView(View):
    """
    الخطوة الثالثة من تفعيل الحساب: التحقق من رمز OTP.
    
    يُدخل المستخدم الرمز المُرسل لبريده الإلكتروني.
    """
    template_name = 'accounts/activation/verify_otp.html'
    
    def get(self, request):
        """عرض نموذج إدخال رمز OTP."""
        user_id = request.session.get('activation_user_id')
        email = request.session.get('activation_email')
        if not user_id or not email:
            return redirect('accounts:activation_step1')
        
        form = OTPVerificationForm()
        return render(request, self.template_name, {
            'form': form,
            'step': 3,
            'email': email
        })
    
    def post(self, request):
        """معالجة التحقق من رمز OTP."""
        user_id = request.session.get('activation_user_id')
        email = request.session.get('activation_email')
        if not user_id or not email:
            return redirect('accounts:activation_step1')
        
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data['otp_code']
            user = get_object_or_404(User, id=user_id)
            
            # البحث عن رمز صالح
            verification = VerificationCode.objects.filter(
                user=user,
                email=email,
                code=otp_code,
                is_used=False
            ).first()
            
            if verification and verification.is_valid():
                verification.is_used = True
                verification.save()
                request.session['otp_verified'] = True
                return redirect('accounts:activation_set_password')
            else:
                # زيادة عدد المحاولات الفاشلة
                if verification:
                    verification.attempts += 1
                    verification.save()
                messages.error(request, 'رمز التحقق غير صحيح أو منتهي الصلاحية.')
        
        return render(request, self.template_name, {
            'form': form,
            'step': 3,
            'email': email
        })


class ActivationSetPasswordView(View):
    """
    الخطوة الرابعة والأخيرة من تفعيل الحساب: تعيين كلمة المرور.
    
    يُعيّن المستخدم كلمة مرور جديدة ويتم تفعيل حسابه.
    """
    template_name = 'accounts/activation/set_password.html'
    
    def get(self, request):
        """عرض نموذج تعيين كلمة المرور."""
        user_id = request.session.get('activation_user_id')
        otp_verified = request.session.get('otp_verified')
        if not user_id or not otp_verified:
            return redirect('accounts:activation_step1')
        
        user = get_object_or_404(User, id=user_id)
        form = SetPasswordActivationForm(user)
        return render(request, self.template_name, {'form': form, 'step': 4})
    
    def post(self, request):
        """معالجة تعيين كلمة المرور وتفعيل الحساب."""
        user_id = request.session.get('activation_user_id')
        otp_verified = request.session.get('otp_verified')
        if not user_id or not otp_verified:
            return redirect('accounts:activation_step1')
        
        user = get_object_or_404(User, id=user_id)
        form = SetPasswordActivationForm(user, request.POST)
        
        if form.is_valid():
            # تحديث بيانات المستخدم
            email = request.session.get('activation_email')
            user.email = email
            user.account_status = 'active'
            user.set_password(form.cleaned_data['new_password1'])
            user.save()
            
            # تنظيف بيانات الجلسة
            for key in ['activation_user_id', 'activation_email', 'otp_verified']:
                request.session.pop(key, None)
            
            # تسجيل في سجل التدقيق
            AuditLog.log(
                user=user,
                action='create',
                model_name='User',
                object_id=user.id,
                object_repr=str(user),
                changes={'action': 'account_activated'},
                request=request
            )
            
            messages.success(request, 'تم تفعيل حسابك بنجاح! يمكنك الآن تسجيل الدخول.')
            return redirect('accounts:login')
        
        return render(request, self.template_name, {'form': form, 'step': 4})


# ========== Password Reset ==========

class PasswordResetRequestView(View):
    """
    طلب إعادة تعيين كلمة المرور.
    
    يُدخل المستخدم بريده الإلكتروني ويتم إرسال رابط إعادة التعيين.
    """
    template_name = 'accounts/password_reset/request.html'
    
    def get(self, request):
        """عرض نموذج طلب إعادة التعيين."""
        form = PasswordResetRequestForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        """معالجة طلب إعادة التعيين."""
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            user = form.user
            
            # إنشاء توكن صالح لساعة واحدة
            token = PasswordResetToken.generate_token()
            PasswordResetToken.objects.create(
                user=user,
                token=token,
                expires_at=timezone.now() + timedelta(hours=1)
            )
            
            # بناء رابط إعادة التعيين
            reset_url = request.build_absolute_uri(
                reverse('accounts:password_reset_confirm', args=[token])
            )
            
            # إرسال البريد
            try:
                send_mail(
                    subject='إعادة تعيين كلمة المرور - S-ACM',
                    message=f'لإعادة تعيين كلمة المرور، اضغط على الرابط التالي:\n\n{reset_url}\n\nهذا الرابط صالح لمدة ساعة واحدة.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                messages.success(request, 'تم إرسال رابط إعادة التعيين إلى بريدك الإلكتروني.')
            except Exception as e:
                # في بيئة التطوير
                messages.info(request, f'رابط إعادة التعيين (للتطوير): {reset_url}')
            
            return redirect('accounts:login')
        
        return render(request, self.template_name, {'form': form})


class PasswordResetConfirmView(View):
    """
    تأكيد إعادة تعيين كلمة المرور.
    
    يُعيّن المستخدم كلمة مرور جديدة باستخدام الرابط المُرسل.
    """
    template_name = 'accounts/password_reset/confirm.html'
    
    def get(self, request, token):
        """عرض نموذج تعيين كلمة المرور الجديدة."""
        reset_token = get_object_or_404(PasswordResetToken, token=token)
        
        if not reset_token.is_valid():
            messages.error(request, 'رابط إعادة التعيين غير صالح أو منتهي الصلاحية.')
            return redirect('accounts:password_reset_request')
        
        form = SetPasswordActivationForm(reset_token.user)
        return render(request, self.template_name, {'form': form})
    
    def post(self, request, token):
        """معالجة تعيين كلمة المرور الجديدة."""
        reset_token = get_object_or_404(PasswordResetToken, token=token)
        
        if not reset_token.is_valid():
            messages.error(request, 'رابط إعادة التعيين غير صالح أو منتهي الصلاحية.')
            return redirect('accounts:password_reset_request')
        
        form = SetPasswordActivationForm(reset_token.user, request.POST)
        if form.is_valid():
            user = reset_token.user
            user.set_password(form.cleaned_data['new_password1'])
            user.save()
            
            # تعطيل التوكن
            reset_token.is_used = True
            reset_token.save()
            
            messages.success(request, 'تم تغيير كلمة المرور بنجاح!')
            return redirect('accounts:login')
        
        return render(request, self.template_name, {'form': form})
