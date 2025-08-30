from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid
import json

class RestoreRequest(models.Model):
    """Manages restore requests with approval workflow"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    RESTORE_TYPE_CHOICES = [
        ('full_database', 'Full Database'),
        ('module_specific', 'Module Specific'),
        ('point_in_time', 'Point-in-Time Recovery'),
        ('selective_records', 'Selective Records'),
        ('staging_test', 'Staging/Test Environment'),
    ]
    
    request_id = models.UUIDField(default=uuid.uuid4, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Restore Configuration
    restore_type = models.CharField(max_length=20, choices=RESTORE_TYPE_CHOICES)
    target_environment = models.CharField(max_length=50, default='production')  # production, staging, test
    
    # Source Backup
    source_backup = models.ForeignKey('backup_scheduler.BackupExecution', on_delete=models.CASCADE, null=True, blank=True)
    source_file_path = models.CharField(max_length=500, blank=True)  # For uploaded files
    source_checksum = models.CharField(max_length=64, blank=True)
    
    # Restore Scope
    restore_modules = models.JSONField(default=list, blank=True)  # List of modules to restore
    restore_tables = models.JSONField(default=list, blank=True)  # Specific tables
    restore_records = models.JSONField(default=dict, blank=True)  # Record-level filters
    
    # Point-in-time recovery
    target_timestamp = models.DateTimeField(null=True, blank=True)
    
    # Scheduling
    scheduled_at = models.DateTimeField(null=True, blank=True)
    estimated_duration = models.PositiveIntegerField(help_text="Estimated duration in minutes", null=True, blank=True)
    
    # Status and Progress
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    progress_percentage = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Approval Workflow
    requires_approval = models.BooleanField(default=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='restore_approvals')
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)
    
    # Execution Details
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    actual_duration = models.PositiveIntegerField(null=True, blank=True)
    
    # Results
    restored_file_path = models.CharField(max_length=500, blank=True)
    restored_file_size_mb = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    restored_records_count = models.PositiveIntegerField(null=True, blank=True)
    
    # Error Handling
    error_message = models.TextField(blank=True)
    error_details = models.JSONField(default=dict, blank=True)
    
    # Safety Features
    backup_before_restore = models.BooleanField(default=True)
    dry_run_enabled = models.BooleanField(default=False)
    rollback_plan = models.TextField(blank=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='restore_requests')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Restore Request"
        verbose_name_plural = "Restore Requests"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"
    
    def can_approve(self, user):
        """Check if user can approve this restore request"""
        return (self.status == 'pending' and 
                self.requires_approval and 
                user.has_perm('backup_scheduler.approve_restorerequest'))
    
    def can_execute(self, user):
        """Check if user can execute this restore request"""
        return (self.status == 'approved' and 
                user.has_perm('backup_scheduler.execute_restorerequest'))
    
    def get_estimated_completion(self):
        """Calculate estimated completion time"""
        if self.scheduled_at and self.estimated_duration:
            return self.scheduled_at + timezone.timedelta(minutes=self.estimated_duration)
        return None

class RestoreExecution(models.Model):
    """Records individual restore executions"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('rolled_back', 'Rolled Back'),
    ]
    
    execution_id = models.UUIDField(default=uuid.uuid4, unique=True)
    restore_request = models.ForeignKey(RestoreRequest, on_delete=models.CASCADE)
    
    # Execution Details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    
    # Progress Tracking
    current_step = models.CharField(max_length=100, blank=True)
    total_steps = models.PositiveIntegerField(default=1)
    current_step_number = models.PositiveIntegerField(default=0)
    
    # Results
    restored_tables = models.JSONField(default=list, blank=True)
    restored_records = models.PositiveIntegerField(null=True, blank=True)
    data_integrity_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Error Details
    error_message = models.TextField(blank=True)
    error_step = models.CharField(max_length=100, blank=True)
    
    # Rollback Information
    rollback_executed = models.BooleanField(default=False)
    rollback_reason = models.TextField(blank=True)
    
    # Metadata
    executed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Restore Execution"
        verbose_name_plural = "Restore Executions"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.restore_request.title} - {self.get_status_display()}"

