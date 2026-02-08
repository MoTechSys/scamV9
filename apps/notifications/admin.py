"""
تسجيل نماذج notifications في لوحة تحكم Django
"""

from django.contrib import admin
from .models import Notification, NotificationRecipient


class NotificationRecipientInline(admin.TabularInline):
    model = NotificationRecipient
    extra = 0
    readonly_fields = ['user', 'is_read', 'read_at']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'notification_type', 'priority', 'sender', 'course', 'recipients_count', 'read_count', 'created_at']
    list_filter = ['notification_type', 'priority', 'is_active', 'created_at']
    search_fields = ['title', 'body', 'sender__full_name']
    readonly_fields = ['created_at']
    autocomplete_fields = ['sender', 'course', 'file']
    inlines = [NotificationRecipientInline]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('محتوى الإشعار', {
            'fields': ('title', 'body', 'notification_type', 'priority')
        }),
        ('المرسل والارتباطات', {
            'fields': ('sender', 'course', 'file')
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
    list_display = ['notification', 'user', 'is_read', 'read_at', 'is_deleted']
    list_filter = ['is_read', 'is_deleted']
    search_fields = ['notification__title', 'user__full_name', 'user__academic_id']
    readonly_fields = ['read_at']
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
