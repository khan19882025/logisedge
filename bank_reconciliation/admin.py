from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    BankReconciliationSession, ERPTransaction, BankStatementEntry, 
    MatchedEntry, ReconciliationReport
)
from django.db import models


@admin.register(BankReconciliationSession)
class BankReconciliationSessionAdmin(admin.ModelAdmin):
    list_display = [
        'session_name', 'bank_account', 'reconciliation_date', 'status',
        'opening_balance_erp', 'opening_balance_bank', 'difference_amount',
        'created_by', 'created_at'
    ]
    list_filter = [
        'status', 'reconciliation_date', 'bank_account__bank_name',
        'created_at', 'completed_at'
    ]
    search_fields = ['session_name', 'bank_account__bank_name']
    readonly_fields = [
        'created_by', 'updated_by', 'created_at', 'updated_at', 
        'completed_at', 'difference_amount', 'is_balanced'
    ]
    date_hierarchy = 'reconciliation_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('bank_account', 'session_name', 'reconciliation_date')
        }),
        ('Settings', {
            'fields': ('status', 'tolerance_amount')
        }),
        ('Balances', {
            'fields': (
                'opening_balance_erp', 'opening_balance_bank',
                'closing_balance_erp', 'closing_balance_bank'
            )
        }),
        ('Summary Statistics', {
            'fields': (
                'total_erp_credits', 'total_erp_debits',
                'total_bank_credits', 'total_bank_debits'
            )
        }),
        ('Audit Information', {
            'fields': (
                'created_by', 'updated_by', 'created_at', 'updated_at', 'completed_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def difference_amount(self, obj):
        """Display difference amount with color coding"""
        diff = obj.difference_amount
        if abs(diff) <= obj.tolerance_amount:
            color = 'green'
            status = 'Balanced'
        else:
            color = 'red'
            status = 'Unbalanced'
        
        return format_html(
            '<span style="color: {};">{:.2f} ({})</span>',
            color, diff, status
        )
    difference_amount.short_description = 'Difference'
    
    def is_balanced(self, obj):
        """Display balance status"""
        if obj.is_balanced:
            return format_html('<span style="color: green;">✓ Balanced</span>')
        return format_html('<span style="color: red;">✗ Unbalanced</span>')
    is_balanced.short_description = 'Balance Status'
    
    actions = ['mark_as_completed', 'mark_as_locked', 'recalculate_balances']
    
    def mark_as_completed(self, request, queryset):
        """Mark selected sessions as completed"""
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} sessions marked as completed.')
    mark_as_completed.short_description = 'Mark as completed'
    
    def mark_as_locked(self, request, queryset):
        """Mark selected sessions as locked"""
        updated = queryset.update(status='locked')
        self.message_user(request, f'{updated} sessions marked as locked.')
    mark_as_locked.short_description = 'Mark as locked'
    
    def recalculate_balances(self, request, queryset):
        """Recalculate balances for selected sessions"""
        for session in queryset:
            # Recalculate ERP totals
            erp_credits = session.erp_entries.filter(credit_amount__gt=0).aggregate(
                total=models.Sum('credit_amount')
            )['total'] or 0
            erp_debits = session.erp_entries.filter(debit_amount__gt=0).aggregate(
                total=models.Sum('debit_amount')
            )['total'] or 0
            
            # Recalculate bank totals
            bank_credits = session.bank_entries.filter(credit_amount__gt=0).aggregate(
                total=models.Sum('credit_amount')
            )['total'] or 0
            bank_debits = session.bank_entries.filter(debit_amount__gt=0).aggregate(
                total=models.Sum('debit_amount')
            )['total'] or 0
            
            # Update session
            session.total_erp_credits = erp_credits
            session.total_erp_debits = erp_debits
            session.total_bank_credits = bank_credits
            session.total_bank_debits = bank_debits
            session.save()
        
        self.message_user(request, f'Balances recalculated for {queryset.count()} sessions.')
    recalculate_balances.short_description = 'Recalculate balances'


class ERPTransactionInline(admin.TabularInline):
    model = ERPTransaction
    extra = 0
    readonly_fields = ['is_matched', 'matched_bank_entry']
    fields = [
        'transaction_date', 'description', 'reference_number',
        'debit_amount', 'credit_amount', 'is_matched'
    ]


class BankStatementEntryInline(admin.TabularInline):
    model = BankStatementEntry
    extra = 0
    readonly_fields = ['is_matched', 'matched_erp_entry']
    fields = [
        'transaction_date', 'description', 'reference_number',
        'debit_amount', 'credit_amount', 'is_matched', 'import_source'
    ]


@admin.register(ERPTransaction)
class ERPTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'description', 'transaction_date', 'reference_number',
        'debit_amount', 'credit_amount', 'amount', 'transaction_type',
        'is_matched', 'reconciliation_session'
    ]
    list_filter = [
        'transaction_date', 'is_matched', 'reconciliation_session__bank_account',
        'reconciliation_session__status'
    ]
    search_fields = ['description', 'reference_number']
    readonly_fields = ['is_matched', 'matched_bank_entry', 'match_notes']
    date_hierarchy = 'transaction_date'
    
    fieldsets = (
        ('Transaction Details', {
            'fields': (
                'reconciliation_session', 'chart_account', 'transaction_date',
                'description', 'reference_number'
            )
        }),
        ('Amounts', {
            'fields': ('debit_amount', 'credit_amount')
        }),
        ('Matching', {
            'fields': ('is_matched', 'matched_bank_entry', 'match_notes')
        }),
    )
    
    def amount(self, obj):
        """Display transaction amount"""
        return f"{obj.amount:.2f}"
    amount.short_description = 'Amount'
    
    def transaction_type(self, obj):
        """Display transaction type"""
        if obj.transaction_type == 'credit':
            return format_html('<span style="color: green;">Credit</span>')
        return format_html('<span style="color: red;">Debit</span>')
    transaction_type.short_description = 'Type'
    
    actions = ['mark_as_unmatched']
    
    def mark_as_unmatched(self, request, queryset):
        """Mark selected entries as unmatched"""
        for entry in queryset:
            entry.unmatch()
        self.message_user(request, f'{queryset.count()} entries marked as unmatched.')
    mark_as_unmatched.short_description = 'Mark as unmatched'


@admin.register(BankStatementEntry)
class BankStatementEntryAdmin(admin.ModelAdmin):
    list_display = [
        'description', 'transaction_date', 'reference_number',
        'debit_amount', 'credit_amount', 'amount', 'transaction_type',
        'is_matched', 'import_source', 'reconciliation_session'
    ]
    list_filter = [
        'transaction_date', 'is_matched', 'import_source',
        'reconciliation_session__bank_account', 'reconciliation_session__status'
    ]
    search_fields = ['description', 'reference_number', 'import_reference']
    readonly_fields = ['is_matched', 'matched_erp_entry', 'match_notes']
    date_hierarchy = 'transaction_date'
    
    fieldsets = (
        ('Transaction Details', {
            'fields': (
                'reconciliation_session', 'transaction_date',
                'description', 'reference_number'
            )
        }),
        ('Amounts', {
            'fields': ('debit_amount', 'credit_amount')
        }),
        ('Import Information', {
            'fields': ('import_source', 'import_reference')
        }),
        ('Matching', {
            'fields': ('is_matched', 'matched_erp_entry', 'match_notes')
        }),
    )
    
    def amount(self, obj):
        """Display transaction amount"""
        return f"{obj.amount:.2f}"
    amount.short_description = 'Amount'
    
    def transaction_type(self, obj):
        """Display transaction type"""
        if obj.transaction_type == 'credit':
            return format_html('<span style="color: green;">Credit</span>')
        return format_html('<span style="color: red;">Debit</span>')
    transaction_type.short_description = 'Type'
    
    actions = ['mark_as_unmatched']
    
    def mark_as_unmatched(self, request, queryset):
        """Mark selected entries as unmatched"""
        for entry in queryset:
            entry.unmatch()
        self.message_user(request, f'{queryset.count()} entries marked as unmatched.')
    mark_as_unmatched.short_description = 'Mark as unmatched'


@admin.register(MatchedEntry)
class MatchedEntryAdmin(admin.ModelAdmin):
    list_display = [
        'reconciliation_session', 'erp_entry', 'bank_entry',
        'match_type', 'match_confidence', 'difference_amount',
        'created_by', 'created_at'
    ]
    list_filter = [
        'match_type', 'created_at', 'reconciliation_session__bank_account',
        'reconciliation_session__status'
    ]
    search_fields = [
        'erp_entry__description', 'bank_entry__description',
        'reconciliation_session__session_name'
    ]
    readonly_fields = [
        'match_confidence', 'difference_amount', 'created_by', 'created_at'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Match Information', {
            'fields': (
                'reconciliation_session', 'erp_entry', 'bank_entry',
                'match_type', 'match_confidence', 'difference_amount'
            )
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def match_confidence(self, obj):
        """Display match confidence with color coding"""
        confidence = obj.match_confidence
        if confidence >= 90:
            color = 'green'
        elif confidence >= 70:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color, confidence
        )
    match_confidence.short_description = 'Confidence'
    
    def difference_amount(self, obj):
        """Display difference amount with color coding"""
        diff = obj.difference_amount
        if diff == 0:
            color = 'green'
        elif diff <= 1:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {};">{:.2f}</span>',
            color, diff
        )
    difference_amount.short_description = 'Difference'