class RestoreLog(models.Model):
    """Logs all restore-related activities for audit purposes"""
    LOG_LEVELS = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    timestamp = models.DateTimeField(auto_now_add=True)
    level = models.CharField(max_length=20, choices=LOG_LEVELS)
    message = models.TextField()
    
    # Related Objects
    restore_request = models.ForeignKey(RestoreRequest, on_delete=models.CASCADE, null=True, blank=True)
    restore_execution = models.ForeignKey(RestoreExecution, on_delete=models.CASCADE, null=True, blank=True)
    
    # Context
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    additional_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = "Restore Log"
        verbose_name_plural = "Restore Logs"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.timestamp} - {self.level}: {self.message}"

class RestoreApprovalWorkflow(models.Model):
    """Defines approval workflows for restore requests"""
    WORKFLOW_TYPES = [
        ('single_approver', 'Single Approver'),
        ('multiple_approvers', 'Multiple Approvers (All Required)'),
        ('hierarchical', 'Hierarchical Approval'),
        ('committee', 'Committee Approval'),
    ]
    
    name = models.CharField(max_length=100)
    workflow_type = models.CharField(max_length=20, choices=WORKFLOW_TYPES)
    description = models.TextField(blank=True)
    
    # Approval Rules
    requires_approval = models.BooleanField(default=True)
    auto_approve_low_priority = models.BooleanField(default=False)
    auto_approve_own_requests = models.BooleanField(default=False)
    
    # Approver Configuration
    approvers = models.JSONField(default=list)  # List of user IDs or roles
    min_approvals_required = models.PositiveIntegerField(default=1)
    
    # Notification Settings
    notify_approvers = models.BooleanField(default=True)
    notify_requestor = models.BooleanField(default=True)
    notify_admins = models.BooleanField(default=False)
    
    # Timeout Settings
    approval_timeout_hours = models.PositiveIntegerField(default=24)
    escalation_enabled = models.BooleanField(default=True)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Restore Approval Workflow"
        verbose_name_plural = "Restore Approval Workflows"
    
    def __str__(self):
        return self.name

class RestoreValidationRule(models.Model):
    """Defines validation rules for restore operations"""
    VALIDATION_TYPES = [
        ('data_integrity', 'Data Integrity Check'),
        ('referential_integrity', 'Referential Integrity Check'),
        ('business_logic', 'Business Logic Validation'),
        ('custom_validation', 'Custom Validation'),
    ]
    
    name = models.CharField(max_length=100)
    validation_type = models.CharField(max_length=20, choices=VALIDATION_TYPES)
    description = models.TextField()
    
    # Validation Configuration
    validation_query = models.TextField(blank=True)  # SQL or custom logic
    validation_script = models.TextField(blank=True)  # Python script
    expected_result = models.TextField(blank=True)
    
    # Execution Settings
    run_before_restore = models.BooleanField(default=False)
    run_after_restore = models.BooleanField(default=True)
    is_critical = models.BooleanField(default=False)  # Must pass for restore to succeed
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Restore Validation Rule"
        verbose_name_plural = "Restore Validation Rules"
    
    def __str__(self):
        return self.name

class RestoreNotification(models.Model):
    """Manages notifications for restore operations"""
    NOTIFICATION_TYPES = [
        ('request_created', 'Request Created'),
        ('approval_required', 'Approval Required'),
        ('approved', 'Request Approved'),
        ('rejected', 'Request Rejected'),
        ('execution_started', 'Execution Started'),
        ('execution_completed', 'Execution Completed'),
        ('execution_failed', 'Execution Failed'),
        ('validation_failed', 'Validation Failed'),
    ]
    
    CHANNEL_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('webhook', 'Webhook'),
        ('dashboard', 'Dashboard'),
        ('slack', 'Slack'),
        ('teams', 'Microsoft Teams'),
    ]
    
    restore_request = models.ForeignKey(RestoreRequest, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    
    # Recipients
    recipients = models.JSONField(default=list)  # List of email/phone numbers
    user_groups = models.JSONField(default=list)  # List of user group IDs
    
    # Content
    subject = models.CharField(max_length=200, blank=True)
    message_template = models.TextField(blank=True)
    
    # Delivery Status
    sent_at = models.DateTimeField(null=True, blank=True)
    delivery_status = models.CharField(max_length=20, default='pending')
    error_message = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Restore Notification"
        verbose_name_plural = "Restore Notifications"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.restore_request.title} - {self.get_notification_type_display()}"
