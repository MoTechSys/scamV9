"""
تسجيل نماذج courses في لوحة تحكم Django
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Course, CourseMajor, InstructorCourse, LectureFile


class CourseMajorInline(admin.TabularInline):
    model = CourseMajor
    extra = 1
    autocomplete_fields = ['major']


class InstructorCourseInline(admin.TabularInline):
    model = InstructorCourse
    extra = 1
    autocomplete_fields = ['instructor']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['course_code', 'course_name', 'level', 'semester', 'credit_hours', 'is_active', 'files_count']
    list_filter = ['level', 'semester', 'is_active']
    search_fields = ['course_code', 'course_name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [CourseMajorInline, InstructorCourseInline]
    
    fieldsets = (
        ('معلومات المقرر', {
            'fields': ('course_code', 'course_name', 'description', 'credit_hours')
        }),
        ('الارتباطات', {
            'fields': ('level', 'semester')
        }),
        ('الحالة', {
            'fields': ('is_active',)
        }),
        ('التواريخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def files_count(self, obj):
        count = obj.files.filter(is_deleted=False).count()
        return format_html('<strong>{}</strong>', count)
    files_count.short_description = 'عدد الملفات'


@admin.register(CourseMajor)
class CourseMajorAdmin(admin.ModelAdmin):
    list_display = ['course', 'major', 'created_at']
    list_filter = ['major']
    search_fields = ['course__course_code', 'course__course_name', 'major__major_name']
    autocomplete_fields = ['course', 'major']


@admin.register(InstructorCourse)
class InstructorCourseAdmin(admin.ModelAdmin):
    list_display = ['instructor', 'course', 'assigned_date', 'is_primary']
    list_filter = ['is_primary', 'assigned_date']
    search_fields = ['instructor__full_name', 'instructor__academic_id', 'course__course_code']
    autocomplete_fields = ['instructor', 'course']


@admin.register(LectureFile)
class LectureFileAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'file_type', 'content_type', 'uploader', 'is_visible', 'is_deleted', 'upload_date']
    list_filter = ['file_type', 'content_type', 'is_visible', 'is_deleted', 'upload_date']
    search_fields = ['title', 'description', 'course__course_code', 'uploader__full_name']
    readonly_fields = ['upload_date', 'updated_at', 'file_size', 'file_extension', 'download_count', 'view_count']
    autocomplete_fields = ['course', 'uploader']
    date_hierarchy = 'upload_date'
    
    fieldsets = (
        ('معلومات الملف', {
            'fields': ('title', 'description', 'file_type')
        }),
        ('المحتوى', {
            'fields': ('content_type', 'local_file', 'external_link')
        }),
        ('الارتباطات', {
            'fields': ('course', 'uploader')
        }),
        ('الحالة', {
            'fields': ('is_visible', 'is_deleted', 'deleted_at')
        }),
        ('الإحصائيات', {
            'fields': ('file_size', 'file_extension', 'download_count', 'view_count'),
            'classes': ('collapse',)
        }),
        ('التواريخ', {
            'fields': ('upload_date', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['make_visible', 'make_hidden', 'soft_delete', 'restore']
    
    def make_visible(self, request, queryset):
        queryset.update(is_visible=True)
        self.message_user(request, f"تم إظهار {queryset.count()} ملف/ملفات")
    make_visible.short_description = "إظهار الملفات المحددة"
    
    def make_hidden(self, request, queryset):
        queryset.update(is_visible=False)
        self.message_user(request, f"تم إخفاء {queryset.count()} ملف/ملفات")
    make_hidden.short_description = "إخفاء الملفات المحددة"
    
    def soft_delete(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_deleted=True, deleted_at=timezone.now())
        self.message_user(request, f"تم حذف {queryset.count()} ملف/ملفات (حذف ناعم)")
    soft_delete.short_description = "حذف ناعم للملفات المحددة"
    
    def restore(self, request, queryset):
        queryset.update(is_deleted=False, deleted_at=None)
        self.message_user(request, f"تم استعادة {queryset.count()} ملف/ملفات")
    restore.short_description = "استعادة الملفات المحذوفة"
