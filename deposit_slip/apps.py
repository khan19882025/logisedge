from django.apps import AppConfig


class DepositSlipConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'deposit_slip'
    verbose_name = 'Deposit Slips'
    
    def ready(self):
        import deposit_slip.signals
