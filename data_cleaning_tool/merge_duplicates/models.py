from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
import json


class DuplicateDetectionSession(models.Model):
    """Session for tracking duplicate detection and merge operations"""
    
    SESSION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=SESSION_STATUS_CHOICES, default='pending')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Configuration settings
    config = models.JSONField(default=dict, help_text="Deduplication configuration parameters")
    
    # Results summary
    total_records_processed = models.IntegerField(default=0)
    duplicates_found = models.IntegerField(default=0)
    records_merged = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"
    
    def start_session(self):
        self.status = 'running'
        self.started_at = timezone.now()
        self.save()
    
    def complete_session(self):
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
    
    def fail_session(self):
        self.status = 'failed'
        self.completed_at = timezone.now()
        self.save()


class DuplicateGroup(models.Model):
    """Group of records identified as potential duplicates"""
    
    session = models.ForeignKey(DuplicateDetectionSession, on_delete=models.CASCADE)
    entity_type = models.CharField(max_length=50, help_text="Type of entity (customer, vendor, item, etc.)")
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, help_text="Confidence score for duplicate detection")
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Merge decision
    is_merged = models.BooleanField(default=False)
    merged_at = models.DateTimeField(null=True, blank=True)
    merged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-confidence_score', '-created_at']
    
    def __str__(self):
        return f"{self.entity_type} duplicates - Score: {self.confidence_score}"


class DuplicateRecord(models.Model):
    """Individual record within a duplicate group"""
    
    duplicate_group = models.ForeignKey(DuplicateGroup, on_delete=models.CASCADE)
    record_id = models.CharField(max_length=100, help_text="ID of the duplicate record")
    record_data = models.JSONField(help_text="Snapshot of record data at detection time")
    is_master = models.BooleanField(default=False, help_text="Whether this is the master record after merge")
    merge_priority = models.IntegerField(default=0, help_text="Priority for selection as master record")
    
    # Data quality metrics
    completeness_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    recency_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    class Meta:
        ordering = ['-overall_score']
    
    def __str__(self):
        return f"Record {self.record_id} (Score: {self.overall_score})"


class MergeOperation(models.Model):
    """Record of a merge operation performed"""
    
    MERGE_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('rolled_back', 'Rolled Back'),
    ]
    
    duplicate_group = models.ForeignKey(DuplicateGroup, on_delete=models.CASCADE)
    master_record = models.ForeignKey(DuplicateRecord, on_delete=models.CASCADE, related_name='master_merges')
    status = models.CharField(max_length=20, choices=MERGE_STATUS_CHOICES, default='pending')
    
    # Merge details
    merge_config = models.JSONField(default=dict, help_text="Configuration used for the merge")
    merge_result = models.JSONField(default=dict, help_text="Result of the merge operation")
    
    # Audit trail
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Error handling
    error_message = models.TextField(blank=True)
    rollback_reason = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Merge {self.id} - {self.duplicate_group.entity_type} ({self.get_status_display()})"


class MergeAuditLog(models.Model):
    """Detailed audit log for merge operations"""
    
    LOG_LEVEL_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    merge_operation = models.ForeignKey(MergeOperation, on_delete=models.CASCADE)
    level = models.CharField(max_length=20, choices=LOG_LEVEL_CHOICES, default='info')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Additional context
    context_data = models.JSONField(default=dict, help_text="Additional context for the log entry")
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.timestamp} - {self.level.upper()}: {self.message}"


class DeduplicationRule(models.Model):
    """Configurable rules for duplicate detection"""
    
    RULE_TYPE_CHOICES = [
        ('exact_match', 'Exact Match'),
        ('fuzzy_match', 'Fuzzy Match'),
        ('phonetic_match', 'Phonetic Match'),
        ('custom_rule', 'Custom Rule'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    rule_type = models.CharField(max_length=20, choices=RULE_TYPE_CHOICES)
    entity_type = models.CharField(max_length=50, help_text="Type of entity this rule applies to")
    
    # Rule configuration
    rule_config = models.JSONField(default=dict, help_text="Configuration parameters for the rule")
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0, help_text="Priority order for rule execution")
    
    # Thresholds
    similarity_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=0.8)
    confidence_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=0.7)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['priority', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_rule_type_display()})"
    
    def clean(self):
        """Validate rule configuration"""
        if self.similarity_threshold < 0 or self.similarity_threshold > 1:
            raise ValidationError("Similarity threshold must be between 0 and 1")
        if self.confidence_threshold < 0 or self.confidence_threshold > 1:
            raise ValidationError("Confidence threshold must be between 0 and 1")


class ScheduledDeduplication(models.Model):
    """Scheduled deduplication tasks"""
    
    SCHEDULE_TYPE_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('custom', 'Custom'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    schedule_type = models.CharField(max_length=20, choices=SCHEDULE_TYPE_CHOICES)
    cron_expression = models.CharField(max_length=100, blank=True, help_text="Cron expression for custom schedules")
    
    # Configuration
    config = models.JSONField(default=dict, help_text="Deduplication configuration for this schedule")
    is_active = models.BooleanField(default=True)
    
    # Execution tracking
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_schedule_type_display()})"
