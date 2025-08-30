from django.apps import AppConfig


class NotificationTemplatesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notification_templates'
    verbose_name = 'Notification Templates'
    
    def ready(self):
        import notification_templates.signals
