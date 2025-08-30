from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
import uuid


class SMSGateway(models.Model):
    """SMS Gateway configuration model"""
    
    GATEWAY_TYPES = [
        ('twilio', 'Twilio'),
        ('nexmo', 'Nexmo/Vonage'),
        ('aws_sns', 'AWS SNS'),
        ('infobip', 'Infobip'),
        ('messagebird', 'MessageBird'),
        ('custom', 'Custom API'),
    ]
    
    ENCRYPTION_CHOICES = [
        ('none', 'None'),
        ('ssl', 'SSL'),
        ('tls', 'TLS'),
        ('starttls', 'STARTTLS'),
    ]
    
    HTTP_METHODS = [
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
    ]
    
    # Basic configuration
    name = models.CharField(max_length=100, help_text="Descriptive name for this gateway")
    gateway_type = models.CharField(max_length=20, choices=GATEWAY_TYPES, default='custom')
    is_active = models.BooleanField(default=True, help_text="Whether this gateway is active")
    
    # API credentials
    api_key = models.CharField(max_length=255, help_text="API key or access token")
    api_secret = models.CharField(max_length=255, help_text="API secret or password")
    username = models.CharField(max_length=100, blank=True, help_text="Username if required")
    sender_id = models.CharField(max_length=20, help_text="Sender ID or from number")
    
    # API endpoint
    api_url = models.URLField(help_text="API endpoint URL")
    http_method = models.CharField(max_length=4, choices=HTTP_METHODS, default='POST')
    
    # Connection settings
    timeout = models.IntegerField(default=30, help_text="Request timeout in seconds")
    max_retries = models.IntegerField(default=3, help_text="Maximum retry attempts")
    encryption = models.CharField(max_length=10, choices=ENCRYPTION_CHOICES, default='none')
    
    # Message settings
    default_encoding = models.CharField(max_length=20, default='UTF-8', help_text="Default message encoding")
    max_message_length = models.IntegerField(default=160, help_text="Maximum message length")
    support_unicode = models.BooleanField(default=True, help_text="Support for Unicode characters")
    
    # Rate limiting
    rate_limit_per_second = models.IntegerField(default=10, help_text="Messages per second limit")
    rate_limit_per_minute = models.IntegerField(default=600, help_text="Messages per minute limit")
    rate_limit_per_hour = models.IntegerField(default=36000, help_text="Messages per hour limit")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sms_gateways_created')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sms_gateways_updated', null=True, blank=True)
    
    # Status tracking
    last_tested = models.DateTimeField(null=True, blank=True)
    last_test_status = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
    ], default='pending')
    
    class Meta:
        verbose_name = 'SMS Gateway'
        verbose_name_plural = 'SMS Gateways'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.gateway_type})"
    
    @property
    def is_healthy(self):
        """Check if gateway is healthy based on last test"""
        if not self.last_tested:
            return False
        return self.last_test_status == 'success'


