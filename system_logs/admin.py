from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    SystemLog, ErrorPattern, DebugSession, LogRetentionPolicy, 
    LogExport, ErrorPatternLog, DebugSessionLog
)
from django.utils import timezone


@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp', 'log_type', 'severity', 'status', 'module', 
        'function', 'user', 'error_message_truncated', 'execution_time_display'
    ]
    list_filter = [
        'log_type', 'severity', 'status', 'module', 'environment',
        'timestamp'
    ]
    search_fields = [
        'error_message', 'error_type', 'module', 'function', 
        'user__username', 'tags', 'stack_trace'
    ]
    readonly_fields = [
        'id', 'timestamp', 'created_at', 'updated_at', 'stack_trace_formatted',
        'context_data_formatted', 'exception_details_formatted'
    ]
    date_hierarchy = 'timestamp'
    list_per_page = 50
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'timestamp', 'log_type', 'severity', 'status')
        }),
        ('Error Details', {
            'fields': ('error_message', 'error_type', 'stack_trace_formatted', 'exception_details_formatted')
        }),
        ('Context Information', {
            'fields': ('module', 'function', 'line_number', 'file_path')
        }),
        ('User and Request', {
            'fields': ('user', 'user_ip', 'user_agent', 'request_method', 'request_url', 'request_data')
        }),
        ('Performance Metrics', {
            'fields': ('execution_time', 'memory_usage', 'cpu_usage')
        }),
        ('Related Objects', {
            'fields': ('content_type', 'object_id', 'object_name')
        }),
        ('Additional Context', {
            'fields': ('tags', 'context_data_formatted', 'environment', 'version')
        }),
        ('Resolution Tracking', {
            'fields': ('resolved_by', 'resolved_at', 'resolution_notes', 'escalation_level')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def error_message_truncated(self, obj):
        if obj.error_message:
            return obj.error_message[:100] + '...' if len(obj.error_message) > 100 else obj.error_message
        return '-'
    error_message_truncated.short_description = 'Error Message'
    
    def execution_time_display(self, obj):
        if obj.execution_time:
            return f"{float(obj.execution_time):.3f}s"
        return '-'
    execution_time_display.short_description = 'Execution Time'
    
    def has_stack_trace(self, obj):
        return bool(obj.stack_trace)
    has_stack_trace.boolean = True
    has_stack_trace.short_description = 'Has Stack Trace'
    
    def has_context_data(self, obj):
        return bool(obj.context_data)
    has_context_data.boolean = True
    has_context_data.short_description = 'Has Context Data'
    
    def stack_trace_formatted(self, obj):
        if obj.stack_trace:
            return format_html('<pre style="background: #f5f5f5; padding: 10px; border-radius: 4px;">{}</pre>', obj.stack_trace)
        return '-'
    stack_trace_formatted.short_description = 'Stack Trace'
    
    def context_data_formatted(self, obj):
        if obj.context_data:
            import json
            formatted = json.dumps(obj.context_data, indent=2)
            return format_html('<pre style="background: #f5f5f5; padding: 10px; border-radius: 4px;">{}</pre>', formatted)
        return '-'
    context_data_formatted.short_description = 'Context Data'
    
    def exception_details_formatted(self, obj):
        if obj.exception_details:
            import json
            formatted = json.dumps(obj.exception_details, indent=2)
            return format_html('<pre style="background: #f5f5f5; padding: 10px; border-radius: 4px;">{}</pre>', formatted)
        return '-'
    exception_details_formatted.short_description = 'Exception Details'
    
    actions = ['mark_resolved', 'mark_ignored', 'escalate_logs', 'archive_logs']
    
    def mark_resolved(self, request, queryset):
        updated = queryset.update(status='RESOLVED', resolved_by=request.user)
        self.message_user(request, f'{updated} logs marked as resolved.')
    mark_resolved.short_description = 'Mark selected logs as resolved'
    
    def mark_ignored(self, request, queryset):
        updated = queryset.update(status='IGNORED')
        self.message_user(request, f'{updated} logs marked as ignored.')
    mark_ignored.short_description = 'Mark selected logs as ignored'
    
    def escalate_logs(self, request, queryset):
        updated = queryset.update(status='ESCALATED', escalation_level=1)
        self.message_user(request, f'{updated} logs escalated.')
    escalate_logs.short_description = 'Escalate selected logs'
    
    def archive_logs(self, request, queryset):
        updated = queryset.update(status='ARCHIVED')
        self.message_user(request, f'{updated} logs archived.')
    archive_logs.short_description = 'Archive selected logs'


@admin.register(ErrorPattern)
class ErrorPatternAdmin(admin.ModelAdmin):
    list_display = [
        'pattern_type', 'error_type', 'module', 'function', 'occurrence_count',
        'max_severity', 'last_occurrence', 'is_resolved'
    ]
    list_filter = [
        'pattern_type', 'is_resolved', 'avg_severity', 'max_severity',
        'first_occurrence', 'last_occurrence'
    ]
    search_fields = [
        'error_signature', 'error_type', 'module', 'function', 'resolution_notes'
    ]
    readonly_fields = [
        'id', 'pattern_hash', 'first_occurrence', 'last_occurrence',
        'occurrence_count', 'total_affected_users', 'avg_execution_time'
    ]
    date_hierarchy = 'last_occurrence'
    
    fieldsets = (
        ('Pattern Information', {
            'fields': ('id', 'pattern_type', 'pattern_hash', 'error_signature', 'error_type')
        }),
        ('Location', {
            'fields': ('module', 'function')
        }),
        ('Statistics', {
            'fields': ('occurrence_count', 'first_occurrence', 'last_occurrence', 'total_affected_users')
        }),
        ('Impact Analysis', {
            'fields': ('avg_severity', 'max_severity', 'avg_execution_time')
        }),
        ('Resolution', {
            'fields': ('is_resolved', 'resolution_notes', 'resolved_by', 'resolved_at')
        }),
    )
    
    actions = ['mark_resolved', 'mark_unresolved']
    
    def mark_resolved(self, request, queryset):
        updated = queryset.update(is_resolved=True, resolved_by=request.user, resolved_at=timezone.now())
        self.message_user(request, f'{updated} error patterns marked as resolved.')
    mark_resolved.short_description = 'Mark selected patterns as resolved'
    
    def mark_unresolved(self, request, queryset):
        updated = queryset.update(is_resolved=False, resolved_by=None, resolved_at=None)
        self.message_user(request, f'{updated} error patterns marked as unresolved.')
    mark_unresolved.short_description = 'Mark selected patterns as unresolved'


@admin.register(DebugSession)
class DebugSessionAdmin(admin.ModelAdmin):
    list_display = [
        'session_name', 'session_type', 'started_by', 'started_at', 
        'is_active', 'log_count', 'duration_display'
    ]
    list_filter = [
        'session_type', 'is_active', 'environment', 'started_at'
    ]
    search_fields = [
        'session_name', 'description', 'started_by__username', 'tags'
    ]
    readonly_fields = [
        'id', 'started_at', 'log_count', 'duration_display'
    ]
    date_hierarchy = 'started_at'
    
    fieldsets = (
        ('Session Information', {
            'fields': ('id', 'session_name', 'session_type', 'description')
        }),
        ('Session Details', {
            'fields': ('started_by', 'started_at', 'ended_at', 'is_active')
        }),
        ('Context', {
            'fields': ('environment', 'version', 'tags', 'context_data')
        }),
        ('Statistics', {
            'fields': ('log_count', 'duration_display')
        }),
    )
    
    def log_count(self, obj):
        return obj.get_log_count()
    log_count.short_description = 'Log Count'
    
    def duration_display(self, obj):
        duration = obj.get_duration()
        if duration:
            total_seconds = int(duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            if hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"
        return '-'
    duration_display.short_description = 'Duration'
    
    actions = ['end_sessions', 'activate_sessions']
    
    def end_sessions(self, request, queryset):
        active_sessions = queryset.filter(is_active=True)
        for session in active_sessions:
            session.end_session()
        self.message_user(request, f'{active_sessions.count()} sessions ended.')
    end_sessions.short_description = 'End selected active sessions'
    
    def activate_sessions(self, request, queryset):
        inactive_sessions = queryset.filter(is_active=False)
        inactive_sessions.update(is_active=True, ended_at=None)
        self.message_user(request, f'{inactive_sessions.count()} sessions activated.')
    activate_sessions.short_description = 'Activate selected inactive sessions'


@admin.register(LogRetentionPolicy)
class LogRetentionPolicyAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'retention_type', 'retention_value', 'action_type', 
        'is_active', 'last_executed', 'total_processed'
    ]
    list_filter = [
        'retention_type', 'action_type', 'is_active', 'created_at'
    ]
    search_fields = [
        'name', 'description', 'created_by__username'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'last_executed', 'total_processed'
    ]
    
    fieldsets = (
        ('Policy Information', {
            'fields': ('id', 'name', 'description')
        }),
        ('Configuration', {
            'fields': ('retention_type', 'retention_value', 'action_type')
        }),
        ('Filters', {
            'fields': ('severity_levels', 'log_types', 'modules', 'tags')
        }),
        ('Status', {
            'fields': ('is_active', 'last_executed', 'next_execution')
        }),
        ('Statistics', {
            'fields': ('total_processed', 'last_processed_count')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )
    
    actions = ['activate_policies', 'deactivate_policies', 'execute_policies']
    
    def activate_policies(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} policies activated.')
    activate_policies.short_description = 'Activate selected policies'
    
    def deactivate_policies(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} policies deactivated.')
    deactivate_policies.short_description = 'Deactivate selected policies'
    
    def execute_policies(self, request, queryset):
        # This would trigger the actual policy execution
        self.message_user(request, f'{queryset.count()} policies queued for execution.')
    execute_policies.short_description = 'Execute selected policies'


@admin.register(LogExport)
class LogExportAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'export_format', 'requested_by', 'requested_at', 
        'status', 'record_count', 'file_size_display'
    ]
    list_filter = [
        'export_format', 'status', 'requested_at', 'completed_at'
    ]
    search_fields = [
        'name', 'description', 'requested_by__username', 'error_message'
    ]
    readonly_fields = [
        'id', 'requested_at', 'completed_at', 'record_count', 'file_size',
        'file_path', 'download_url', 'retry_count'
    ]
    date_hierarchy = 'requested_at'
    
    fieldsets = (
        ('Export Information', {
            'fields': ('id', 'name', 'description')
        }),
        ('Configuration', {
            'fields': ('export_format', 'filter_criteria', 'include_metadata', 'max_records')
        }),
        ('Request Details', {
            'fields': ('requested_by', 'requested_at', 'status')
        }),
        ('Results', {
            'fields': ('record_count', 'file_size', 'file_path', 'download_url')
        }),
        ('Error Handling', {
            'fields': ('error_message', 'retry_count', 'completed_at')
        }),
    )
    
    def file_size_display(self, obj):
        if obj.file_size:
            if obj.file_size < 1024:
                return f"{obj.file_size} B"
            elif obj.file_size < 1024 * 1024:
                return f"{obj.file_size / 1024:.1f} KB"
            else:
                return f"{obj.file_size / (1024 * 1024):.1f} MB"
        return '-'
    file_size_display.short_description = 'File Size'
    
    actions = ['retry_failed_exports', 'cancel_pending_exports']
    
    def retry_failed_exports(self, request, queryset):
        failed_exports = queryset.filter(status='FAILED')
        failed_exports.update(status='PENDING', retry_count=0)
        self.message_user(request, f'{failed_exports.count()} failed exports queued for retry.')
    retry_failed_exports.short_description = 'Retry failed exports'
    
    def cancel_pending_exports(self, request, queryset):
        pending_exports = queryset.filter(status='PENDING')
        pending_exports.update(status='CANCELLED')
        self.message_user(request, f'{pending_exports.count()} pending exports cancelled.')
    cancel_pending_exports.short_description = 'Cancel pending exports'


# Through models (optional, for advanced admin features)
@admin.register(ErrorPatternLog)
class ErrorPatternLogAdmin(admin.ModelAdmin):
    list_display = ['pattern', 'log_entry', 'matched_at']
    list_filter = ['matched_at', 'pattern__pattern_type']
    search_fields = ['pattern__error_type', 'log_entry__error_message']
    readonly_fields = ['pattern', 'log_entry', 'matched_at']


@admin.register(DebugSessionLog)
class DebugSessionLogAdmin(admin.ModelAdmin):
    list_display = ['session', 'log_entry', 'added_at']
    list_filter = ['added_at', 'session__session_type']
    search_fields = ['session__session_name', 'log_entry__error_message']
    readonly_fields = ['session', 'log_entry', 'added_at']


# Customize admin site
admin.site.site_header = 'System Logs Administration'
admin.site.site_title = 'System Logs Admin'
admin.site.index_title = 'System Error & Debug Logs Management'
