from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
import uuid
import json


class LogHistory(models.Model):
    """
    Comprehensive log history model that captures every user and system activity
    """
    
    # Action Types
    ACTION_CREATE = 'CREATE'
    ACTION_UPDATE = 'UPDATE'
    ACTION_DELETE = 'DELETE'
    ACTION_LOGIN = 'LOGIN'
    ACTION_LOGOUT = 'LOGOUT'
    ACTION_VIEW = 'VIEW'
    ACTION_EXPORT = 'EXPORT'
    ACTION_IMPORT = 'IMPORT'
    ACTION_DOWNLOAD = 'DOWNLOAD'
    ACTION_UPLOAD = 'UPLOAD'
    ACTION_APPROVE = 'APPROVE'
    ACTION_REJECT = 'REJECT'
    ACTION_ASSIGN = 'ASSIGN'
    ACTION_UNASSIGN = 'UNASSIGN'
    ACTION_STATUS_CHANGE = 'STATUS_CHANGE'
    ACTION_PERMISSION_CHANGE = 'PERMISSION_CHANGE'
    ACTION_ROLE_CHANGE = 'ROLE_CHANGE'
    ACTION_SYSTEM = 'SYSTEM'
    ACTION_ERROR = 'ERROR'
    ACTION_WARNING = 'WARNING'
    ACTION_INFO = 'INFO'
    
    ACTION_CHOICES = [
        (ACTION_CREATE, 'Create'),
        (ACTION_UPDATE, 'Update'),
        (ACTION_DELETE, 'Delete'),
        (ACTION_LOGIN, 'Login'),
        (ACTION_LOGOUT, 'Logout'),
        (ACTION_VIEW, 'View'),
        (ACTION_EXPORT, 'Export'),
        (ACTION_IMPORT, 'Import'),
        (ACTION_DOWNLOAD, 'Download'),
        (ACTION_UPLOAD, 'Upload'),
        (ACTION_APPROVE, 'Approve'),
        (ACTION_REJECT, 'Reject'),
        (ACTION_ASSIGN, 'Assign'),
        (ACTION_UNASSIGN, 'Unassign'),
        (ACTION_STATUS_CHANGE, 'Status Change'),
        (ACTION_PERMISSION_CHANGE, 'Permission Change'),
        (ACTION_ROLE_CHANGE, 'Role Change'),
        (ACTION_SYSTEM, 'System'),
        (ACTION_ERROR, 'Error'),
        (ACTION_WARNING, 'Warning'),
        (ACTION_INFO, 'Info'),
    ]
    
    # Severity Levels
    SEVERITY_LOW = 'LOW'
    SEVERITY_MEDIUM = 'MEDIUM'
    SEVERITY_HIGH = 'HIGH'
    SEVERITY_CRITICAL = 'CRITICAL'
    
    SEVERITY_CHOICES = [
        (SEVERITY_LOW, 'Low'),
        (SEVERITY_MEDIUM, 'Medium'),
        (SEVERITY_HIGH, 'High'),
        (SEVERITY_CRITICAL, 'Critical'),
    ]
    
    # Status
    STATUS_ACTIVE = 'ACTIVE'
    STATUS_ARCHIVED = 'ARCHIVED'
    STATUS_DELETED = 'DELETED'
    
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_ARCHIVED, 'Archived'),
        (STATUS_DELETED, 'Deleted'),
    ]
    
    # Core Fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    action_type = models.CharField(max_length=50, choices=ACTION_CHOICES, db_index=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default=SEVERITY_LOW)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    
    # User Information
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='log_entries')
    user_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    user_session = models.CharField(max_length=255, blank=True)
    
    # Target Object Information
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.CharField(max_length=255, null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    object_name = models.CharField(max_length=255, blank=True)
    object_type = models.CharField(max_length=100, blank=True)
    
    # Action Details
    description = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    before_values = models.JSONField(default=dict, blank=True)
    after_values = models.JSONField(default=dict, blank=True)
    changed_fields = models.JSONField(default=list, blank=True)
    
    # Context Information
    module = models.CharField(max_length=100, blank=True)
    function = models.CharField(max_length=100, blank=True)
    line_number = models.IntegerField(null=True, blank=True)
    stack_trace = models.TextField(blank=True)
    
    # Performance Metrics
    execution_time = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    memory_usage = models.BigIntegerField(null=True, blank=True)
    
    # Metadata
    tags = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'log_history'
        verbose_name = 'Log History Entry'
        verbose_name_plural = 'Log History Entries'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp', 'action_type']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['severity', 'timestamp']),
            models.Index(fields=['module', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.action_type} - {self.object_name or 'System'} - {self.timestamp}"
    
    def get_action_display(self):
        return dict(self.ACTION_CHOICES).get(self.action_type, self.action_type)
    
    def get_severity_display(self):
        return dict(self.SEVERITY_CHOICES).get(self.severity, self.severity)
    
    def get_status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)
    
    def get_changed_fields_summary(self):
        """Return a human-readable summary of changed fields"""
        if not self.changed_fields:
            return "No fields changed"
        
        if isinstance(self.changed_fields, list):
            return ", ".join(self.changed_fields)
        return str(self.changed_fields)
    
    def get_before_after_summary(self):
        """Return a summary of before/after values for changed fields"""
        if not self.changed_fields or not self.before_values or not self.after_values:
            return ""
        
        summary = []
        for field in self.changed_fields:
            before = self.before_values.get(field, 'N/A')
            after = self.after_values.get(field, 'N/A')
            summary.append(f"{field}: {before} → {after}")
        
        return "; ".join(summary)
    
    def archive(self):
        """Archive the log entry"""
        self.status = self.STATUS_ARCHIVED
        self.save(update_fields=['status', 'updated_at'])
    
    def soft_delete(self):
        """Soft delete the log entry"""
        self.status = self.STATUS_DELETED
        self.save(update_fields=['status', 'updated_at'])


class LogCategory(models.Model):
    """
    Categories for organizing log entries
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#007bff')  # Hex color
    icon = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'log_categories'
        verbose_name = 'Log Category'
        verbose_name_plural = 'Log Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class LogFilter(models.Model):
    """
    Saved filters for log history queries
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='log_filters')
    description = models.TextField(blank=True)
    filter_criteria = models.JSONField()  # Store filter parameters
    is_default = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'log_filters'
        verbose_name = 'Log Filter'
        verbose_name_plural = 'Log Filters'
        ordering = ['-created_at']
        unique_together = ['user', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.user.username}"


