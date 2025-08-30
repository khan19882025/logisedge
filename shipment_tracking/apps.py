from django.apps import AppConfig


class ShipmentTrackingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shipment_tracking'
    verbose_name = 'Shipment Tracking & Status Updates'
    
    def ready(self):
        import shipment_tracking.signals
