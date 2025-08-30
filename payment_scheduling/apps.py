from django.apps import AppConfig


class PaymentSchedulingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payment_scheduling'
    verbose_name = 'Payment Scheduling'

    def ready(self):
        import payment_scheduling.signals
