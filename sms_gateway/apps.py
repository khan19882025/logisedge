from django.apps import AppConfig


class SmsGatewayConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sms_gateway'
    verbose_name = 'SMS Gateway'
    
    def ready(self):
        """Import signals when the app is ready"""
        try:
            import sms_gateway.signals
        except ImportError:
            pass
