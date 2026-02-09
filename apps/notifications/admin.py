"""
تسجيل نماذج notifications v2 في لوحة تحكم Django
S-ACM - Smart Academic Content Management System
"""

from django.contrib import admin
from .models import Notification, NotificationRecipient, NotificationPreference


class NotificationRecipientInline(admin.TabularInline):
    model = NotificationRecipient
    extra = 0
    readonly_fields = ['user', 'is_read', 'read_at', 'is_deleted', 'deleted_at', 'is_archived']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'notification_type', 'priority', 'sender',
        'course', 'recipients_count', 'read_count', 'created_at'
    ]
    list_filter = ['notification_type', 'priority', 'is_active', 'created_at']
    search_fields = ['title', 'body', 'sender__full_name']
    readonly_fields = ['created_at', 'content_type', 'object_id']
    autocomplete_fields = ['sender', 'course']
    inlines = [NotificationRecipientInline]
    date_hierarchy = 'created_at'

    fieldsets = (
        ('محتوى الإشعار', {
            'fields': ('title', 'body', 'notification_type', 'priority')
        }),
        ('المرسل والارتباطات', {
            'fields': ('sender', 'course', 'content_type', 'object_id')
        }),
        ('الحالة', {
            'fields': ('is_active', 'expires_at')
        }),
        ('التواريخ', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def recipients_count(self, obj):
        return obj.recipients.count()
    recipients_count.short_description = 'عدد المستلمين'

    def read_count(self, obj):
        return obj.recipients.filter(is_read=True).count()
    read_count.short_description = 'عدد القراء'


@admin.register(NotificationRecipient)
class NotificationRecipientAdmin(admin.ModelAdmin):
    list_display = ['notification', 'user', 'is_read', 'read_at', 'is_deleted', 'is_archived']
    list_filter = ['is_read', 'is_deleted', 'is_archived']
    search_fields = ['notification__title', 'user__full_name', 'user__academic_id']
    readonly_fields = ['read_at', 'deleted_at']
    autocomplete_fields = ['notification', 'user']

    actions = ['mark_as_read', 'mark_as_unread']

    def mark_as_read(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_read=True, read_at=timezone.now())
        self.message_user(request, f"تم تحديد {queryset.count()} إشعار/إشعارات كمقروءة")
    mark_as_read.short_description = "تحديد كمقروء"

    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False, read_at=None)
        self.message_user(request, f"تم تحديد {queryset.count()} إشعار/إشعارات كغير مقروءة")
    mark_as_unread.short_description = "تحديد كغير مقروء"


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'email_enabled', 'updated_at']
    list_filter = ['email_enabled']
    search_fields = ['user__full_name', 'user__academic_id']
    autocomplete_fields = ['user']
