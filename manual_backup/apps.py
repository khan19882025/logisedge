from django.apps import AppConfig


class ManualBackupConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'manual_backup'
    verbose_name = 'Manual Backup System'
    
    def ready(self):
        """Import signals when the app is ready"""
        try:
            import manual_backup.signals
        except ImportError:
            pass
