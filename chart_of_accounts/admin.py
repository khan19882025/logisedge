from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    ChartOfAccount, AccountType, AccountBalance, AccountGroup, 
    AccountTemplate, AccountTemplateItem
)


@admin.register(AccountType)
class AccountTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['category', 'name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'description')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class AccountBalanceInline(admin.TabularInline):
    model = AccountBalance
    extra = 0
    readonly_fields = ['created_at', 'updated_at']
    fields = ['fiscal_year', 'period', 'opening_balance', 'debit_total', 'credit_total', 'closing_balance']


@admin.register(ChartOfAccount)
class ChartOfAccountAdmin(admin.ModelAdmin):
    list_display = [
        'account_code', 'name', 'account_type', 'account_nature', 
        'parent_account_link', 'is_group', 'current_balance_display', 
        'is_active', 'company'
    ]
    list_filter = [
        'account_type__category', 'account_type', 'account_nature', 
        'is_group', 'is_active', 'company', 'currency', 'created_at'
    ]
    search_fields = ['account_code', 'name', 'description']
    ordering = ['account_code']
    readonly_fields = ['level', 'created_at', 'updated_at', 'created_by', 'updated_by']
    list_per_page = 50
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('account_code', 'name', 'description')
        }),
        ('Account Classification', {
            'fields': ('account_type', 'account_nature', 'is_group')
        }),
        ('Hierarchical Structure', {
            'fields': ('parent_account', 'level')
        }),
        ('Financial Settings', {
            'fields': ('currency', 'opening_balance', 'current_balance')
        }),
        ('Company & Status', {
            'fields': ('company', 'is_active')
        }),
        ('Audit Information', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [AccountBalanceInline]
    
    def parent_account_link(self, obj):
        if obj.parent_account:
            url = reverse('admin:chart_of_accounts_chartofaccount_change', args=[obj.parent_account.pk])
            return format_html('<a href="{}">{}</a>', url, obj.parent_account)
        return '-'
    parent_account_link.short_description = 'Parent Account'
    
    def current_balance_display(self, obj):
        if obj.current_balance >= 0:
            color = 'green'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{:.2f}</span>', 
            color, 
            obj.current_balance
        )
    current_balance_display.short_description = 'Current Balance'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(AccountBalance)
class AccountBalanceAdmin(admin.ModelAdmin):
    list_display = [
        'account', 'fiscal_year', 'period', 'opening_balance', 
        'debit_total', 'credit_total', 'closing_balance', 'net_movement_display'
    ]
    list_filter = ['fiscal_year', 'period', 'created_at']
    search_fields = ['account__account_code', 'account__name']
    ordering = ['account__account_code', 'period']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Account Information', {
            'fields': ('account', 'fiscal_year', 'period')
        }),
        ('Balances', {
            'fields': ('opening_balance', 'debit_total', 'credit_total', 'closing_balance')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def net_movement_display(self, obj):
        movement = obj.net_movement
        if movement >= 0:
            color = 'green'
            sign = '+'
        else:
            color = 'red'
            sign = ''
        return format_html(
            '<span style="color: {};">{}{:.2f}</span>', 
            color, 
            sign,
            movement
        )
    net_movement_display.short_description = 'Net Movement'


@admin.register(AccountGroup)
class AccountGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'account_type', 'is_system', 'is_active', 'created_at']
    list_filter = ['account_type__category', 'account_type', 'is_system', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'account_type')
        }),
        ('Status', {
            'fields': ('is_system', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class AccountTemplateItemInline(admin.TabularInline):
    model = AccountTemplateItem
    extra = 1
    fields = ['account_code', 'name', 'description', 'account_type', 'account_nature', 'parent_code', 'is_group']


@admin.register(AccountTemplate)
class AccountTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'item_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [AccountTemplateItemInline]
    
    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = 'Items'


@admin.register(AccountTemplateItem)
class AccountTemplateItemAdmin(admin.ModelAdmin):
    list_display = ['template', 'account_code', 'name', 'account_type', 'account_nature', 'is_group']
    list_filter = ['template', 'account_type__category', 'account_type', 'account_nature', 'is_group']
    search_fields = ['account_code', 'name', 'description']
    ordering = ['template', 'account_code']
    
    fieldsets = (
        ('Template Information', {
            'fields': ('template',)
        }),
        ('Account Information', {
            'fields': ('account_code', 'name', 'description')
        }),
        ('Account Classification', {
            'fields': ('account_type', 'account_nature', 'is_group')
        }),
        ('Hierarchy', {
            'fields': ('parent_code',)
        }),
    )


# Custom admin site configuration
admin.site.site_header = "logisEdge Chart of Accounts Administration"
admin.site.site_title = "Chart of Accounts Admin"
admin.site.index_title = "Welcome to Chart of Accounts Administration"
