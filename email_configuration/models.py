from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class EmailConfiguration(models.Model):
    """Email configuration settings for the ERP system"""
    
    ENCRYPTION_CHOICES = [
        ('none', 'None'),
        ('ssl', 'SSL'),
        ('tls', 'TLS'),
        ('starttls', 'STARTTLS'),
    ]
    
    PROTOCOL_CHOICES = [
        ('smtp', 'SMTP'),
        ('imap', 'IMAP'),
        ('pop3', 'POP3'),
    ]
    
    name = models.CharField(max_length=100, help_text="Configuration name (e.g., Primary SMTP, Backup SMTP)")
    protocol = models.CharField(max_length=10, choices=PROTOCOL_CHOICES, default='smtp')
    host = models.CharField(max_length=255, help_text="Email server hostname or IP address")
    port = models.IntegerField(help_text="Email server port number")
    encryption = models.CharField(max_length=10, choices=ENCRYPTION_CHOICES, default='tls')
    username = models.CharField(max_length=255, help_text="Email server username")
    password = models.CharField(max_length=255, help_text="Email server password")
    use_authentication = models.BooleanField(default=True, help_text="Whether to use authentication")
    timeout = models.IntegerField(default=30, help_text="Connection timeout in seconds")
    max_connections = models.IntegerField(default=10, help_text="Maximum concurrent connections")
    
    # Additional settings for incoming email
    delete_after_fetch = models.BooleanField(default=False, help_text="Delete emails after fetching (POP3)")
    fetch_interval = models.IntegerField(default=5, help_text="Fetch interval in minutes")
    
    # Status and metadata
    is_active = models.BooleanField(default=True, help_text="Whether this configuration is active")
    is_default = models.BooleanField(default=False, help_text="Whether this is the default configuration")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_configs_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_configs_updated')
    updated_at = models.DateTimeField(auto_now=True)
    
    # Test results
    last_tested = models.DateTimeField(null=True, blank=True)
    last_test_status = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('untested', 'Untested'),
    ], default='untested')
    last_test_message = models.TextField(blank=True, help_text="Last test result message")
    
    class Meta:
        verbose_name = 'Email Configuration'
        verbose_name_plural = 'Email Configurations'
        ordering = ['-is_default', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.protocol.upper()})"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Ensure only one default configuration per protocol
        if self.is_default:
            EmailConfiguration.objects.filter(
                protocol=self.protocol,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class EmailTestResult(models.Model):
    """Results of email configuration tests"""
    
    TEST_TYPE_CHOICES = [
        ('connection', 'Connection Test'),
        ('authentication', 'Authentication Test'),
        ('send_test', 'Send Test Email'),
        ('receive_test', 'Receive Test Email'),
        ('full_test', 'Full Configuration Test'),
    ]
    
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('partial', 'Partial Success'),
        ('timeout', 'Timeout'),
        ('error', 'Error'),
    ]
    
    configuration = models.ForeignKey(EmailConfiguration, on_delete=models.CASCADE, related_name='test_results')
    test_type = models.CharField(max_length=20, choices=TEST_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration = models.FloatField(null=True, blank=True, help_text="Test duration in seconds")
    
    # Test details
    test_message = models.TextField(blank=True, help_text="Detailed test message")
    error_details = models.TextField(blank=True, help_text="Error details if test failed")
    stack_trace = models.TextField(blank=True, help_text="Stack trace for debugging")
    
    # Test parameters
    test_email = models.EmailField(blank=True, help_text="Test email address used")
    test_subject = models.CharField(max_length=255, blank=True, help_text="Test email subject")
    
    # Tested by
    tested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_tests_performed')
    
    class Meta:
        verbose_name = 'Email Test Result'
        verbose_name_plural = 'Email Test Results'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.configuration.name} - {self.test_type} ({self.status})"
    
    def save(self, *args, **kwargs):
        if self.completed_at and self.started_at:
            self.duration = (self.completed_at - self.started_at).total_seconds()
        super().save(*args, **kwargs)


class EmailNotification(models.Model):
    """Email notifications and alerts for the ERP system"""
    
    NOTIFICATION_TYPE_CHOICES = [
        ('system_alert', 'System Alert'),
        ('user_notification', 'User Notification'),
        ('business_workflow', 'Business Workflow'),
        ('error_report', 'Error Report'),
        ('backup_notification', 'Backup Notification'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    # Basic notification info
    name = models.CharField(max_length=100, help_text="Descriptive name for this notification", default="Notification")
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    subject = models.CharField(max_length=255)
    message = models.TextField()
    
    # Recipients
    recipient_email = models.EmailField(help_text="Primary recipient email address", default="admin@example.com")
    recipients = models.JSONField(help_text="List of recipient email addresses", default=list)
    cc_recipients = models.JSONField(default=list, blank=True, help_text="List of CC recipient email addresses")
    bcc_recipients = models.JSONField(default=list, blank=True, help_text="List of BCC recipient email addresses")
    
    # Configuration used
    configuration = models.ForeignKey(EmailConfiguration, on_delete=models.CASCADE, related_name='notifications')
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ], default='pending')
    
    # Timing
    scheduled_at = models.DateTimeField(null=True, blank=True, help_text="When to send the notification")
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications_created')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications_updated', null=True, blank=True)
    retry_count = models.IntegerField(default=0, help_text="Number of retry attempts")
    max_retries = models.IntegerField(default=3, help_text="Maximum retry attempts")
    
    # Error tracking
    error_message = models.TextField(blank=True, help_text="Error message if sending failed")
    last_retry_at = models.DateTimeField(null=True, blank=True)
    
    # Active status
    is_active = models.BooleanField(default=True, help_text="Whether this notification is active")
    
    class Meta:
        verbose_name = 'Email Notification'
        verbose_name_plural = 'Email Notifications'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.recipient_email}"
    
    def is_retryable(self):
        """Check if this notification can be retried"""
        return self.status == 'failed' and self.retry_count < self.max_retries
    
    def can_send(self):
        """Check if this notification can be sent"""
        if not self.is_active:
            return False
        
        if self.scheduled_at and self.scheduled_at > timezone.now():
            return False
        
        return self.status in ['pending', 'failed']
    
    @property
    def notification_type(self):
        """Property to match template expectations"""
        return self.type
