from django.apps import AppConfig


class SystemLogsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'system_logs'
    verbose_name = 'System Error & Debug Logs'
    
    def ready(self):
        import system_logs.signals
