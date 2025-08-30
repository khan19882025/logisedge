import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class EmailTemplate(models.Model):
    """Email template with HTML and plain text versions"""
    
    TEMPLATE_TYPES = [
        ('newsletter', 'Newsletter'),
        ('promotional', 'Promotional'),
        ('transactional', 'Transactional'),
        ('notification', 'Notification'),
        ('custom', 'Custom'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, help_text="Template name")
    subject = models.CharField(max_length=255, help_text="Email subject line")
    html_content = models.TextField(help_text="HTML email content")
    plain_text_content = models.TextField(help_text="Plain text email content")
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES, default='custom')
    
    # Template metadata
    description = models.TextField(blank=True, help_text="Template description")
    tags = models.JSONField(default=list, blank=True, help_text="Template tags")
    is_active = models.BooleanField(default=True, help_text="Template availability")
    
    # Placeholder variables
    available_placeholders = models.JSONField(
        default=list, 
        blank=True, 
        help_text="Available placeholder variables (e.g., {{customer_name}})"
    )
    
    # Template settings
    sender_name = models.CharField(max_length=100, blank=True, help_text="Default sender name")
    sender_email = models.EmailField(blank=True, help_text="Default sender email")
    reply_to_email = models.EmailField(blank=True, help_text="Reply-to email address")
    
    # Audit fields
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_templates_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    version = models.PositiveIntegerField(default=1, help_text="Template version")
    
    class Meta:
        verbose_name = 'Email Template'
        verbose_name_plural = 'Email Templates'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} (v{self.version})"
    
    def get_placeholder_list(self):
        """Extract placeholders from content"""
        import re
        html_placeholders = re.findall(r'\{\{(\w+)\}\}', self.html_content)
        text_placeholders = re.findall(r'\{\{(\w+)\}\}', self.plain_text_content)
        return list(set(html_placeholders + text_placeholders))


class EmailCampaign(models.Model):
    """Email campaign configuration and settings"""
    
    CAMPAIGN_STATUS = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('queued', 'Queued'),
        ('sending', 'Sending'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, help_text="Campaign name")
    description = models.TextField(blank=True, help_text="Campaign description")
    
    # Campaign settings
    template = models.ForeignKey(EmailTemplate, on_delete=models.CASCADE, related_name='campaigns')
    status = models.CharField(max_length=20, choices=CAMPAIGN_STATUS, default='draft')
    priority = models.CharField(max_length=20, choices=PRIORITY_LEVELS, default='normal')
    
    # Sending configuration
    sender_name = models.CharField(max_length=100, help_text="Campaign sender name")
    sender_email = models.EmailField(help_text="Campaign sender email")
    reply_to_email = models.EmailField(blank=True, help_text="Reply-to email address")
    
    # Scheduling and throttling
    scheduled_at = models.DateTimeField(null=True, blank=True, help_text="When to start sending")
    send_speed = models.PositiveIntegerField(
        default=100, 
        validators=[MinValueValidator(1), MaxValueValidator(10000)],
        help_text="Emails per minute"
    )
    batch_size = models.PositiveIntegerField(
        default=1000,
        validators=[MinValueValidator(1), MaxValueValidator(10000)],
        help_text="Emails per batch"
    )
    
    # Campaign metadata
    tags = models.JSONField(default=list, blank=True, help_text="Campaign tags")
    category = models.CharField(max_length=100, blank=True, help_text="Campaign category")
    
    # Tracking settings
    track_opens = models.BooleanField(default=True, help_text="Track email opens")
    track_clicks = models.BooleanField(default=True, help_text="Track link clicks")
    track_unsubscribes = models.BooleanField(default=True, help_text="Track unsubscribes")
    
    # Compliance
    include_unsubscribe_link = models.BooleanField(default=True, help_text="Include unsubscribe link")
    unsubscribe_text = models.CharField(
        max_length=200, 
        default="Unsubscribe",
        help_text="Unsubscribe link text"
    )
    
    # Audit fields
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='campaigns_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Email Campaign'
        verbose_name_plural = 'Email Campaigns'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    @property
    def total_recipients(self):
        return self.recipients.count()
    
    @property
    def sent_count(self):
        return self.recipients.filter(status='sent').count()
    
    @property
    def delivered_count(self):
        return self.recipients.filter(status='delivered').count()
    
    @property
    def failed_count(self):
        return self.recipients.filter(status='failed').count()
    
    @property
    def open_rate(self):
        total_sent = self.sent_count
        if total_sent == 0:
            return 0
        opened_count = self.recipients.filter(tracked_opens__isnull=False).distinct().count()
        return (opened_count / total_sent) * 100


