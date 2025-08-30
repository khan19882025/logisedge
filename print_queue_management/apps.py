from django.apps import AppConfig


class PrintQueueManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'print_queue_management'
    verbose_name = 'Print Queue Management'
    
    def ready(self):
        import print_queue_management.signals
