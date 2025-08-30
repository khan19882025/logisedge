import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, time, timedelta


class ScheduledTask(models.Model):
    """Model for storing scheduled task configurations"""
    
    TASK_TYPE_CHOICES = [
        ('backup', 'Database Backup'),
        ('report', 'Report Generation'),
        ('email', 'Email Notification'),
        ('sync', 'Data Sync'),
        ('custom', 'Custom Task'),
    ]
    
    SCHEDULE_TYPE_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('specific_datetime', 'Specific Date/Time'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('paused', 'Paused'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, help_text="Task name for identification")
    description = models.TextField(blank=True, help_text="Detailed description of the task")
    
    task_type = models.CharField(
        max_length=20, 
        choices=TASK_TYPE_CHOICES,
        help_text="Type of task to execute"
    )
    
    schedule_type = models.CharField(
        max_length=20,
        choices=SCHEDULE_TYPE_CHOICES,
        help_text="How often the task should run"
    )
    
    # Schedule configuration
    schedule_time = models.TimeField(help_text="Time of day to run the task")
    schedule_date = models.DateField(
        null=True, 
        blank=True, 
        help_text="Specific date for one-time tasks"
    )
    
    # Weekly schedule (for weekly tasks)
    monday = models.BooleanField(default=False)
    tuesday = models.BooleanField(default=False)
    wednesday = models.BooleanField(default=False)
    thursday = models.BooleanField(default=False)
    friday = models.BooleanField(default=False)
    saturday = models.BooleanField(default=False)
    sunday = models.BooleanField(default=False)
    
    # Monthly schedule (for monthly tasks)
    day_of_month = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        help_text="Day of month (1-31) for monthly tasks"
    )
    
    # Task configuration
    task_function = models.CharField(
        max_length=255,
        help_text="Python function path to execute (e.g., 'auto_task_scheduler.tasks.backup_database')"
    )
    
    task_parameters = models.JSONField(
        default=dict,
        blank=True,
        help_text="Parameters to pass to the task function"
    )
    
    # Status and execution
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='inactive',
        help_text="Current status of the task"
    )
    
    last_run_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When the task was last executed"
    )
    
    next_run_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When the task will run next"
    )
    
    # Task settings
    max_execution_time = models.PositiveIntegerField(
        default=300,
        help_text="Maximum execution time in seconds"
    )
    
    retry_on_failure = models.BooleanField(
        default=True,
        help_text="Whether to retry the task if it fails"
    )
    
    max_retries = models.PositiveIntegerField(
        default=3,
        help_text="Maximum number of retry attempts"
    )
    
    retry_delay = models.PositiveIntegerField(
        default=300,
        help_text="Delay between retries in seconds"
    )
    
    # User and permissions
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='scheduled_tasks',
        help_text="User who owns this task"
    )
    
    is_public = models.BooleanField(
        default=False,
        help_text="Whether other users can view this task"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Scheduled Task'
        verbose_name_plural = 'Scheduled Tasks'
        ordering = ['-created_at']
        permissions = [
            ("can_manage_tasks", "Can manage scheduled tasks"),
            ("can_run_tasks", "Can manually run scheduled tasks"),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_task_type_display()})"
    
    def clean(self):
        """Validate task configuration"""
        super().clean()
        
        # Validate schedule configuration based on schedule type
        if self.schedule_type == 'specific_datetime':
            if not self.schedule_date:
                raise ValidationError("Specific date is required for specific_datetime schedule type")
        
        elif self.schedule_type == 'weekly':
            # At least one day must be selected for weekly tasks
            weekdays = [self.monday, self.tuesday, self.wednesday, 
                       self.thursday, self.friday, self.saturday, self.sunday]
            if not any(weekdays):
                raise ValidationError("At least one weekday must be selected for weekly tasks")
        
        elif self.schedule_type == 'monthly':
            if not self.day_of_month or not (1 <= self.day_of_month <= 31):
                raise ValidationError("Day of month must be between 1 and 31 for monthly tasks")
        
        # Validate task parameters
        if not self.task_function:
            raise ValidationError("Task function is required")
    
    def save(self, *args, **kwargs):
        """Override save to calculate next run time"""
        if self.status == 'active':
            self.calculate_next_run()
        super().save(*args, **kwargs)
    
    def calculate_next_run(self):
        """Calculate when the task should run next"""
        now = timezone.now()
        
        if self.schedule_type == 'daily':
            # Next run is today or tomorrow at the specified time
            next_run = datetime.combine(now.date(), self.schedule_time)
            if next_run <= now:
                next_run += timedelta(days=1)
        
        elif self.schedule_type == 'weekly':
            # Find next occurrence based on selected weekdays
            next_run = self._get_next_weekly_run()
        
        elif self.schedule_type == 'monthly':
            # Next run is this month or next month on the specified day
            next_run = self._get_next_monthly_run()
        
        elif self.schedule_type == 'specific_datetime':
            # One-time task
            next_run = datetime.combine(self.schedule_date, self.schedule_time)
            if next_run <= now:
                self.status = 'inactive'  # Task is in the past
                next_run = None
        
        self.next_run_at = next_run
    
    def _get_next_weekly_run(self):
        """Calculate next weekly run based on selected weekdays"""
        now = timezone.now()
        current_weekday = now.weekday()
        
        # Map weekday numbers to our boolean fields
        weekdays = [
            self.monday, self.tuesday, self.wednesday, 
            self.thursday, self.friday, self.saturday, self.sunday
        ]
        
        # Check remaining days this week
        for i in range(current_weekday + 1, 7):
            if weekdays[i]:
                days_ahead = i - current_weekday
                next_run = datetime.combine(now.date(), self.schedule_time) + timedelta(days=days_ahead)
                if next_run > now:
                    return next_run
        
        # Check next week
        for i in range(7):
            if weekdays[i]:
                days_ahead = 7 - current_weekday + i
                next_run = datetime.combine(now.date(), self.schedule_time) + timedelta(days=days_ahead)
                return next_run
        
        return None
    
    def _get_next_monthly_run(self):
        """Calculate next monthly run"""
        now = timezone.now()
        current_day = now.day
        
        if current_day < self.day_of_month:
            # This month
            next_run = now.replace(day=self.day_of_month, 
                                 hour=self.schedule_time.hour,
                                 minute=self.schedule_time.minute,
                                 second=0, microsecond=0)
        else:
            # Next month
            if now.month == 12:
                next_run = now.replace(year=now.year + 1, month=1, day=self.day_of_month,
                                     hour=self.schedule_time.hour,
                                     minute=self.schedule_time.minute,
                                     second=0, microsecond=0)
            else:
                next_run = now.replace(month=now.month + 1, day=self.day_of_month,
                                     hour=self.schedule_time.hour,
                                     minute=self.schedule_time.minute,
                                     second=0, microsecond=0)
        
        return next_run
    
    def should_run_now(self):
        """Check if the task should run now"""
        if self.status != 'active':
            return False
        
        if not self.next_run_at:
            return False
        
        now = timezone.now()
        return now >= self.next_run_at
    
    def mark_as_run(self):
        """Mark the task as executed and calculate next run"""
        self.last_run_at = timezone.now()
        self.calculate_next_run()
        self.save(update_fields=['last_run_at', 'next_run_at'])
    
    def activate(self):
        """Activate the task"""
        self.status = 'active'
        self.calculate_next_run()
        self.save()
    
    def deactivate(self):
        """Deactivate the task"""
        self.status = 'inactive'
        self.next_run_at = None
        self.save()
    
    def pause(self):
        """Pause the task"""
        self.status = 'paused'
        self.save()


