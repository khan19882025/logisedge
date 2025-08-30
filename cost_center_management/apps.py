from django.apps import AppConfig


class CostCenterManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cost_center_management'
    verbose_name = 'Cost Center Management'
    
    def ready(self):
        import cost_center_management.signals
