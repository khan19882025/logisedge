from django.apps import AppConfig


class LogHistoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'log_history'
    verbose_name = 'Log History'
    
    def ready(self):
        """
        Import signals when the app is ready
        """
        try:
            import log_history.signals
        except ImportError:
            pass
