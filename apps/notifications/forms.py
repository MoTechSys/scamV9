"""
نماذج (Forms) لتطبيق notifications
S-ACM - Smart Academic Content Management System
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
