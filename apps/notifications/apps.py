from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notifications'
    verbose_name = 'نظام الإشعارات'

    def ready(self):
        """تسجيل Django Signals عند جاهزية التطبيق"""
        import apps.notifications.signals  # noqa: F401
