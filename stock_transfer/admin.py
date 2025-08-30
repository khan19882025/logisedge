from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import StockTransfer, StockTransferItem, StockLedger


class StockTransferItemInline(admin.TabularInline):
    """Inline admin for stock transfer items"""
    model = StockTransferItem
    extra = 1
    fields = [
        'item', 'quantity', 'available_quantity', 'unit_of_measure',
        'batch_number', 'serial_number', 'source_location', 'destination_location',
        'unit_cost', 'total_value', 'notes'
    ]
    readonly_fields = ['available_quantity', 'total_value']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('item')


class StockLedgerInline(admin.TabularInline):
    """Inline admin for stock ledger entries"""
    model = StockLedger
    extra = 0
    fields = [
        'movement_date', 'movement_type', 'facility', 'location',
        'quantity_in', 'quantity_out', 'running_balance', 'reference_number'
    ]
    readonly_fields = ['movement_date', 'movement_type', 'facility', 'location',
                      'quantity_in', 'quantity_out', 'running_balance', 'reference_number']
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(StockTransfer)
class StockTransferAdmin(admin.ModelAdmin):
    """Admin configuration for StockTransfer model"""
    
    list_display = [
        'transfer_number', 'transfer_date', 'transfer_type', 'status',
        'source_facility', 'destination_facility', 'total_items',
        'total_quantity', 'total_value', 'created_by', 'created_at'
    ]
    
    list_filter = [
        'status', 'transfer_type', 'transfer_date', 'source_facility',
        'destination_facility', 'created_at'
    ]
    
    search_fields = [
        'transfer_number', 'reference_number', 'notes',
        'source_facility__facility_name', 'destination_facility__facility_name',
        'created_by__username'
    ]
    
    readonly_fields = [
        'transfer_number', 'total_items', 'total_quantity', 'total_weight',
        'total_volume', 'total_value', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'transfer_number', 'transfer_date', 'transfer_type', 'status',
                'reference_number'
            )
        }),
        ('Facilities', {
            'fields': ('source_facility', 'destination_facility')
        }),
        ('Additional Information', {
            'fields': ('notes', 'special_instructions'),
            'classes': ('collapse',)
        }),
        ('Totals', {
            'fields': (
                'total_items', 'total_quantity', 'total_weight',
                'total_volume', 'total_value'
            ),
            'classes': ('collapse',)
        }),
        ('Approval Information', {
            'fields': (
                'approved_by', 'approved_at', 'processed_by', 'processed_at'
            ),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [StockTransferItemInline, StockLedgerInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'source_facility', 'destination_facility', 'created_by'
        )
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        else:
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def has_delete_permission(self, request, obj=None):
        if obj and obj.status in ['completed', 'cancelled']:
            return False
        return super().has_delete_permission(request, obj)
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status in ['approved', 'completed', 'cancelled']:
            return self.readonly_fields + ('status', 'source_facility', 'destination_facility')
        return self.readonly_fields


@admin.register(StockTransferItem)
class StockTransferItemAdmin(admin.ModelAdmin):
    """Admin configuration for StockTransferItem model"""
    
    list_display = [
        'transfer', 'item', 'quantity', 'unit_of_measure',
        'total_value', 'batch_number', 'serial_number'
    ]
    
    list_filter = [
        'transfer__status', 'transfer__transfer_type', 'unit_of_measure',
        'transfer__transfer_date'
    ]
    
    search_fields = [
        'transfer__transfer_number', 'item__item_name', 'item__item_code',
        'batch_number', 'serial_number'
    ]
    
    readonly_fields = ['total_value', 'total_weight', 'total_volume']
    
    fieldsets = (
        ('Transfer Information', {
            'fields': ('transfer', 'item')
        }),
        ('Quantity Information', {
            'fields': (
                'quantity', 'available_quantity', 'unit_of_measure'
            )
        }),
        ('Batch and Serial Information', {
            'fields': ('batch_number', 'serial_number', 'expiry_date')
        }),
        ('Location Information', {
            'fields': ('source_location', 'destination_location')
        }),
        ('Pricing and Value', {
            'fields': ('unit_cost', 'total_value')
        }),
        ('Physical Properties', {
            'fields': ('unit_weight', 'total_weight', 'unit_volume', 'total_volume')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('transfer', 'item')


@admin.register(StockLedger)
class StockLedgerAdmin(admin.ModelAdmin):
    """Admin configuration for StockLedger model"""
    
    list_display = [
        'movement_date', 'item', 'facility', 'movement_type',
        'quantity_in', 'quantity_out', 'running_balance', 'reference_number'
    ]
    
    list_filter = [
        'movement_type', 'movement_date', 'facility', 'item__status'
    ]
    
    search_fields = [
        'item__item_name', 'item__item_code', 'facility__facility_name',
        'reference_number', 'batch_number', 'serial_number'
    ]
    
    readonly_fields = [
        'running_balance', 'total_value', 'created_at'
    ]
    
    fieldsets = (
        ('Movement Information', {
            'fields': (
                'movement_date', 'movement_type', 'reference_number'
            )
        }),
        ('Item and Location', {
            'fields': ('item', 'facility', 'location')
        }),
        ('Quantity Information', {
            'fields': ('quantity_in', 'quantity_out', 'running_balance')
        }),
        ('Batch and Serial Information', {
            'fields': ('batch_number', 'serial_number')
        }),
        ('Value Information', {
            'fields': ('unit_cost', 'total_value')
        }),
        ('Related Transfer', {
            'fields': ('stock_transfer',)
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('item', 'facility', 'stock_transfer')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
