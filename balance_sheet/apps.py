from django.apps import AppConfig


class BalanceSheetConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'balance_sheet'
    verbose_name = 'Balance Sheet Reports'
    
    def ready(self):
        # Import signals if needed
        pass
