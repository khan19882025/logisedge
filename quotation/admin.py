from django.contrib import admin
from .models import Quotation, QuotationItem


class QuotationItemInline(admin.TabularInline):
    model = QuotationItem
    extra = 1
    fields = ['service', 'description', 'quantity', 'unit_price', 'total_price', 'notes']


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ['quotation_number', 'customer', 'facility', 'salesman', 'subject', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'created_at', 'facility', 'salesman']
    search_fields = ['quotation_number', 'customer__name', 'subject']
    readonly_fields = ['quotation_number', 'created_at', 'updated_at', 'subtotal', 'total_amount']
    inlines = [QuotationItemInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('quotation_number', 'customer', 'facility', 'salesman', 'subject', 'description')
        }),
        ('Dates', {
            'fields': ('quotation_date', 'valid_until')
        }),
        ('Financial', {
            'fields': ('subtotal', 'tax_amount', 'discount_amount', 'total_amount', 'currency')
        }),
        ('Status & Tracking', {
            'fields': ('status', 'created_by', 'created_at', 'updated_at')
        }),
        ('Additional', {
            'fields': ('terms_conditions', 'notes')
        }),
    )


@admin.register(QuotationItem)
class QuotationItemAdmin(admin.ModelAdmin):
    list_display = ['quotation', 'service', 'description', 'quantity', 'unit_price', 'total_price']
    list_filter = ['quotation__status', 'service__service_type']
    search_fields = ['quotation__quotation_number', 'service__service_name', 'description']
    readonly_fields = ['total_price']

#admin.site.register(Quotation)
#admin.site.register(QuotationItem) 