from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    EmailTemplate, EmailCampaign, RecipientList, Recipient, 
    EmailTracking, EmailQueue, EmailSettings
)


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'template_type', 'subject', 'is_active', 
        'created_by', 'created_at', 'version'
    ]
    list_filter = ['template_type', 'is_active', 'created_at']
    search_fields = ['name', 'subject', 'description']
    readonly_fields = ['created_by', 'created_at', 'updated_at', 'version']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'subject', 'template_type', 'description', 'is_active')
        }),
        ('Content', {
            'fields': ('html_content', 'plain_text_content')
        }),
        ('Sender Information', {
            'fields': ('sender_name', 'sender_email', 'reply_to_email')
        }),
        ('Metadata', {
            'fields': ('tags', 'available_placeholders')
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at', 'version'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(EmailCampaign)
class EmailCampaignAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'status', 'priority', 'template', 'total_recipients_display',
        'sent_count_display', 'delivery_rate_display', 'open_rate_display',
        'created_by', 'created_at'
    ]
    list_filter = ['status', 'priority', 'template', 'created_at', 'scheduled_at']
    search_fields = ['name', 'description']
    readonly_fields = [
        'created_by', 'created_at', 'updated_at', 'started_at', 'completed_at',
        'total_recipients', 'sent_count', 'delivered_count'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'template', 'status', 'priority')
        }),
        ('Sending Configuration', {
            'fields': ('sender_name', 'sender_email', 'reply_to_email')
        }),
        ('Scheduling & Throttling', {
            'fields': ('scheduled_at', 'send_speed', 'batch_size')
        }),
        ('Campaign Metadata', {
            'fields': ('tags', 'category')
        }),
        ('Tracking Settings', {
            'fields': ('track_opens', 'track_clicks', 'track_unsubscribes')
        }),
        ('Compliance', {
            'fields': ('include_unsubscribe_link', 'unsubscribe_text')
        }),
                       ('Statistics', {
                   'fields': ('total_recipients', 'sent_count', 'delivered_count'),
                   'classes': ('collapse',)
               }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at', 'started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def total_recipients_display(self, obj):
        return obj.total_recipients
    total_recipients_display.short_description = 'Total Recipients'
    
    def sent_count_display(self, obj):
        return obj.sent_count
    sent_count_display.short_description = 'Sent'
    
    def delivery_rate_display(self, obj):
        if obj.total_recipients > 0:
            rate = (obj.delivered_count / obj.total_recipients) * 100
            return f"{rate:.1f}%"
        return "0%"
    delivery_rate_display.short_description = 'Delivery Rate'
    
    def open_rate_display(self, obj):
        # Calculate open rate manually since it's a property
        total_sent = obj.sent_count
        if total_sent == 0:
            return "0.0%"
        opened_count = obj.recipients.filter(tracked_opens__isnull=False).distinct().count()
        open_rate = (opened_count / total_sent) * 100
        return f"{open_rate:.1f}%"
    open_rate_display.short_description = 'Open Rate'
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(RecipientList)
class RecipientListAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'list_type', 'total_recipients_display', 
        'created_by', 'created_at'
    ]
    list_filter = ['list_type', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_by', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'list_type')
        }),
        ('Source Configuration', {
            'fields': ('source_file', 'query_model', 'query_filters')
        }),
        ('Metadata', {
            'fields': ('tags', 'category')
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def total_recipients_display(self, obj):
        return obj.recipients.count()
    total_recipients_display.short_description = 'Total Recipients'
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    list_display = [
        'email', 'campaign_link', 'status', 'full_name', 
        'sent_at', 'opened_at', 'clicked_at'
    ]
    list_filter = ['status', 'campaign', 'created_at', 'sent_at']
    search_fields = ['email', 'first_name', 'last_name', 'campaign__name']
    readonly_fields = [
        'campaign', 'recipient_list', 'created_at', 'updated_at',
        'sent_at', 'delivered_at', 'opened_at', 'clicked_at'
    ]
    fieldsets = (
        ('Recipient Information', {
            'fields': ('email', 'first_name', 'last_name', 'full_name')
        }),
        ('Campaign Information', {
            'fields': ('campaign', 'recipient_list')
        }),
        ('Status & Tracking', {
            'fields': ('status', 'message_id', 'tracking_id')
        }),
        ('Timing', {
            'fields': ('sent_at', 'delivered_at', 'opened_at', 'clicked_at')
        }),
        ('Custom Fields', {
            'fields': ('custom_fields',)
        }),
        ('Error Handling', {
            'fields': ('error_message', 'retry_count', 'max_retries')
        }),
        ('Compliance', {
            'fields': ('is_unsubscribed', 'unsubscribe_date')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def campaign_link(self, obj):
        if obj.campaign:
            url = reverse('admin:bulk_email_sender_emailcampaign_change', args=[obj.campaign.pk])
            return format_html('<a href="{}">{}</a>', url, obj.campaign.name)
        return '-'
    campaign_link.short_description = 'Campaign'
    
    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'Full Name'


@admin.register(EmailTracking)
class EmailTrackingAdmin(admin.ModelAdmin):
    list_display = [
        'recipient_email', 'campaign_name', 'tracking_type', 
        'timestamp', 'ip_address'
    ]
    list_filter = ['tracking_type', 'timestamp']
    search_fields = ['recipient__email', 'recipient__campaign__name']
    readonly_fields = ['recipient', 'timestamp']
    fieldsets = (
        ('Tracking Information', {
            'fields': ('recipient', 'tracking_type', 'timestamp')
        }),
        ('Event Details', {
            'fields': ('clicked_url', 'link_text', 'bounce_type', 'bounce_reason')
        }),
        ('Technical Details', {
            'fields': ('ip_address', 'user_agent', 'location_data')
        }),
        ('Additional Data', {
            'fields': ('metadata',)
        }),
    )
    
    def recipient_email(self, obj):
        return obj.recipient.email
    recipient_email.short_description = 'Recipient Email'
    
    def campaign_name(self, obj):
        return obj.recipient.campaign.name
    campaign_name.short_description = 'Campaign'


@admin.register(EmailQueue)
class EmailQueueAdmin(admin.ModelAdmin):
    list_display = [
        'campaign_name', 'batch_number', 'status', 'total_emails',
        'sent_emails', 'failed_emails', 'created_at'
    ]
    list_filter = ['status', 'campaign', 'created_at']
    search_fields = ['campaign__name']
    readonly_fields = ['campaign', 'batch_number', 'created_at']
    fieldsets = (
        ('Queue Information', {
            'fields': ('campaign', 'batch_number', 'status')
        }),
        ('Batch Details', {
            'fields': ('total_emails', 'sent_emails', 'failed_emails')
        }),
        ('Timing', {
            'fields': ('created_at', 'started_at', 'completed_at')
        }),
        ('Error Handling', {
            'fields': ('error_message', 'retry_count')
        }),
    )
    
    def campaign_name(self, obj):
        return obj.campaign.name
    campaign_name.short_description = 'Campaign'


@admin.register(EmailSettings)
class EmailSettingsAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'provider', 'is_active', 'daily_limit', 
        'hourly_limit', 'rate_limit', 'created_by'
    ]
    list_filter = ['provider', 'is_active', 'created_at']
    search_fields = ['name', 'provider']
    readonly_fields = ['created_by', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'is_active', 'provider')
        }),
        ('SMTP Configuration', {
            'fields': (
                'smtp_host', 'smtp_port', 'smtp_username', 'smtp_password',
                'smtp_use_tls', 'smtp_use_ssl'
            ),
            'classes': ('collapse',)
        }),
        ('API Configuration', {
            'fields': ('api_key', 'api_secret', 'api_url'),
            'classes': ('collapse',)
        }),
        ('Sending Limits', {
            'fields': ('daily_limit', 'hourly_limit', 'rate_limit')
        }),
        ('Default Settings', {
            'fields': ('default_sender_name', 'default_sender_email', 'default_reply_to')
        }),
        ('DNS Configuration', {
            'fields': ('spf_record', 'dkim_private_key', 'dkim_selector', 'dmarc_policy'),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_fieldsets(self, request, obj=None):
        """Show only relevant fields based on provider selection"""
        fieldsets = super().get_fieldsets(request, obj)
        
        if obj and obj.provider == 'smtp':
            # Show SMTP fields, hide API fields
            for fieldset in fieldsets:
                if fieldset[0] == 'API Configuration':
                    fieldset[1]['classes'] = ('collapse',)
                elif fieldset[0] == 'SMTP Configuration':
                    fieldset[1]['classes'] = ()
        elif obj and obj.provider in ['sendgrid', 'mailgun', 'amazon_ses', 'postmark']:
            # Show API fields, hide SMTP fields
            for fieldset in fieldsets:
                if fieldset[0] == 'SMTP Configuration':
                    fieldset[1]['classes'] = ('collapse',)
                elif fieldset[0] == 'API Configuration':
                    fieldset[1]['classes'] = ()
        
        return fieldsets


# Customize admin site
admin.site.site_header = 'Bulk Email Sender Administration'
admin.site.site_title = 'Bulk Email Sender Admin'
admin.site.index_title = 'Welcome to Bulk Email Sender Administration'
