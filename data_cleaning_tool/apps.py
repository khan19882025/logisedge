from django.apps import AppConfig


class DataCleaningToolConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'data_cleaning_tool'
    verbose_name = 'Data Cleaning Tool'
    
    def ready(self):
        """Import signals when the app is ready"""
        try:
            import data_cleaning_tool.signals
        except ImportError:
            pass
