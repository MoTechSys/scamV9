"""
تسجيل نماذج ai_features في لوحة تحكم Django
S-ACM - Smart Academic Content Management System
"""

from django.contrib import admin
# تصحيح الاستيراد: استخدام AIGeneratedQuestion بدلاً من AIQuestion
from .models import AISummary, AIGeneratedQuestion, AIChat, AIUsageLog


@admin.register(AISummary)
class AISummaryAdmin(admin.ModelAdmin):
    list_display = ['file', 'user', 'word_count', 'model_used', 'is_cached', 'generated_at']
    list_filter = ['model_used', 'is_cached', 'language', 'generated_at']
    search_fields = ['file__title', 'user__full_name', 'summary_text']
    readonly_fields = ['generated_at', 'generation_time', 'word_count']
    # autocomplete_fields = ['file', 'user']
    date_hierarchy = 'generated_at'
    
    fieldsets = (
        ('معلومات الملخص', {
            'fields': ('file', 'user', 'summary_text')
        }),
        ('التفاصيل', {
            'fields': ('language', 'word_count', 'model_used', 'is_cached')
        }),
        ('الإحصائيات', {
            'fields': ('generated_at', 'generation_time'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AIGeneratedQuestion)
class AIGeneratedQuestionAdmin(admin.ModelAdmin):
    # تم تحديث الاسم واستخدام الحقول الجديدة (question_text بدلاً من json)
    list_display = ['file', 'question_preview', 'question_type', 'difficulty_level', 'is_cached', 'generated_at']
    list_filter = ['question_type', 'difficulty_level', 'is_cached', 'generated_at']
    search_fields = ['file__title', 'question_text', 'user__full_name']
    readonly_fields = ['generated_at']
    # autocomplete_fields = ['file', 'user']
    date_hierarchy = 'generated_at'
    
    fieldsets = (
        ('معلومات السؤال', {
            'fields': ('file', 'user', 'question_text', 'question_type')
        }),
        ('الإجابة والخيارات', {
            'fields': ('options', 'correct_answer', 'explanation')
        }),
        ('التفاصيل', {
            'fields': ('difficulty_level', 'is_cached')
        }),
        ('الإحصائيات', {
            'fields': ('generated_at',),
            'classes': ('collapse',)
        }),
    )

    def question_preview(self, obj):
        # التأكد من وجود النص قبل قصه لتجنب الأخطاء
        if obj.question_text:
            return obj.question_text[:50] + '...' if len(obj.question_text) > 50 else obj.question_text
        return ""
    question_preview.short_description = 'نص السؤال'


@admin.register(AIChat)
class AIChatAdmin(admin.ModelAdmin):
    list_display = ['file', 'user', 'question_preview', 'is_helpful', 'response_time', 'created_at']
    list_filter = ['is_helpful', 'created_at']
    search_fields = ['file__title', 'user__full_name', 'question', 'answer']
    readonly_fields = ['created_at', 'response_time']
    # autocomplete_fields = ['file', 'user']
    date_hierarchy = 'created_at'
    
    def question_preview(self, obj):
        if obj.question:
            return obj.question[:50] + '...' if len(obj.question) > 50 else obj.question
        return ""
    question_preview.short_description = 'السؤال'


@admin.register(AIUsageLog)
class AIUsageLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'request_type', 'file', 'tokens_used', 'was_cached', 'success', 'request_time']
    list_filter = ['request_type', 'was_cached', 'success', 'request_time']
    search_fields = ['user__full_name', 'user__academic_id', 'file__title']
    readonly_fields = ['request_time']
    # autocomplete_fields = ['user', 'file']
    date_hierarchy = 'request_time'
    
    fieldsets = (
        ('معلومات الطلب', {
            'fields': ('user', 'request_type', 'file')
        }),
        ('التفاصيل', {
            'fields': ('tokens_used', 'was_cached', 'success', 'error_message')
        }),
        ('الوقت', {
            'fields': ('request_time',),
            'classes': ('collapse',)
        }),
    )