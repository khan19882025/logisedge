from django.contrib import admin
from .models import CustomerPayment, CustomerPaymentInvoice

@admin.register(CustomerPayment)
class CustomerPaymentAdmin(admin.ModelAdmin):
    list_display = ['formatted_payment_id', 'customer', 'payment_date', 'amount', 'payment_method', 'bank_account', 'partial_payment_option']
    list_filter = ['payment_method', 'payment_date', 'partial_payment_option', 'bank_account']
    search_fields = ['customer__customer_name', 'formatted_payment_id']
    readonly_fields = ['formatted_payment_id']
    date_hierarchy = 'payment_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('customer', 'payment_date', 'amount', 'payment_method', 'bank_account')
        }),
        ('Payment Options', {
            'fields': ('partial_payment_option', 'notes'),
            'classes': ('collapse',)
        }),
    )

@admin.register(CustomerPaymentInvoice)
class CustomerPaymentInvoiceAdmin(admin.ModelAdmin):
    list_display = ['payment', 'invoice', 'amount_received', 'original_amount', 'discount_amount']
    list_filter = ['payment__payment_date', 'payment__payment_method']
    search_fields = ['payment__formatted_payment_id', 'invoice__invoice_number']
    readonly_fields = ['payment', 'invoice']
