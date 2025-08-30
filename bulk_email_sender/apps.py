from django.apps import AppConfig


class BulkEmailSenderConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bulk_email_sender'
    verbose_name = 'Bulk Email Sender'
    
    def ready(self):
        import bulk_email_sender.signals
