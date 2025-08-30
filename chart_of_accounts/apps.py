from django.apps import AppConfig


class ChartOfAccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chart_of_accounts'
    verbose_name = 'Chart of Accounts'
    
    def ready(self):
        import chart_of_accounts.signals
