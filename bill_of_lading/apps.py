from django.apps import AppConfig


class BillOfLadingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bill_of_lading'
    verbose_name = 'Bill of Lading Management'
    
    def ready(self):
        import bill_of_lading.signals
