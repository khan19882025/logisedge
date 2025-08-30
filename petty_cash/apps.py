from django.apps import AppConfig


class PettyCashConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'petty_cash'
    
    def ready(self):
        import petty_cash.signals
