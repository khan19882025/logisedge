from django.apps import AppConfig


class PdfPreviewToolConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pdf_preview_tool'
    verbose_name = 'PDF Preview Tool'
    
    def ready(self):
        import pdf_preview_tool.signals
