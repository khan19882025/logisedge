from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import AssetMovementLog, AssetMovementTemplate, AssetMovementSettings


@admin.register(AssetMovementLog)
class AssetMovementLogAdmin(admin.ModelAdmin):
    list_display = [
        'movement_id', 'asset_link', 'movement_type', 'movement_date', 
        'from_location', 'to_location', 'moved_by', 'is_completed', 'is_approved'
    ]
    list_filter = [
        'movement_type', 'movement_reason', 'is_completed', 'is_approved',
        'movement_date', 'from_location', 'to_location'
    ]
    search_fields = [
        'asset__asset_code', 'asset__asset_name', 'notes', 'reason_description'
    ]
    readonly_fields = [
        'movement_id', 'created_at', 'updated_at', 'created_by', 'updated_by'
    ]
    date_hierarchy = 'movement_date'
    ordering = ['-movement_date']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('movement_id', 'asset', 'movement_type', 'movement_date')
        }),
        ('Location Information', {
            'fields': ('from_location', 'to_location', 'from_user', 'to_user')
        }),
        ('Movement Details', {
            'fields': ('movement_reason', 'reason_description', 'notes')
        }),
        ('Duration', {
            'fields': ('estimated_duration', 'actual_return_date')
        }),
        ('Status', {
            'fields': ('is_completed', 'is_approved', 'approved_by', 'approved_date')
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def asset_link(self, obj):
        if obj.asset:
            url = reverse('admin:asset_register_asset_change', args=[obj.asset.id])
            return format_html('<a href="{}">{}</a>', url, obj.asset.asset_code)
        return '-'
    asset_link.short_description = 'Asset'
    asset_link.admin_order_field = 'asset__asset_code'
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(AssetMovementTemplate)
class AssetMovementTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'movement_type', 'movement_reason', 'estimated_duration', 'is_active'
    ]
    list_filter = ['movement_type', 'movement_reason', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Movement Details', {
            'fields': ('movement_type', 'movement_reason', 'default_notes', 'estimated_duration')
        }),
    )


@admin.register(AssetMovementSettings)
class AssetMovementSettingsAdmin(admin.ModelAdmin):
    list_display = [
        'require_approval', 'auto_approve_assignments', 'require_reason', 
        'max_duration_days', 'enable_notifications'
    ]
    
    def has_add_permission(self, request):
        # Only allow one settings instance
        return not AssetMovementSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of settings
        return False
