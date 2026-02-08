"""
نماذج (Forms) لتطبيق accounts
S-ACM - Smart Academic Content Management System
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.core.exceptions import ValidationError
from .models import User, VerificationCode, Major, Level, Role


class LoginForm(AuthenticationForm):
    """
    نموذج تسجيل الدخول
    """
    username = forms.CharField(
        label='الرقم الأكاديمي/الوظيفي',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'أدخل الرقم الأكاديمي أو الوظيفي',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label='كلمة المرور',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'أدخل كلمة المرور'
        })
    )
    remember_me = forms.BooleanField(
        label='تذكرني',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    error_messages = {
        'invalid_login': 'الرقم الأكاديمي أو كلمة المرور غير صحيحة.',
        'inactive': 'هذا الحساب غير مفعّل.',
    }


class ActivationStep1Form(forms.Form):
    """
    نموذج الخطوة الأولى من التفعيل: التحقق من الهوية
    """
    academic_id = forms.CharField(
        label='الرقم الأكاديمي/الوظيفي',
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'أدخل الرقم الأكاديمي أو الوظيفي',
            'autofocus': True
        })
    )
    id_card_number = forms.CharField(
        label='رقم البطاقة الشخصية',
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'أدخل رقم البطاقة الشخصية'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        academic_id = cleaned_data.get('academic_id')
        id_card_number = cleaned_data.get('id_card_number')
        
        if academic_id and id_card_number:
            try:
                user = User.objects.get(
                    academic_id=academic_id,
                    id_card_number=id_card_number
                )
                # التحقق من حالة الحساب
                if user.account_status == 'active':
                    raise ValidationError(
                        'هذا الحساب مفعّل بالفعل. إذا نسيت كلمة المرور، استخدم خيار "نسيت كلمة المرور".'
                    )
                elif user.account_status == 'suspended':
                    raise ValidationError(
                        'هذا الحساب موقوف. يرجى التواصل مع الإدارة.'
                    )
                cleaned_data['user'] = user
            except User.DoesNotExist:
                raise ValidationError(
                    'البيانات المدخلة غير صحيحة. تأكد من الرقم الأكاديمي ورقم البطاقة.'
                )
        
        return cleaned_data


class ActivationStep2Form(forms.Form):
    """
    نموذج الخطوة الثانية من التفعيل: إدخال البريد الإلكتروني
    """
    email = forms.EmailField(
        label='البريد الإلكتروني',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'أدخل بريدك الإلكتروني',
            'autofocus': True
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError(
                'هذا البريد الإلكتروني مستخدم بالفعل.'
            )
        return email


class OTPVerificationForm(forms.Form):
    """
    نموذج التحقق من رمز OTP
    """
    otp_code = forms.CharField(
        label='رمز التحقق',
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control text-center',
            'placeholder': '------',
            'maxlength': '6',
            'pattern': '[0-9]{6}',
            'autofocus': True,
            'style': 'letter-spacing: 10px; font-size: 24px;'
        })
    )
    
    def clean_otp_code(self):
        otp_code = self.cleaned_data.get('otp_code')
        if not otp_code.isdigit():
            raise ValidationError('رمز التحقق يجب أن يكون أرقاماً فقط.')
        return otp_code


class SetPasswordActivationForm(SetPasswordForm):
    """
    نموذج تعيين كلمة المرور عند التفعيل
    """
    new_password1 = forms.CharField(
        label='كلمة المرور الجديدة',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'أدخل كلمة المرور الجديدة'
        }),
        help_text='يجب أن تكون 8 أحرف على الأقل وتحتوي على أرقام وحروف.'
    )
    new_password2 = forms.CharField(
        label='تأكيد كلمة المرور',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'أعد إدخال كلمة المرور'
        })
    )


class PasswordResetRequestForm(forms.Form):
    """
    نموذج طلب إعادة تعيين كلمة المرور
    """
    email = forms.EmailField(
        label='البريد الإلكتروني',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'أدخل بريدك الإلكتروني المسجل',
            'autofocus': True
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        try:
            user = User.objects.get(email=email, account_status='active')
            self.user = user
        except User.DoesNotExist:
            raise ValidationError(
                'لا يوجد حساب مفعّل بهذا البريد الإلكتروني.'
            )
        return email


class ProfileUpdateForm(forms.ModelForm):
    """
    نموذج تحديث الملف الشخصي
    """
    class Meta:
        model = User
        fields = ['full_name', 'email', 'phone_number', 'profile_picture']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '05xxxxxxxx'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control'
            })
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError('هذا البريد الإلكتروني مستخدم بالفعل.')
        return email


class ChangePasswordForm(forms.Form):
    """
    نموذج تغيير كلمة المرور
    """
    current_password = forms.CharField(
        label='كلمة المرور الحالية',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'أدخل كلمة المرور الحالية'
        })
    )
    new_password1 = forms.CharField(
        label='كلمة المرور الجديدة',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'أدخل كلمة المرور الجديدة'
        }),
        help_text='يجب أن تكون 8 أحرف على الأقل.'
    )
    new_password2 = forms.CharField(
        label='تأكيد كلمة المرور الجديدة',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'أعد إدخال كلمة المرور الجديدة'
        })
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise ValidationError('كلمة المرور الحالية غير صحيحة.')
        return current_password
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError('كلمتا المرور غير متطابقتين.')
        
        return cleaned_data


# ========== نماذج الإدارة (Admin Forms) ==========

class UserBulkImportForm(forms.Form):
    """
    نموذج استيراد المستخدمين بالجملة من CSV
    """
    csv_file = forms.FileField(
        label='ملف CSV',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv'
        }),
        help_text='الملف يجب أن يحتوي على الأعمدة: academic_id, id_card_number, full_name, role, major, level'
    )
    
    def clean_csv_file(self):
        csv_file = self.cleaned_data.get('csv_file')
        if not csv_file.name.endswith('.csv'):
            raise ValidationError('يجب أن يكون الملف بصيغة CSV.')
        return csv_file


class UserCreateForm(forms.ModelForm):
    """
    نموذج إنشاء مستخدم جديد (للأدمن)
    """
    class Meta:
        model = User
        fields = ['academic_id', 'id_card_number', 'full_name', 'role', 'major', 'level']
        widgets = {
            'academic_id': forms.TextInput(attrs={'class': 'form-control'}),
            'id_card_number': forms.TextInput(attrs={'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'major': forms.Select(attrs={'class': 'form-select'}),
            'level': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['major'].required = False
        self.fields['level'].required = False


class StudentPromotionForm(forms.Form):
    """
    نموذج ترقية الطلاب الجماعية
    """
    from_level = forms.ModelChoiceField(
        queryset=Level.objects.all(),
        label='من المستوى',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    to_level = forms.ModelChoiceField(
        queryset=Level.objects.all(),
        label='إلى المستوى',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    major = forms.ModelChoiceField(
        queryset=Major.objects.filter(is_active=True),
        label='التخصص',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='اتركه فارغاً لترقية جميع التخصصات'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        from_level = cleaned_data.get('from_level')
        to_level = cleaned_data.get('to_level')
        
        if from_level and to_level:
            if from_level.level_number >= to_level.level_number:
                raise ValidationError(
                    'المستوى الجديد يجب أن يكون أعلى من المستوى الحالي.'
                )
        
        return cleaned_data
