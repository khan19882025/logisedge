from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
import json
import hashlib
import uuid


class ActivityLog(models.Model):
    """
    Main model for logging all user activities and system events
    """
    LOG_LEVELS = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Information'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    ACTIVITY_TYPES = [
        ('LOGIN', 'User Login'),
        ('LOGOUT', 'User Logout'),
        ('CREATE', 'Data Creation'),
        ('UPDATE', 'Data Update'),
        ('DELETE', 'Data Deletion'),
        ('VIEW', 'Data View'),
        ('EXPORT', 'Data Export'),
        ('IMPORT', 'Data Import'),
        ('BACKUP', 'Backup Operation'),
        ('RESTORE', 'Restore Operation'),
        ('PERMISSION_CHANGE', 'Permission Change'),
        ('APPROVAL', 'Approval Action'),
        ('REJECTION', 'Rejection Action'),
        ('SYSTEM', 'System Event'),
        ('SECURITY', 'Security Event'),
        ('COMPLIANCE', 'Compliance Event'),
    ]
    
    # Unique identifier for the log entry
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic information
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    log_level = models.CharField(max_length=10, choices=LOG_LEVELS, default='INFO')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES, db_index=True)
    
    # User information
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='erp_activity_logs')
    user_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_id = models.CharField(max_length=100, blank=True)
    
    # Target object information
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True, related_name='erp_activity_logs')
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Activity details
    action = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    module = models.CharField(max_length=100, db_index=True)
    
    # Data changes
    old_values = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    new_values = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    tags = models.JSONField(default=list, blank=True)
    
    # Security and compliance
    is_sensitive = models.BooleanField(default=False)
    compliance_category = models.CharField(max_length=50, blank=True)
    
    # Integrity verification
    data_hash = models.CharField(max_length=64, blank=True)
    signature = models.TextField(blank=True)
    
    # Retention and archiving
    retention_date = models.DateTimeField(null=True, blank=True)
    is_archived = models.BooleanField(default=False)
    archive_location = models.CharField(max_length=255, blank=True)
    
    class Meta:
        db_table = 'activity_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp', 'activity_type']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['module', 'timestamp']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['is_sensitive', 'timestamp']),
            models.Index(fields=['compliance_category', 'timestamp']),
        ]
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'
    
    def __str__(self):
        return f"{self.timestamp} - {self.user} - {self.action} - {self.module}"
    
    def save(self, *args, **kwargs):
        # Generate data hash for integrity verification
        if not self.data_hash:
            self.generate_data_hash()
        super().save(*args, **kwargs)
    
    def generate_data_hash(self):
        """Generate SHA-256 hash of critical data for integrity verification"""
        data_string = f"{self.timestamp}{self.user_id}{self.action}{self.module}{self.description}"
        if self.old_values:
            data_string += json.dumps(self.old_values, sort_keys=True)
        if self.new_values:
            data_string += json.dumps(self.new_values, sort_keys=True)
        
        self.data_hash = hashlib.sha256(data_string.encode()).hexdigest()
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('activity_logs:activity_log_detail', kwargs={'pk': self.pk})


class AuditTrail(models.Model):
    """
    Model for tracking complete audit trails of specific objects
    """
    TRAIL_TYPES = [
        ('DATA', 'Data Changes'),
        ('ACCESS', 'Access Log'),
        ('PERMISSION', 'Permission Changes'),
        ('WORKFLOW', 'Workflow Changes'),
        ('SECURITY', 'Security Events'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Trail identification
    trail_name = models.CharField(max_length=255)
    trail_type = models.CharField(max_length=20, choices=TRAIL_TYPES)
    
    # Target object
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Trail metadata
    description = models.TextField(blank=True)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    
    # Related logs
    activity_logs = models.ManyToManyField(ActivityLog, related_name='audit_trails')
    
    # Compliance
    compliance_requirements = models.JSONField(default=list, blank=True)
    retention_policy = models.CharField(max_length=100, blank=True)
    
    class Meta:
        db_table = 'audit_trails'
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['trail_type', 'start_date']),
        ]
        verbose_name = 'Audit Trail'
        verbose_name_plural = 'Audit Trails'
    
    def __str__(self):
        return f"{self.trail_name} - {self.content_type.model} #{self.object_id}"


