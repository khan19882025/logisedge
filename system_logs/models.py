from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
import uuid
import json


class SystemLog(models.Model):
    """
    Main model for system error and debug logging
    """
    SEVERITY_LEVELS = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
        ('FATAL', 'Fatal'),
    ]
    
    LOG_TYPES = [
        ('EXCEPTION', 'Exception'),
        ('WARNING', 'Warning'),
        ('DEBUG', 'Debug'),
        ('INFO', 'Information'),
        ('PERFORMANCE', 'Performance'),
        ('SECURITY', 'Security'),
        ('AUDIT', 'Audit'),
        ('SYSTEM', 'System'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('RESOLVED', 'Resolved'),
        ('IGNORED', 'Ignored'),
        ('ESCALATED', 'Escalated'),
        ('ARCHIVED', 'Archived'),
    ]
    
    # Core identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    log_type = models.CharField(max_length=20, choices=LOG_TYPES, default='EXCEPTION')
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='ERROR')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    
    # Error details
    error_message = models.TextField()
    error_type = models.CharField(max_length=255, blank=True)
    stack_trace = models.TextField(blank=True)
    exception_details = models.JSONField(default=dict, blank=True)
    
    # Context information
    module = models.CharField(max_length=100, blank=True)
    function = models.CharField(max_length=100, blank=True)
    line_number = models.IntegerField(null=True, blank=True)
    file_path = models.CharField(max_length=500, blank=True)
    
    # User and request context
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    user_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    request_url = models.URLField(max_length=1000, blank=True)
    request_data = models.JSONField(default=dict, blank=True)
    
    # Performance metrics
    execution_time = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    memory_usage = models.CharField(max_length=50, blank=True)
    cpu_usage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Related objects
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    object_name = models.CharField(max_length=255, blank=True)
    generic_object = GenericForeignKey('content_type', 'object_id')
    
    # Additional context
    tags = models.JSONField(default=list, blank=True)
    context_data = models.JSONField(default=dict, blank=True)
    environment = models.CharField(max_length=50, default='production')
    version = models.CharField(max_length=50, blank=True)
    
    # Resolution tracking
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_logs')
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    escalation_level = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'system_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp', 'severity']),
            models.Index(fields=['log_type', 'status']),
            models.Index(fields=['module', 'function']),
            models.Index(fields=['user', 'timestamp']),
        ]
        verbose_name = 'System Log'
        verbose_name_plural = 'System Logs'
    
    def __str__(self):
        return f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {self.severity} - {self.error_message[:100]}"
    
    def get_severity_display(self):
        return dict(self.SEVERITY_LEVELS).get(self.severity, self.severity)
    
    def get_log_type_display(self):
        return dict(self.LOG_TYPES).get(self.log_type, self.log_type)
    
    def get_status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)
    
    def is_resolved(self):
        return self.status == 'RESOLVED'
    
    def is_critical(self):
        return self.severity in ['CRITICAL', 'FATAL']
    
    def get_execution_time_ms(self):
        if self.execution_time:
            return float(self.execution_time) * 1000
        return None
    
    def add_tag(self, tag):
        if tag not in self.tags:
            self.tags.append(tag)
            self.save(update_fields=['tags', 'updated_at'])
    
    def remove_tag(self, tag):
        if tag in self.tags:
            self.tags.remove(tag)
            self.save(update_fields=['tags', 'updated_at'])
    
    def resolve(self, user, notes=""):
        self.status = 'RESOLVED'
        self.resolved_by = user
        self.resolved_at = timezone.now()
        self.resolution_notes = notes
        self.save()
    
    def escalate(self, level):
        self.escalation_level = level
        self.status = 'ESCALATED'
        self.save(update_fields=['escalation_level', 'status', 'updated_at'])


