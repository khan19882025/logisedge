from django.apps import AppConfig


class ChequeRegisterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cheque_register'
    verbose_name = 'Cheque Register'
    
    def ready(self):
        import cheque_register.signals