class SecurityEvent(models.Model):
    """
    Model for tracking security-related events and incidents
    """
    SEVERITY_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    EVENT_TYPES = [
        ('LOGIN_FAILURE', 'Login Failure'),
        ('UNAUTHORIZED_ACCESS', 'Unauthorized Access'),
        ('PERMISSION_VIOLATION', 'Permission Violation'),
        ('DATA_BREACH', 'Data Breach'),
        ('SYSTEM_INTRUSION', 'System Intrusion'),
        ('MALWARE_DETECTION', 'Malware Detection'),
        ('ANOMALOUS_ACTIVITY', 'Anomalous Activity'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Event details
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS)
    
    # User and source information
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    source_ip = models.GenericIPAddressField()
    source_location = models.CharField(max_length=100, blank=True)
    
    # Event description
    title = models.CharField(max_length=255)
    description = models.TextField()
    details = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    
    # Response and status
    is_resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_security_events')
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Related logs
    related_logs = models.ManyToManyField(ActivityLog, related_name='security_events')
    
    class Meta:
        db_table = 'security_events'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp', 'severity']),
            models.Index(fields=['event_type', 'is_resolved']),
            models.Index(fields=['user', 'timestamp']),
        ]
        verbose_name = 'Security Event'
        verbose_name_plural = 'Security Events'
    
    def __str__(self):
        return f"{self.timestamp} - {self.event_type} - {self.title}"


class ComplianceReport(models.Model):
    """
    Model for generating and storing compliance reports
    """
    REPORT_TYPES = [
        ('SOX', 'Sarbanes-Oxley'),
        ('GDPR', 'General Data Protection Regulation'),
        ('ISO27001', 'ISO 27001'),
        ('HIPAA', 'Health Insurance Portability and Accountability Act'),
        ('PCI_DSS', 'Payment Card Industry Data Security Standard'),
        ('CUSTOM', 'Custom Compliance'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Report details
    report_name = models.CharField(max_length=255)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Report content
    report_data = models.JSONField(encoder=DjangoJSONEncoder)
    report_summary = models.TextField()
    
    # Compliance period
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Status and approval
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_reports')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Export and storage
    pdf_file = models.FileField(upload_to='compliance_reports/', null=True, blank=True)
    csv_file = models.FileField(upload_to='compliance_reports/', null=True, blank=True)
    
    class Meta:
        db_table = 'compliance_reports'
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['report_type', 'start_date', 'end_date']),
            models.Index(fields=['generated_by', 'generated_at']),
        ]
        verbose_name = 'Compliance Report'
        verbose_name_plural = 'Compliance Reports'
    
    def __str__(self):
        return f"{self.report_name} - {self.report_type} - {self.start_date} to {self.end_date}"


class RetentionPolicy(models.Model):
    """
    Model for defining data retention policies
    """
    POLICY_TYPES = [
        ('ACTIVITY_LOGS', 'Activity Logs'),
        ('SECURITY_EVENTS', 'Security Events'),
        ('AUDIT_TRAILS', 'Audit Trails'),
        ('COMPLIANCE_REPORTS', 'Compliance Reports'),
        ('USER_SESSIONS', 'User Sessions'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Policy details
    name = models.CharField(max_length=255)
    policy_type = models.CharField(max_length=30, choices=POLICY_TYPES)
    description = models.TextField()
    
    # Retention settings
    retention_period_days = models.PositiveIntegerField()
    archive_after_days = models.PositiveIntegerField(null=True, blank=True)
    delete_after_days = models.PositiveIntegerField(null=True, blank=True)
    
    # Compliance requirements
    compliance_standards = models.JSONField(default=list, blank=True)
    legal_requirements = models.TextField(blank=True)
    
    # Policy status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'retention_policies'
        ordering = ['name']
        verbose_name = 'Retention Policy'
        verbose_name_plural = 'Retention Policies'
    
    def __str__(self):
        return f"{self.name} - {self.policy_type}"


class AlertRule(models.Model):
    """
    Model for defining alert rules and notifications
    """
    ALERT_TYPES = [
        ('EMAIL', 'Email'),
        ('SMS', 'SMS'),
        ('WEBHOOK', 'Webhook'),
        ('DASHBOARD', 'Dashboard'),
        ('SLACK', 'Slack'),
        ('TEAMS', 'Microsoft Teams'),
    ]
    
    TRIGGER_TYPES = [
        ('THRESHOLD', 'Threshold Exceeded'),
        ('PATTERN', 'Pattern Detected'),
        ('ANOMALY', 'Anomaly Detected'),
        ('SCHEDULE', 'Scheduled'),
        ('MANUAL', 'Manual Trigger'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Rule details
    name = models.CharField(max_length=255)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    
    # Trigger conditions
    trigger_type = models.CharField(max_length=20, choices=TRIGGER_TYPES)
    trigger_conditions = models.JSONField(encoder=DjangoJSONEncoder)
    
    # Alert configuration
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    recipients = models.JSONField(default=list, blank=True)
    message_template = models.TextField()
    
    # Thresholds and limits
    threshold_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    time_window_minutes = models.PositiveIntegerField(null=True, blank=True)
    
    # Status and history
    last_triggered = models.DateTimeField(null=True, blank=True)
    trigger_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'alert_rules'
        ordering = ['name']
        verbose_name = 'Alert Rule'
        verbose_name_plural = 'Alert Rules'
    
    def __str__(self):
        return f"{self.name} - {self.trigger_type}"
