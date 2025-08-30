from django.apps import AppConfig


class ManualJournalEntryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'manual_journal_entry'
    verbose_name = 'Manual Journal Entry'
    
    def ready(self):
        import manual_journal_entry.signals