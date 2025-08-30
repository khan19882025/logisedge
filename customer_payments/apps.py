from django.apps import AppConfig


class CustomerPaymentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'customer_payments'
    verbose_name = 'Customer Payments'

    def ready(self):
        """
        Import and register signals when the app is ready
        """
        try:
            import customer_payments.signals
            print("✅ Customer Payments signals loaded successfully")
        except Exception as e:
            print(f"❌ Error loading Customer Payments signals: {e}")
