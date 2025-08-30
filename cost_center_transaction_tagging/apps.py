from django.apps import AppConfig


class CostCenterTransactionTaggingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cost_center_transaction_tagging'
    verbose_name = 'Cost Center Transaction Tagging'
    
    def ready(self):
        import cost_center_transaction_tagging.signals
