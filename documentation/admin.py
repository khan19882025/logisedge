from django.contrib import admin
from .models import Documentation, DocumentationCargo


@admin.register(Documentation)
class DocumentationAdmin(admin.ModelAdmin):
    list_display = ['document_no', 'job_no', 'customer', 'document_type', 'date', 'ship_mode', 'created_by', 'created_at']
    list_filter = ['created_at', 'updated_at', 'created_by', 'customer', 'document_type', 'ship_mode']
    search_fields = ['document_no', 'job_no', 'customer__customer_name', 'document_type', 'bl_number', 'boe']
    readonly_fields = ['created_by', 'created_at', 'updated_at']
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(DocumentationCargo)
class DocumentationCargoAdmin(admin.ModelAdmin):
    list_display = ['documentation', 'item_name', 'item_code', 'quantity', 'unit', 'rate', 'amount']
    list_filter = ['created_at', 'documentation__document_type']
    search_fields = ['documentation__document_no', 'item_name', 'item_code', 'hs_code']
    readonly_fields = ['created_at', 'updated_at'] 