class SMSTestResult(models.Model):
    """SMS test results and delivery status"""
    
    TEST_TYPES = [
        ('connection', 'Connection Test'),
        ('authentication', 'Authentication Test'),
        ('message_send', 'Message Send Test'),
        ('delivery_status', 'Delivery Status Test'),
        ('unicode_test', 'Unicode/Encoding Test'),
        ('rate_limit', 'Rate Limit Test'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('timeout', 'Timeout'),
        ('rate_limited', 'Rate Limited'),
    ]
    
    # Test identification
    test_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    test_type = models.CharField(max_length=20, choices=TEST_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Gateway and configuration
    gateway = models.ForeignKey(SMSGateway, on_delete=models.CASCADE, related_name='test_results')
    
    # Test parameters
    test_message = models.TextField(help_text="Test message content")
    recipient_number = models.CharField(max_length=20, help_text="Test recipient phone number")
    message_encoding = models.CharField(max_length=20, default='UTF-8')
    
    # Results
    success = models.BooleanField(default=False)
    response_code = models.CharField(max_length=10, blank=True, help_text="HTTP response code")
    response_message = models.TextField(blank=True, help_text="Response message from gateway")
    error_message = models.TextField(blank=True, help_text="Error message if test failed")
    
    # Performance metrics
    response_time = models.FloatField(null=True, blank=True, help_text="Response time in seconds")
    message_id = models.CharField(max_length=100, blank=True, help_text="Message ID from gateway")
    delivery_status = models.CharField(max_length=20, blank=True, help_text="Delivery status from gateway")
    
    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Test execution details
    executed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sms_tests_executed')
    test_environment = models.CharField(max_length=50, default='production', help_text="Test environment")
    
    class Meta:
        verbose_name = 'SMS Test Result'
        verbose_name_plural = 'SMS Test Results'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.test_type} - {self.gateway.name} - {self.status}"
    
    @property
    def duration(self):
        """Calculate test duration"""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class SMSMessage(models.Model):
    """SMS message model for tracking sent messages"""
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    DELIVERY_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
        ('rejected', 'Rejected'),
    ]
    
    # Message identification
    message_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    external_message_id = models.CharField(max_length=100, blank=True, help_text="Message ID from gateway")
    
    # Message content
    recipient_number = models.CharField(max_length=20, help_text="Recipient phone number")
    sender_id = models.CharField(max_length=20, help_text="Sender ID")
    message_content = models.TextField(help_text="SMS message content")
    message_encoding = models.CharField(max_length=20, default='UTF-8')
    message_length = models.IntegerField(help_text="Message length in characters")
    
    # Message settings
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    scheduled_at = models.DateTimeField(null=True, blank=True, help_text="Scheduled send time")
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Message expiration time")
    
    # Gateway and delivery
    gateway = models.ForeignKey(SMSGateway, on_delete=models.CASCADE, related_name='messages')
    delivery_status = models.CharField(max_length=20, choices=DELIVERY_STATUS_CHOICES, default='pending')
    
    # Delivery tracking
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    delivery_attempts = models.IntegerField(default=0)
    max_delivery_attempts = models.IntegerField(default=3)
    
    # Response and errors
    response_code = models.CharField(max_length=10, blank=True)
    response_message = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    error_code = models.CharField(max_length=50, blank=True)
    
    # Cost and billing
    cost = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, help_text="Message cost")
    currency = models.CharField(max_length=3, default='AED', help_text="Cost currency")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sms_messages_created')
    
    # Tags and categorization
    tags = models.JSONField(default=list, blank=True, help_text="Message tags for categorization")
    category = models.CharField(max_length=50, blank=True, help_text="Message category")
    
    class Meta:
        verbose_name = 'SMS Message'
        verbose_name_plural = 'SMS Messages'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.recipient_number} - {self.delivery_status} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def is_delivered(self):
        """Check if message was delivered"""
        return self.delivery_status == 'delivered'
    
    @property
    def is_failed(self):
        """Check if message delivery failed"""
        return self.delivery_status in ['failed', 'expired', 'rejected']
    
    @property
    def delivery_time(self):
        """Calculate delivery time if delivered"""
        if self.delivered_at and self.sent_at:
            return (self.delivered_at - self.sent_at).total_seconds()
        return None


class SMSDeliveryLog(models.Model):
    """Detailed delivery status logs for SMS messages"""
    
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
        ('rejected', 'Rejected'),
        ('undelivered', 'Undelivered'),
    ]
    
    # Log identification
    log_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    message = models.ForeignKey(SMSMessage, on_delete=models.CASCADE, related_name='delivery_logs')
    
    # Status information
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    status_code = models.CharField(max_length=10, blank=True, help_text="Status code from gateway")
    status_message = models.TextField(blank=True, help_text="Status message from gateway")
    
    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Additional details
    gateway_response = models.JSONField(default=dict, blank=True, help_text="Full gateway response")
    error_details = models.JSONField(default=dict, blank=True, help_text="Error details if any")
    
    class Meta:
        verbose_name = 'SMS Delivery Log'
        verbose_name_plural = 'SMS Delivery Logs'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.message.recipient_number} - {self.status} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"


class SMSGatewayHealth(models.Model):
    """Gateway health monitoring and metrics"""
    
    # Gateway reference
    gateway = models.ForeignKey(SMSGateway, on_delete=models.CASCADE, related_name='health_records')
    
    # Health metrics
    is_healthy = models.BooleanField(default=True)
    response_time = models.FloatField(help_text="Average response time in seconds")
    success_rate = models.FloatField(help_text="Success rate percentage")
    error_rate = models.FloatField(help_text="Error rate percentage")
    
    # System metrics
    cpu_usage = models.FloatField(null=True, blank=True, help_text="CPU usage percentage")
    memory_usage = models.FloatField(null=True, blank=True, help_text="Memory usage percentage")
    active_connections = models.IntegerField(default=0, help_text="Active connections")
    
    # Rate limiting status
    rate_limit_status = models.CharField(max_length=20, choices=[
        ('normal', 'Normal'),
        ('approaching', 'Approaching Limit'),
        ('limited', 'Rate Limited'),
    ], default='normal')
    
    # Timestamp
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'SMS Gateway Health'
        verbose_name_plural = 'SMS Gateway Health Records'
        ordering = ['-recorded_at']
    
    def __str__(self):
        return f"{self.gateway.name} - {self.recorded_at.strftime('%Y-%m-%d %H:%M')} - {'Healthy' if self.is_healthy else 'Unhealthy'}"
