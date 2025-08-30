from django.apps import AppConfig


class TaxSettingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tax_settings'
    verbose_name = 'Tax Settings (VAT)'
    
    def ready(self):
        import tax_settings.signals
