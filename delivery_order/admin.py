from django.contrib import admin
from .models import DeliveryOrder, DeliveryOrderItem

class DeliveryOrderItemInline(admin.TabularInline):
    model = DeliveryOrderItem
    extra = 1
    fields = ['item', 'requested_qty', 'shipped_qty', 'delivered_qty', 'source_location', 'unit_price', 'total_price']
    readonly_fields = ['total_price']

@admin.register(DeliveryOrder)
class DeliveryOrderAdmin(admin.ModelAdmin):
    list_display = [
        'do_number', 'customer', 'status', 'priority', 'do_date', 
        'requested_date', 'assigned_to', 'created_by', 'created_at'
    ]
    list_filter = [
        'status', 'priority', 'do_date', 'requested_date', 
        'facility', 'assigned_to', 'created_at'
    ]
    search_fields = [
        'do_number', 'customer__customer_name', 'customer_ref', 
        'delivery_contact', 'tracking_number'
    ]
    readonly_fields = ['do_number', 'created_by', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    inlines = [DeliveryOrderItemInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('do_number', 'description', 'customer', 'customer_ref', 'facility', 'grn')
        }),
        ('Delivery Information', {
            'fields': ('delivery_address', 'delivery_contact', 'delivery_phone', 'delivery_email')
        }),
        ('Dates', {
            'fields': ('do_date', 'requested_date', 'actual_delivery_date')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority', 'assigned_to')
        }),
        ('Shipping Information', {
            'fields': ('shipping_method', 'tracking_number', 'carrier')
        }),
        ('Totals', {
            'fields': ('total_quantity', 'total_weight', 'total_volume')
        }),
        ('Notes', {
            'fields': ('notes', 'special_instructions')
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by for new objects
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(DeliveryOrderItem)
class DeliveryOrderItemAdmin(admin.ModelAdmin):
    list_display = [
        'delivery_order', 'item', 'requested_qty', 'shipped_qty', 
        'delivered_qty', 'source_location', 'unit_price', 'total_price'
    ]
    list_filter = ['delivery_order__status', 'source_location', 'created_at']
    search_fields = [
        'delivery_order__do_number', 'item__item_name', 'item__item_code'
    ]
    readonly_fields = ['total_price', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('delivery_order', 'item')
        }),
        ('Quantity Information', {
            'fields': ('requested_qty', 'shipped_qty', 'delivered_qty')
        }),
        ('Location & Pricing', {
            'fields': ('source_location', 'unit_price', 'total_price')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
