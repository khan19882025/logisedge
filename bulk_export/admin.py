from django.contrib import admin
from .models import ExportLog


@admin.register(ExportLog)
class ExportLogAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'export_type', 'export_format', 'filename', 
        'records_exported', 'status', 'created_at', 'completed_at'
    ]
    list_filter = [
        'export_type', 'export_format', 'status', 'created_at', 'completed_at'
    ]
    search_fields = ['user__username', 'filename', 'export_type']
    readonly_fields = [
        'id', 'user', 'export_type', 'export_format', 'filename', 
        'filters_applied', 'records_exported', 'file_size', 'created_at', 
        'completed_at', 'status', 'error_message'
    ]
    ordering = ['-created_at']
    
    def has_add_permission(self, request):
        """Disable manual creation of export logs"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing of export logs"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Allow deletion of export logs"""
        return True
