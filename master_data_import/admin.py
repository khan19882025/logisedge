from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    ImportTemplate, ImportJob, ImportValidationRule, 
    ImportAuditLog, ImportDataError, ImportFile
)


@admin.register(ImportTemplate)
class ImportTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'data_type', 'is_active', 'created_by', 'created_at', 'updated_at']
    list_filter = ['data_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = []
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'data_type', 'description', 'is_active')
        }),
        ('Configuration', {
            'fields': ('column_mappings', 'validation_rules', 'required_fields'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ImportJob)
class ImportJobAdmin(admin.ModelAdmin):
    list_display = [
        'job_name', 'template', 'status', 'progress_display', 
        'total_rows', 'successful_rows', 'failed_rows', 
        'created_by', 'created_at'
    ]
    list_filter = ['status', 'template__data_type', 'created_at']
    search_fields = ['job_name', 'file_name']
    readonly_fields = [
        'created_at', 'started_at', 'completed_at', 'duration_display',
        'progress_percentage', 'error_log', 'import_summary'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Job Information', {
            'fields': ('job_name', 'template', 'file_name', 'file_size', 'status')
        }),
        ('Progress', {
            'fields': ('total_rows', 'processed_rows', 'successful_rows', 'failed_rows', 'progress_percentage')
        }),
        ('Timing', {
            'fields': ('created_at', 'started_at', 'completed_at', 'duration_display')
        }),
        ('Details', {
            'fields': ('error_log', 'import_summary'),
            'classes': ('collapse',)
        }),
    )
    
    def progress_display(self, obj):
        return format_html(
            '<div class="progress" style="width: 100px; height: 20px;">'
            '<div class="progress-bar" role="progressbar" '
            'style="width: {}%;" aria-valuenow="{}" aria-valuemin="0" aria-valuemax="100">'
            '{:.1f}%</div></div>',
            obj.progress_percentage, obj.progress_percentage, obj.progress_percentage
        )
    progress_display.short_description = 'Progress'
    
    def duration_display(self, obj):
        if obj.duration:
            return str(obj.duration)
        return 'N/A'
    duration_display.short_description = 'Duration'
    
    actions = ['cancel_jobs', 'retry_failed_jobs']
    
    def cancel_jobs(self, request, queryset):
        cancelled = queryset.filter(status__in=['pending', 'processing']).update(status='cancelled')
        self.message_user(request, f'{cancelled} jobs cancelled successfully.')
    cancel_jobs.short_description = 'Cancel selected jobs'
    
    def retry_failed_jobs(self, request, queryset):
        retried = queryset.filter(status='failed').update(status='pending')
        self.message_user(request, f'{retried} failed jobs queued for retry.')
    retry_failed_jobs.short_description = 'Retry failed jobs'


@admin.register(ImportValidationRule)
class ImportValidationRuleAdmin(admin.ModelAdmin):
    list_display = ['template', 'field_name', 'rule_type', 'validation_type', 'is_active', 'created_at']
    list_filter = ['rule_type', 'validation_type', 'is_active', 'template']
    search_fields = ['field_name', 'error_message']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Rule Information', {
            'fields': ('template', 'field_name', 'rule_type', 'validation_type', 'is_active')
        }),
        ('Configuration', {
            'fields': ('rule_config', 'error_message'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(ImportAuditLog)
class ImportAuditLogAdmin(admin.ModelAdmin):
    list_display = ['import_job', 'action', 'message', 'ip_address', 'timestamp']
    list_filter = ['action', 'timestamp', 'import_job__template__data_type']
    search_fields = ['message', 'import_job__job_name']
    readonly_fields = ['timestamp', 'ip_address', 'user_agent']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Log Information', {
            'fields': ('import_job', 'action', 'message')
        }),
        ('Request Details', {
            'fields': ('ip_address', 'user_agent', 'details'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False  # Audit logs should only be created by the system


@admin.register(ImportDataError)
class ImportDataErrorAdmin(admin.ModelAdmin):
    list_display = ['import_job', 'row_number', 'column_name', 'error_type', 'error_message', 'created_at']
    list_filter = ['error_type', 'created_at', 'import_job__template__data_type']
    search_fields = ['error_message', 'field_value', 'import_job__job_name']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Error Information', {
            'fields': ('import_job', 'row_number', 'column_name', 'error_type', 'error_message')
        }),
        ('Details', {
            'fields': ('field_value', 'suggested_correction'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False  # Import errors should only be created by the system


@admin.register(ImportFile)
class ImportFileAdmin(admin.ModelAdmin):
    list_display = ['original_filename', 'import_job', 'file_size_display', 'uploaded_at']
    list_filter = ['uploaded_at', 'import_job__template__data_type']
    search_fields = ['original_filename', 'import_job__job_name']
    readonly_fields = ['uploaded_at', 'file_hash']
    date_hierarchy = 'uploaded_at'
    
    fieldsets = (
        ('File Information', {
            'fields': ('import_job', 'file', 'original_filename')
        }),
        ('Metadata', {
            'fields': ('file_hash', 'uploaded_at'),
            'classes': ('collapse',)
        }),
    )
    
    def file_size_display(self, obj):
        if obj.file:
            return f"{obj.file.size / (1024*1024):.2f} MB"
        return 'N/A'
    file_size_display.short_description = 'File Size'


# Customize admin site
admin.site.site_header = "LogisEdge ERP Admin"
admin.site.site_title = "LogisEdge Admin Portal"
admin.site.index_title = "Welcome to LogisEdge ERP Administration"
