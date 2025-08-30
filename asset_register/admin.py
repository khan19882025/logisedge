from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Asset, AssetCategory, AssetLocation, AssetStatus, AssetDepreciation,
    AssetMovement, AssetMaintenance
)


@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent_category', 'created_at']
    list_filter = ['parent_category', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    list_per_page = 20


@admin.register(AssetLocation)
class AssetLocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'building', 'floor', 'room', 'is_active', 'created_at']
    list_filter = ['is_active', 'building', 'created_at']
    search_fields = ['name', 'building', 'floor', 'room', 'description']
    ordering = ['name']
    list_per_page = 20
    list_editable = ['is_active']


@admin.register(AssetStatus)
class AssetStatusAdmin(admin.ModelAdmin):
    list_display = ['name', 'color_display', 'is_active', 'description']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    ordering = ['name']
    list_per_page = 20
    list_editable = ['is_active']

    def color_display(self, obj):
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px;">{}</span>',
            obj.color,
            obj.color
        )
    color_display.short_description = 'Color'


@admin.register(AssetDepreciation)
class AssetDepreciationAdmin(admin.ModelAdmin):
    list_display = ['name', 'method', 'rate_percentage', 'useful_life_years', 'is_active']
    list_filter = ['method', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['name']
    list_per_page = 20
    list_editable = ['is_active']


class AssetMovementInline(admin.TabularInline):
    model = AssetMovement
    extra = 0
    readonly_fields = ['created_by', 'created_at']
    fields = ['movement_type', 'from_location', 'to_location', 'from_user', 'to_user', 'movement_date', 'reason']
    can_delete = False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('from_location', 'to_location', 'from_user', 'to_user')


class AssetMaintenanceInline(admin.TabularInline):
    model = AssetMaintenance
    extra = 0
    readonly_fields = ['created_by', 'created_at']
    fields = ['maintenance_type', 'maintenance_date', 'description', 'cost', 'performed_by', 'next_maintenance_date']
    can_delete = False


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = [
        'asset_code', 'asset_name', 'category', 'location', 'status_display',
        'purchase_date', 'purchase_value', 'book_value', 'assigned_to', 'qr_barcode_links'
    ]
    list_filter = [
        'category', 'location', 'status', 'depreciation_method',
        'purchase_date', 'disposal_date', 'is_deleted'
    ]
    search_fields = [
        'asset_code', 'asset_name', 'description', 'serial_number',
        'model_number', 'manufacturer'
    ]
    readonly_fields = [
        'asset_code', 'created_by', 'created_at', 'updated_by', 'updated_at',
        'deleted_by', 'deleted_at', 'qr_code_display', 'barcode_display'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('asset_code', 'asset_name', 'description', 'category', 'location', 'status')
        }),
        ('Financial Information', {
            'fields': ('purchase_date', 'purchase_value', 'current_value', 'salvage_value')
        }),
        ('Depreciation', {
            'fields': ('depreciation_method', 'useful_life_years', 'accumulated_depreciation', 'book_value')
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'assigned_date')
        }),
        ('Technical Details', {
            'fields': ('serial_number', 'model_number', 'manufacturer')
        }),
        ('Warranty & Insurance', {
            'fields': ('warranty_expiry', 'insurance_policy', 'insurance_expiry')
        }),
        ('Maintenance', {
            'fields': ('last_maintenance_date', 'next_maintenance_date', 'maintenance_notes')
        }),
        ('Disposal', {
            'fields': ('disposal_date', 'disposal_reason', 'disposal_value')
        }),
        ('QR Code & Barcode', {
            'fields': ('qr_code_display', 'barcode_display')
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Deletion', {
            'fields': ('is_deleted', 'deleted_by', 'deleted_at'),
            'classes': ('collapse',)
        })
    )
    inlines = [AssetMovementInline, AssetMaintenanceInline]
    ordering = ['asset_code']
    list_per_page = 25
    actions = ['mark_as_disposed', 'mark_as_active', 'export_assets']

    def status_display(self, obj):
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px;">{}</span>',
            obj.get_status_color(),
            obj.status.name if obj.status else 'Unknown'
        )
    status_display.short_description = 'Status'

    def qr_barcode_links(self, obj):
        links = []
        if obj.qr_code:
            links.append(f'<a href="{obj.qr_code.url}" target="_blank">QR</a>')
        if obj.barcode:
            links.append(f'<a href="{obj.barcode.url}" target="_blank">Barcode</a>')
        return mark_safe(' | '.join(links)) if links else '-'
    qr_barcode_links.short_description = 'Codes'

    def qr_code_display(self, obj):
        if obj.qr_code:
            return format_html(
                '<img src="{}" alt="QR Code" style="max-width: 200px; height: auto;" />',
                obj.qr_code.url
            )
        return 'No QR code generated'
    qr_code_display.short_description = 'QR Code'

    def barcode_display(self, obj):
        if obj.barcode:
            return format_html(
                '<img src="{}" alt="Barcode" style="max-width: 200px; height: auto;" />',
                obj.barcode.url
            )
        return 'No barcode generated'
    barcode_display.short_description = 'Barcode'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'category', 'location', 'status', 'assigned_to', 'depreciation_method'
        )

    def save_model(self, request, obj, form, change):
        if not change:  # Creating new asset
            obj.created_by = request.user
        else:  # Updating existing asset
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def mark_as_disposed(self, request, queryset):
        disposed_status = AssetStatus.objects.filter(name__icontains='disposed').first()
        if disposed_status:
            updated = queryset.update(status=disposed_status, updated_by=request.user)
            self.message_user(request, f'{updated} assets marked as disposed.')
        else:
            self.message_user(request, 'No "Disposed" status found. Please create one first.', level='ERROR')
    mark_as_disposed.short_description = 'Mark selected assets as disposed'

    def mark_as_active(self, request, queryset):
        active_status = AssetStatus.objects.filter(name__icontains='active').first()
        if active_status:
            updated = queryset.update(status=active_status, updated_by=request.user)
            self.message_user(request, f'{updated} assets marked as active.')
        else:
            self.message_user(request, 'No "Active" status found. Please create one first.', level='ERROR')
    mark_as_active.short_description = 'Mark selected assets as active'

    def export_assets(self, request, queryset):
        # This would implement CSV/Excel export functionality
        self.message_user(request, f'{queryset.count()} assets selected for export.')
    export_assets.short_description = 'Export selected assets'