class RecipientList(models.Model):
    """List of recipients for email campaigns"""
    
    LIST_TYPES = [
        ('csv_upload', 'CSV Upload'),
        ('database_query', 'Database Query'),
        ('manual_entry', 'Manual Entry'),
        ('api_import', 'API Import'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, help_text="Recipient list name")
    description = models.TextField(blank=True, help_text="List description")
    
    # List configuration
    list_type = models.CharField(max_length=20, choices=LIST_TYPES, default='csv_upload')
    source_file = models.FileField(upload_to='recipient_lists/', blank=True, null=True, help_text="Uploaded CSV/Excel file")
    
    # Database query settings (for database_query type)
    query_model = models.CharField(max_length=100, blank=True, help_text="Django model name for query")
    query_filters = models.JSONField(default=dict, blank=True, help_text="Query filters")
    
    # List metadata
    tags = models.JSONField(default=list, blank=True, help_text="List tags")
    category = models.CharField(max_length=100, blank=True, help_text="List category")
    
    # Audit fields
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipient_lists_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Recipient List'
        verbose_name_plural = 'Recipient Lists'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_list_type_display()})"


class Recipient(models.Model):
    """Individual recipient for email campaigns"""
    
    RECIPIENT_STATUS = [
        ('pending', 'Pending'),
        ('queued', 'Queued'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
        ('bounced', 'Bounced'),
        ('failed', 'Failed'),
        ('unsubscribed', 'Unsubscribed'),
        ('spam', 'Marked as Spam'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(EmailCampaign, on_delete=models.CASCADE, related_name='recipients')
    recipient_list = models.ForeignKey(RecipientList, on_delete=models.CASCADE, related_name='recipients', null=True, blank=True)
    
    # Recipient information
    email = models.EmailField(help_text="Recipient email address")
    first_name = models.CharField(max_length=100, blank=True, help_text="Recipient first name")
    last_name = models.CharField(max_length=100, blank=True, help_text="Recipient last name")
    
    # Custom fields (stored as JSON)
    custom_fields = models.JSONField(default=dict, blank=True, help_text="Custom recipient fields")
    
    # Email status
    status = models.CharField(max_length=20, choices=RECIPIENT_STATUS, default='pending')
    
    # Sending details
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    
    # Tracking data
    message_id = models.CharField(max_length=255, blank=True, help_text="Email message ID")
    tracking_id = models.CharField(max_length=255, blank=True, help_text="Tracking identifier")
    
    # Error handling
    error_message = models.TextField(blank=True, help_text="Error details if sending failed")
    retry_count = models.PositiveIntegerField(default=0, help_text="Number of retry attempts")
    max_retries = models.PositiveIntegerField(default=3, help_text="Maximum retry attempts")
    
    # Compliance
    is_unsubscribed = models.BooleanField(default=False, help_text="Recipient unsubscribed")
    unsubscribe_date = models.DateTimeField(null=True, blank=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Recipient'
        verbose_name_plural = 'Recipients'
        ordering = ['-created_at']
        unique_together = ['campaign', 'email']
    
    def __str__(self):
        return f"{self.email} - {self.campaign.name}"
    
    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.email


class EmailTracking(models.Model):
    """Detailed tracking information for emails"""
    
    TRACKING_TYPES = [
        ('open', 'Email Open'),
        ('click', 'Link Click'),
        ('bounce', 'Bounce'),
        ('unsubscribe', 'Unsubscribe'),
        ('spam', 'Spam Report'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(Recipient, on_delete=models.CASCADE, related_name='tracking_events')
    
    # Tracking details
    tracking_type = models.CharField(max_length=20, choices=TRACKING_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Event-specific data
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="IP address of the event")
    user_agent = models.TextField(blank=True, help_text="User agent string")
    location_data = models.JSONField(default=dict, blank=True, help_text="Geographic location data")
    
    # Click tracking
    clicked_url = models.URLField(blank=True, help_text="URL that was clicked")
    link_text = models.CharField(max_length=255, blank=True, help_text="Text of the clicked link")
    
    # Bounce details
    bounce_type = models.CharField(max_length=50, blank=True, help_text="Type of bounce (hard/soft)")
    bounce_reason = models.TextField(blank=True, help_text="Reason for bounce")
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional tracking metadata")
    
    class Meta:
        verbose_name = 'Email Tracking'
        verbose_name_plural = 'Email Tracking'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.recipient.email} - {self.get_tracking_type_display()} at {self.timestamp}"


class EmailQueue(models.Model):
    """Queue for managing email sending batches"""
    
    QUEUE_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(EmailCampaign, on_delete=models.CASCADE, related_name='queues')
    
    # Queue configuration
    batch_number = models.PositiveIntegerField(help_text="Batch sequence number")
    status = models.CharField(max_length=20, choices=QUEUE_STATUS, default='pending')
    
    # Batch details
    total_emails = models.PositiveIntegerField(help_text="Total emails in this batch")
    sent_emails = models.PositiveIntegerField(default=0, help_text="Successfully sent emails")
    failed_emails = models.PositiveIntegerField(default=0, help_text="Failed emails")
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Error handling
    error_message = models.TextField(blank=True, help_text="Batch error details")
    retry_count = models.PositiveIntegerField(default=0, help_text="Number of retry attempts")
    
    class Meta:
        verbose_name = 'Email Queue'
        verbose_name_plural = 'Email Queues'
        ordering = ['campaign', 'batch_number']
        unique_together = ['campaign', 'batch_number']
    
    def __str__(self):
        return f"Batch {self.batch_number} - {self.campaign.name}"


class EmailSettings(models.Model):
    """Global email configuration settings"""
    
    PROVIDER_CHOICES = [
        ('smtp', 'SMTP'),
        ('sendgrid', 'SendGrid'),
        ('mailgun', 'Mailgun'),
        ('amazon_ses', 'Amazon SES'),
        ('postmark', 'Postmark'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, help_text="Configuration name")
    is_active = models.BooleanField(default=True, help_text="Active configuration")
    
    # Provider settings
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default='smtp')
    
    # SMTP settings
    smtp_host = models.CharField(max_length=255, blank=True, help_text="SMTP server host")
    smtp_port = models.PositiveIntegerField(default=587, help_text="SMTP server port")
    smtp_username = models.CharField(max_length=255, blank=True, help_text="SMTP username")
    smtp_password = models.CharField(max_length=255, blank=True, help_text="SMTP password")
    smtp_use_tls = models.BooleanField(default=True, help_text="Use TLS encryption")
    smtp_use_ssl = models.BooleanField(default=False, help_text="Use SSL encryption")
    
    # API settings
    api_key = models.CharField(max_length=255, blank=True, help_text="API key for service")
    api_secret = models.CharField(max_length=255, blank=True, help_text="API secret for service")
    api_url = models.URLField(blank=True, help_text="API endpoint URL")
    
    # Sending limits
    daily_limit = models.PositiveIntegerField(default=10000, help_text="Daily sending limit")
    hourly_limit = models.PositiveIntegerField(default=1000, help_text="Hourly sending limit")
    rate_limit = models.PositiveIntegerField(default=100, help_text="Emails per minute")
    
    # Compliance settings
    default_sender_name = models.CharField(max_length=100, blank=True, help_text="Default sender name")
    default_sender_email = models.EmailField(blank=True, help_text="Default sender email")
    default_reply_to = models.EmailField(blank=True, help_text="Default reply-to email")
    
    # SPF, DKIM, DMARC settings
    spf_record = models.TextField(blank=True, help_text="SPF record configuration")
    dkim_private_key = models.TextField(blank=True, help_text="DKIM private key")
    dkim_selector = models.CharField(max_length=100, blank=True, help_text="DKIM selector")
    dmarc_policy = models.CharField(max_length=100, blank=True, help_text="DMARC policy")
    
    # Audit fields
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_settings_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Email Settings'
        verbose_name_plural = 'Email Settings'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_provider_display()})"
