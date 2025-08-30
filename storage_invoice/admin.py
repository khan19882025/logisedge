from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import StorageInvoice, StorageInvoiceItem

class StorageInvoiceItemInline(admin.TabularInline):
    model = StorageInvoiceItem
    extra = 0
    readonly_fields = ['line_total']
    fields = ['item', 'pallet_id', 'location', 'quantity', 'weight', 'volume', 
              'storage_days', 'charge_type', 'rate', 'line_total', 'description']

@admin.register(StorageInvoice)
class StorageInvoiceAdmin(admin.ModelAdmin):
    list_display = [
        'invoice_number', 'customer', 'invoice_date', 'storage_period_display',
        'total_amount', 'status', 'generated_by', 'created_at'
    ]
    list_filter = [
        'status', 'invoice_date', 'storage_period_from', 'storage_period_to',
        'customer', 'generated_by'
    ]
    search_fields = [
        'invoice_number', 'customer__customer_name', 'notes'
    ]
    readonly_fields = [
        'invoice_number', 'created_at', 'updated_at', 'finalized_at', 'cancelled_at',
        'generated_by', 'finalized_by', 'cancelled_by'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('invoice_number', 'customer', 'invoice_date', 'status')
        }),
        ('Storage Period', {
            'fields': ('storage_period_from', 'storage_period_to')
        }),
        ('Financial', {
            'fields': ('subtotal', 'tax_amount', 'total_amount')
        }),
        ('Notes', {
            'fields': ('notes', 'terms_conditions'),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('generated_by', 'finalized_by', 'cancelled_by', 
                      'created_at', 'updated_at', 'finalized_at', 'cancelled_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [StorageInvoiceItemInline]
    actions = ['finalize_invoices', 'cancel_invoices']
    
    def storage_period_display(self, obj):
        return f"{obj.storage_period_from} to {obj.storage_period_to}"
    storage_period_display.short_description = "Storage Period"
    
    def finalize_invoices(self, request, queryset):
        count = 0
        for invoice in queryset.filter(status='draft'):
            invoice.finalize(request.user)
            count += 1
        self.message_user(request, f"Finalized {count} invoice(s).")
    finalize_invoices.short_description = "Finalize selected invoices"
    
    def cancel_invoices(self, request, queryset):
        count = 0
        for invoice in queryset.filter(status__in=['draft', 'finalized']):
            invoice.cancel(request.user)
            count += 1
        self.message_user(request, f"Cancelled {count} invoice(s).")
    cancel_invoices.short_description = "Cancel selected invoices"
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.generated_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(StorageInvoiceItem)
class StorageInvoiceItemAdmin(admin.ModelAdmin):
    list_display = [
        'invoice', 'item', 'pallet_id', 'location', 'quantity',
        'storage_days', 'rate', 'line_total'
    ]
    list_filter = [
        'charge_type', 'invoice__customer', 'location'
    ]
    search_fields = [
        'invoice__invoice_number', 'item__item_name', 'pallet_id'
    ]
    readonly_fields = ['line_total']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('invoice', 'item', 'location')