class LogExport(models.Model):
    """
    Track log export operations
    """
    EXPORT_FORMAT_CSV = 'CSV'
    EXPORT_FORMAT_JSON = 'JSON'
    EXPORT_FORMAT_XML = 'XML'
    EXPORT_FORMAT_PDF = 'PDF'
    
    EXPORT_FORMAT_CHOICES = [
        (EXPORT_FORMAT_CSV, 'CSV'),
        (EXPORT_FORMAT_JSON, 'JSON'),
        (EXPORT_FORMAT_XML, 'XML'),
        (EXPORT_FORMAT_PDF, 'PDF'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='log_exports')
    export_format = models.CharField(max_length=10, choices=EXPORT_FORMAT_CHOICES)
    filter_criteria = models.JSONField(default=dict)
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    record_count = models.IntegerField(default=0)
    status = models.CharField(max_length=20, default='PENDING')
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'log_exports'
        verbose_name = 'Log Export'
        verbose_name_plural = 'Log Exports'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.export_format} Export - {self.user.username} - {self.created_at}"


class LogRetentionPolicy(models.Model):
    """
    Policies for log retention and archival
    """
    RETENTION_PERIOD_1_MONTH = 30
    RETENTION_PERIOD_3_MONTHS = 90
    RETENTION_PERIOD_6_MONTHS = 180
    RETENTION_PERIOD_1_YEAR = 365
    RETENTION_PERIOD_2_YEARS = 730
    RETENTION_PERIOD_5_YEARS = 1825
    RETENTION_PERIOD_10_YEARS = 3650
    RETENTION_PERIOD_FOREVER = -1
    
    RETENTION_PERIOD_CHOICES = [
        (RETENTION_PERIOD_1_MONTH, '1 Month'),
        (RETENTION_PERIOD_3_MONTHS, '3 Months'),
        (RETENTION_PERIOD_6_MONTHS, '6 Months'),
        (RETENTION_PERIOD_1_YEAR, '1 Year'),
        (RETENTION_PERIOD_2_YEARS, '2 Years'),
        (RETENTION_PERIOD_5_YEARS, '5 Years'),
        (RETENTION_PERIOD_10_YEARS, '10 Years'),
        (RETENTION_PERIOD_FOREVER, 'Forever'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    action_type = models.CharField(max_length=50, choices=LogHistory.ACTION_CHOICES, blank=True)
    severity = models.CharField(max_length=20, choices=LogHistory.SEVERITY_CHOICES, blank=True)
    module = models.CharField(max_length=100, blank=True)
    retention_period = models.IntegerField(choices=RETENTION_PERIOD_CHOICES, default=RETENTION_PERIOD_1_YEAR)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'log_retention_policies'
        verbose_name = 'Log Retention Policy'
        verbose_name_plural = 'Log Retention Policies'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.get_retention_period_display()}"
    
    def get_retention_period_display(self):
        return dict(self.RETENTION_PERIOD_CHOICES).get(self.retention_period, str(self.retention_period))
