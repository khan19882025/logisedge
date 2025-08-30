from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import EmailConfiguration, EmailTestResult, EmailNotification


@admin.register(EmailConfiguration)
class EmailConfigurationAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'protocol', 'host', 'port', 'encryption', 
        'username', 'is_active', 'is_default', 'last_test_status',
        'last_tested', 'created_by', 'created_at'
    ]
    list_filter = [
        'protocol', 'encryption', 'is_active', 'is_default', 
        'last_test_status', 'use_authentication', 'created_at'
    ]
    search_fields = ['name', 'host', 'username', 'created_by__username']
    readonly_fields = ['created_by', 'created_at', 'updated_by', 'updated_at', 'last_tested', 'last_test_status', 'last_test_message']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'protocol', 'is_active', 'is_default')
        }),
        ('Server Settings', {
            'fields': ('host', 'port', 'encryption', 'timeout', 'max_connections')
        }),
        ('Authentication', {
            'fields': ('use_authentication', 'username', 'password')
        }),
        ('Incoming Email Settings', {
            'fields': ('delete_after_fetch', 'fetch_interval'),
            'classes': ('collapse',),
            'description': 'Settings for IMAP/POP3 configurations'
        }),
        ('Status & Testing', {
            'fields': ('last_test_status', 'last_test_message', 'last_tested'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by', 'updated_by')
    
    def test_configuration_link(self, obj):
        if obj.pk:
            url = reverse('email_configuration:test_configuration', args=[obj.pk])
            return format_html('<a href="{}" class="button">Test Configuration</a>', url)
        return '-'
    test_configuration_link.short_description = 'Test'
    
    actions = ['test_selected_configurations', 'activate_selected', 'deactivate_selected']
    
    def test_selected_configurations(self, request, queryset):
        # This would trigger testing for selected configurations
        count = queryset.count()
        self.message_user(request, f'Testing initiated for {count} configuration(s).')
    test_selected_configurations.short_description = "Test selected configurations"
    
    def activate_selected(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} configuration(s) activated successfully.')
    activate_selected.short_description = "Activate selected configurations"
    
    def deactivate_selected(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} configuration(s) deactivated successfully.')
    deactivate_selected.short_description = "Deactivate selected configurations"


@admin.register(EmailTestResult)
class EmailTestResultAdmin(admin.ModelAdmin):
    list_display = [
        'configuration', 'test_type', 'status', 'started_at', 
        'completed_at', 'duration', 'tested_by'
    ]
    list_filter = ['test_type', 'status', 'started_at', 'configuration__protocol']
    search_fields = ['configuration__name', 'test_message', 'error_details', 'tested_by__username']
    readonly_fields = ['configuration', 'test_type', 'started_at', 'completed_at', 'duration', 'tested_by']
    
    fieldsets = (
        ('Test Information', {
            'fields': ('configuration', 'test_type', 'status', 'started_at', 'completed_at', 'duration')
        }),
        ('Test Details', {
            'fields': ('test_message', 'error_details', 'stack_trace')
        }),
        ('Test Parameters', {
            'fields': ('test_email', 'test_subject'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('tested_by',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('configuration', 'tested_by')
    
    def has_add_permission(self, request):
        return False  # Test results are created automatically
    
    def has_change_permission(self, request, obj=None):
        return False  # Test results should not be modified


@admin.register(EmailNotification)
class EmailNotificationAdmin(admin.ModelAdmin):
    list_display = [
        'subject', 'type', 'priority', 'status', 'configuration',
        'created_by', 'created_at', 'scheduled_at', 'sent_at'
    ]
    list_filter = ['type', 'priority', 'status', 'created_at', 'scheduled_at']
    search_fields = ['subject', 'message', 'created_by__username', 'configuration__name']
    readonly_fields = ['created_by', 'created_at', 'retry_count', 'last_retry_at']
    
    fieldsets = (
        ('Notification Details', {
            'fields': ('type', 'priority', 'subject', 'message')
        }),
        ('Recipients', {
            'fields': ('recipients', 'cc_recipients', 'bcc_recipients')
        }),
        ('Configuration & Timing', {
            'fields': ('configuration', 'scheduled_at', 'sent_at')
        }),
        ('Status & Retries', {
            'fields': ('status', 'retry_count', 'max_retries', 'last_retry_at', 'error_message'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('configuration', 'created_by')
    
    def recipients_display(self, obj):
        if obj.recipients:
            return ', '.join(obj.recipients[:3]) + ('...' if len(obj.recipients) > 3 else '')
        return '-'
    recipients_display.short_description = 'Recipients'
    
    def can_retry(self, obj):
        return obj.is_retryable()
    can_retry.boolean = True
    can_retry.short_description = 'Can Retry'
    
    actions = ['resend_failed_notifications', 'cancel_pending_notifications']
    
    def resend_failed_notifications(self, request, queryset):
        failed_notifications = queryset.filter(status='failed')
        count = failed_notifications.count()
        failed_notifications.update(status='pending', retry_count=0)
        self.message_user(request, f'{count} failed notification(s) queued for retry.')
    resend_failed_notifications.short_description = "Resend failed notifications"
    
    def cancel_pending_notifications(self, request, queryset):
        pending_notifications = queryset.filter(status='pending')
        count = pending_notifications.count()
        pending_notifications.update(status='cancelled')
        self.message_user(request, f'{count} pending notification(s) cancelled.')
    cancel_pending_notifications.short_description = "Cancel pending notifications"
