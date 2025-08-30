from django.apps import AppConfig


class BulkExportConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bulk_export'
    verbose_name = 'Bulk Export'
    
    def ready(self):
        """Import signals when app is ready"""
        try:
            import bulk_export.signals
        except ImportError:
            pass
