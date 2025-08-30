from django.contrib import admin
from .models import Service

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = [
        'service_code', 'service_name', 'service_type', 
        'sale_price', 'cost_price', 'currency', 'has_vat', 'status', 'is_featured', 'created_at'
    ]
    list_filter = [
        'service_type', 'status', 'is_featured', 
        'is_available_online', 'has_vat', 'currency', 'created_at', 'updated_at'
    ]
    search_fields = [
        'service_code', 'service_name', 'description', 
        'short_description', 'pricing_model'
    ]
    readonly_fields = [
        'service_code', 'created_by', 'created_at', 
        'updated_by', 'updated_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'service_code', 'service_name', 'service_type', 
                'description', 'short_description'
            )
        }),
        ('Pricing', {
            'fields': (
                'sale_price', 'cost_price', 'base_price', 'currency', 'pricing_model', 'has_vat'
            )
        }),
        ('Service Details', {
            'fields': (
                'duration', 'requirements', 'deliverables'
            )
        }),
        ('Status and Configuration', {
            'fields': (
                'status', 'is_featured', 'is_available_online'
            )
        }),
        ('System Information', {
            'fields': (
                'created_by', 'created_at', 'updated_by', 'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new service
            obj.created_by = request.user
        else:  # Updating existing service
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)
