from django.apps import AppConfig


class EmailConfigurationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'email_configuration'
    verbose_name = 'Email Configuration & Testing'
    
    def ready(self):
        import email_configuration.signals
