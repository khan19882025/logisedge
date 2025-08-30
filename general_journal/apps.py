from django.apps import AppConfig


class GeneralJournalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'general_journal'
    verbose_name = 'General Journal'
    
    def ready(self):
        import general_journal.signals
