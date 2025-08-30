from django.apps import AppConfig


class ApprovalWorkflowConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'approval_workflow'
    verbose_name = 'Approval Workflow'
    
    def ready(self):
        import approval_workflow.signals
