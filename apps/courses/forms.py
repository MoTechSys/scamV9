"""
نماذج (Forms) لتطبيق courses
S-ACM - Smart Academic Content Management System
"""

from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from django.conf import settings
from pathlib import Path

from .models import Course, CourseMajor, InstructorCourse, LectureFile
from apps.accounts.models import Major, Level, Semester


class CourseForm(forms.ModelForm):
    """نموذج إنشاء/تحديث المقرر"""
    
    class Meta:
        model = Course
        fields = ['course_code', 'course_name', 'description', 'level', 'semester', 'credit_hours', 'is_active']
        widgets = {
            'course_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثال: CS101'
            }),
            'course_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم المقرر'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'وصف المقرر (اختياري)'
            }),
            'level': forms.Select(attrs={'class': 'form-select'}),
            'semester': forms.Select(attrs={'class': 'form-select'}),
            'credit_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 6
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }


class CourseMajorForm(forms.ModelForm):
    """نموذج ربط المقرر بالتخصص"""
    
    class Meta:
        model = CourseMajor
        fields = ['major']
        widgets = {
            'major': forms.Select(attrs={'class': 'form-select'})
        }


# FormSet لربط المقررات بالتخصصات
CourseMajorFormSet = inlineformset_factory(
    Course,
    CourseMajor,
    form=CourseMajorForm,
    extra=1,
    can_delete=True
)


class InstructorCourseForm(forms.ModelForm):
    """نموذج تعيين مدرس لمقرر"""
    
    class Meta:
        model = InstructorCourse
        fields = ['instructor', 'is_primary']
        widgets = {
            'instructor': forms.Select(attrs={'class': 'form-select'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }


class LectureFileForm(forms.ModelForm):
    """نموذج رفع/تحديث ملف"""
    
    class Meta:
        model = LectureFile
        fields = ['course', 'title', 'description', 'file_type', 'content_type', 'local_file', 'external_link', 'is_visible']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'عنوان الملف'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'وصف الملف (اختياري)'
            }),
            'file_type': forms.Select(attrs={'class': 'form-select'}),
            'content_type': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'local_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.ppt,.pptx,.txt,.md,.mp4,.webm,.avi,.mov,.jpg,.jpeg,.png,.gif'
            }),
            'external_link': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://...'
            }),
            'is_visible': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # تحديد المقررات المتاحة للمدرس
        if self.user:
            if self.user.is_admin():
                self.fields['course'].queryset = Course.objects.filter(is_active=True)
            else:
                self.fields['course'].queryset = Course.objects.filter(
                    instructor_courses__instructor=self.user,
                    is_active=True
                )
    
    def clean(self):
        cleaned_data = super().clean()
        content_type = cleaned_data.get('content_type')
        local_file = cleaned_data.get('local_file')
        external_link = cleaned_data.get('external_link')
        
        # التحقق من وجود محتوى
        if content_type == 'local_file' and not local_file:
            if not self.instance.pk or not self.instance.local_file:
                raise ValidationError('يجب رفع ملف عند اختيار "ملف محلي".')
        
        if content_type == 'external_link' and not external_link:
            raise ValidationError('يجب إدخال رابط عند اختيار "رابط خارجي".')
        
        return cleaned_data
    
    def clean_local_file(self):
        local_file = self.cleaned_data.get('local_file')
        
        if local_file:
            # التحقق من حجم الملف
            max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 50 * 1024 * 1024)
            if local_file.size > max_size:
                raise ValidationError(f'حجم الملف يتجاوز الحد المسموح ({max_size // (1024*1024)} MB).')
            
            # التحقق من امتداد الملف
            ext = Path(local_file.name).suffix.lower()
            allowed_extensions = (
                getattr(settings, 'ALLOWED_FILE_EXTENSIONS', []) +
                getattr(settings, 'ALLOWED_VIDEO_EXTENSIONS', []) +
                getattr(settings, 'ALLOWED_IMAGE_EXTENSIONS', [])
            )
            
            if allowed_extensions and ext not in allowed_extensions:
                raise ValidationError(f'نوع الملف غير مسموح. الأنواع المسموحة: {", ".join(allowed_extensions)}')
        
        return local_file


class CourseSearchForm(forms.Form):
    """نموذج البحث في المقررات"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'بحث...'
        })
    )
    level = forms.ModelChoiceField(
        queryset=Level.objects.all(),
        required=False,
        empty_label='جميع المستويات',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    semester = forms.ModelChoiceField(
        queryset=Semester.objects.all(),
        required=False,
        empty_label='جميع الفصول',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    major = forms.ModelChoiceField(
        queryset=Major.objects.filter(is_active=True),
        required=False,
        empty_label='جميع التخصصات',
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class FileFilterForm(forms.Form):
    """نموذج فلترة الملفات"""
    
    FILE_TYPE_CHOICES = [('', 'جميع الأنواع')] + list(LectureFile.FILE_TYPE_CHOICES)
    
    file_type = forms.ChoiceField(
        choices=FILE_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'بحث في الملفات...'
        })
    )
