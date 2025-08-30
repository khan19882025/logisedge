from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import date, datetime, timedelta
import uuid

from employees.models import Employee, Department


class AttendancePolicy(models.Model):
    """Attendance policy configuration"""
    name = models.CharField(max_length=100)
    grace_period_minutes = models.PositiveIntegerField(default=15, help_text="Grace period for late arrival in minutes")
    half_day_threshold_hours = models.DecimalField(max_digits=4, decimal_places=2, default=4.0, help_text="Hours required for half day")
    full_day_threshold_hours = models.DecimalField(max_digits=4, decimal_places=2, default=8.0, help_text="Hours required for full day")
    overtime_threshold_hours = models.DecimalField(max_digits=4, decimal_places=2, default=8.0, help_text="Hours after which overtime starts")
    break_duration_minutes = models.PositiveIntegerField(default=60, help_text="Total break duration in minutes")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Attendance Policies"

    def __str__(self):
        return self.name


class Shift(models.Model):
    """Work shift configuration"""
    SHIFT_TYPES = [
        ('morning', 'Morning'),
        ('afternoon', 'Afternoon'),
        ('night', 'Night'),
        ('flexible', 'Flexible'),
    ]
    
    name = models.CharField(max_length=100)
    shift_type = models.CharField(max_length=20, choices=SHIFT_TYPES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    break_start = models.TimeField(null=True, blank=True)
    break_end = models.TimeField(null=True, blank=True)
    total_hours = models.DecimalField(max_digits=4, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Shifts"

    def __str__(self):
        return f"{self.name} ({self.start_time} - {self.end_time})"


class Holiday(models.Model):
    """Holiday calendar"""
    HOLIDAY_TYPES = [
        ('public', 'Public Holiday'),
        ('company', 'Company Holiday'),
        ('optional', 'Optional Holiday'),
    ]
    
    name = models.CharField(max_length=200)
    date = models.DateField()
    holiday_type = models.CharField(max_length=20, choices=HOLIDAY_TYPES)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Holidays"
        ordering = ['date']

    def __str__(self):
        return f"{self.name} ({self.date})"


class Attendance(models.Model):
    """Daily attendance record"""
    ATTENDANCE_STATUS = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('half_day', 'Half Day'),
        ('on_leave', 'On Leave'),
        ('week_off', 'Week Off'),
        ('holiday', 'Holiday'),
        ('late', 'Late'),
        ('early_departure', 'Early Departure'),
    ]
    
    PUNCH_TYPES = [
        ('manual', 'Manual'),
        ('biometric', 'Biometric'),
        ('web', 'Web'),
        ('mobile', 'Mobile'),
        ('api', 'API'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    shift = models.ForeignKey(Shift, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Check-in details
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_in_location = models.CharField(max_length=255, blank=True)
    check_in_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    check_in_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    check_in_ip = models.GenericIPAddressField(null=True, blank=True)
    check_in_type = models.CharField(max_length=20, choices=PUNCH_TYPES, default='manual')
    
    # Check-out details
    check_out_time = models.DateTimeField(null=True, blank=True)
    check_out_location = models.CharField(max_length=255, blank=True)
    check_out_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    check_out_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    check_out_ip = models.GenericIPAddressField(null=True, blank=True)
    check_out_type = models.CharField(max_length=20, choices=PUNCH_TYPES, default='manual')
    
    # Calculated fields
    total_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    break_hours = models.DecimalField(max_digits=4, decimal_places=2, default=0.0)
    net_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Status and notes
    status = models.CharField(max_length=20, choices=ATTENDANCE_STATUS, default='absent')
    notes = models.TextField(blank=True)
    is_late = models.BooleanField(default=False)
    is_early_departure = models.BooleanField(default=False)
    
    # Audit fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='attendance_created')
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='attendance_modified')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Attendance Records"
        unique_together = ['employee', 'date']
        ordering = ['-date', 'employee__first_name']

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.date} ({self.status})"

    def save(self, *args, **kwargs):
        # Calculate total hours if both check-in and check-out times are present
        if self.check_in_time and self.check_out_time:
            duration = self.check_out_time - self.check_in_time
            self.total_hours = duration.total_seconds() / 3600
            
            # Calculate net hours (total - break)
            self.net_hours = self.total_hours - self.break_hours
            
            # Calculate overtime (assuming 8 hours standard day)
            if self.net_hours > 8:
                self.overtime_hours = self.net_hours - 8
            else:
                self.overtime_hours = 0
                
            # Determine status based on hours
            if self.net_hours >= 8:
                self.status = 'present'
            elif self.net_hours >= 4:
                self.status = 'half_day'
            else:
                self.status = 'absent'
        
        super().save(*args, **kwargs)


class Break(models.Model):
    """Break periods during work hours"""
    BREAK_TYPES = [
        ('lunch', 'Lunch'),
        ('tea', 'Tea/Coffee'),
        ('personal', 'Personal'),
        ('other', 'Other'),
    ]
    
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name='breaks')
    break_type = models.CharField(max_length=20, choices=BREAK_TYPES)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Breaks"
        ordering = ['start_time']

    def __str__(self):
        return f"{self.attendance.employee.get_full_name()} - {self.break_type} ({self.start_time.date()})"

    def save(self, *args, **kwargs):
        if self.end_time and self.start_time:
            duration = self.end_time - self.start_time
            self.duration_minutes = duration.total_seconds() / 60
        super().save(*args, **kwargs)


class TimeSheet(models.Model):
    """Weekly/Monthly timesheet for payroll"""
    TIMESHEET_PERIODS = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='timesheets')
    period_type = models.CharField(max_length=20, choices=TIMESHEET_PERIODS)
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Summary fields
    total_days = models.PositiveIntegerField(default=0)
    present_days = models.PositiveIntegerField(default=0)
    absent_days = models.PositiveIntegerField(default=0)
    leave_days = models.PositiveIntegerField(default=0)
    half_days = models.PositiveIntegerField(default=0)
    
    # Hours
    total_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)
    overtime_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)
    break_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)
    net_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)
    
    # Status
    is_submitted = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='timesheets_approved')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Time Sheets"
        unique_together = ['employee', 'start_date', 'end_date']
        ordering = ['-start_date', 'employee__first_name']

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.start_date} to {self.end_date}"


