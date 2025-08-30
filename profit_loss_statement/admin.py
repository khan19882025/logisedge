from django.contrib import admin
from .models import ProfitLossReport, ReportTemplate


@admin.register(ProfitLossReport)
class ProfitLossReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'from_date', 'to_date', 'company', 'created_by', 'created_at']
    list_filter = ['created_at', 'report_period', 'comparison_type', 'company']
    search_fields = ['title', 'created_by__username', 'created_by__first_name', 'created_by__last_name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Report Information', {
            'fields': ('title', 'from_date', 'to_date', 'company', 'report_period', 'comparison_type')
        }),
        ('Report Data', {
            'fields': ('report_data',),
            'classes': ('collapse',)
        }),
        ('Export Settings', {
            'fields': ('include_headers', 'include_totals', 'include_comparison', 'currency_format')
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
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'description', 'is_default')
        }),
        ('Section Visibility', {
            'fields': ('show_revenue_section', 'show_cogs_section', 'show_expenses_section', 'show_other_income_expenses')
        }),
        ('Styling Options', {
            'fields': ('primary_color', 'secondary_color', 'font_family')
        }),
        ('Grouping Options', {
            'fields': ('group_by_department', 'group_by_cost_center')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    ) 