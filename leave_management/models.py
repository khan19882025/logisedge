from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import date, timedelta
import uuid


class LeaveType(models.Model):
    """Model for different types of leaves"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default="#007bff", help_text="Hex color code")
    is_active = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=True)
    max_days_per_year = models.PositiveIntegerField(default=30)
    max_consecutive_days = models.PositiveIntegerField(default=14)
    min_notice_days = models.PositiveIntegerField(default=1)
    is_paid = models.BooleanField(default=True)
    can_carry_forward = models.BooleanField(default=False)
    max_carry_forward_days = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class LeavePolicy(models.Model):
    """Model for leave policies and rules"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    probation_period_months = models.PositiveIntegerField(default=6)
    annual_leave_days = models.PositiveIntegerField(default=30)
    sick_leave_days = models.PositiveIntegerField(default=15)
    casual_leave_days = models.PositiveIntegerField(default=10)
    maternity_leave_days = models.PositiveIntegerField(default=90)
    paternity_leave_days = models.PositiveIntegerField(default=14)
    carry_forward_percentage = models.PositiveIntegerField(
        default=50, 
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    encashment_allowed = models.BooleanField(default=False)
    encashment_percentage = models.PositiveIntegerField(
        default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Leave Policies"

    def __str__(self):
        return self.name


class LeaveRequest(models.Model):
    """Model for leave requests"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    request_id = models.CharField(max_length=20, unique=True, blank=True)
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    total_days = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    reason = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    attachment = models.FileField(upload_to='leave_attachments/', blank=True, null=True)
    
    # Approval workflow
    current_approver = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='pending_approvals'
    )
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='approved_leave_requests'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_comments = models.TextField(blank=True)
    
    # Timestamps
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Auto-calculated fields
    is_half_day = models.BooleanField(default=False)
    is_emergency = models.BooleanField(default=False)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.leave_type.name} ({self.start_date} to {self.end_date})"

    def save(self, *args, **kwargs):
        if not self.request_id:
            self.request_id = f"LR{timezone.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
        
        # Calculate total days
        if self.start_date and self.end_date:
            delta = self.end_date - self.start_date
            self.total_days = delta.days + 1  # Include both start and end dates
        
        super().save(*args, **kwargs)

    @property
    def is_overlapping(self):
        """Check if this leave request overlaps with existing approved leaves"""
        overlapping_leaves = LeaveRequest.objects.filter(
            employee=self.employee,
            status='approved',
            start_date__lte=self.end_date,
            end_date__gte=self.start_date
        ).exclude(id=self.id)
        return overlapping_leaves.exists()

    @property
    def can_be_approved(self):
        """Check if the leave request can be approved"""
        return (
            self.status == 'pending' and 
            not self.is_overlapping and
            self.has_sufficient_balance
        )

    @property
    def has_sufficient_balance(self):
        """Check if employee has sufficient leave balance"""
        balance = LeaveBalance.objects.filter(
            employee=self.employee,
            leave_type=self.leave_type,
            year=date.today().year
        ).first()
        
        if not balance:
            return False
        
        return balance.available_days >= self.total_days


class LeaveBalance(models.Model):
    """Model for tracking leave balances per employee and leave type"""
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_balances')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    year = models.PositiveIntegerField()
    
    # Balance fields
    allocated_days = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    used_days = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    carried_forward_days = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    encashed_days = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    
    # Auto-calculated fields
    available_days = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    total_balance = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['employee', 'leave_type', 'year']
        ordering = ['-year', 'leave_type__name']

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.leave_type.name} ({self.year})"

    def save(self, *args, **kwargs):
        # Calculate available days
        self.total_balance = self.allocated_days + self.carried_forward_days
        self.available_days = self.total_balance - self.used_days - self.encashed_days
        super().save(*args, **kwargs)

    @property
    def utilization_percentage(self):
        """Calculate leave utilization percentage"""
        if self.total_balance == 0:
            return 0
        return (self.used_days / self.total_balance) * 100


class LeaveApproval(models.Model):
    """Model for tracking approval workflow"""
    ACTION_CHOICES = [
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('return', 'Return for Revision'),
    ]

    leave_request = models.ForeignKey(LeaveRequest, on_delete=models.CASCADE, related_name='approvals')
    approver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_approvals')
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.approver.get_full_name()} - {self.action} - {self.leave_request}"


class LeaveNotification(models.Model):
    """Model for leave-related notifications"""
    NOTIFICATION_TYPES = [
        ('request_submitted', 'Leave Request Submitted'),
        ('request_approved', 'Leave Request Approved'),
        ('request_rejected', 'Leave Request Rejected'),
        ('request_cancelled', 'Leave Request Cancelled'),
        ('approval_required', 'Approval Required'),
        ('balance_low', 'Low Leave Balance'),
        ('leave_reminder', 'Leave Reminder'),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    related_leave_request = models.ForeignKey(
        LeaveRequest, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.recipient.get_full_name()} - {self.title}"


class LeaveCalendar(models.Model):
    """Model for calendar view of leaves"""
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_calendar_entries')
    leave_request = models.ForeignKey(LeaveRequest, on_delete=models.CASCADE, related_name='calendar_entries')
    date = models.DateField()
    is_half_day = models.BooleanField(default=False)
    half_day_type = models.CharField(
        max_length=10, 
        choices=[('morning', 'Morning'), ('afternoon', 'Afternoon')],
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['employee', 'date']
        ordering = ['date']

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.date}"


class LeaveEncashment(models.Model):
    """Model for leave encashment requests"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='encashment_requests')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    encashment_year = models.PositiveIntegerField()
    days_to_encash = models.DecimalField(max_digits=5, decimal_places=1)
    encashment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='approved_encashments'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.days_to_encash} days encashment"
