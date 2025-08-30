from django.apps import AppConfig


class PaymentSourceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payment_source'
    verbose_name = 'Payment Source Management'
    
    def ready(self):
        """Import signals when app is ready"""
        try:
            import payment_source.signals
        except ImportError:
            pass
