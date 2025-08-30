from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid
import os

class BackupType(models.Model):
    """Defines different types of backups available"""
    BACKUP_TYPES = [
        ('full', 'Full Backup'),
        ('incremental', 'Incremental Backup'),
        ('differential', 'Differential Backup'),
    ]
    
    name = models.CharField(max_length=50, choices=BACKUP_TYPES, unique=True)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Backup Type"
        verbose_name_plural = "Backup Types"

class BackupScope(models.Model):
    """Defines what data to include in backups"""
    SCOPE_CHOICES = [
        ('full_database', 'Full Database'),
        ('customers', 'Customers'),
        ('items', 'Items'),
        ('transactions', 'Transactions'),
        ('financial_data', 'Financial Data'),
        ('documents', 'Documents'),
        ('custom', 'Custom Selection'),
    ]
    
    name = models.CharField(max_length=50, choices=SCOPE_CHOICES, unique=True)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Backup Scope"
        verbose_name_plural = "Backup Scopes"

class StorageLocation(models.Model):
    """Defines storage locations for backups"""
    STORAGE_TYPES = [
        ('local', 'Local Storage'),
        ('network', 'Network Storage'),
        ('cloud', 'Cloud Storage'),
        ('ftp', 'FTP Server'),
        ('s3', 'Amazon S3'),
        ('azure', 'Azure Blob'),
        ('gcp', 'Google Cloud Storage'),
    ]
    
    name = models.CharField(max_length=100)
    storage_type = models.CharField(max_length=20, choices=STORAGE_TYPES)
    path = models.CharField(max_length=500)
    credentials = models.JSONField(default=dict, blank=True)  # Encrypted credentials
    is_active = models.BooleanField(default=True)
    max_capacity_gb = models.PositiveIntegerField(default=100)
    used_capacity_gb = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.storage_type})"
    
    class Meta:
        verbose_name = "Storage Location"
        verbose_name_plural = "Storage Locations"

class BackupSchedule(models.Model):
    """Defines automated backup schedules"""
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('custom', 'Custom'),
    ]
    
    WEEKDAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    backup_type = models.ForeignKey(BackupType, on_delete=models.CASCADE)
    backup_scope = models.ForeignKey(BackupScope, on_delete=models.CASCADE)
    storage_location = models.ForeignKey(StorageLocation, on_delete=models.CASCADE)
    
    # Scheduling
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    start_time = models.TimeField()
    start_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    # Weekly specific
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES, null=True, blank=True)
    
    # Monthly specific
    day_of_month = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        null=True, blank=True
    )
    
    # Custom cron expression
    cron_expression = models.CharField(max_length=100, blank=True)
    
    # Retention
    retention_days = models.PositiveIntegerField(default=30)
    max_backups = models.PositiveIntegerField(default=10)
    
    # Parallel execution
    allow_parallel = models.BooleanField(default=True)
    
    # Created by
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.frequency}"
    
    class Meta:
        verbose_name = "Backup Schedule"
        verbose_name_plural = "Backup Schedules"

class BackupExecution(models.Model):
    """Records individual backup executions"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    execution_id = models.UUIDField(default=uuid.uuid4, unique=True)
    schedule = models.ForeignKey(BackupSchedule, on_delete=models.CASCADE, null=True, blank=True)
    backup_type = models.ForeignKey(BackupType, on_delete=models.CASCADE)
    backup_scope = models.ForeignKey(BackupScope, on_delete=models.CASCADE)
    storage_location = models.ForeignKey(StorageLocation, on_delete=models.CASCADE)
    
    # Execution details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    
    # File details
    file_path = models.CharField(max_length=500, blank=True)
    file_size_mb = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    checksum = models.CharField(max_length=64, blank=True)
    
    # Error details
    error_message = models.TextField(blank=True)
    error_details = models.JSONField(default=dict, blank=True)
    
    # Manual vs Scheduled
    is_manual = models.BooleanField(default=False)
    triggered_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.execution_id} - {self.status}"
    
    class Meta:
        verbose_name = "Backup Execution"
        verbose_name_plural = "Backup Executions"
        ordering = ['-created_at']

class BackupRetentionPolicy(models.Model):
    """Defines retention policies for different backup types"""
    name = models.CharField(max_length=100)
    backup_type = models.ForeignKey(BackupType, on_delete=models.CASCADE)
    retention_days = models.PositiveIntegerField()
    retention_count = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.retention_days} days"
    
    class Meta:
        verbose_name = "Retention Policy"
        verbose_name_plural = "Retention Policies"

class BackupAlert(models.Model):
    """Defines alert configurations for backup monitoring"""
    ALERT_TYPES = [
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('failure', 'Failure'),
        ('storage_full', 'Storage Full'),
        ('retention_cleanup', 'Retention Cleanup'),
    ]
    
    CHANNEL_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('webhook', 'Webhook'),
        ('dashboard', 'Dashboard'),
    ]
    
    name = models.CharField(max_length=100)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    recipients = models.JSONField(default=list)  # List of email/phone numbers
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.alert_type}"
    
    class Meta:
        verbose_name = "Backup Alert"
        verbose_name_plural = "Backup Alerts"

class BackupLog(models.Model):
    """Logs all backup-related activities for audit purposes"""
    LOG_LEVELS = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    timestamp = models.DateTimeField(auto_now_add=True)
    level = models.CharField(max_length=20, choices=LOG_LEVELS)
    message = models.TextField()
    execution = models.ForeignKey(BackupExecution, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    additional_data = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        return f"{self.timestamp} - {self.level}: {self.message}"
    
    class Meta:
        verbose_name = "Backup Log"
        verbose_name_plural = "Backup Logs"
        ordering = ['-timestamp']

class DisasterRecoveryPlan(models.Model):
    """Defines disaster recovery procedures and test schedules"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    backup_execution = models.ForeignKey(BackupExecution, on_delete=models.CASCADE)
    recovery_procedures = models.JSONField(default=dict)
    test_schedule = models.CharField(max_length=100)  # Cron expression
    last_tested = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Disaster Recovery Plan"
        verbose_name_plural = "Disaster Recovery Plans"
