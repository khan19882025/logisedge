from django.apps import AppConfig


class BankAccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bank_accounts'
    verbose_name = 'Bank Accounts Management'
    
    def ready(self):
        """Import signals when app is ready"""
        import bank_accounts.signals
