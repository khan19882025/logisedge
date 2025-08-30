from django.contrib import admin
from .models import BalanceSheetReport, ReportTemplate, AccountGroup


@admin.register(BalanceSheetReport)
class BalanceSheetReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'as_of_date', 'company', 'branch', 'department', 'created_by', 'created_at']
    list_filter = ['as_of_date', 'company', 'created_at']
    search_fields = ['title', 'branch', 'department']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Report Information', {
            'fields': ('title', 'as_of_date', 'company', 'branch', 'department')
        }),
        ('Report Data', {
            'fields': ('report_data',),
            'classes': ('collapse',)
        }),
        ('Export Options', {
            'fields': ('include_headers', 'include_totals', 'include_comparison', 'include_percentages'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_default', 'created_by', 'created_at']
    list_filter = ['is_default', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'description', 'is_default')
        }),
        ('Configuration', {
            'fields': ('template_config',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AccountGroup)
class AccountGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'asset_type', 'parent_group', 'order', 'is_active']
    list_filter = ['asset_type', 'is_active', 'parent_group']
    search_fields = ['name']
    ordering = ['asset_type', 'order', 'name']
    
    fieldsets = (
        ('Group Information', {
            'fields': ('name', 'asset_type', 'parent_group', 'order', 'is_active')
        }),
        ('Accounts', {
            'fields': ('accounts',),
        }),
    )
    
    filter_horizontal = ['accounts']