@admin.register(AssetMovement)
class AssetMovementAdmin(admin.ModelAdmin):
    list_display = [
        'asset', 'movement_type', 'from_location', 'to_location',
        'from_user', 'to_user', 'movement_date', 'created_by'
    ]
    list_filter = ['movement_type', 'movement_date', 'created_at']
    search_fields = ['asset__asset_code', 'asset__asset_name', 'reason', 'notes']
    readonly_fields = ['created_by', 'created_at']
    ordering = ['-movement_date']
    list_per_page = 25

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'asset', 'from_location', 'to_location', 'from_user', 'to_user', 'created_by'
        )

    def save_model(self, request, obj, form, change):
        if not change:  # Creating new movement
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(AssetMaintenance)
class AssetMaintenanceAdmin(admin.ModelAdmin):
    list_display = [
        'asset', 'maintenance_type', 'maintenance_date', 'cost',
        'performed_by', 'next_maintenance_date', 'created_by'
    ]
    list_filter = ['maintenance_type', 'maintenance_date', 'created_at']
    search_fields = ['asset__asset_code', 'asset__asset_name', 'description', 'performed_by']
    readonly_fields = ['created_by', 'created_at']
    ordering = ['-maintenance_date']
    list_per_page = 25

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('asset', 'created_by')

    def save_model(self, request, obj, form, change):
        if not change:  # Creating new maintenance record
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# Customize admin site
admin.site.site_header = "Asset Register Administration"
admin.site.site_title = "Asset Register Admin"
admin.site.index_title = "Welcome to Asset Register Administration" 