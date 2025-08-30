from django.contrib import admin
from .models import (
    CostCenterFinancialReport, CostCenterReportFilter, 
    CostCenterReportExport, CostCenterReportSchedule
)


@admin.register(CostCenterFinancialReport)
class CostCenterFinancialReportAdmin(admin.ModelAdmin):
    list_display = [
        'report_name', 'report_type', 'start_date', 'end_date', 
        'cost_center', 'department', 'status', 'generated_at', 'generated_by'
    ]
    list_filter = ['report_type', 'status', 'generated_at', 'cost_center__department']
    search_fields = ['report_name', 'cost_center__name', 'department__name']
    readonly_fields = ['generated_at', 'generated_by']
    date_hierarchy = 'generated_at'
    
    fieldsets = (
        ('Report Information', {
            'fields': ('report_name', 'report_type', 'status')
        }),
        ('Date Range', {
            'fields': ('start_date', 'end_date')
        }),
        ('Scope', {
            'fields': ('cost_center', 'department', 'include_inactive')
        }),
        ('Report Data', {
            'fields': ('report_data',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('generated_at', 'generated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set generated_by on creation
            obj.generated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CostCenterReportFilter)
class CostCenterReportFilterAdmin(admin.ModelAdmin):
    list_display = ['report', 'filter_name', 'filter_value', 'filter_type', 'created_at']
    list_filter = ['filter_type', 'created_at']
    search_fields = ['filter_name', 'filter_value', 'report__report_name']
    readonly_fields = ['created_at']


@admin.register(CostCenterReportExport)
class CostCenterReportExportAdmin(admin.ModelAdmin):
    list_display = [
        'report', 'export_type', 'file_size', 'generated_at', 'generated_by'
    ]
    list_filter = ['export_type', 'generated_at']
    search_fields = ['report__report_name']
    readonly_fields = ['generated_at', 'generated_by', 'file_size']


@admin.register(CostCenterReportSchedule)
class CostCenterReportScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'schedule_name', 'report_type', 'frequency', 'start_date', 
        'end_date', 'is_active', 'created_by'
    ]
    list_filter = ['report_type', 'frequency', 'is_active', 'created_at']
    search_fields = ['schedule_name']
    readonly_fields = ['created_at', 'created_by']
    
    fieldsets = (
        ('Schedule Information', {
            'fields': ('schedule_name', 'report_type', 'frequency')
        }),
        ('Date Range', {
            'fields': ('start_date', 'end_date')
        }),
        ('Configuration', {
            'fields': ('is_active', 'recipients')
        }),
        ('Metadata', {
            'fields': ('created_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