class AttendanceReport(models.Model):
    """Generated attendance reports"""
    REPORT_TYPES = [
        ('daily', 'Daily Attendance'),
        ('weekly', 'Weekly Summary'),
        ('monthly', 'Monthly Summary'),
        ('late_arrival', 'Late Arrival'),
        ('overtime', 'Overtime'),
        ('department', 'Department-wise'),
        ('custom', 'Custom Period'),
    ]
    
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Report data (JSON field for flexibility)
    report_data = models.JSONField(default=dict)
    
    # File attachments
    excel_file = models.FileField(upload_to='attendance_reports/excel/', null=True, blank=True)
    pdf_file = models.FileField(upload_to='attendance_reports/pdf/', null=True, blank=True)
    
    # Metadata
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    is_archived = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Attendance Reports"
        ordering = ['-generated_at']

    def __str__(self):
        return f"{self.name} ({self.start_date} to {self.end_date})"


class AttendanceAlert(models.Model):
    """Alerts for attendance issues"""
    ALERT_TYPES = [
        ('missing_punch', 'Missing Punch'),
        ('late_arrival', 'Late Arrival'),
        ('early_departure', 'Early Departure'),
        ('absent', 'Absent'),
        ('overtime', 'Overtime'),
        ('break_violation', 'Break Violation'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance_alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='medium')
    date = models.DateField()
    
    # Alert details
    title = models.CharField(max_length=200)
    description = models.TextField()
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='alerts_resolved')
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Attendance Alerts"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.alert_type} ({self.date})"


class PunchLog(models.Model):
    """Detailed punch-in/out logs for audit"""
    PUNCH_ACTIONS = [
        ('check_in', 'Check In'),
        ('check_out', 'Check Out'),
        ('break_start', 'Break Start'),
        ('break_end', 'Break End'),
    ]
    
    PUNCH_METHODS = [
        ('biometric', 'Biometric'),
        ('web', 'Web Interface'),
        ('mobile', 'Mobile App'),
        ('api', 'API'),
        ('manual', 'Manual Entry'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='punch_logs')
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name='punch_logs')
    punch_action = models.CharField(max_length=20, choices=PUNCH_ACTIONS)
    punch_method = models.CharField(max_length=20, choices=PUNCH_METHODS)
    punch_time = models.DateTimeField()
    
    # Location data
    location = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Additional data
    device_id = models.CharField(max_length=100, blank=True)
    session_id = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    # Audit
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='punch_logs_created')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Punch Logs"
        ordering = ['-punch_time']

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.punch_action} at {self.punch_time}"


# Utility functions
def get_attendance_status(employee, date):
    """Get attendance status for an employee on a specific date"""
    try:
        attendance = Attendance.objects.get(employee=employee, date=date)
        return attendance.status
    except Attendance.DoesNotExist:
        return 'absent'


def calculate_work_hours(check_in, check_out, breaks=None):
    """Calculate total work hours excluding breaks"""
    if not check_in or not check_out:
        return 0
    
    total_duration = check_out - check_in
    total_hours = total_duration.total_seconds() / 3600
    
    if breaks:
        break_hours = sum(b.duration_minutes for b in breaks) / 60
        return total_hours - break_hours
    
    return total_hours


def is_holiday(date):
    """Check if a date is a holiday"""
    return Holiday.objects.filter(date=date, is_active=True).exists()


def get_shift_hours(shift):
    """Get total hours for a shift"""
    if not shift:
        return 8.0  # Default 8 hours
    
    start = datetime.combine(date.today(), shift.start_time)
    end = datetime.combine(date.today(), shift.end_time)
    
    if end < start:  # Night shift
        end += timedelta(days=1)
    
    duration = end - start
    return duration.total_seconds() / 3600
