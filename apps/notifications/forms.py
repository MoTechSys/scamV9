"""
نماذج (Forms) لنظام الإشعارات v2
S-ACM - Smart Academic Content Management System

=== Forms ===
1. ComposerForm: نموذج إنشاء إشعار جديد (للدكتور والأدمن) مع استهداف ذكي
2. NotificationPreferenceForm: تفضيلات إشعارات المستخدم
"""

from django import forms
from .models import Notification, NotificationPreference
from apps.courses.models import Course
from apps.accounts.models import Major, Level


class ComposerForm(forms.Form):
    """
    نموذج إنشاء إشعار جديد - Composer View
    يدعم الاستهداف الذكي عبر HTMX Cascading Dropdowns
    """

    # === بيانات الإشعار ===
    title = forms.CharField(
        label='عنوان الإشعار',
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'أدخل عنوان الإشعار...',
        })
    )
    body = forms.CharField(
        label='محتوى الإشعار',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'أدخل محتوى الإشعار...',
        })
    )
    notification_type = forms.ChoiceField(
        label='نوع الإشعار',
        choices=Notification.NOTIFICATION_TYPES,
        initial='general',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    priority = forms.ChoiceField(
        label='الأولوية',
        choices=Notification.PRIORITY_CHOICES,
        initial='normal',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    # === المستهدفون ===
    TARGET_CHOICES = [
        ('course_students', 'طلاب مقرر محدد'),
        ('major_students', 'طلاب تخصص ومستوى'),
        ('all_students', 'جميع الطلاب'),
        ('all_instructors', 'جميع المدرسين'),
        ('everyone', 'الجميع'),
        ('specific_student', 'طالب محدد'),
    ]

    target_type = forms.ChoiceField(
        label='نوع الاستهداف',
        choices=TARGET_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'hx-get': '',  # سيتم تعبئته في JS
            'hx-target': '#targeting-details',
            'hx-swap': 'innerHTML',
        })
    )

    # === فلاتر ديناميكية ===
    course = forms.ModelChoiceField(
        label='المقرر',
        queryset=Course.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    major = forms.ModelChoiceField(
        label='التخصص',
        queryset=Major.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'hx-get': '',  # سيتم تعبئته ديناميكياً
            'hx-target': '#level-select',
            'hx-swap': 'innerHTML',
        })
    )
    level = forms.ModelChoiceField(
        label='المستوى',
        queryset=Level.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    specific_user_id = forms.IntegerField(
        label='معرف المستخدم',
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'أدخل الرقم الأكاديمي أو المعرف...',
        })
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        is_admin = kwargs.pop('is_admin', False)
        super().__init__(*args, **kwargs)

        if is_admin:
            # الأدمن يرى جميع المقررات النشطة
            self.fields['course'].queryset = Course.objects.filter(
                is_active=True
            ).order_by('course_code')
        elif user:
            # المدرس يرى مقرراته فقط
            self.fields['course'].queryset = Course.objects.filter(
                instructor_courses__instructor=user,
                is_active=True
            ).order_by('course_code')

            # المدرس لا يستطيع إرسال لجميع المدرسين أو الجميع
            self.fields['target_type'].choices = [
                ('course_students', 'طلاب مقرر محدد'),
                ('major_students', 'طلاب تخصص ومستوى'),
                ('specific_student', 'طالب محدد'),
            ]

    def clean(self):
        cleaned_data = super().clean()
        target_type = cleaned_data.get('target_type')
        course = cleaned_data.get('course')
        major = cleaned_data.get('major')

        if target_type == 'course_students' and not course:
            self.add_error('course', 'يجب اختيار مقرر عند استهداف طلاب المقرر.')

        if target_type == 'major_students' and not major:
            self.add_error('major', 'يجب اختيار تخصص عند استهداف طلاب تخصص.')

        if target_type == 'specific_student' and not cleaned_data.get('specific_user_id'):
            self.add_error('specific_user_id', 'يجب تحديد المستخدم.')

        return cleaned_data


class NotificationPreferenceForm(forms.ModelForm):
    """
    نموذج تفضيلات إشعارات المستخدم
    """
    class Meta:
        model = NotificationPreference
        fields = [
            'email_enabled',
            'email_file_upload',
            'email_announcement',
            'email_assignment',
            'email_exam',
            'email_grade',
            'email_system',
        ]
        widgets = {
            'email_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
            'email_file_upload': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_announcement': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_assignment': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_exam': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_grade': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_system': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
