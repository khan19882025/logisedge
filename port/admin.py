from django.contrib import admin
from .models import Port

@admin.register(Port)
class PortAdmin(admin.ModelAdmin):
    list_display = ['port_code', 'port_name', 'port_type', 'country', 'status', 'created_at']
    list_filter = ['port_type', 'status', 'country']
    search_fields = ['port_code', 'port_name', 'country', 'city']
    ordering = ['port_name']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('port_code', 'port_name', 'port_type', 'status')
        }),
        ('Location', {
            'fields': ('country', 'city', 'state_province', 'latitude', 'longitude')
        }),
        ('Contact Information', {
            'fields': ('phone', 'email', 'website'),
            'classes': ('collapse',)
        }),
        ('Operational Information', {
            'fields': ('timezone', 'customs_office', 'customs_phone'),
            'classes': ('collapse',)
        }),
        ('Capacity and Facilities', {
            'fields': ('max_vessel_size', 'berth_count', 'container_capacity'),
            'classes': ('collapse',)
        }),
        ('Financial Information', {
            'fields': ('currency', 'handling_fee', 'storage_fee'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('description', 'notes'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
