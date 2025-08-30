from django.apps import AppConfig


class SupplierPaymentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'supplier_payments'
    
    def ready(self):
        import supplier_payments.signals