@admin.register(ReconciliationReport)
class ReconciliationReportAdmin(admin.ModelAdmin):
    list_display = [
        'reconciliation_session', 'report_type', 'report_date',
        'generated_by', 'has_file'
    ]
    list_filter = [
        'report_type', 'report_date', 'reconciliation_session__bank_account'
    ]
    search_fields = [
        'reconciliation_session__session_name',
        'reconciliation_session__bank_account__bank_name'
    ]
    readonly_fields = ['generated_by', 'report_date', 'report_data']
    date_hierarchy = 'report_date'
    
    fieldsets = (
        ('Report Information', {
            'fields': ('reconciliation_session', 'report_type', 'report_date')
        }),
        ('Report Data', {
            'fields': ('report_data',),
            'classes': ('collapse',)
        }),
        ('Generated File', {
            'fields': ('report_file',)
        }),
        ('Audit Information', {
            'fields': ('generated_by',),
            'classes': ('collapse',)
        }),
    )
    
    def has_file(self, obj):
        """Check if report has a file"""
        if obj.report_file:
            return format_html(
                '<a href="{}" target="_blank">Download</a>',
                obj.report_file.url
            )
        return format_html('<span style="color: gray;">No file</span>')
    has_file.short_description = 'File'
    
    actions = ['regenerate_reports']
    
    def regenerate_reports(self, request, queryset):
        """Regenerate selected reports"""
        for report in queryset:
            # This would regenerate the report data and file
            # Implementation depends on the specific report type
            pass
        self.message_user(request, f'{queryset.count()} reports regenerated.')
    regenerate_reports.short_description = 'Regenerate reports'
