import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
import croniter


class CronJob(models.Model):
    """Model to store cron job configurations"""
    SCHEDULE_TYPE_CHOICES = [
        ('cron', 'Cron Expression'),
        ('interval', 'Interval'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=200,
        help_text="Human-readable name for the cron job"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description of what this job does"
    )
    task = models.CharField(
        max_length=200,
        help_text="Celery task name to execute"
    )
    schedule = models.CharField(
        max_length=100,
        help_text="Cron expression (e.g., '0 0 * * *') or interval (e.g., '5 minutes')"
    )
    schedule_type = models.CharField(
        max_length=20,
        choices=SCHEDULE_TYPE_CHOICES,
        default='cron',
        help_text="Type of schedule"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the job is currently active"
    )
    next_run_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Next scheduled run time"
    )
    last_run_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Last execution time"
    )
    last_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_cron_jobs',
        help_text="User who owns this cron job"
    )
    
    class Meta:
        verbose_name = 'Cron Job'
        verbose_name_plural = 'Cron Jobs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.owner.username})"
    
    def clean(self):
        """Validate the schedule format"""
        if self.schedule_type == 'cron':
            try:
                croniter.croniter(self.schedule)
            except ValueError as e:
                raise ValidationError(f"Invalid cron expression: {e}")
        elif self.schedule_type == 'interval':
            # Basic interval validation
            if not any(unit in self.schedule.lower() for unit in ['second', 'minute', 'hour', 'day', 'week']):
                raise ValidationError("Interval must specify a time unit (e.g., '5 minutes', '1 hour')")
    
    def calculate_next_run(self):
        """Calculate the next run time based on schedule"""
        if self.schedule_type == 'cron':
            try:
                cron = croniter.croniter(self.schedule, timezone.now())
                self.next_run_at = cron.get_next(datetime)
                return self.next_run_at
            except Exception:
                return None
        elif self.schedule_type == 'interval':
            # Parse interval and calculate next run
            try:
                # Simple interval parsing (e.g., "5 minutes", "1 hour")
                parts = self.schedule.lower().split()
                if len(parts) == 2:
                    value = int(parts[0])
                    unit = parts[1]
                    
                    if unit.startswith('second'):
                        delta = timedelta(seconds=value)
                    elif unit.startswith('minute'):
                        delta = timedelta(minutes=value)
                    elif unit.startswith('hour'):
                        delta = timedelta(hours=value)
                    elif unit.startswith('day'):
                        delta = timedelta(days=value)
                    elif unit.startswith('week'):
                        delta = timedelta(weeks=value)
                    else:
                        return None
                    
                    self.next_run_at = timezone.now() + delta
                    return self.next_run_at
            except Exception:
                return None
        return None
    
    def save(self, *args, **kwargs):
        """Override save to calculate next run time"""
        if not self.next_run_at:
            self.calculate_next_run()
        super().save(*args, **kwargs)
    
    def mark_completed(self, success=True):
        """Mark job as completed"""
        self.last_run_at = timezone.now()
        self.last_status = 'success' if success else 'failed'
        self.calculate_next_run()
        self.save()
    
    def get_schedule_display(self):
        """Return human-readable schedule description"""
        if self.schedule_type == 'cron':
            try:
                cron = croniter.croniter(self.schedule)
                return cron.get_description()
            except:
                return self.schedule
        else:
            return f"Every {self.schedule}"


class CronJobLog(models.Model):
    """Model to store execution logs for cron jobs"""
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(
        CronJob,
        on_delete=models.CASCADE,
        related_name='execution_logs'
    )
    run_started_at = models.DateTimeField(auto_now_add=True)
    run_ended_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    output_message = models.TextField(
        blank=True,
        help_text="Task output or error message"
    )
    celery_task_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Celery task ID for tracking"
    )
    execution_time = models.FloatField(
        blank=True,
        null=True,
        help_text="Execution time in seconds"
    )
    worker_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Name of the worker that executed the task"
    )
    
    class Meta:
        verbose_name = 'Cron Job Log'
        verbose_name_plural = 'Cron Job Logs'
        ordering = ['-run_started_at']
    
    def __str__(self):
        return f"{self.job.name} - {self.status} at {self.run_started_at}"
    
    def mark_completed(self, success=True, output="", task_id=None, worker_name=None):
        """Mark log entry as completed"""
        self.run_ended_at = timezone.now()
        self.status = 'success' if success else 'failed'
        self.output_message = output
        self.celery_task_id = task_id
        self.worker_name = worker_name
        
        # Calculate execution time
        if self.run_started_at and self.run_ended_at:
            self.execution_time = (self.run_ended_at - self.run_started_at).total_seconds()
        
        self.save()
    
    def get_duration_formatted(self):
        """Return formatted execution duration"""
        if not self.execution_time:
            return "N/A"
        
        if self.execution_time < 60:
            return f"{self.execution_time:.1f}s"
        elif self.execution_time < 3600:
            minutes = int(self.execution_time // 60)
            seconds = int(self.execution_time % 60)
            return f"{minutes}m {seconds}s"
        else:
            hours = int(self.execution_time // 3600)
            minutes = int((self.execution_time % 3600) // 60)
            return f"{hours}h {minutes}m"
