from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
import hashlib
import os


class BackupConfiguration(models.Model):
    """Configuration settings for backup operations"""
    
    BACKUP_TYPES = [
        ('full', 'Full System Backup'),
        ('database', 'Database Only'),
        ('files', 'Files Only'),
        ('config', 'Configuration Only'),
    ]
    
    COMPRESSION_LEVELS = [
        ('none', 'None'),
        ('fast', 'Fast'),
        ('balanced', 'Balanced'),
        ('maximum', 'Maximum'),
    ]
    
    ENCRYPTION_TYPES = [
        ('none', 'None'),
        ('aes128', 'AES-128'),
        ('aes256', 'AES-256'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    backup_type = models.CharField(max_length=20, choices=BACKUP_TYPES, default='full')
    compression_level = models.CharField(max_length=20, choices=COMPRESSION_LEVELS, default='balanced')
    encryption_type = models.CharField(max_length=20, choices=ENCRYPTION_TYPES, default='aes256')
    retention_days = models.IntegerField(default=30)
    include_media = models.BooleanField(default=True)
    include_static = models.BooleanField(default=True)
    include_database = models.BooleanField(default=True)
    include_config = models.BooleanField(default=True)
    exclude_patterns = models.TextField(blank=True, help_text="File patterns to exclude (one per line)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Backup Configuration"
        verbose_name_plural = "Backup Configurations"
    
    def __str__(self):
        return self.name


class BackupSession(models.Model):
    """Individual backup session with detailed tracking"""
    
    BACKUP_REASONS = [
        ('general', 'General System Backup'),
        ('predepLOY', 'Pre-Deployment Backup'),
        ('postdeploy', 'Post-Deployment Backup'),
        ('maintenance', 'System Maintenance'),
        ('emergency', 'Emergency Backup'),
        ('scheduled', 'Scheduled Backup'),
        ('manual', 'Manual Backup'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Unique identifier for the backup
    backup_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    
    # Basic information
    name = models.CharField(max_length=255, help_text="Backup filename")
    reason = models.CharField(max_length=20, choices=BACKUP_REASONS)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_LEVELS, default='normal')
    
    # Configuration
    configuration = models.ForeignKey(BackupConfiguration, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Status and progress
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress_percentage = models.IntegerField(default=0)
    current_step = models.CharField(max_length=100, blank=True)
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    
    # File information
    file_size_bytes = models.BigIntegerField(null=True, blank=True)
    file_path = models.CharField(max_length=500, blank=True)
    checksum_sha256 = models.CharField(max_length=64, blank=True)
    
    # Storage locations
    primary_storage_path = models.CharField(max_length=500, blank=True)
    secondary_storage_path = models.CharField(max_length=500, blank=True)
    
    # Verification
    integrity_verified = models.BooleanField(default=False)
    verification_checksum = models.CharField(max_length=64, blank=True)
    verification_timestamp = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='backups_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Notifications
    notify_emails = models.TextField(blank=True, help_text="Comma-separated list of email addresses")
    notification_sent = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Backup Session"
        verbose_name_plural = "Backup Sessions"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        # Generate backup name if not provided
        if not self.name:
            timestamp = timezone.now().strftime("%Y%m%d_%H%M")
            reason_prefix = self.reason.upper()
            self.name = f"{reason_prefix}_{timestamp}_{self.reason}"
        
        super().save(*args, **kwargs)
    
    @property
    def duration_formatted(self):
        """Return formatted duration string"""
        if not self.duration_seconds:
            return "N/A"
        
        hours = self.duration_seconds // 3600
        minutes = (self.duration_seconds % 3600) // 60
        seconds = self.duration_seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    @property
    def file_size_formatted(self):
        """Return formatted file size string"""
        if not self.file_size_bytes:
            return "N/A"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if self.file_size_bytes < 1024.0:
                return f"{self.file_size_bytes:.1f} {unit}"
            self.file_size_bytes /= 1024.0
        return f"{self.file_size_bytes:.1f} PB"


class BackupStep(models.Model):
    """Individual steps within a backup session"""
    
    STEP_TYPES = [
        ('preparation', 'Preparation'),
        ('database_backup', 'Database Backup'),
        ('file_backup', 'File Backup'),
        ('checksum_generation', 'Checksum Generation'),
        ('encryption', 'Encryption'),
        ('storage', 'Storage'),
        ('verification', 'Verification'),
        ('cleanup', 'Cleanup'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ]
    
    backup_session = models.ForeignKey(BackupSession, on_delete=models.CASCADE, related_name='steps')
    step_type = models.CharField(max_length=30, choices=STEP_TYPES)
    step_name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    order = models.IntegerField()
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    
    # Progress and details
    progress_percentage = models.IntegerField(default=0)
    details = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Backup Step"
        verbose_name_plural = "Backup Steps"
        ordering = ['backup_session', 'order']
        unique_together = ['backup_session', 'order']
    
    def __str__(self):
        return f"{self.backup_session.name} - {self.step_name}"


class BackupAuditLog(models.Model):
    """Comprehensive audit log for all backup operations"""
    
    LOG_LEVELS = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    backup_session = models.ForeignKey(BackupSession, on_delete=models.CASCADE, related_name='audit_logs', null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    level = models.CharField(max_length=20, choices=LOG_LEVELS, default='info')
    message = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    
    # User context
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Backup Audit Log"
        verbose_name_plural = "Backup Audit Logs"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.timestamp} - {self.get_level_display()}: {self.message[:50]}"


class BackupStorageLocation(models.Model):
    """Storage locations for backup files"""
    
    STORAGE_TYPES = [
        ('local', 'Local Storage'),
        ('network', 'Network Storage'),
        ('cloud', 'Cloud Storage'),
        ('tape', 'Tape Storage'),
        ('offline', 'Offline/Air-gapped'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    storage_type = models.CharField(max_length=20, choices=STORAGE_TYPES)
    path = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    
    # Capacity and usage
    total_capacity_bytes = models.BigIntegerField(null=True, blank=True)
    available_capacity_bytes = models.BigIntegerField(null=True, blank=True)
    
    # Configuration
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    encryption_required = models.BooleanField(default=True)
    
    # Connection details
    host = models.CharField(max_length=255, blank=True)
    port = models.IntegerField(null=True, blank=True)
    username = models.CharField(max_length=100, blank=True)
    credentials_encrypted = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Backup Storage Location"
        verbose_name_plural = "Backup Storage Locations"
    
    def __str__(self):
        return f"{self.name} ({self.get_storage_type_display()})"
    
    @property
    def usage_percentage(self):
        """Calculate storage usage percentage"""
        if not self.total_capacity_bytes or not self.available_capacity_bytes:
            return 0
        
        used = self.total_capacity_bytes - self.available_capacity_bytes
        return (used / self.total_capacity_bytes) * 100


class BackupRetentionPolicy(models.Model):
    """Retention policies for backup files"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    # Retention rules
    keep_daily_for_days = models.IntegerField(default=7)
    keep_weekly_for_weeks = models.IntegerField(default=4)
    keep_monthly_for_months = models.IntegerField(default=12)
    keep_yearly_for_years = models.IntegerField(default=5)
    
    # Special retention
    keep_forever = models.BooleanField(default=False)
    minimum_retention_days = models.IntegerField(default=1)
    
    # Cleanup settings
    auto_cleanup = models.BooleanField(default=True)
    cleanup_schedule = models.CharField(max_length=100, blank=True, help_text="Cron expression for cleanup schedule")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Backup Retention Policy"
        verbose_name_plural = "Backup Retention Policies"
    
    def __str__(self):
        return self.name
