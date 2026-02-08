"""
لوحة تحكم Django للذكاء الاصطناعي - Enterprise v2 (Dynamic Governance)
S-ACM - Smart Academic Content Management System

=== Features ===
- AIConfiguration: Singleton admin with all AI settings
- APIKey: Encrypted key management with Test Connection action
- Health Dashboard: Real-time key health indicators
- AI Usage monitoring with filters
"""

import time
import logging
from datetime import timedelta

from django.contrib import admin, messages
from django.db.models import Count, Sum, Q, Avg
from django.http import JsonResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html

from .models import (
    AIConfiguration, APIKey,
    AISummary, AIGeneratedQuestion, AIChat, AIUsageLog,
    AIGenerationJob, StudentProgress,
)

logger = logging.getLogger('ai_features')


# ========================================================================
# Phase 2: AIConfiguration Singleton Admin
# ========================================================================

@admin.register(AIConfiguration)
class AIConfigurationAdmin(admin.ModelAdmin):
    """
    Singleton Admin for AI Configuration.
    Only one instance exists. Delete is disabled.
    """
    list_display = [
        'active_model', 'chunk_size', 'max_output_tokens',
        'temperature', 'user_rate_limit_per_hour',
        'service_status_badge', 'updated_at',
    ]
    readonly_fields = ['updated_at', 'updated_by']

    fieldsets = (
        ('نموذج الذكاء الاصطناعي', {
            'fields': ('active_model', 'is_service_enabled', 'maintenance_message'),
            'description': 'اختر النموذج النشط وحالة الخدمة.',
        }),
        ('إعدادات التقطيع (Chunking)', {
            'fields': ('chunk_size', 'chunk_overlap'),
            'description': 'التحكم في كيفية تقسيم النصوص الكبيرة قبل إرسالها لـ AI.',
        }),
        ('إعدادات الإخراج', {
            'fields': ('max_output_tokens', 'temperature'),
            'description': 'التحكم في حجم وجودة استجابات AI.',
        }),
        ('حدود الاستخدام', {
            'fields': ('user_rate_limit_per_hour',),
            'description': 'حد الطلبات لكل مستخدم في الساعة.',
        }),
        ('بيانات التدقيق', {
            'fields': ('updated_at', 'updated_by'),
            'classes': ('collapse',),
        }),
    )

    def service_status_badge(self, obj):
        if obj.is_service_enabled:
            return format_html(
                '<span style="color: #10b981; font-weight: bold;">🟢 مفعّل</span>'
            )
        return format_html(
            '<span style="color: #ef4444; font-weight: bold;">🔴 معطّل</span>'
        )
    service_status_badge.short_description = 'حالة الخدمة'

    def has_add_permission(self, request):
        """Only allow one instance."""
        return not AIConfiguration.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion."""
        return False

    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
        AIConfiguration.invalidate_cache()
        messages.success(request, '✅ تم حفظ إعدادات AI بنجاح. التغييرات سارية فوراً.')


# ========================================================================
# Phase 2: APIKey Admin with Health Check
# ========================================================================

@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    """
    API Key management with:
    - Encrypted key display (hint only)
    - Test Connection action
    - Health status indicators
    - RPM configuration
    """
    list_display = [
        'label', 'provider', 'status_badge', 'key_hint',
        'error_count', 'total_requests', 'latency_display',
        'rpm_limit', 'tokens_used_today', 'is_active',
    ]
    list_filter = ['provider', 'status', 'is_active']
    search_fields = ['label', 'key_hint']
    readonly_fields = [
        'key_hint', 'status', 'error_count', 'total_requests',
        'last_error', 'last_error_at', 'last_success_at',
        'last_latency_ms', 'tokens_used_today', 'tokens_reset_date',
        'cooldown_until', 'created_at', 'updated_at',
    ]
    actions = ['test_connection_action', 'reset_errors_action', 'activate_keys', 'deactivate_keys']

    fieldsets = (
        ('معلومات المفتاح', {
            'fields': ('label', 'provider', 'is_active', 'priority'),
        }),
        ('المفتاح', {
            'fields': ('api_key_input', 'key_hint'),
            'description': 'أدخل مفتاح API الكامل. يتم تشفيره تلقائياً عند الحفظ.',
        }),
        ('حدود الاستخدام', {
            'fields': ('rpm_limit',),
            'description': 'حد الطلبات في الدقيقة حسب خطة Google Cloud.',
        }),
        ('حالة الصحة', {
            'fields': (
                'status', 'error_count', 'total_requests',
                'last_latency_ms', 'tokens_used_today',
            ),
            'classes': ('collapse',),
        }),
        ('سجل الأحداث', {
            'fields': (
                'last_success_at', 'last_error_at', 'last_error',
                'cooldown_until', 'tokens_reset_date',
            ),
            'classes': ('collapse',),
        }),
        ('البيانات الوصفية', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def get_fieldsets(self, request, obj=None):
        fieldsets = list(super().get_fieldsets(request, obj))
        # Replace 'api_key_input' placeholder with actual field handling
        return fieldsets

    class APIKeyForm(admin.ModelAdmin):
        pass

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Add a custom field for raw key input
        from django import forms
        form.base_fields['api_key_input'] = forms.CharField(
            label='مفتاح API',
            required=False,
            widget=forms.PasswordInput(attrs={
                'class': 'vTextField',
                'placeholder': 'أدخل مفتاح API الجديد (اتركه فارغاً للإبقاء على الحالي)',
                'autocomplete': 'off',
            }),
            help_text='أدخل المفتاح الكامل. سيتم تشفيره وحفظه بأمان.'
        )
        return form

    def save_model(self, request, obj, form, change):
        """Encrypt the API key on save."""
        raw_key = form.cleaned_data.get('api_key_input', '')
        if raw_key:
            obj.set_key(raw_key)
            messages.success(request, f'✅ تم تشفير وحفظ مفتاح "{obj.label}" بنجاح.')
        elif not change:
            messages.error(request, '⚠️ يجب إدخال مفتاح API عند الإنشاء.')
            return
        super().save_model(request, obj, form, change)

    def status_badge(self, obj):
        colors = {
            'active': ('#10b981', '🟢'),
            'cooldown': ('#f59e0b', '🟡'),
            'disabled': ('#6b7280', '⚫'),
            'error': ('#ef4444', '🔴'),
        }
        color, icon = colors.get(obj.status, ('#6b7280', '⚪'))
        return format_html(
            '<span style="color: {};">{} {}</span>',
            color, icon, obj.get_status_display()
        )
    status_badge.short_description = 'الحالة'

    def latency_display(self, obj):
        ms = obj.last_latency_ms
        if ms == 0:
            return '-'
        color = '#10b981' if ms < 500 else '#f59e0b' if ms < 2000 else '#ef4444'
        return format_html('<span style="color: {};">{} ms</span>', color, ms)
    latency_display.short_description = 'زمن الاستجابة'

    # ---- Custom Actions ----

    @admin.action(description='🔍 اختبار الاتصال للمفاتيح المحددة')
    def test_connection_action(self, request, queryset):
        """Test connection for selected API keys."""
        results = []
        for key_obj in queryset:
            raw_key = key_obj.get_key()
            if not raw_key:
                results.append(f'❌ {key_obj.label}: فشل فك التشفير')
                continue

            try:
                from google import genai
                from google.genai import types

                client = genai.Client(api_key=raw_key)

                try:
                    config = AIConfiguration.get_config()
                    model_name = config.active_model
                except Exception:
                    model_name = 'gemini-2.0-flash'

                start_ms = int(time.time() * 1000)
                response = client.models.generate_content(
                    model=model_name,
                    contents="Say: Hello, I'm ready!",
                    config=types.GenerateContentConfig(max_output_tokens=20)
                )
                latency_ms = int(time.time() * 1000) - start_ms

                if response.text:
                    key_obj.mark_success(latency_ms)
                    results.append(
                        f'✅ {key_obj.label}: نجح ({latency_ms}ms) - "{response.text[:50]}"'
                    )
                else:
                    key_obj.mark_error("Empty response")
                    results.append(f'⚠️ {key_obj.label}: استجابة فارغة')

            except ImportError:
                results.append(f'❌ {key_obj.label}: google-genai غير مثبت')
            except Exception as e:
                error_str = str(e)
                is_rate_limit = any(kw in error_str.lower() for kw in ['rate', 'quota', '429'])
                key_obj.mark_error(error_str[:200], is_rate_limit=is_rate_limit)
                results.append(f'❌ {key_obj.label}: {error_str[:100]}')

        for result in results:
            if result.startswith('✅'):
                messages.success(request, result)
            elif result.startswith('⚠️'):
                messages.warning(request, result)
            else:
                messages.error(request, result)

    @admin.action(description='🔄 إعادة تعيين عداد الأخطاء')
    def reset_errors_action(self, request, queryset):
        """Reset error counts for selected keys."""
        count = queryset.update(
            error_count=0,
            status='active',
            cooldown_until=None,
            last_error=None,
            last_error_at=None,
        )
        messages.success(request, f'✅ تم إعادة تعيين {count} مفتاح(مفاتيح).')

    @admin.action(description='✅ تفعيل المفاتيح المحددة')
    def activate_keys(self, request, queryset):
        count = queryset.update(is_active=True, status='active')
        messages.success(request, f'✅ تم تفعيل {count} مفتاح(مفاتيح).')

    @admin.action(description='⛔ تعطيل المفاتيح المحددة')
    def deactivate_keys(self, request, queryset):
        count = queryset.update(is_active=False, status='disabled')
        messages.success(request, f'⛔ تم تعطيل {count} مفتاح(مفاتيح).')

    # ---- Custom Admin URLs ----

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'ai-dashboard/',
                self.admin_site.admin_view(self.ai_dashboard_view),
                name='ai_dashboard',
            ),
            path(
                'test-key/<int:key_id>/',
                self.admin_site.admin_view(self.test_single_key_view),
                name='ai_test_key',
            ),
        ]
        return custom_urls + urls

    def ai_dashboard_view(self, request):
        """
        Custom Admin View: /admin/ai_features/apikey/ai-dashboard/
        Shows real-time health of all keys, token usage, and failure rates.
        """
        from apps.ai_features.services import HydraKeyManager

        manager = HydraKeyManager()
        key_health = manager.get_health_status()

        # Aggregate stats
        now = timezone.now()
        today = now.date()
        one_hour_ago = now - timedelta(hours=1)

        total_requests_today = AIUsageLog.objects.filter(
            request_time__date=today
        ).count()
        total_tokens_today = AIUsageLog.objects.filter(
            request_time__date=today
        ).aggregate(total=Sum('tokens_used'))['total'] or 0
        failure_count_today = AIUsageLog.objects.filter(
            request_time__date=today, success=False
        ).count()
        success_count_today = total_requests_today - failure_count_today
        failure_rate = (failure_count_today / total_requests_today * 100) if total_requests_today > 0 else 0

        # Hourly breakdown for chart
        hourly_stats = []
        for i in range(24):
            hour_start = now.replace(hour=i, minute=0, second=0, microsecond=0)
            if hour_start.date() != today:
                continue
            hour_end = hour_start + timedelta(hours=1)
            count = AIUsageLog.objects.filter(
                request_time__gte=hour_start,
                request_time__lt=hour_end
            ).count()
            hourly_stats.append({'hour': i, 'count': count})

        try:
            config = AIConfiguration.get_config()
        except Exception:
            config = None

        context = {
            **self.admin_site.each_context(request),
            'title': 'لوحة مراقبة الذكاء الاصطناعي',
            'key_health': key_health,
            'total_keys': len(key_health),
            'active_keys': sum(1 for k in key_health if k['is_available']),
            'total_requests_today': total_requests_today,
            'total_tokens_today': total_tokens_today,
            'failure_rate': round(failure_rate, 1),
            'success_count_today': success_count_today,
            'failure_count_today': failure_count_today,
            'hourly_stats': hourly_stats,
            'config': config,
        }
        return TemplateResponse(
            request,
            'admin/ai_features/ai_dashboard.html',
            context
        )

    def test_single_key_view(self, request, key_id):
        """AJAX endpoint: Test a single key."""
        try:
            key_obj = APIKey.objects.get(pk=key_id)
        except APIKey.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'مفتاح غير موجود'})

        raw_key = key_obj.get_key()
        if not raw_key:
            return JsonResponse({'success': False, 'error': 'فشل فك التشفير'})

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=raw_key)
            start_ms = int(time.time() * 1000)
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents="Say: Hello!",
                config=types.GenerateContentConfig(max_output_tokens=10)
            )
            latency_ms = int(time.time() * 1000) - start_ms

            if response.text:
                key_obj.mark_success(latency_ms)
                return JsonResponse({
                    'success': True,
                    'latency_ms': latency_ms,
                    'response': response.text[:50]
                })

            key_obj.mark_error("Empty response")
            return JsonResponse({'success': False, 'error': 'استجابة فارغة'})

        except Exception as e:
            key_obj.mark_error(str(e)[:200])
            return JsonResponse({'success': False, 'error': str(e)[:200]})


# ========================================================================
# Existing Admin Classes (Enhanced)
# ========================================================================

@admin.register(AISummary)
class AISummaryAdmin(admin.ModelAdmin):
    list_display = ['file', 'user', 'word_count', 'model_used', 'is_cached', 'generated_at']
    list_filter = ['model_used', 'is_cached', 'language', 'generated_at']
    search_fields = ['file__title', 'user__full_name', 'summary_text']
    readonly_fields = ['generated_at', 'generation_time', 'word_count']
    date_hierarchy = 'generated_at'

    fieldsets = (
        ('معلومات الملخص', {
            'fields': ('file', 'user', 'summary_text')
        }),
        ('التفاصيل', {
            'fields': ('language', 'word_count', 'model_used', 'is_cached', 'md_file_path')
        }),
        ('الإحصائيات', {
            'fields': ('generated_at', 'generation_time'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AIGeneratedQuestion)
class AIGeneratedQuestionAdmin(admin.ModelAdmin):
    list_display = ['file', 'question_preview', 'question_type', 'score', 'difficulty_level', 'is_cached', 'generated_at']
    list_filter = ['question_type', 'difficulty_level', 'is_cached', 'generated_at']
    search_fields = ['file__title', 'question_text', 'user__full_name']
    readonly_fields = ['generated_at']
    date_hierarchy = 'generated_at'

    fieldsets = (
        ('معلومات السؤال', {
            'fields': ('file', 'user', 'question_text', 'question_type')
        }),
        ('الإجابة والخيارات', {
            'fields': ('options', 'correct_answer', 'explanation', 'score')
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
    date_hierarchy = 'created_at'

    def question_preview(self, obj):
        if obj.question:
            return obj.question[:50] + '...' if len(obj.question) > 50 else obj.question
        return ""
    question_preview.short_description = 'السؤال'


@admin.register(AIUsageLog)
class AIUsageLogAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'request_type', 'file', 'tokens_used',
        'was_cached', 'success', 'api_key_used', 'request_time',
    ]
    list_filter = ['request_type', 'was_cached', 'success', 'request_time']
    search_fields = ['user__full_name', 'user__academic_id', 'file__title']
    readonly_fields = ['request_time']
    date_hierarchy = 'request_time'

    fieldsets = (
        ('معلومات الطلب', {
            'fields': ('user', 'request_type', 'file', 'api_key_used')
        }),
        ('التفاصيل', {
            'fields': ('tokens_used', 'was_cached', 'success', 'error_message')
        }),
        ('الوقت', {
            'fields': ('request_time',),
            'classes': ('collapse',)
        }),
    )


@admin.register(AIGenerationJob)
class AIGenerationJobAdmin(admin.ModelAdmin):
    list_display = ['instructor', 'file', 'job_type', 'status', 'created_at', 'completed_at']
    list_filter = ['job_type', 'status', 'created_at']
    search_fields = ['instructor__full_name', 'file__title']
    readonly_fields = ['created_at', 'completed_at']
    date_hierarchy = 'created_at'


@admin.register(StudentProgress)
class StudentProgressAdmin(admin.ModelAdmin):
    list_display = ['student', 'file', 'progress', 'last_position', 'last_accessed']
    list_filter = ['progress', 'last_accessed']
    search_fields = ['student__full_name', 'file__title']
    readonly_fields = ['last_accessed']
