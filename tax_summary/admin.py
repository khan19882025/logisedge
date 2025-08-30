from django.contrib import admin
from .models import TaxSummaryReport, TaxSummaryTransaction, TaxSummaryFilter, TaxSummaryExport


@admin.register(TaxSummaryReport)
class TaxSummaryReportAdmin(admin.ModelAdmin):
    list_display = [
        'report_name', 'report_type', 'start_date', 'end_date', 'currency',
        'total_input_tax', 'total_output_tax', 'net_vat_payable', 'status',
        'generated_by', 'generated_at'
    ]
    list_filter = ['report_type', 'status', 'currency', 'generated_at']
    search_fields = ['report_name', 'generated_by__username']
    readonly_fields = ['generated_at', 'total_input_tax', 'total_output_tax', 'net_vat_payable']
    date_hierarchy = 'generated_at'
    
    fieldsets = (
        ('Report Information', {
            'fields': ('report_name', 'report_type', 'start_date', 'end_date', 'currency')
        }),
        ('Summary Totals', {
            'fields': ('total_input_tax', 'total_output_tax', 'net_vat_payable'),
            'classes': ('collapse',)
        }),
        ('Transaction Counts', {
            'fields': ('input_transactions_count', 'output_transactions_count'),
            'classes': ('collapse',)
        }),
        ('Status and Metadata', {
            'fields': ('status', 'generated_by', 'generated_at', 'filters_applied')
        }),
    )


@admin.register(TaxSummaryTransaction)
class TaxSummaryTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'invoice_number', 'party_name', 'transaction_type', 'transaction_date',
        'taxable_amount', 'vat_percentage', 'vat_amount', 'total_amount', 'currency'
    ]
    list_filter = ['transaction_type', 'currency', 'transaction_date', 'vat_percentage']
    search_fields = ['invoice_number', 'party_name', 'vat_number']
    readonly_fields = ['created_at']
    date_hierarchy = 'transaction_date'
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('report', 'transaction_date', 'invoice_number', 'party_name', 'vat_number')
        }),
        ('Tax Information', {
            'fields': ('transaction_type', 'taxable_amount', 'vat_percentage', 'vat_amount', 'total_amount', 'currency')
        }),
        ('Reference Information', {
            'fields': ('original_transaction_id', 'original_transaction_type', 'created_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TaxSummaryFilter)
class TaxSummaryFilterAdmin(admin.ModelAdmin):
    list_display = ['report', 'filter_type', 'filter_label', 'filter_value']
    list_filter = ['filter_type']
    search_fields = ['filter_label', 'filter_value']


@admin.register(TaxSummaryExport)
class TaxSummaryExportAdmin(admin.ModelAdmin):
    list_display = [
        'report', 'export_format', 'exported_by', 'exported_at', 'file_size'
    ]
    list_filter = ['export_format', 'exported_at']
    search_fields = ['report__report_name', 'exported_by__username']
    readonly_fields = ['exported_at']
    date_hierarchy = 'exported_at'
