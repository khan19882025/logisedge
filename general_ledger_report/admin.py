from django.contrib import admin
from .models import GeneralLedgerReport, ReportTemplate


@admin.register(GeneralLedgerReport)
class GeneralLedgerReportAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'report_type', 'from_date', 'to_date', 'account', 
        'company', 'created_by', 'created_at', 'is_saved'
    ]
    list_filter = [
        'report_type', 'is_saved', 'include_sub_accounts', 
        'include_opening_balance', 'include_closing_balance',
        'created_at', 'company'
    ]
    search_fields = ['name', 'description', 'account__name', 'account__account_code']
    readonly_fields = ['created_at', 'updated_at', 'last_generated']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Report Information', {
            'fields': ('name', 'report_type', 'company', 'fiscal_year')
        }),
        ('Date Range', {
            'fields': ('from_date', 'to_date')
        }),
        ('Account Filters', {
            'fields': ('account', 'include_sub_accounts')
        }),
        ('Amount Filters', {
            'fields': ('min_amount', 'max_amount')
        }),
        ('Reconciliation Filters', {
            'fields': ('include_reconciled_only', 'include_unreconciled_only')
        }),
        ('Export Settings', {
            'fields': ('export_format', 'include_opening_balance', 'include_closing_balance')
        }),
        ('Status', {
            'fields': ('is_saved', 'last_generated')
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


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'template_type', 'is_active', 'is_public', 
        'company', 'created_by', 'created_at'
    ]
    list_filter = [
        'template_type', 'is_active', 'is_public', 
        'include_sub_accounts', 'include_opening_balance', 'include_closing_balance',
        'created_at', 'company'
    ]
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'description', 'template_type', 'company')
        }),
        ('Default Settings', {
            'fields': (
                'default_from_date', 'default_to_date', 'default_account_codes',
                'include_sub_accounts', 'include_opening_balance', 'include_closing_balance',
                'default_export_format'
            )
        }),
        ('Access Control', {
            'fields': ('is_active', 'is_public')
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
