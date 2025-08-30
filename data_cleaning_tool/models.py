from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class DataCleaningSession(models.Model):
    """Model to track data cleaning sessions"""
    SESSION_STATUS = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    CLEANING_TYPE = [
        ('master', 'Master Data'),
        ('transactional', 'Transactional Data'),
        ('financial', 'Financial Data'),
        ('comprehensive', 'Comprehensive'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    cleaning_type = models.CharField(max_length=50, choices=CLEANING_TYPE)
    status = models.CharField(max_length=20, choices=SESSION_STATUS, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Data selection criteria
    date_from = models.DateField(null=True, blank=True)
    date_to = models.DateField(null=True, blank=True)
    batch_size = models.IntegerField(default=1000)
    
    # Cleaning options
    remove_duplicates = models.BooleanField(default=False)
    fill_mandatory = models.BooleanField(default=False)
    standardize_format = models.BooleanField(default=False)
    validate_data = models.BooleanField(default=False)
    archive_old = models.BooleanField(default=False)
    create_backup = models.BooleanField(default=True)
    
    # Custom configuration
    custom_rules = models.JSONField(default=dict, blank=True)
    
    # Notification settings
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    notification_email = models.EmailField(blank=True)
    
    # Tracking fields
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_modified = models.DateTimeField(auto_now=True)
    
    # Statistics
    total_records_scanned = models.IntegerField(default=0)
    total_records_cleaned = models.IntegerField(default=0)
    total_errors_found = models.IntegerField(default=0)
    total_warnings_found = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"


class DataCleaningRule(models.Model):
    """Model to store configurable data cleaning rules"""
    RULE_TYPE = [
        ('duplicate_detection', 'Duplicate Detection'),
        ('format_validation', 'Format Validation'),
        ('mandatory_field_check', 'Mandatory Field Check'),
        ('data_type_validation', 'Data Type Validation'),
        ('business_rule_validation', 'Business Rule Validation'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    rule_type = models.CharField(max_length=50, choices=RULE_TYPE)
    target_model = models.CharField(max_length=100)  # Django model name
    target_field = models.CharField(max_length=100, blank=True)
    rule_config = models.JSONField(default=dict)  # Store rule-specific configuration
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['priority', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.get_rule_type_display()}"


class DataCleaningAuditLog(models.Model):
    """Model to track all data cleaning activities for audit purposes"""
    ACTION_TYPE = [
        ('record_created', 'Record Created'),
        ('record_updated', 'Record Updated'),
        ('record_deleted', 'Record Deleted'),
        ('record_merged', 'Record Merged'),
        ('field_updated', 'Field Updated'),
        ('validation_error', 'Validation Error'),
        ('warning_generated', 'Warning Generated'),
    ]
    
    session = models.ForeignKey(DataCleaningSession, on_delete=models.CASCADE)
    rule = models.ForeignKey(DataCleaningRule, on_delete=models.SET_NULL, null=True, blank=True)
    action_type = models.CharField(max_length=50, choices=ACTION_TYPE)
    target_model = models.CharField(max_length=100)
    target_record_id = models.CharField(max_length=100)
    field_name = models.CharField(max_length=100, blank=True)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.action_type} - {self.target_model}:{self.target_record_id}"


class DataQualityReport(models.Model):
    """Model to store data quality reports"""
    session = models.OneToOneField(DataCleaningSession, on_delete=models.CASCADE)
    report_data = models.JSONField(default=dict)  # Store comprehensive report data
    summary = models.TextField()
    recommendations = models.TextField()
    generated_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Quality Report - {self.session.name}"


class AutomatedCleaningSchedule(models.Model):
    """Model to configure automated data cleaning schedules"""
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    cleaning_type = models.CharField(max_length=50, choices=DataCleaningSession.CLEANING_TYPE)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.frequency}"
