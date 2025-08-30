from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    BackupConfiguration, BackupSession, BackupStep, 
    BackupAuditLog, BackupStorageLocation, BackupRetentionPolicy
)


@admin.register(BackupConfiguration)
class BackupConfigurationAdmin(admin.ModelAdmin):
    list_display = ['name', 'backup_type', 'compression_level', 'encryption_type', 'retention_days', 'is_active', 'created_at']
    list_filter = ['backup_type', 'compression_level', 'encryption_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'backup_type', 'is_active')
        }),
        ('Backup Settings', {
            'fields': ('compression_level', 'encryption_type', 'retention_days')
        }),
        ('Components', {
            'fields': ('include_media', 'include_static', 'include_database', 'include_config')
        }),
        ('Advanced', {
            'fields': ('exclude_patterns',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(BackupSession)
class BackupSessionAdmin(admin.ModelAdmin):
    list_display = [
        'backup_id', 'name', 'reason', 'status', 'priority', 'created_by', 
        'progress_percentage', 'created_at', 'duration_formatted', 'file_size_formatted'
    ]
    list_filter = ['status', 'reason', 'priority', 'created_at', 'started_at', 'completed_at']
    search_fields = ['name', 'description', 'created_by__username']
    readonly_fields = [
        'backup_id', 'created_at', 'updated_at', 'started_at', 'completed_at',
        'duration_seconds', 'duration_formatted', 'file_size_formatted'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('backup_id', 'name', 'reason', 'description', 'priority')
        }),
        ('Configuration', {
            'fields': ('configuration',)
        }),
        ('Status & Progress', {
            'fields': ('status', 'progress_percentage', 'current_step')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at', 'duration_seconds', 'duration_formatted')
        }),
        ('File Information', {
            'fields': ('file_size_bytes', 'file_path', 'checksum_sha256', 'file_size_formatted')
        }),
        ('Storage', {
            'fields': ('primary_storage_path', 'secondary_storage_path')
        }),
        ('Verification', {
            'fields': ('integrity_verified', 'verification_checksum', 'verification_timestamp')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
        ('Notifications', {
            'fields': ('notify_emails', 'notification_sent')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by', 'configuration')
    
    def backup_id_link(self, obj):
        if obj.backup_id:
            url = reverse('manual_backup:backup_detail', args=[obj.backup_id])
            return format_html('<a href="{}">{}</a>', url, obj.backup_id)
        return '-'
    backup_id_link.short_description = 'Backup ID'
    backup_id_link.admin_order_field = 'backup_id'


@admin.register(BackupStep)
class BackupStepAdmin(admin.ModelAdmin):
    list_display = ['id', 'backup_session', 'step_type', 'step_name', 'status', 'order', 'progress_percentage', 'created_at']
    list_filter = ['step_type', 'status', 'created_at']
    search_fields = ['step_name', 'backup_session__name']
    readonly_fields = ['created_at', 'updated_at', 'started_at', 'completed_at', 'duration_seconds']
    
    fieldsets = (
        ('Step Information', {
            'fields': ('backup_session', 'step_type', 'step_name', 'order')
        }),
        ('Status & Progress', {
            'fields': ('status', 'progress_percentage')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at', 'duration_seconds')
        }),
        ('Details', {
            'fields': ('details', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('backup_session')


@admin.register(BackupAuditLog)
class BackupAuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'level', 'backup_session', 'user', 'message', 'ip_address']
    list_filter = ['level', 'timestamp', 'backup_session__status']
    search_fields = ['message', 'user__username', 'backup_session__name']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Log Information', {
            'fields': ('timestamp', 'level', 'message')
        }),
        ('Context', {
            'fields': ('backup_session', 'user', 'ip_address', 'user_agent')
        }),
        ('Details', {
            'fields': ('details',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('backup_session', 'user')


@admin.register(BackupStorageLocation)
class BackupStorageLocationAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'storage_type', 'path', 'is_primary', 'is_active', 
        'usage_percentage', 'total_capacity_bytes', 'available_capacity_bytes'
    ]
    list_filter = ['storage_type', 'is_primary', 'is_active', 'encryption_required']
    search_fields = ['name', 'path', 'host', 'username']
    readonly_fields = ['created_at', 'updated_at', 'usage_percentage']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'storage_type', 'path', 'description')
        }),
        ('Capacity', {
            'fields': ('total_capacity_bytes', 'available_capacity_bytes', 'usage_percentage')
        }),
        ('Configuration', {
            'fields': ('is_primary', 'is_active', 'encryption_required')
        }),
        ('Connection Details', {
            'fields': ('host', 'port', 'username', 'credentials_encrypted')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def usage_percentage_display(self, obj):
        if obj.usage_percentage > 90:
            color = 'red'
        elif obj.usage_percentage > 75:
            color = 'orange'
        else:
            color = 'green'
        
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color, obj.usage_percentage
        )
    usage_percentage_display.short_description = 'Usage %'


@admin.register(BackupRetentionPolicy)
class BackupRetentionPolicyAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'keep_daily_for_days', 'keep_weekly_for_weeks', 
        'keep_monthly_for_months', 'keep_yearly_for_years', 'keep_forever', 'is_active'
    ]
    list_filter = ['is_active', 'auto_cleanup', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Retention Rules', {
            'fields': (
                'keep_daily_for_days', 'keep_weekly_for_weeks', 
                'keep_monthly_for_months', 'keep_yearly_for_years'
            )
        }),
        ('Special Retention', {
            'fields': ('keep_forever', 'minimum_retention_days')
        }),
        ('Cleanup Settings', {
            'fields': ('auto_cleanup', 'cleanup_schedule')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Customize admin site
admin.site.site_header = "LogisEdge Backup Administration"
admin.site.site_title = "Backup Admin"
admin.site.index_title = "Backup Management Dashboard"
