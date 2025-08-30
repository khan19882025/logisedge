from django.apps import AppConfig


class RolesPermissionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'roles_permissions'
    verbose_name = 'Roles & Permissions'

    def ready(self):
        import roles_permissions.signals
