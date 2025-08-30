from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import BankAccount, BankAccountTransaction


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = [
        'bank_name', 'account_number_display', 'account_type', 
        'currency', 'current_balance_display', 'status_badge', 
        'default_indicators', 'created_at'
    ]
    list_filter = [
        'status', 'account_type', 'currency', 'is_default_for_payments', 
        'is_default_for_receipts', 'created_at'
    ]
    search_fields = ['bank_name', 'account_number', 'branch_name', 'ifsc_code']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    list_per_page = 25
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('bank_name', 'account_number', 'account_type', 'branch_name', 'ifsc_code')
        }),
        ('Financial Settings', {
            'fields': ('currency', 'opening_balance', 'current_balance', 'chart_account')
        }),
        ('Status & Settings', {
            'fields': ('status', 'is_default_for_payments', 'is_default_for_receipts')
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Company & Audit', {
            'fields': ('company', 'created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def account_number_display(self, obj):
        """Display masked account number"""
        return obj.masked_account_number
    account_number_display.short_description = 'Account Number'
    
    def current_balance_display(self, obj):
        """Display formatted balance"""
        return obj.balance_formatted
    current_balance_display.short_description = 'Current Balance'
    
    def status_badge(self, obj):
        """Display status as colored badge"""
        status_colors = {
            'active': 'success',
            'inactive': 'secondary',
            'suspended': 'warning',
            'closed': 'danger'
        }
        color = status_colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def default_indicators(self, obj):
        """Display default account indicators"""
        indicators = []
        if obj.is_default_for_payments:
            indicators.append('<span class="badge bg-primary">Payments</span>')
        if obj.is_default_for_receipts:
            indicators.append('<span class="badge bg-info">Receipts</span>')
        return mark_safe(' '.join(indicators)) if indicators else '-'
    default_indicators.short_description = 'Default For'
    
    def save_model(self, request, obj, form, change):
        """Set created_by/updated_by fields"""
        if not change:  # New object
            obj.created_by = request.user
        else:
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """Optimize queryset with related fields"""
        return super().get_queryset(request).select_related(
            'currency', 'chart_account', 'company', 'created_by', 'updated_by'
        )


@admin.register(BankAccountTransaction)
class BankAccountTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'bank_account_link', 'transaction_date', 'transaction_type_badge',
        'amount_display', 'description', 'balance_after_display'
    ]
    list_filter = [
        'transaction_type', 'transaction_date', 'bank_account__bank_name',
        'created_at'
    ]
    search_fields = [
        'bank_account__bank_name', 'description', 'reference_number'
    ]
    readonly_fields = [
        'balance_before', 'balance_after', 'created_by', 'created_at'
    ]
    list_per_page = 50
    date_hierarchy = 'transaction_date'
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('bank_account', 'transaction_date', 'transaction_type', 'amount')
        }),
        ('Description', {
            'fields': ('description', 'reference_number')
        }),
        ('Balance Information', {
            'fields': ('balance_before', 'balance_after'),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def bank_account_link(self, obj):
        """Display bank account as link"""
        if obj.bank_account:
            url = reverse('admin:bank_accounts_bankaccount_change', args=[obj.bank_account.id])
            return format_html('<a href="{}">{}</a>', url, obj.bank_account)
        return '-'
    bank_account_link.short_description = 'Bank Account'
    
    def transaction_type_badge(self, obj):
        """Display transaction type as colored badge"""
        color = 'success' if obj.transaction_type == 'credit' else 'danger'
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_transaction_type_display()
        )
    transaction_type_badge.short_description = 'Type'
    
    def amount_display(self, obj):
        """Display formatted amount with currency"""
        currency_symbol = obj.bank_account.currency.symbol if obj.bank_account else ''
        return f"{currency_symbol} {obj.amount:,.2f}"
    amount_display.short_description = 'Amount'
    
    def balance_after_display(self, obj):
        """Display formatted balance after"""
        currency_symbol = obj.bank_account.currency.symbol if obj.bank_account else ''
        return f"{currency_symbol} {obj.balance_after:,.2f}"
    balance_after_display.short_description = 'Balance After'
    
    def save_model(self, request, obj, form, change):
        """Set created_by field for new transactions"""
        if not change:  # New transaction
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """Optimize queryset with related fields"""
        return super().get_queryset(request).select_related(
            'bank_account', 'bank_account__currency', 'created_by'
        )
