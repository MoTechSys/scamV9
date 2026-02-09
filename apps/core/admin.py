"""
تسجيل نماذج core في لوحة تحكم Django
S-ACM - Smart Academic Content Management System
"""

from django.contrib import admin
from django.http import HttpResponse
import openpyxl
from .models import SystemSetting, AuditLog

# 1. تعريف دالة التصدير إلى إكسل (مع إصلاح مشكلة النصوص المترجمة)
@admin.action(description="تصدير السجلات المحددة إلى ملف Excel")
def export_to_excel(modeladmin, request, queryset):
    # إنشاء استجابة بملف إكسل
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{queryset.model._meta.verbose_name_plural}.xlsx"'
    
    # إنشاء ملف العمل (Workbook)
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = 'البيانات المصدّرة'
    
    # جلب أسماء الحقول البرمجية (field.name) مع استبعاد الحقول الحساسة والطويلة
    field_names = [field.name for field in queryset.model._meta.fields if field.name not in ['password', 'id', 'changes']]
    
    # التعديل الهام: تحويل verbose_name إلى string صريح لتجنب خطأ الترجمة (Proxy objects)
    headers = [str(field.verbose_name) for field in queryset.model._meta.fields if field.name not in ['password', 'id', 'changes']]
    worksheet.append(headers)
    
    # جلب البيانات من قاعدة البيانات وإضافتها للصفوف
    for obj in queryset:
        row = []
        for field in field_names:
            value = getattr(obj, field)
            # تحويل جميع القيم (نصوص، تواريخ، منطقية) إلى نص بسيط لضمان التوافق مع إكسل
            row.append(str(value) if value is not None else "")
        worksheet.append(row)
        
    workbook.save(response)
    return response

# 2. تسجيل نموذج إعدادات النظام
@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ['key', 'value_preview', 'is_public', 'updated_at']
    list_filter = ['is_public']
    search_fields = ['key', 'value', 'description']
    readonly_fields = ['updated_at']
    
    def value_preview(self, obj):
        return obj.value[:50] + '...' if len(obj.value) > 50 else obj.value
    value_preview.short_description = 'القيمة'

# 3. تسجيل نموذج سجلات التدقيق (نسخة واحدة مدمجة ومنظمة)
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'model_name', 'object_repr', 'ip_address', 'timestamp']
    list_filter = ['action', 'model_name', 'timestamp']
    search_fields = ['user__full_name', 'user__academic_id', 'model_name', 'object_repr']
    readonly_fields = ['user', 'action', 'model_name', 'object_id', 'object_repr', 'changes', 'ip_address', 'user_agent', 'timestamp']
    date_hierarchy = 'timestamp'
    
    # تفعيل ميزة التصدير في واجهة سجلات التدقيق
    actions = [export_to_excel]
    
    # منع العمليات اليدوية (إضافة، تعديل، حذف) لضمان نزاهة سجلات التدقيق
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False