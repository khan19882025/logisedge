from django.contrib import admin
from .models import GRN, GRNItem, GRNPallet


class GRNItemInline(admin.TabularInline):
    """Inline admin for GRN items"""
    model = GRNItem
    extra = 1
    fields = [
        'item', 'item_code', 'item_name', 'hs_code', 'unit',
        'expected_qty', 'received_qty', 'damaged_qty', 'short_qty',
        'net_weight', 'gross_weight', 'volume',
        'coo', 'batch_number', 'expiry_date', 'remark'
    ]
    readonly_fields = ['created_at', 'updated_at']


class GRNPalletInline(admin.TabularInline):
    """Inline admin for GRN pallets"""
    model = GRNPallet
    extra = 1
    fields = [
        'pallet_no', 'description', 'quantity', 'weight', 'volume',
        'location', 'status', 'remark'
    ]
    readonly_fields = ['created_at', 'updated_at']


@admin.register(GRN)
class GRNAdmin(admin.ModelAdmin):
    """Admin configuration for GRN model"""
    list_display = ('grn_number', 'customer', 'grn_date', 'status', 'priority')
    list_filter = [
        'status', 'priority', 'document_type', 'facility',
        'grn_date', 'expected_date', 'created_at'
    ]
    search_fields = [
        'grn_number', 'customer__customer_name', 
        'supplier_name', 'container_number', 'bl_number'
    ]
    readonly_fields = [
        'grn_number', 'created_at', 'updated_at'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('grn_number', 'description', 'customer', 'facility')
        }),
        ('Document Information', {
            'fields': ('document_type', 'reference_number')
        }),
        ('Supplier Information', {
            'fields': ('supplier_name', 'supplier_address', 'supplier_phone', 'supplier_email')
        }),
        ('Dates', {
            'fields': ('grn_date', 'expected_date', 'received_date')
        }),
        ('Shipping Information', {
            'fields': ('vessel', 'voyage', 'container_number', 'seal_number', 'bl_number')
        }),
        ('Driver and Vehicle Information', {
            'fields': ('driver_name', 'contact_no', 'vehicle_no')
        }),
        ('Status and Priority', {
            'fields': ('status', 'priority')
        }),
        ('Totals', {
            'fields': ('total_packages', 'total_weight', 'total_volume')
        }),
        ('Notes', {
            'fields': ('notes', 'special_instructions')
        }),
        ('Assignment', {
            'fields': ('created_by', 'assigned_to')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [GRNItemInline, GRNPalletInline]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(GRNItem)
class GRNItemAdmin(admin.ModelAdmin):
    """Admin configuration for GRNItem model"""
    list_display = [
        'grn', 'item', 'item_code', 'item_name', 
        'expected_qty', 'received_qty', 'damaged_qty', 'short_qty'
    ]
    list_filter = [
        'grn__status', 'grn__facility', 'coo', 'expiry_date'
    ]
    search_fields = [
        'grn__grn_number', 'item__item_code', 'item__item_name',
        'item_code', 'item_name', 'batch_number'
    ]
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('GRN Information', {
            'fields': ('grn', 'item')
        }),
        ('Item Details', {
            'fields': ('item_code', 'item_name', 'hs_code', 'unit')
        }),
        ('Quantities', {
            'fields': ('expected_qty', 'received_qty', 'damaged_qty', 'short_qty')
        }),
        ('Weights and Dimensions', {
            'fields': ('net_weight', 'gross_weight', 'volume')
        }),
        ('Additional Information', {
            'fields': ('coo', 'batch_number', 'expiry_date', 'remark')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    ordering = ['-created_at']


@admin.register(GRNPallet)
class GRNPalletAdmin(admin.ModelAdmin):
    """Admin configuration for GRNPallet model"""
    list_display = [
        'grn', 'pallet_no', 'description', 'quantity', 
        'weight', 'volume', 'location', 'status'
    ]
    list_filter = [
        'grn__status', 'status', 'grn__facility', 'created_at'
    ]
    search_fields = [
        'grn__grn_number', 'pallet_no', 'description', 'location'
    ]
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('GRN Information', {
            'fields': ('grn', 'item')
        }),
        ('Pallet Details', {
            'fields': ('pallet_no', 'description', 'quantity')
        }),
        ('Weights and Dimensions', {
            'fields': ('weight', 'volume')
        }),
        ('Location and Status', {
            'fields': ('location', 'status')
        }),
        ('Additional Information', {
            'fields': ('remark',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    ordering = ['-created_at']
