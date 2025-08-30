from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import DispatchNote, DispatchItem

class DispatchItemInline(admin.TabularInline):
    model = DispatchItem
    extra = 1
    fields = [
        'grn_no', 'item_code', 'item', 'item_name', 'hs_code', 'unit', 'quantity',
        'coo', 'n_weight', 'g_weight', 'cbm', 'p_date', 'e_date', 'color', 'size',
        'barcode', 'rate', 'amount', 'ed', 'ctnr'
    ]
    readonly_fields = ['amount']

@admin.register(DispatchNote)
class DispatchNoteAdmin(admin.ModelAdmin):
    list_display = [
        'gdn_number', 'dispatch_date', 'customer', 'deliver_to', 'facility', 
        'mode', 'vehicle_no', 'status', 'total_items', 'created_at'
    ]
    list_filter = [
        'status', 'dispatch_date', 'mode', 'facility', 'created_at'
    ]
    search_fields = [
        'gdn_number', 'customer__customer_name', 'deliver_to', 'facility'
    ]
    readonly_fields = ['gdn_number', 'created_at', 'updated_at', 'created_by', 'updated_by']
    inlines = [DispatchItemInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('gdn_number', 'dispatch_date', 'customer', 'job')
        }),
        ('Delivery Information', {
            'fields': ('deliver_to', 'deliver_address', 'facility')
        }),
        ('Transport Information', {
            'fields': ('mode', 'vehicle_no', 'name', 'contact_number')
        }),
        ('Status & Notes', {
            'fields': ('status', 'notes')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('customer', 'job')

@admin.register(DispatchItem)
class DispatchItemAdmin(admin.ModelAdmin):
    list_display = [
        'dispatch_note', 'item_name', 'quantity', 'rate', 'amount', 
        'grn_no', 'item_code', 'unit'
    ]
    list_filter = [
        'dispatch_note__status', 'unit', 'p_date', 'e_date'
    ]
    search_fields = [
        'item_name', 'grn_no', 'item_code', 'barcode', 'dispatch_note__gdn_number'
    ]
    readonly_fields = ['amount']
    
    fieldsets = (
        ('Item Information', {
            'fields': ('dispatch_note', 'grn_no', 'item_code', 'item', 'item_name', 'hs_code')
        }),
        ('Quantity & Pricing', {
            'fields': ('unit', 'quantity', 'rate', 'amount')
        }),
        ('Physical Details', {
            'fields': ('coo', 'n_weight', 'g_weight', 'cbm', 'color', 'size')
        }),
        ('Dates & Tracking', {
            'fields': ('p_date', 'e_date', 'barcode', 'ed', 'ctnr')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('dispatch_note', 'item')
