from django.contrib import admin
from .models import TaxFilingReport, TaxFilingTransaction, TaxFilingValidation, TaxFilingExport, TaxFilingSettings


@admin.register(TaxFilingReport)
class TaxFilingReportAdmin(admin.ModelAdmin):
    list_display = [
        'report_name', 'filing_period', 'start_date', 'end_date', 'currency',
        'total_output_tax', 'total_input_tax', 'total_adjustments', 'net_tax_payable',
        'status', 'generated_by', 'generated_at'
    ]
    list_filter = [
        'filing_period', 'status', 'currency', 'has_missing_vat_numbers', 
        'has_mismatched_rates', 'generated_at'
    ]
    search_fields = ['report_name', 'filing_reference', 'generated_by__username']
    readonly_fields = [
        'id', 'total_output_tax', 'total_input_tax', 'total_adjustments', 
        'net_tax_payable', 'output_transactions_count', 'input_transactions_count',
        'adjustment_transactions_count', 'has_missing_vat_numbers', 'has_mismatched_rates',
        'validation_errors', 'generated_at', 'filing_date'
    ]
    date_hierarchy = 'generated_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('report_name', 'filing_period', 'start_date', 'end_date', 'currency', 'notes')
        }),
        ('Tax Totals', {
            'fields': ('total_output_tax', 'total_input_tax', 'total_adjustments', 'net_tax_payable'),
            'classes': ('collapse',)
        }),
        ('Transaction Counts', {
            'fields': ('output_transactions_count', 'input_transactions_count', 'adjustment_transactions_count'),
            'classes': ('collapse',)
        }),
        ('Validation Status', {
            'fields': ('has_missing_vat_numbers', 'has_mismatched_rates', 'validation_errors'),
            'classes': ('collapse',)
        }),
        ('Filing Information', {
            'fields': ('status', 'filing_reference', 'filing_date', 'filed_by'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'generated_by', 'generated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TaxFilingTransaction)
class TaxFilingTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'invoice_number', 'party_name', 'transaction_type', 'transaction_date',
        'taxable_amount', 'vat_percentage', 'vat_amount', 'total_amount', 'currency',
        'has_vat_number', 'vat_rate_matches'
    ]
    list_filter = [
        'transaction_type', 'adjustment_type', 'currency', 'has_vat_number', 
        'vat_rate_matches', 'transaction_date'
    ]
    search_fields = ['invoice_number', 'party_name', 'vat_number']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'transaction_date'
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('report', 'transaction_date', 'invoice_number', 'party_name', 'vat_number')
        }),
        ('Tax Information', {
            'fields': ('transaction_type', 'adjustment_type', 'taxable_amount', 'vat_percentage', 'vat_amount', 'total_amount', 'currency')
        }),
        ('Validation', {
            'fields': ('has_vat_number', 'vat_rate_matches', 'validation_notes'),
            'classes': ('collapse',)
        }),
        ('Reference', {
            'fields': ('original_transaction_id', 'original_transaction_type'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TaxFilingValidation)
class TaxFilingValidationAdmin(admin.ModelAdmin):
    list_display = [
        'validation_type', 'severity', 'description', 'report', 'transaction',
        'is_resolved', 'created_at'
    ]
    list_filter = [
        'validation_type', 'severity', 'is_resolved', 'created_at'
    ]
    search_fields = ['description', 'field_name', 'report__report_name']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Validation Details', {
            'fields': ('report', 'transaction', 'validation_type', 'severity', 'description')
        }),
        ('Field Information', {
            'fields': ('field_name', 'expected_value', 'actual_value'),
            'classes': ('collapse',)
        }),
        ('Resolution', {
            'fields': ('is_resolved', 'resolved_at', 'resolved_by'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TaxFilingExport)
class TaxFilingExportAdmin(admin.ModelAdmin):
    list_display = [
        'report', 'export_format', 'file_size', 'exported_by', 'exported_at'
    ]
    list_filter = ['export_format', 'exported_at']
    search_fields = ['report__report_name', 'exported_by__username']
    readonly_fields = ['id', 'exported_at']
    date_hierarchy = 'exported_at'


@admin.register(TaxFilingSettings)
class TaxFilingSettingsAdmin(admin.ModelAdmin):
    list_display = [
        'tax_authority_name', 'tax_authority_code', 'filing_deadline_days',
        'auto_validation', 'require_vat_numbers', 'default_currency'
    ]
    list_filter = ['auto_validation', 'require_vat_numbers', 'default_currency']
    search_fields = ['tax_authority_name', 'tax_authority_code']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Tax Authority', {
            'fields': ('tax_authority_name', 'tax_authority_code')
        }),
        ('Filing Settings', {
            'fields': ('filing_deadline_days', 'default_currency')
        }),
        ('Validation Settings', {
            'fields': ('auto_validation', 'require_vat_numbers')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
