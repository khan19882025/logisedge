from django.contrib import admin
from .models import Ledger, LedgerBatch


@admin.register(Ledger)
class LedgerAdmin(admin.ModelAdmin):
    list_display = [
        'ledger_number', 'entry_date', 'account', 'entry_type', 
        'amount', 'running_balance', 'status', 'is_reconciled', 
        'company', 'fiscal_year'
    ]
    list_filter = [
        'entry_type', 'status', 'is_reconciled', 'entry_date', 
        'company', 'fiscal_year', 'account'
    ]
    search_fields = [
        'ledger_number', 'reference', 'description', 'voucher_number', 
        'cheque_number', 'bank_reference'
    ]
    readonly_fields = [
        'ledger_number', 'running_balance', 'created_by', 'created_at', 
        'updated_by', 'updated_at'
    ]
    date_hierarchy = 'entry_date'
    ordering = ['-entry_date', '-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('ledger_number', 'entry_date', 'reference', 'description')
        }),
        ('Account Information', {
            'fields': ('account', 'entry_type', 'amount', 'running_balance')
        }),
        ('Status and Control', {
            'fields': ('status', 'is_reconciled', 'reconciliation_date')
        }),
        ('Additional Information', {
            'fields': ('voucher_number', 'cheque_number', 'bank_reference'),
            'classes': ('collapse',)
        }),
        ('Company and Fiscal Year', {
            'fields': ('company', 'fiscal_year'),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(LedgerBatch)
class LedgerBatchAdmin(admin.ModelAdmin):
    list_display = [
        'batch_number', 'batch_type', 'description', 'total_debit', 
        'total_credit', 'is_balanced', 'is_posted', 'company', 'fiscal_year'
    ]
    list_filter = [
        'batch_type', 'is_balanced', 'is_posted', 'created_at', 
        'company', 'fiscal_year'
    ]
    search_fields = ['batch_number', 'description']
    readonly_fields = [
        'batch_number', 'total_debit', 'total_credit', 'is_balanced', 
        'created_by', 'created_at', 'posted_by', 'posted_at'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('batch_number', 'batch_type', 'description')
        }),
        ('Amounts', {
            'fields': ('total_debit', 'total_credit', 'is_balanced')
        }),
        ('Status', {
            'fields': ('is_posted', 'posted_by', 'posted_at')
        }),
        ('Company and Fiscal Year', {
            'fields': ('company', 'fiscal_year'),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
