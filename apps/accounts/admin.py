"""
تسجيل نماذج accounts في لوحة تحكم Django
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import (
    Role, Permission, RolePermission, Major, Level, 
    Semester, User, VerificationCode, PasswordResetToken, UserActivity
)
# استيراد دالة التصدير من تطبيق core
from apps.core.admin import export_to_excel

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['code', 'display_name', 'is_system', 'is_active', 'users_count', 'created_at']
    list_filter = ['is_system', 'is_active']
    search_fields = ['code', 'display_name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    def users_count(self, obj):
        return obj.users.count()
    users_count.short_description = 'عدد المستخدمين'

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['code', 'display_name', 'category', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['code', 'display_name', 'description']

@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ['role', 'permission']
    list_filter = ['role']
    search_fields = ['role__code', 'role__display_name', 'permission__code']

@admin.register(Major)
class MajorAdmin(admin.ModelAdmin):
    list_display = ['major_name', 'is_active', 'students_count', 'created_at']
    list_filter = ['is_active']
    search_fields = ['major_name', 'description']
    readonly_fields = ['created_at']
    
    def students_count(self, obj):
        return obj.students.count()
    students_count.short_description = 'عدد الطلاب'

@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ['level_name', 'level_number', 'students_count']
    ordering = ['level_number']
    
    def students_count(self, obj):
        return obj.students.count()
    students_count.short_description = 'عدد الطلاب'

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ['name', 'academic_year', 'semester_number', 'is_current', 'start_date', 'end_date']
    list_filter = ['is_current', 'academic_year']
    search_fields = ['name', 'academic_year']
    readonly_fields = ['created_at']
    
    def save_model(self, request, obj, form, change):
        if obj.is_current:
            Semester.objects.filter(is_current=True).exclude(pk=obj.pk).update(is_current=False)
        super().save_model(request, obj, form, change)

# النسخة الكاملة والموحدة من UserAdmin
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['academic_id', 'full_name', 'email', 'role', 'status_badge', 'major', 'level']
    list_filter = ['account_status', 'role', 'major', 'level', 'is_staff']
    search_fields = ['academic_id', 'full_name', 'email', 'id_card_number']
    ordering = ['academic_id']
    
    # إضافة ميزة التصدير هنا
    actions = [export_to_excel]
    
    fieldsets = (
        ('معلومات الهوية', {
            'fields': ('academic_id', 'id_card_number', 'full_name', 'email')
        }),
        ('كلمة المرور', {
            'fields': ('password',),
            'description': 'كلمات المرور مشفرة. <a href="../password/">اضغط هنا لتغيير كلمة المرور</a>'
        }),
        ('الدور والتخصص', {
            'fields': ('role', 'major', 'level', 'account_status')
        }),
        ('الصلاحيات', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('معلومات إضافية', {
            'fields': ('profile_picture', 'phone_number'),
            'classes': ('collapse',)
        }),
        ('التواريخ', {
            'fields': ('date_joined', 'last_login'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('academic_id', 'id_card_number', 'full_name', 'role', 'major', 'level', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login']
    
    def status_badge(self, obj):
        colors = {'active': 'green', 'inactive': 'orange', 'suspended': 'red'}
        color = colors.get(obj.account_status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.get_account_status_display()
        )
    status_badge.short_description = 'الحالة'

@admin.register(VerificationCode)
class VerificationCodeAdmin(admin.ModelAdmin):
    list_display = ['user', 'email', 'code', 'is_used', 'expires_at', 'attempts']
    list_filter = ['is_used']
    search_fields = ['user__academic_id', 'email']
    readonly_fields = ['created_at']

@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_used', 'expires_at', 'created_at']
    list_filter = ['is_used']
    search_fields = ['user__academic_id', 'user__email']
    readonly_fields = ['created_at', 'token']

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'activity_type', 'ip_address', 'activity_time']
    list_filter = ['activity_type', 'activity_time']
    search_fields = ['user__academic_id', 'user__full_name', 'description']
    readonly_fields = ['activity_time']
    date_hierarchy = 'activity_time'