class ErrorPattern(models.Model):
    """
    Model to track recurring error patterns for analysis
    """
    PATTERN_TYPES = [
        ('EXCEPTION', 'Exception Pattern'),
        ('PERFORMANCE', 'Performance Pattern'),
        ('SECURITY', 'Security Pattern'),
        ('BUSINESS_LOGIC', 'Business Logic Pattern'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pattern_type = models.CharField(max_length=20, choices=PATTERN_TYPES, default='EXCEPTION')
    pattern_hash = models.CharField(max_length=64, unique=True, db_index=True)
    error_signature = models.TextField()
    error_type = models.CharField(max_length=255)
    module = models.CharField(max_length=100, blank=True)
    function = models.CharField(max_length=100, blank=True)
    
    # Pattern statistics
    occurrence_count = models.PositiveIntegerField(default=1)
    first_occurrence = models.DateTimeField(auto_now_add=True)
    last_occurrence = models.DateTimeField(auto_now=True)
    total_affected_users = models.PositiveIntegerField(default=0)
    
    # Impact analysis
    avg_severity = models.CharField(max_length=20, choices=SystemLog.SEVERITY_LEVELS, default='ERROR')
    max_severity = models.CharField(max_length=20, choices=SystemLog.SEVERITY_LEVELS, default='ERROR')
    avg_execution_time = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    
    # Resolution tracking
    is_resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Related logs
    related_logs = models.ManyToManyField(SystemLog, through='ErrorPatternLog')
    
    class Meta:
        db_table = 'error_patterns'
        ordering = ['-occurrence_count', '-last_occurrence']
        verbose_name = 'Error Pattern'
        verbose_name_plural = 'Error Patterns'
    
    def __str__(self):
        return f"{self.pattern_type} - {self.error_type} ({self.occurrence_count} occurrences)"
    
    def update_statistics(self, log_entry):
        """Update pattern statistics with new log entry"""
        self.occurrence_count += 1
        self.last_occurrence = log_entry.timestamp
        
        # Update severity statistics
        severity_levels = {'DEBUG': 1, 'INFO': 2, 'WARNING': 3, 'ERROR': 4, 'CRITICAL': 5, 'FATAL': 6}
        current_max = severity_levels.get(self.max_severity, 0)
        new_level = severity_levels.get(log_entry.severity, 0)
        
        if new_level > current_max:
            self.max_severity = log_entry.severity
        
        # Update execution time average
        if log_entry.execution_time:
            if self.avg_execution_time:
                total_time = self.avg_execution_time * (self.occurrence_count - 1) + log_entry.execution_time
                self.avg_execution_time = total_time / self.occurrence_count
            else:
                self.avg_execution_time = log_entry.execution_time
        
        self.save()


class ErrorPatternLog(models.Model):
    """
    Through model linking error patterns to system logs
    """
    pattern = models.ForeignKey(ErrorPattern, on_delete=models.CASCADE)
    log_entry = models.ForeignKey(SystemLog, on_delete=models.CASCADE)
    matched_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'error_pattern_logs'
        unique_together = ['pattern', 'log_entry']


class DebugSession(models.Model):
    """
    Model to track debug sessions and their associated logs
    """
    SESSION_TYPES = [
        ('DEVELOPMENT', 'Development'),
        ('TESTING', 'Testing'),
        ('DEBUGGING', 'Debugging'),
        ('MONITORING', 'Monitoring'),
        ('AUDIT', 'Audit'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_name = models.CharField(max_length=255)
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES, default='DEBUGGING')
    description = models.TextField(blank=True)
    
    # Session details
    started_by = models.ForeignKey(User, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Session context
    environment = models.CharField(max_length=50, default='development')
    version = models.CharField(max_length=50, blank=True)
    tags = models.JSONField(default=list, blank=True)
    context_data = models.JSONField(default=dict, blank=True)
    
    # Associated logs
    logs = models.ManyToManyField(SystemLog, through='DebugSessionLog')
    
    class Meta:
        db_table = 'debug_sessions'
        ordering = ['-started_at']
        verbose_name = 'Debug Session'
        verbose_name_plural = 'Debug Sessions'
    
    def __str__(self):
        return f"{self.session_name} ({self.session_type}) - {self.started_by.username}"
    
    def end_session(self):
        self.is_active = False
        self.ended_at = timezone.now()
        self.save()
    
    def get_duration(self):
        if self.ended_at:
            return self.ended_at - self.started_at
        return timezone.now() - self.started_at
    
    def get_log_count(self):
        return self.logs.count()


class DebugSessionLog(models.Model):
    """
    Through model linking debug sessions to system logs
    """
    session = models.ForeignKey(DebugSession, on_delete=models.CASCADE)
    log_entry = models.ForeignKey(SystemLog, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'debug_session_logs'
        unique_together = ['session', 'log_entry']


class LogRetentionPolicy(models.Model):
    """
    Model to define log retention policies
    """
    RETENTION_TYPES = [
        ('TIME_BASED', 'Time-based'),
        ('SIZE_BASED', 'Size-based'),
        ('SEVERITY_BASED', 'Severity-based'),
        ('PATTERN_BASED', 'Pattern-based'),
    ]
    
    ACTION_TYPES = [
        ('ARCHIVE', 'Archive'),
        ('DELETE', 'Delete'),
        ('COMPRESS', 'Compress'),
        ('MOVE', 'Move to cold storage'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    
    # Policy configuration
    retention_type = models.CharField(max_length=20, choices=RETENTION_TYPES, default='TIME_BASED')
    retention_value = models.IntegerField(help_text="Days for time-based, MB for size-based, etc.")
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES, default='ARCHIVE')
    
    # Filters
    severity_levels = models.JSONField(default=list, blank=True)
    log_types = models.JSONField(default=list, blank=True)
    modules = models.JSONField(default=list, blank=True)
    tags = models.JSONField(default=list, blank=True)
    
    # Policy status
    is_active = models.BooleanField(default=True)
    last_executed = models.DateTimeField(null=True, blank=True)
    next_execution = models.DateTimeField(null=True, blank=True)
    
    # Statistics
    total_processed = models.PositiveIntegerField(default=0)
    last_processed_count = models.PositiveIntegerField(default=0)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'system_log_retention_policies'
        ordering = ['name']
        verbose_name = 'System Log Retention Policy'
        verbose_name_plural = 'System Log Retention Policies'
    
    def __str__(self):
        return f"{self.name} ({self.retention_type})"
    
    def get_retention_display(self):
        if self.retention_type == 'TIME_BASED':
            return f"{self.retention_value} days"
        elif self.retention_type == 'SIZE_BASED':
            return f"{self.retention_value} MB"
        return str(self.retention_value)
    
    def should_process_log(self, log_entry):
        """Check if a log entry matches this policy's filters"""
        if not self.is_active:
            return False
        
        # Check severity levels
        if self.severity_levels and log_entry.severity not in self.severity_levels:
            return False
        
        # Check log types
        if self.log_types and log_entry.log_type not in self.log_types:
            return False
        
        # Check modules
        if self.modules and log_entry.module not in self.modules:
            return False
        
        # Check tags
        if self.tags and not any(tag in log_entry.tags for tag in self.tags):
            return False
        
        return True


class LogExport(models.Model):
    """
    Model to track log exports
    """
    EXPORT_FORMATS = [
        ('CSV', 'CSV'),
        ('JSON', 'JSON'),
        ('XML', 'XML'),
        ('PDF', 'PDF'),
        ('EXCEL', 'Excel'),
    ]
    
    EXPORT_STATUS = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Export configuration
    export_format = models.CharField(max_length=20, choices=EXPORT_FORMATS, default='CSV')
    filter_criteria = models.JSONField(default=dict)
    include_metadata = models.BooleanField(default=True)
    max_records = models.PositiveIntegerField(null=True, blank=True)
    
    # Export details
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE)
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=EXPORT_STATUS, default='PENDING')
    
    # Results
    record_count = models.PositiveIntegerField(default=0)
    file_size = models.PositiveIntegerField(null=True, blank=True)
    file_path = models.CharField(max_length=500, blank=True)
    download_url = models.URLField(max_length=1000, blank=True)
    
    # Error handling
    error_message = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'system_log_exports'
        ordering = ['-requested_at']
        verbose_name = 'System Log Export'
        verbose_name_plural = 'System Log Exports'
    
    def __str__(self):
        return f"{self.name} ({self.export_format}) - {self.status}"
    
    def get_status_display(self):
        return dict(self.EXPORT_STATUS).get(self.status, self.status)
    
    def get_format_display(self):
        return dict(self.EXPORT_FORMATS).get(self.export_format, self.export_format)
    
    def is_completed(self):
        return self.status == 'COMPLETED'
    
    def is_failed(self):
        return self.status == 'FAILED'
    
    def mark_completed(self, record_count, file_size, file_path):
        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        self.record_count = record_count
        self.file_size = file_size
        self.file_path = file_path
        self.save()
    
    def mark_failed(self, error_message):
        self.status = 'FAILED'
        self.error_message = error_message
        self.retry_count += 1
        self.save()
