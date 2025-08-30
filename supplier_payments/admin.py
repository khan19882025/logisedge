from django.contrib import admin
from .models import SupplierPayment

@admin.register(SupplierPayment)
class SupplierPaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_id', 'supplier', 'payment_date', 'amount', 'payment_method', 'reference_number', 'created_at']
    list_filter = ['payment_method', 'payment_date', 'created_at']
    search_fields = ['payment_id', 'supplier__name', 'reference_number', 'notes']
    readonly_fields = ['payment_id', 'created_at', 'updated_at']
    date_hierarchy = 'payment_date'
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('payment_id', 'supplier', 'payment_date', 'amount', 'payment_method', 'ledger_account')
        }),
        ('Additional Details', {
            'fields': ('reference_number', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('supplier')
