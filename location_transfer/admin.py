from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Pallet, PalletItem, LocationTransfer, LocationTransferHistory

class PalletItemInline(admin.TabularInline):
    model = PalletItem
    extra = 1
    fields = ['item', 'quantity', 'unit_of_measure', 'batch_number', 'serial_number', 'expiry_date', 'unit_cost', 'total_value']
    readonly_fields = ['total_value']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('item')

class LocationTransferHistoryInline(admin.TabularInline):
    model = LocationTransferHistory
    extra = 0
    readonly_fields = ['action', 'description', 'performed_by', 'performed_at']
    fields = ['action', 'description', 'performed_by', 'performed_at']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Pallet)
class PalletAdmin(admin.ModelAdmin):
    list_display = [
        'pallet_id', 'description', 'current_location_display', 'status', 
        'weight', 'volume', 'created_at', 'created_by'
    ]
    list_filter = ['status', 'current_location__facility', 'current_location__location_type', 'created_at']
    search_fields = ['pallet_id', 'description', 'current_location__location_name']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    inlines = [PalletItemInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('pallet_id', 'description', 'status')
        }),
        ('Location', {
            'fields': ('current_location',)
        }),
        ('Physical Specifications', {
            'fields': ('weight', 'volume', 'dimensions')
        }),
        ('Source Information', {
            'fields': ('grn_pallet',)
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def current_location_display(self, obj):
        if obj.current_location:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:facility_facilitylocation_change', args=[obj.current_location.id]),
                obj.current_location.display_name
            )
        return '-'
    current_location_display.short_description = 'Current Location'
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        else:
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(PalletItem)
class PalletItemAdmin(admin.ModelAdmin):
    list_display = [
        'pallet', 'item', 'quantity', 'unit_of_measure', 'batch_number', 
        'serial_number', 'total_value', 'created_at'
    ]
    list_filter = ['pallet__status', 'item__item_category', 'created_at']
    search_fields = ['pallet__pallet_id', 'item__item_name', 'item__item_code', 'batch_number', 'serial_number']
    readonly_fields = ['total_value', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Item Information', {
            'fields': ('pallet', 'item', 'quantity', 'unit_of_measure')
        }),
        ('Tracking Information', {
            'fields': ('batch_number', 'serial_number', 'expiry_date')
        }),
        ('Financial Information', {
            'fields': ('unit_cost', 'total_value')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(LocationTransfer)
class LocationTransferAdmin(admin.ModelAdmin):
    list_display = [
        'transfer_number', 'pallet', 'transfer_type', 'source_location_display', 
        'destination_location_display', 'status', 'priority', 'created_at', 'created_by'
    ]
    list_filter = [
        'status', 'transfer_type', 'priority', 'source_location__facility', 
        'destination_location__facility', 'created_at'
    ]
    search_fields = [
        'transfer_number', 'pallet__pallet_id', 'source_location__location_name',
        'destination_location__location_name'
    ]
    readonly_fields = [
        'transfer_number', 'created_at', 'updated_at', 'created_by', 'updated_by',
        'approved_at', 'processed_at', 'completed_date'
    ]
    inlines = [LocationTransferHistoryInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('transfer_number', 'transfer_type', 'status', 'priority')
        }),
        ('Pallet Information', {
            'fields': ('pallet',)
        }),
        ('Location Information', {
            'fields': ('source_location', 'destination_location')
        }),
        ('Transfer Details', {
            'fields': ('transfer_date', 'scheduled_date', 'completed_date')
        }),
        ('Notes and Instructions', {
            'fields': ('notes', 'special_instructions')
        }),
        ('Approval and Processing', {
            'fields': ('approved_by', 'approved_at', 'processed_by', 'processed_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def source_location_display(self, obj):
        if obj.source_location:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:facility_facilitylocation_change', args=[obj.source_location.id]),
                obj.source_location.display_name
            )
        return '-'
    source_location_display.short_description = 'Source Location'
    
    def destination_location_display(self, obj):
        if obj.destination_location:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:facility_facilitylocation_change', args=[obj.destination_location.id]),
                obj.destination_location.display_name
            )
        return '-'
    destination_location_display.short_description = 'Destination Location'
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        else:
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['approve_transfers', 'process_transfers', 'cancel_transfers']
    
    def approve_transfers(self, request, queryset):
        approved_count = 0
        for transfer in queryset.filter(status='pending'):
            transfer.approve(request.user)
            approved_count += 1
        self.message_user(request, f'{approved_count} transfers approved successfully.')
    approve_transfers.short_description = "Approve selected transfers"
    
    def process_transfers(self, request, queryset):
        processed_count = 0
        for transfer in queryset.filter(status__in=['pending', 'in_progress']):
            try:
                transfer.process(request.user)
                processed_count += 1
            except ValueError:
                continue
        self.message_user(request, f'{processed_count} transfers processed successfully.')
    process_transfers.short_description = "Process selected transfers"
    
    def cancel_transfers(self, request, queryset):
        cancelled_count = 0
        for transfer in queryset.exclude(status__in=['completed', 'cancelled']):
            transfer.status = 'cancelled'
            transfer.updated_by = request.user
            transfer.save()
            cancelled_count += 1
        self.message_user(request, f'{cancelled_count} transfers cancelled successfully.')
    cancel_transfers.short_description = "Cancel selected transfers"

@admin.register(LocationTransferHistory)
class LocationTransferHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'transfer', 'action', 'performed_by', 'performed_at', 'description_short'
    ]
    list_filter = ['action', 'performed_at', 'transfer__status']
    search_fields = ['transfer__transfer_number', 'transfer__pallet__pallet_id', 'description']
    readonly_fields = ['transfer', 'action', 'description', 'performed_by', 'performed_at', 'additional_data']
    
    fieldsets = (
        ('Transfer Information', {
            'fields': ('transfer',)
        }),
        ('Action Details', {
            'fields': ('action', 'description', 'performed_by', 'performed_at')
        }),
        ('Additional Data', {
            'fields': ('additional_data',),
            'classes': ('collapse',)
        }),
    )
    
    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
