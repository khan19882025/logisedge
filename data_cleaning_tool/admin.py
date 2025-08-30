from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    DataCleaningSession, DataCleaningRule, DataCleaningAuditLog,
    DataQualityReport, AutomatedCleaningSchedule
)


@admin.register(DataCleaningSession)
class DataCleaningSessionAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'cleaning_type', 'status', 'created_by', 'created_at',
        'total_records_scanned', 'total_records_cleaned', 'total_errors_found'
    ]
    list_filter = ['status', 'cleaning_type', 'created_at', 'created_by']
    search_fields = ['name', 'description', 'created_by__username']
    readonly_fields = ['created_at', 'started_at', 'completed_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'cleaning_type', 'created_by')
        }),
        ('Status', {
            'fields': ('status', 'started_at', 'completed_at')
        }),
        ('Statistics', {
            'fields': ('total_records_scanned', 'total_records_cleaned', 'total_errors_found', 'total_warnings_found')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')


@admin.register(DataCleaningRule)
class DataCleaningRuleAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'rule_type', 'target_model', 'target_field', 'priority', 'is_active', 'created_at'
    ]
    list_filter = ['rule_type', 'is_active', 'priority', 'created_at']
    search_fields = ['name', 'description', 'target_model', 'target_field']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['priority', 'is_active']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'rule_type')
        }),
        ('Target Configuration', {
            'fields': ('target_model', 'target_field', 'rule_config')
        }),
        ('Settings', {
            'fields': ('priority', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DataCleaningAuditLog)
class DataCleaningAuditLogAdmin(admin.ModelAdmin):
    list_display = [
        'action_type', 'target_model', 'target_record_id', 'severity', 'session', 'created_at'
    ]
    list_filter = ['action_type', 'severity', 'target_model', 'created_at', 'session']
    search_fields = ['target_model', 'target_record_id', 'description', 'session__name']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Action Details', {
            'fields': ('action_type', 'severity', 'description')
        }),
        ('Target Information', {
            'fields': ('target_model', 'target_record_id', 'field_name')
        }),
        ('Values', {
            'fields': ('old_value', 'new_value')
        }),
        ('Context', {
            'fields': ('session', 'rule')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('session', 'rule')


@admin.register(DataQualityReport)
class DataQualityReportAdmin(admin.ModelAdmin):
    list_display = [
        'session', 'summary_preview', 'generated_at'
    ]
    list_filter = ['generated_at', 'session__cleaning_type']
    search_fields = ['session__name', 'summary', 'recommendations']
    readonly_fields = ['generated_at']
    date_hierarchy = 'generated_at'
    
    fieldsets = (
        ('Session Information', {
            'fields': ('session',)
        }),
        ('Report Content', {
            'fields': ('summary', 'recommendations', 'report_data')
        }),
        ('Metadata', {
            'fields': ('generated_at',)
        }),
    )
    
    def summary_preview(self, obj):
        return obj.summary[:100] + '...' if len(obj.summary) > 100 else obj.summary
    summary_preview.short_description = 'Summary Preview'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('session')


@admin.register(AutomatedCleaningSchedule)
class AutomatedCleaningScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'cleaning_type', 'frequency', 'is_active', 'last_run', 'next_run', 'created_by'
    ]
    list_filter = ['cleaning_type', 'frequency', 'is_active', 'created_at', 'created_by']
    search_fields = ['name', 'description', 'created_by__username']
    readonly_fields = ['created_at', 'last_run', 'next_run']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'cleaning_type', 'frequency')
        }),
        ('Schedule Status', {
            'fields': ('is_active', 'last_run', 'next_run')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')


# Custom admin site configuration
admin.site.site_header = "LogisEdge ERP - Data Cleaning Tool Administration"
admin.site.site_title = "Data Cleaning Tool Admin"
admin.site.index_title = "Data Cleaning Tool Management"
