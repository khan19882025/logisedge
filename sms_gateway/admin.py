from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import SMSGateway, SMSTestResult, SMSMessage, SMSDeliveryLog, SMSGatewayHealth


@admin.register(SMSGateway)
class SMSGatewayAdmin(admin.ModelAdmin):
    """Admin interface for SMS Gateway"""
    
    list_display = [
        'name', 'gateway_type', 'is_active', 'sender_id', 
        'last_test_status', 'last_tested', 'created_at'
    ]
    
    list_filter = [
        'gateway_type', 'is_active', 'last_test_status', 
        'encryption', 'support_unicode', 'created_at'
    ]
    
    search_fields = ['name', 'sender_id', 'api_url']
    
    readonly_fields = [
        'created_at', 'updated_at', 'last_tested', 
        'last_test_status', 'created_by', 'updated_by'
    ]
    
    fieldsets = (
        ('Basic Configuration', {
            'fields': ('name', 'gateway_type', 'is_active')
        }),
        ('API Credentials', {
            'fields': ('api_key', 'api_secret', 'username', 'sender_id'),
            'classes': ('collapse',)
        }),
        ('API Endpoint', {
            'fields': ('api_url', 'http_method', 'encryption')
        }),
        ('Connection Settings', {
            'fields': ('timeout', 'max_retries'),
            'classes': ('collapse',)
        }),
        ('Message Settings', {
            'fields': ('default_encoding', 'max_message_length', 'support_unicode')
        }),
        ('Rate Limiting', {
            'fields': ('rate_limit_per_second', 'rate_limit_per_minute', 'rate_limit_per_hour'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('last_tested', 'last_test_status'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        else:  # Existing object
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by', 'updated_by')
    
    def test_gateway(self, request, queryset):
        """Admin action to test selected gateways"""
        for gateway in queryset:
            # This would trigger the actual test logic
            pass
        self.message_user(request, f"Testing initiated for {queryset.count()} gateway(s)")
    
    test_gateway.short_description = "Test selected gateways"
    
    actions = ['test_gateway']


@admin.register(SMSTestResult)
class SMSTestResultAdmin(admin.ModelAdmin):
    """Admin interface for SMS Test Results"""
    
    list_display = [
        'test_id', 'gateway', 'test_type', 'status', 'success', 
        'recipient_number', 'response_time', 'started_at'
    ]
    
    list_filter = [
        'test_type', 'status', 'success', 'test_environment', 
        'started_at', 'gateway'
    ]
    
    search_fields = ['test_id', 'gateway__name', 'recipient_number', 'test_message']
    
    readonly_fields = [
        'test_id', 'started_at', 'completed_at', 'response_time',
        'message_id', 'delivery_status'
    ]
    
    fieldsets = (
        ('Test Information', {
            'fields': ('test_id', 'test_type', 'status', 'success')
        }),
        ('Gateway & Configuration', {
            'fields': ('gateway', 'test_environment', 'executed_by')
        }),
        ('Test Parameters', {
            'fields': ('test_message', 'recipient_number', 'message_encoding')
        }),
        ('Results', {
            'fields': ('response_code', 'response_message', 'error_message')
        }),
        ('Performance', {
            'fields': ('response_time', 'message_id', 'delivery_status')
        }),
        ('Timestamps', {
            'fields': ('started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('gateway', 'executed_by')
    
    def has_add_permission(self, request):
        return False  # Test results are created by the system, not manually


@admin.register(SMSMessage)
class SMSMessageAdmin(admin.ModelAdmin):
    """Admin interface for SMS Messages"""
    
    list_display = [
        'message_id', 'recipient_number', 'gateway', 'delivery_status', 
        'priority', 'message_length', 'created_at'
    ]
    
    list_filter = [
        'delivery_status', 'priority', 'gateway', 'created_at', 'sent_at'
    ]
    
    search_fields = ['message_id', 'recipient_number', 'message_content', 'gateway__name']
    
    readonly_fields = [
        'message_id', 'external_message_id', 'message_length', 
        'created_at', 'updated_at', 'sent_at', 'delivered_at',
        'delivery_attempts', 'created_by'
    ]
    
    fieldsets = (
        ('Message Information', {
            'fields': ('message_id', 'external_message_id', 'priority')
        }),
        ('Content', {
            'fields': ('message_content', 'message_encoding', 'message_length')
        }),
        ('Recipients', {
            'fields': ('recipient_number', 'sender_id')
        }),
        ('Gateway & Delivery', {
            'fields': ('gateway', 'delivery_status', 'delivery_attempts')
        }),
        ('Scheduling', {
            'fields': ('scheduled_at', 'expires_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('sent_at', 'delivered_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Response & Errors', {
            'fields': ('response_code', 'response_message', 'error_message', 'error_code'),
            'classes': ('collapse',)
        }),
        ('Cost & Billing', {
            'fields': ('cost', 'currency'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('category', 'tags', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('gateway', 'created_by')
    
    def has_add_permission(self, request):
        return False  # Messages are created by the system, not manually
    
    def resend_message(self, request, queryset):
        """Admin action to resend failed messages"""
        count = 0
        for message in queryset.filter(delivery_status__in=['failed', 'expired', 'rejected']):
            # Reset delivery status and attempt resend
            message.delivery_status = 'pending'
            message.delivery_attempts = 0
            message.save()
            count += 1
        
        if count > 0:
            self.message_user(request, f"Resend initiated for {count} message(s)")
        else:
            self.message_user(request, "No failed messages to resend")
    
    resend_message.short_description = "Resend failed messages"
    
    actions = ['resend_message']


@admin.register(SMSDeliveryLog)
class SMSDeliveryLogAdmin(admin.ModelAdmin):
    """Admin interface for SMS Delivery Logs"""
    
    list_display = [
        'log_id', 'message', 'status', 'status_code', 'timestamp'
    ]
    
    list_filter = ['status', 'timestamp', 'message__gateway']
    
    search_fields = ['log_id', 'message__recipient_number', 'status_message']
    
    readonly_fields = [
        'log_id', 'timestamp', 'gateway_response', 'error_details'
    ]
    
    fieldsets = (
        ('Log Information', {
            'fields': ('log_id', 'message', 'status', 'status_code')
        }),
        ('Details', {
            'fields': ('status_message', 'gateway_response', 'error_details')
        }),
        ('Timestamp', {
            'fields': ('timestamp',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('message', 'message__gateway')
    
    def has_add_permission(self, request):
        return False  # Delivery logs are created by the system, not manually


@admin.register(SMSGatewayHealth)
class SMSGatewayHealthAdmin(admin.ModelAdmin):
    """Admin interface for SMS Gateway Health"""
    
    list_display = [
        'gateway', 'is_healthy', 'response_time', 'success_rate', 
        'error_rate', 'rate_limit_status', 'recorded_at'
    ]
    
    list_filter = [
        'is_healthy', 'rate_limit_status', 'recorded_at', 'gateway'
    ]
    
    search_fields = ['gateway__name']
    
    readonly_fields = [
        'recorded_at'
    ]
    
    fieldsets = (
        ('Health Status', {
            'fields': ('gateway', 'is_healthy', 'rate_limit_status')
        }),
        ('Performance Metrics', {
            'fields': ('response_time', 'success_rate', 'error_rate')
        }),
        ('System Metrics', {
            'fields': ('cpu_usage', 'memory_usage', 'active_connections'),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('recorded_at',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('gateway')
    
    def has_add_permission(self, request):
        return False  # Health records are created by the system, not manually


# Customize admin site
admin.site.site_header = "SMS Gateway Administration"
admin.site.site_title = "SMS Gateway Admin"
admin.site.index_title = "SMS Gateway Management"
