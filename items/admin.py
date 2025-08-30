from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Item


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    """Admin configuration for Item model"""
    
    list_display = [
        'item_code', 'item_name', 'item_category', 'status', 'brand', 
        'unit_of_measure', 'hs_code', 'country_of_origin', 'cost_price', 'selling_price', 'currency',
        'supplier', 'created_at', 'is_active_display'
    ]
    
    list_filter = [
        'item_category', 'status', 'brand', 'currency', 'created_at', 'updated_at'
    ]
    
    search_fields = [
        'item_code', 'item_name', 'brand', 'model', 'supplier', 
        'barcode', 'description'
    ]
    
    list_editable = ['status']
    
    readonly_fields = [
        'created_at', 'updated_at', 'created_by', 'updated_by',
        'profit_margin_display', 'profit_amount_display'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('item_code', 'item_name', 'item_category', 'status')
        }),
        ('Description', {
            'fields': ('description', 'short_description'),
            'classes': ('collapse',)
        }),
        ('Specifications', {
            'fields': ('brand', 'model', 'size', 'weight', 'color', 'material'),
            'classes': ('collapse',)
        }),
        ('Customs & Shipping', {
            'fields': ('hs_code', 'country_of_origin', 'cbm', 'net_weight', 'gross_weight'),
            'classes': ('collapse',)
        }),
        ('Inventory', {
            'fields': ('unit_of_measure', 'min_stock_level', 'max_stock_level', 'reorder_point')
        }),
        ('Pricing', {
            'fields': ('cost_price', 'selling_price', 'currency', 'profit_margin_display', 'profit_amount_display')
        }),
        ('Supplier Information', {
            'fields': ('supplier', 'supplier_code', 'lead_time'),
            'classes': ('collapse',)
        }),
        ('Location', {
            'fields': ('warehouse_location', 'shelf_number', 'bin_number'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('barcode', 'serial_number', 'warranty_period'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes', 'internal_notes'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['item_name']
    
    list_per_page = 25
    
    date_hierarchy = 'created_at'
    
    actions = ['activate_items', 'deactivate_items', 'export_items']
    
    def is_active_display(self, obj):
        """Display active status with color coding"""
        if obj.is_active:
            return format_html(
                '<span style="color: green;">✓ Active</span>'
            )
        else:
            return format_html(
                '<span style="color: red;">✗ Inactive</span>'
            )
    is_active_display.short_description = 'Status'
    
    def profit_margin_display(self, obj):
        """Display profit margin as percentage"""
        if obj.profit_margin > 0:
            return format_html(
                '<span style="color: green;">{:.1f}%</span>',
                obj.profit_margin
            )
        elif obj.profit_margin < 0:
            return format_html(
                '<span style="color: red;">{:.1f}%</span>',
                obj.profit_margin
            )
        else:
            return '0.0%'
    profit_margin_display.short_description = 'Profit Margin'
    
    def profit_amount_display(self, obj):
        """Display profit amount per unit"""
        if obj.profit_amount > 0:
            return format_html(
                '<span style="color: green;">{:.2f} {}</span>',
                obj.profit_amount, obj.currency
            )
        elif obj.profit_amount < 0:
            return format_html(
                '<span style="color: red;">{:.2f} {}</span>',
                obj.profit_amount, obj.currency
            )
        else:
            return f'0.00 {obj.currency}'
    profit_amount_display.short_description = 'Profit per Unit'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('created_by', 'updated_by')
    
    def save_model(self, request, obj, form, change):
        """Set created_by and updated_by fields"""
        if not change:  # Creating new object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def activate_items(self, request, queryset):
        """Action to activate selected items"""
        updated = queryset.update(status='active')
        self.message_user(
            request,
            f'{updated} item(s) were successfully activated.'
        )
    activate_items.short_description = "Activate selected items"
    
    def deactivate_items(self, request, queryset):
        """Action to deactivate selected items"""
        updated = queryset.update(status='inactive')
        self.message_user(
            request,
            f'{updated} item(s) were successfully deactivated.'
        )
    deactivate_items.short_description = "Deactivate selected items"
    
    def export_items(self, request, queryset):
        """Action to export selected items"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="items_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Item Code', 'Item Name', 'Category', 'Status', 'Brand', 'Model',
            'Unit', 'Cost Price', 'Selling Price', 'Currency', 'Supplier',
            'Barcode', 'Created Date'
        ])
        
        for item in queryset:
            writer.writerow([
                item.item_code, item.item_name, item.get_item_category_display(), item.status,
                item.brand, item.model, item.unit_of_measure, item.cost_price,
                item.selling_price, item.currency, item.supplier, item.barcode,
                item.created_at.strftime('%Y-%m-%d')
            ])
        
        return response
    export_items.short_description = "Export selected items to CSV"
