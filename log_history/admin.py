from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import LogHistory, LogCategory, LogFilter, LogExport, LogRetentionPolicy


@admin.register(LogHistory)
class LogHistoryAdmin(admin.ModelAdmin):
    """
    Admin interface for LogHistory model
    """
    list_display = [
        'id', 'timestamp', 'action_type', 'severity', 'user_display', 
        'object_info', 'module', 'description_short', 'status'
    ]
    list_filter = [
        'action_type', 'severity', 'status', 'timestamp', 'module', 'user',
    ]
    search_fields = [
        'description', 'object_name', 'module', 'function', 'user__username',
        'user_ip', 'tags'
    ]
    readonly_fields = [
        'id', 'timestamp', 'created_at', 'updated_at', 'execution_time',
        'memory_usage', 'stack_trace'
    ]
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    list_per_page = 100
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'timestamp', 'action_type', 'severity', 'status', 'description')
        }),
        ('User Information', {
            'fields': ('user', 'user_ip', 'user_agent', 'user_session'),
            'classes': ('collapse',)
        }),
        ('Target Object', {
            'fields': ('content_type', 'object_id', 'object_name', 'object_type'),
            'classes': ('collapse',)
        }),
        ('Action Details', {
            'fields': ('details', 'before_values', 'after_values', 'changed_fields'),
            'classes': ('collapse',)
        }),
        ('Context Information', {
            'fields': ('module', 'function', 'line_number', 'stack_trace'),
            'classes': ('collapse',)
        }),
        ('Performance Metrics', {
            'fields': ('execution_time', 'memory_usage'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('tags', 'metadata'),
            'classes': ('collapse',)
        }),
        ('System Fields', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_display(self, obj):
        """Display user information with link"""
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return 'System'
    user_display.short_description = 'User'
    user_display.admin_order_field = 'user__username'
    
    def object_info(self, obj):
        """Display object information"""
        if obj.object_name:
            return f"{obj.object_type or 'Unknown'}: {obj.object_name}"
        return obj.object_type or 'N/A'
    object_info.short_description = 'Object'
    
    def description_short(self, obj):
        """Display truncated description"""
        return obj.description[:100] + '...' if len(obj.description) > 100 else obj.description
    description_short.short_description = 'Description'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user', 'content_type')
    
    def has_add_permission(self, request):
        """Logs are created automatically, not manually"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Allow editing of certain fields"""
        return request.user.has_perm('log_history.change_loghistory')
    
    def has_delete_permission(self, request, obj=None):
        """Allow deletion with proper permissions"""
        return request.user.has_perm('log_history.delete_loghistory')
    
    actions = ['archive_logs', 'delete_logs', 'export_logs']
    
    def archive_logs(self, request, queryset):
        """Archive selected logs"""
        count = queryset.update(status=LogHistory.STATUS_ARCHIVED)
        self.message_user(request, f'{count} logs have been archived.')
    archive_logs.short_description = 'Archive selected logs'
    
    def delete_logs(self, request, queryset):
        """Soft delete selected logs"""
        count = queryset.update(status=LogHistory.STATUS_DELETED)
        self.message_user(request, f'{count} logs have been deleted.')
    delete_logs.short_description = 'Delete selected logs'
    
    def export_logs(self, request, queryset):
        """Export selected logs"""
        # This would redirect to the export view with selected IDs
        self.message_user(request, f'{queryset.count()} logs selected for export.')
    export_logs.short_description = 'Export selected logs'


@admin.register(LogCategory)
class LogCategoryAdmin(admin.ModelAdmin):
    """
    Admin interface for LogCategory model
    """
    list_display = ['name', 'description_short', 'color_display', 'icon', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Styling', {
            'fields': ('color', 'icon')
        }),
        ('System Fields', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def description_short(self, obj):
        """Display truncated description"""
        return obj.description[:100] + '...' if len(obj.description) > 100 else obj.description
    description_short.short_description = 'Description'
    
    def color_display(self, obj):
        """Display color as a colored square"""
        return format_html(
            '<span style="display: inline-block; width: 20px; height: 20px; '
            'background-color: {}; border: 1px solid #ccc; border-radius: 3px;"></span> {}',
            obj.color, obj.color
        )
    color_display.short_description = 'Color'
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(LogFilter)
class LogFilterAdmin(admin.ModelAdmin):
    """
    Admin interface for LogFilter model
    """
    list_display = ['name', 'user', 'description_short', 'is_default', 'is_public', 'created_at']
    list_filter = ['is_default', 'is_public', 'created_at', 'user']
    search_fields = ['name', 'description', 'user__username']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'user')
        }),
        ('Filter Settings', {
            'fields': ('filter_criteria', 'is_default', 'is_public')
        }),
        ('System Fields', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def description_short(self, obj):
        """Display truncated description"""
        return obj.description[:100] + '...' if len(obj.description) > 100 else obj.description
    description_short.short_description = 'Description'
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user')


@admin.register(LogExport)
class LogExportAdmin(admin.ModelAdmin):
    """
    Admin interface for LogExport model
    """
    list_display = [
        'id', 'user', 'export_format', 'record_count', 'status', 
        'file_size_display', 'created_at', 'completed_at'
    ]
    list_filter = ['export_format', 'status', 'created_at', 'user']
    search_fields = ['user__username', 'file_path']
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'completed_at']
    
    fieldsets = (
        ('Export Information', {
            'fields': ('id', 'user', 'export_format', 'status')
        }),
        ('Filter Criteria', {
            'fields': ('filter_criteria',),
            'classes': ('collapse',)
        }),
        ('Results', {
            'fields': ('record_count', 'file_path', 'file_size', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def file_size_display(self, obj):
        """Display file size in human-readable format"""
        if obj.file_size:
            for unit in ['B', 'KB', 'MB', 'GB']:
                if obj.file_size < 1024.0:
                    return f"{obj.file_size:.1f} {unit}"
                obj.file_size /= 1024.0
            return f"{obj.file_size:.1f} TB"
        return 'N/A'
    file_size_display.short_description = 'File Size'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user')


@admin.register(LogRetentionPolicy)
class LogRetentionPolicyAdmin(admin.ModelAdmin):
    """
    Admin interface for LogRetentionPolicy model
    """
    list_display = [
        'name', 'action_type', 'severity', 'module', 'retention_period_display', 
        'is_active', 'created_at'
    ]
    list_filter = ['is_active', 'action_type', 'severity', 'retention_period', 'created_at']
    search_fields = ['name', 'description', 'module']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Filter Criteria', {
            'fields': ('action_type', 'severity', 'module')
        }),
        ('Retention Settings', {
            'fields': ('retention_period',)
        }),
        ('System Fields', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def retention_period_display(self, obj):
        """Display retention period in human-readable format"""
        if obj.retention_period == -1:
            return 'Forever'
        elif obj.retention_period == 30:
            return '1 Month'
        elif obj.retention_period == 90:
            return '3 Months'
        elif obj.retention_period == 180:
            return '6 Months'
        elif obj.retention_period == 365:
            return '1 Year'
        elif obj.retention_period == 730:
            return '2 Years'
        elif obj.retention_period == 1825:
            return '5 Years'
        elif obj.retention_period == 3650:
            return '10 Years'
        else:
            return f'{obj.retention_period} Days'
    retention_period_display.short_description = 'Retention Period'
    
    readonly_fields = ['created_at', 'updated_at']
    
    actions = ['enable_policies', 'disable_policies']
    
    def enable_policies(self, request, queryset):
        """Enable selected policies"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} policies have been enabled.')
    enable_policies.short_description = 'Enable selected policies'
    
    def disable_policies(self, request, queryset):
        """Disable selected policies"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} policies have been disabled.')
    disable_policies.short_description = 'Disable selected policies'


# Customize admin site
admin.site.site_header = 'Log History Administration'
admin.site.site_title = 'Log History Admin'
admin.site.index_title = 'Log History Management'
