"""
نماذج (Forms) لتطبيق notifications - Enterprise v2
S-ACM - Smart Academic Content Management System

=== Phase 3: Broadcast Tab ===
- BroadcastNotificationForm: Target "All Students in Course X"
"""

from django import forms
from .models import Notification
from apps.courses.models import Course


class NotificationForm(forms.ModelForm):
    """نموذج إنشاء إشعار عام (للأدمن)"""

    TARGET_CHOICES = [
        ('all', 'جميع المستخدمين'),
        ('students', 'الطلاب فقط'),
        ('instructors', 'المدرسين فقط'),
    ]

    target = forms.ChoiceField(
        choices=TARGET_CHOICES,
        label='المستهدفون',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Notification
        fields = ['title', 'body', 'notification_type', 'priority']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'عنوان الإشعار'
            }),
            'body': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'محتوى الإشعار'
            }),
            'notification_type': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
        }


class CourseNotificationForm(forms.Form):
    """نموذج إنشاء إشعار لمقرر معين (للمدرس)"""

    course = forms.ModelChoiceField(
        queryset=Course.objects.none(),
        label='المقرر',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    title = forms.CharField(
        label='العنوان',
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'عنوان الإشعار'
        })
    )
    body = forms.CharField(
        label='المحتوى',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'محتوى الإشعار'
        })
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            # المقررات المعينة للمدرس
            self.fields['course'].queryset = Course.objects.filter(
                instructor_courses__instructor=user,
                is_active=True
            )


class BroadcastNotificationForm(forms.Form):
    """
    Phase 3: Broadcast Tab - Target students in a specific course.
    Used by both Admins and Instructors.
    """

    BROADCAST_TARGET_CHOICES = [
        ('course_students', 'جميع طلاب المقرر المحدد'),
        ('all_students', 'جميع الطلاب في النظام'),
        ('all_instructors', 'جميع المدرسين'),
        ('everyone', 'الجميع'),
    ]

    target_type = forms.ChoiceField(
        choices=BROADCAST_TARGET_CHOICES,
        label='نوع الاستهداف',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    course = forms.ModelChoiceField(
        queryset=Course.objects.none(),
        label='المقرر (عند اختيار طلاب المقرر)',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    title = forms.CharField(
        label='عنوان الإشعار',
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'عنوان الإشعار'
        })
    )
    body = forms.CharField(
        label='محتوى الإشعار',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'محتوى الإشعار...'
        })
    )
    priority = forms.ChoiceField(
        choices=Notification.PRIORITY_CHOICES,
        label='الأولوية',
        initial='normal',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        is_admin = kwargs.pop('is_admin', False)
        super().__init__(*args, **kwargs)

        if is_admin:
            self.fields['course'].queryset = Course.objects.filter(is_active=True)
        elif user:
            self.fields['course'].queryset = Course.objects.filter(
                instructor_courses__instructor=user,
                is_active=True
            )
            # Instructors can only target their course students
            self.fields['target_type'].choices = [
                ('course_students', 'جميع طلاب المقرر المحدد'),
            ]

    def clean(self):
        cleaned_data = super().clean()
        target_type = cleaned_data.get('target_type')
        course = cleaned_data.get('course')

        if target_type == 'course_students' and not course:
            self.add_error('course', 'يجب اختيار مقرر عند استهداف طلاب المقرر.')

        return cleaned_data
