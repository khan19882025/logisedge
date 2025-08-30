import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import FileExtensionValidator
import json


class ImportTemplate(models.Model):
    """Model for managing import templates with predefined column mappings"""
    DATA_TYPES = [
        ('customers', 'Customers'),
        ('vendors', 'Vendors'),
        ('products', 'Products'),
        ('chart_of_accounts', 'Chart of Accounts'),
        ('employees', 'Employees'),
        ('inventory_items', 'Inventory Items'),
        ('price_lists', 'Price Lists'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    data_type = models.CharField(max_length=50, choices=DATA_TYPES)
    description = models.TextField(blank=True)
    column_mappings = models.JSONField(default=dict)  # Store column mappings
    validation_rules = models.JSONField(default=dict)  # Store validation rules
    required_fields = models.JSONField(default=list)  # List of required fields
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_templates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Import Template'
        verbose_name_plural = 'Import Templates'
    
    def __str__(self):
        return f"{self.name} ({self.get_data_type_display()})"


class ImportJob(models.Model):
    """Model for tracking import jobs and their status"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_name = models.CharField(max_length=200)
    template = models.ForeignKey(ImportTemplate, on_delete=models.CASCADE, related_name='import_jobs')
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField()  # File size in bytes
    total_rows = models.IntegerField(default=0)
    processed_rows = models.IntegerField(default=0)
    successful_rows = models.IntegerField(default=0)
    failed_rows = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='import_jobs')
    created_at = models.DateTimeField(auto_now_add=True)
    error_log = models.JSONField(default=list)  # Store error details
    import_summary = models.JSONField(default=dict)  # Store import summary
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Import Job'
        verbose_name_plural = 'Import Jobs'
    
    def __str__(self):
        return f"{self.job_name} - {self.get_status_display()}"
    
    @property
    def duration(self):
        """Calculate job duration"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None
    
    @property
    def progress_percentage(self):
        """Calculate progress percentage"""
        if self.total_rows > 0:
            return (self.processed_rows / self.total_rows) * 100
        return 0


class ImportValidationRule(models.Model):
    """Model for defining validation rules for different data types"""
    RULE_TYPES = [
        ('required', 'Required Field'),
        ('unique', 'Unique Value'),
        ('format', 'Format Validation'),
        ('range', 'Range Validation'),
        ('reference', 'Foreign Key Reference'),
        ('custom', 'Custom Validation'),
    ]
    
    VALIDATION_TYPES = [
        ('email', 'Email'),
        ('phone', 'Phone Number'),
        ('date', 'Date'),
        ('number', 'Number'),
        ('decimal', 'Decimal'),
        ('url', 'URL'),
        ('regex', 'Regular Expression'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(ImportTemplate, on_delete=models.CASCADE, related_name='template_validation_rules')
    field_name = models.CharField(max_length=100)
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES)
    validation_type = models.CharField(max_length=20, choices=VALIDATION_TYPES, blank=True)
    rule_config = models.JSONField(default=dict)  # Store rule configuration
    error_message = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['template', 'field_name']
        verbose_name = 'Import Validation Rule'
        verbose_name_plural = 'Import Validation Rules'
    
    def __str__(self):
        return f"{self.template.name} - {self.field_name} ({self.get_rule_type_display()})"


class ImportAuditLog(models.Model):
    """Model for auditing import operations"""
    ACTION_TYPES = [
        ('upload', 'File Upload'),
        ('validate', 'Data Validation'),
        ('import', 'Data Import'),
        ('error', 'Error Occurred'),
        ('complete', 'Import Complete'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    import_job = models.ForeignKey(ImportJob, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    message = models.TextField()
    details = models.JSONField(default=dict)  # Store additional details
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Import Audit Log'
        verbose_name_plural = 'Import Audit Logs'
    
    def __str__(self):
        return f"{self.import_job.job_name} - {self.get_action_display()}"


class ImportDataError(models.Model):
    """Model for storing detailed import errors"""
    ERROR_TYPES = [
        ('validation', 'Validation Error'),
        ('duplicate', 'Duplicate Error'),
        ('reference', 'Reference Error'),
        ('format', 'Format Error'),
        ('system', 'System Error'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    import_job = models.ForeignKey(ImportJob, on_delete=models.CASCADE, related_name='errors')
    row_number = models.IntegerField()
    column_name = models.CharField(max_length=100, blank=True)
    error_type = models.CharField(max_length=20, choices=ERROR_TYPES)
    error_message = models.TextField()
    field_value = models.TextField(blank=True)  # The problematic value
    suggested_correction = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['import_job', 'row_number']
        verbose_name = 'Import Error'
        verbose_name_plural = 'Import Errors'
    
    def __str__(self):
        return f"Row {self.row_number}: {self.error_message}"


class ImportFile(models.Model):
    """Model for storing uploaded import files"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    import_job = models.OneToOneField(ImportJob, on_delete=models.CASCADE, related_name='import_file')
    file = models.FileField(
        upload_to='import_files/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['csv', 'xlsx', 'xls'])]
    )
    original_filename = models.CharField(max_length=255)
    file_hash = models.CharField(max_length=64, blank=True)  # For duplicate detection
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Import File'
        verbose_name_plural = 'Import Files'
    
    def __str__(self):
        return f"{self.original_filename} ({self.import_job.job_name})"