class ScheduledTaskLog(models.Model):
    """Model for logging task execution results"""
    
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failure', 'Failure'),
        ('running', 'Running'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(
        ScheduledTask,
        on_delete=models.CASCADE,
        related_name='execution_logs'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='running'
    )
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    execution_time = models.FloatField(
        null=True, 
        blank=True,
        help_text="Execution time in seconds"
    )
    
    output_message = models.TextField(
        blank=True,
        help_text="Task output or error message"
    )
    
    error_traceback = models.TextField(
        blank=True,
        help_text="Full error traceback if task failed"
    )
    
    # Task execution details
    celery_task_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Celery task ID for tracking"
    )
    
    worker_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Name of the worker that executed the task"
    )
    
    # Retry information
    retry_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of retry attempts"
    )
    
    is_retry = models.BooleanField(
        default=False,
        help_text="Whether this execution was a retry"
    )
    
    class Meta:
        verbose_name = 'Task Execution Log'
        verbose_name_plural = 'Task Execution Logs'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.task.name} - {self.get_status_display()} ({self.started_at})"
    
    def mark_completed(self, status='success', output_message='', error_traceback=''):
        """Mark the task execution as completed"""
        self.status = status
        self.completed_at = timezone.now()
        self.output_message = output_message
        self.error_traceback = error_traceback
        
        if self.completed_at and self.started_at:
            self.execution_time = (self.completed_at - self.started_at).total_seconds()
        
        self.save()
    
    def mark_failed(self, error_message, traceback=''):
        """Mark the task execution as failed"""
        self.mark_completed(
            status='failure',
            output_message=error_message,
            error_traceback=traceback
        )
    
    @property
    def duration_formatted(self):
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


class TaskSchedule(models.Model):
    """Model for storing Celery beat schedule configurations"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.OneToOneField(
        ScheduledTask,
        on_delete=models.CASCADE,
        related_name='celery_schedule'
    )
    
    schedule_key = models.CharField(
        max_length=255,
        unique=True,
        help_text="Unique key for Celery beat schedule"
    )
    
    is_registered = models.BooleanField(
        default=False,
        help_text="Whether this schedule is registered with Celery beat"
    )
    
    last_sync = models.DateTimeField(
        auto_now=True,
        help_text="When the schedule was last synchronized with Celery"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this schedule was created"
    )
    
    class Meta:
        verbose_name = 'Task Schedule'
        verbose_name_plural = 'Task Schedules'
    
    def __str__(self):
        return f"Schedule for {self.task.name}"
