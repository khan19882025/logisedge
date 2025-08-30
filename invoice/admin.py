from django.contrib import admin
from .models import Invoice

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'customer', 'invoice_date', 'status', 'created_at']
    list_filter = ['status', 'invoice_date', 'customer']
    search_fields = ['invoice_number', 'customer__customer_name', 'shipper', 'consignee', 'bl_number', 'container_number', 'items_count']
    readonly_fields = ['invoice_number', 'created_at', 'updated_at']
    date_hierarchy = 'invoice_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('invoice_number', 'invoice_date', 'customer', 'jobs', 'delivery_order')
        }),
        ('Shipping Information', {
            'fields': ('shipper', 'consignee', 'origin', 'destination', 'bl_number', 'ed_number', 'container_number', 'items_count')
        }),
        ('Status and Notes', {
            'fields': ('status', 'notes')
        }),
        ('System Information', {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by for new objects
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
