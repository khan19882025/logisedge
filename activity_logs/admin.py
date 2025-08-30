from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    ActivityLog, AuditTrail, SecurityEvent, ComplianceReport, 
    RetentionPolicy, AlertRule
)


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'activity_type', 'log_level', 'user_ip', 
        'timestamp', 'module', 'data_hash_short'
    ]
    list_filter = [
        'activity_type', 'log_level', 'module', 'timestamp', 'user'
    ]
    search_fields = [
        'description', 'user__username', 'user__email', 'user_ip'
    ]
    readonly_fields = [
        'id', 'data_hash', 'timestamp'
    ]
    date_hierarchy = 'timestamp'
    list_per_page = 50
    
    def data_hash_short(self, obj):
        if obj.data_hash:
            return format_html(
                '<code title="{}">{}</code>',
                obj.data_hash,
                obj.data_hash[:16] + '...'
            )
        return '-'
    data_hash_short.short_description = 'Data Hash'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'activity_type', 'log_level', 'action', 'description')
        }),
        ('Context', {
            'fields': ('module', 'content_type', 'object_id', 'user_ip', 'user_agent')
        }),
        ('Data Changes', {
            'fields': ('old_values', 'new_values', 'data_hash'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('timestamp', 'metadata', 'tags'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AuditTrail)
class AuditTrailAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'trail_name', 'trail_type', 'start_date', 
        'content_type', 'object_id', 'description_short'
    ]
    list_filter = [
        'trail_type', 'start_date', 'content_type'
    ]
    search_fields = [
        'trail_name', 'description', 'content_type__model'
    ]
    readonly_fields = [
        'id', 'start_date'
    ]
    date_hierarchy = 'start_date'
    list_per_page = 50
    
    def description_short(self, obj):
        if obj.description:
            return format_html(
                '<span title="{}">{}</span>',
                obj.description,
                obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
            )
        return '-'
    description_short.short_description = 'Description'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('content_type')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('trail_name', 'trail_type', 'description')
        }),
        ('Object Information', {
            'fields': ('content_type', 'object_id')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('timestamp', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'event_type', 'severity', 'user', 'source_ip', 
        'timestamp', 'is_resolved', 'title_short'
    ]
    list_filter = [
        'event_type', 'severity', 'is_resolved', 
        'timestamp', 'user'
    ]
    search_fields = [
        'title', 'description', 'user__username', 'source_ip', 'event_type'
    ]
    readonly_fields = [
        'id', 'timestamp'
    ]
    date_hierarchy = 'timestamp'
    list_per_page = 50
    actions = ['mark_as_resolved', 'escalate_event']
    
    def title_short(self, obj):
        if obj.title:
            return format_html(
                '<span title="{}">{}</span>',
                obj.title,
                obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
            )
        return '-'
    title_short.short_description = 'Title'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    @admin.action(description='Mark selected events as resolved')
    def mark_as_resolved(self, request, queryset):
        updated = queryset.update(is_resolved=True)
        self.message_user(request, f'{updated} security events marked as resolved.')
    
    @admin.action(description='Escalate selected events')
    def escalate_event(self, request, queryset):
        updated = queryset.update(severity='CRITICAL')
        self.message_user(request, f'{updated} security events escalated.')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('event_type', 'severity', 'title', 'description')
        }),
        ('User and Source', {
            'fields': ('user', 'source_ip', 'source_location')
        }),
        ('Event Details', {
            'fields': ('details', 'is_resolved', 'resolution_notes'),
            'classes': ('collapse',)
        }),
        ('Response', {
            'fields': ('resolved_by', 'resolved_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ComplianceReport)
class ComplianceReportAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'report_type', 'start_date', 'end_date', 
        'is_approved', 'generated_by', 'generated_at'
    ]
    list_filter = [
        'report_type', 'is_approved', 'generated_at', 'generated_by'
    ]
    search_fields = [
        'report_name', 'report_summary', 'generated_by__username'
    ]
    readonly_fields = [
        'id', 'generated_at'
    ]
    date_hierarchy = 'generated_at'
    list_per_page = 50
    actions = ['regenerate_report', 'approve_report']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('generated_by')
    
    @admin.action(description='Approve selected reports')
    def approve_report(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} reports approved.')
    
    fieldsets = (
        ('Report Information', {
            'fields': ('report_name', 'report_type', 'start_date', 'end_date')
        }),
        ('Content', {
            'fields': ('report_data', 'report_summary'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('status', 'generated_by', 'approved_by', 'approval_notes'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('generated_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(RetentionPolicy)
class RetentionPolicyAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'name', 'policy_type', 'retention_period_days', 
        'archive_after_days', 'is_active'
    ]
    list_filter = [
        'policy_type', 'is_active', 'created_at'
    ]
    search_fields = [
        'name', 'description', 'policy_type'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at'
    ]
    list_per_page = 50
    
    def get_queryset(self, request):
        return super().get_queryset(request)
    
    fieldsets = (
        ('Policy Information', {
            'fields': ('name', 'description', 'data_type')
        }),
        ('Retention Settings', {
            'fields': ('retention_period', 'retention_unit', 'archive_enabled')
        }),
        ('Advanced Settings', {
            'fields': ('encryption_required', 'compression_enabled', 'is_active'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'name', 'trigger_type', 'alert_type', 'is_active', 
        'notification_channels', 'created_at'
    ]
    list_filter = [
        'trigger_type', 'alert_type', 'is_active', 'created_at'
    ]
    search_fields = [
        'name', 'description', 'trigger_type'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at'
    ]
    list_per_page = 50
    actions = ['activate_rules', 'deactivate_rules']
    
    def notification_channels(self, obj):
        if obj.alert_type == 'EMAIL':
            return 'Email'
        elif obj.alert_type == 'SMS':
            return 'SMS'
        elif obj.alert_type == 'WEBHOOK':
            return 'Webhook'
        elif obj.alert_type == 'DASHBOARD':
            return 'Dashboard'
        elif obj.alert_type == 'SLACK':
            return 'Slack'
        elif obj.alert_type == 'TEAMS':
            return 'Teams'
        return obj.alert_type
    notification_channels.short_description = 'Notification Channel'
    
    def get_queryset(self, request):
        return super().get_queryset(request)
    
    @admin.action(description='Activate selected rules')
    def activate_rules(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} alert rules activated.')
    
    @admin.action(description='Deactivate selected rules')
    def deactivate_rules(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} alert rules deactivated.')
    
    fieldsets = (
        ('Rule Information', {
            'fields': ('name', 'description', 'rule_type', 'severity')
        }),
        ('Conditions', {
            'fields': ('conditions', 'threshold', 'time_window'),
            'classes': ('collapse',)
        }),
        ('Notifications', {
            'fields': ('email_enabled', 'sms_enabled', 'webhook_enabled', 'webhook_url'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Customize admin site
admin.site.site_header = 'Activity Logs & Audit Trail Administration'
admin.site.site_title = 'Activity Logs Admin'
admin.site.index_title = 'Welcome to Activity Logs Administration'
