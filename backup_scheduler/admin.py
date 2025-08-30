from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    BackupType, BackupScope, StorageLocation, BackupSchedule, 
    BackupExecution, BackupRetentionPolicy, BackupAlert,
    DisasterRecoveryPlan, BackupLog
)

@admin.register(BackupType)
class BackupTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']

@admin.register(BackupScope)
class BackupScopeAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']

@admin.register(StorageLocation)
class StorageLocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'storage_type', 'path', 'is_active', 'capacity_display', 'created_at']
    list_filter = ['storage_type', 'is_active', 'created_at']
    search_fields = ['name', 'path']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'storage_type', 'path', 'is_active')
        }),
        ('Storage Configuration', {
            'fields': ('max_capacity_gb', 'used_capacity_gb')
        }),
        ('Credentials', {
            'fields': ('credentials',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']
    
    def capacity_display(self, obj):
        used_percentage = (obj.used_capacity_gb / obj.max_capacity_gb * 100) if obj.max_capacity_gb > 0 else 0
        color = 'green' if used_percentage < 70 else 'orange' if used_percentage < 90 else 'red'
        return format_html(
            '<span style="color: {};">{:.1f} GB / {:.1f} GB ({:.1f}%)</span>',
            color, obj.used_capacity_gb, obj.max_capacity_gb, used_percentage
        )
    capacity_display.short_description = 'Capacity Usage'

@admin.register(BackupSchedule)
class BackupScheduleAdmin(admin.ModelAdmin):
    list_display = ['name', 'backup_type', 'backup_scope', 'frequency', 'start_time', 'is_active', 'created_by', 'created_at']
    list_filter = ['frequency', 'is_active', 'backup_type', 'backup_scope', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'backup_type', 'backup_scope', 'storage_location')
        }),
        ('Scheduling', {
            'fields': ('frequency', 'start_time', 'start_date', 'is_active')
        }),
        ('Frequency Specific', {
            'fields': ('weekday', 'day_of_month', 'cron_expression'),
            'classes': ('collapse',)
        }),
        ('Retention', {
            'fields': ('retention_days', 'max_backups', 'allow_parallel')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_by', 'created_at', 'updated_at']
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by for new objects
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(BackupExecution)
class BackupExecutionAdmin(admin.ModelAdmin):
    list_display = ['execution_id', 'backup_type', 'backup_scope', 'status', 'started_at', 'duration_display', 'is_manual', 'triggered_by']
    list_filter = ['status', 'backup_type', 'backup_scope', 'is_manual', 'created_at']
    search_fields = ['execution_id', 'error_message']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Execution Details', {
            'fields': ('execution_id', 'schedule', 'backup_type', 'backup_scope', 'storage_location')
        }),
        ('Status', {
            'fields': ('status', 'started_at', 'completed_at', 'duration_seconds')
        }),
        ('File Information', {
            'fields': ('file_path', 'file_size_mb', 'checksum'),
            'classes': ('collapse',)
        }),
        ('Error Information', {
            'fields': ('error_message', 'error_details'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('is_manual', 'triggered_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['execution_id', 'created_at']
    
    def duration_display(self, obj):
        if obj.duration_seconds:
            minutes = obj.duration_seconds // 60
            seconds = obj.duration_seconds % 60
            return f"{minutes}m {seconds}s"
        return "-"
    duration_display.short_description = 'Duration'

@admin.register(BackupRetentionPolicy)
class BackupRetentionPolicyAdmin(admin.ModelAdmin):
    list_display = ['name', 'backup_type', 'retention_days', 'retention_count', 'is_active', 'created_at']
    list_filter = ['backup_type', 'is_active', 'created_at']
    search_fields = ['name']
    ordering = ['name']
    
    fieldsets = (
        ('Policy Information', {
            'fields': ('name', 'backup_type', 'is_active')
        }),
        ('Retention Settings', {
            'fields': ('retention_days', 'retention_count')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']

@admin.register(BackupAlert)
class BackupAlertAdmin(admin.ModelAdmin):
    list_display = ['name', 'alert_type', 'channel', 'recipients_display', 'is_active', 'created_at']
    list_filter = ['alert_type', 'channel', 'is_active', 'created_at']
    search_fields = ['name']
    ordering = ['name']
    
    fieldsets = (
        ('Alert Configuration', {
            'fields': ('name', 'alert_type', 'channel', 'is_active')
        }),
        ('Recipients', {
            'fields': ('recipients',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']
    
    def recipients_display(self, obj):
        if obj.recipients:
            return ', '.join(obj.recipients[:3]) + ('...' if len(obj.recipients) > 3 else '')
        return "-"
    recipients_display.short_description = 'Recipients'

@admin.register(DisasterRecoveryPlan)
class DisasterRecoveryPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'backup_execution', 'test_schedule', 'last_tested', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    fieldsets = (
        ('Plan Information', {
            'fields': ('name', 'description', 'backup_execution', 'is_active')
        }),
        ('Testing', {
            'fields': ('test_schedule', 'last_tested')
        }),
        ('Recovery Procedures', {
            'fields': ('recovery_procedures',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']

@admin.register(BackupLog)
class BackupLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'level', 'message', 'user', 'execution_link', 'ip_address']
    list_filter = ['level', 'timestamp', 'user']
    search_fields = ['message', 'user__username']
    ordering = ['-timestamp']
    
    fieldsets = (
        ('Log Information', {
            'fields': ('timestamp', 'level', 'message')
        }),
        ('Context', {
            'fields': ('execution', 'user', 'ip_address')
        }),
        ('Additional Data', {
            'fields': ('additional_data',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['timestamp', 'execution_link']
    
    def execution_link(self, obj):
        if obj.execution:
            url = reverse('admin:backup_scheduler_backupexecution_change', args=[obj.execution.pk])
            return format_html('<a href="{}">{}</a>', url, obj.execution.execution_id)
        return "-"
    execution_link.short_description = 'Execution'
    
    def has_add_permission(self, request):
        return False  # Logs are created automatically
    
    def has_change_permission(self, request, obj=None):
        return False  # Logs should not be modified
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Only superusers can delete logs
