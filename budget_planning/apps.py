from django.apps import AppConfig


class BudgetPlanningConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'budget_planning'
    verbose_name = 'Budget Planning'
    
    def ready(self):
        import budget_planning.signals
