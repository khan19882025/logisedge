from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, datetime, timedelta
import json

from .models import (
    Attendance, Break, Shift, Holiday, AttendancePolicy, 
    TimeSheet, AttendanceReport, AttendanceAlert, PunchLog
)
from employees.models import Employee, Department


class AttendanceEntryForm(forms.ModelForm):
    """Form for manual attendance entry"""
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(status='active'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        initial=date.today()
    )
    check_in_time = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'})
    )
    check_out_time = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'})
    )
    
    class Meta:
        model = Attendance
        fields = [
            'employee', 'date', 'shift', 'check_in_time', 'check_out_time',
            'check_in_location', 'check_out_location', 'notes', 'status'
        ]
        widgets = {
            'shift': forms.Select(attrs={'class': 'form-select'}),
            'check_in_location': forms.TextInput(attrs={'class': 'form-control'}),
            'check_out_location': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        employee = cleaned_data.get('employee')
        date = cleaned_data.get('date')
        check_in_time = cleaned_data.get('check_in_time')
        check_out_time = cleaned_data.get('check_out_time')
        
        # Check if attendance already exists for this employee and date
        if employee and date:
            existing_attendance = Attendance.objects.filter(
                employee=employee, date=date
            ).exclude(pk=self.instance.pk if self.instance.pk else None)
            
            if existing_attendance.exists():
                raise ValidationError(
                    f"Attendance record already exists for {employee.get_full_name()} on {date}"
                )
        
        # Validate check-in and check-out times
        if check_in_time and check_out_time:
            if check_out_time <= check_in_time:
                raise ValidationError("Check-out time must be after check-in time")
            
            # Check if times are on the same date
            if check_in_time.date() != check_out_time.date():
                raise ValidationError("Check-in and check-out must be on the same date")
        
        return cleaned_data


class BulkAttendanceForm(forms.Form):
    """Form for bulk attendance entry"""
    date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        initial=date.today()
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=[('', 'Select Status')] + Attendance.ATTENDANCE_STATUS,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    employees = forms.ModelMultipleChoiceField(
        queryset=Employee.objects.filter(status='active'),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employees'].queryset = Employee.objects.filter(status='active')


class BreakForm(forms.ModelForm):
    """Form for break management"""
    start_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'})
    )
    end_time = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'})
    )
    
    class Meta:
        model = Break
        fields = ['attendance', 'break_type', 'start_time', 'end_time', 'notes']
        widgets = {
            'attendance': forms.Select(attrs={'class': 'form-select'}),
            'break_type': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        attendance = cleaned_data.get('attendance')
        
        if start_time and end_time:
            if end_time <= start_time:
                raise ValidationError("Break end time must be after start time")
            
            # Check if break is within attendance hours
            if attendance:
                if attendance.check_in_time and start_time < attendance.check_in_time:
                    raise ValidationError("Break cannot start before check-in time")
                
                if attendance.check_out_time and end_time > attendance.check_out_time:
                    raise ValidationError("Break cannot end after check-out time")
        
        return cleaned_data


class ShiftForm(forms.ModelForm):
    """Form for shift configuration"""
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    break_start = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    break_end = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    
    class Meta:
        model = Shift
        fields = [
            'name', 'shift_type', 'start_time', 'end_time', 
            'break_start', 'break_end', 'total_hours', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'shift_type': forms.Select(attrs={'class': 'form-select'}),
            'total_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        break_start = cleaned_data.get('break_start')
        break_end = cleaned_data.get('break_end')
        
        if start_time and end_time:
            # Calculate total hours
            start_dt = datetime.combine(date.today(), start_time)
            end_dt = datetime.combine(date.today(), end_time)
            
            if end_dt <= start_dt:  # Night shift
                end_dt += timedelta(days=1)
            
            duration = end_dt - start_dt
            total_hours = duration.total_seconds() / 3600
            
            # Auto-calculate total hours if not provided
            if not cleaned_data.get('total_hours'):
                cleaned_data['total_hours'] = total_hours
        
        # Validate break times
        if break_start and break_end:
            if break_end <= break_start:
                raise ValidationError("Break end time must be after start time")
            
            if start_time and end_time:
                if break_start < start_time or break_end > end_time:
                    raise ValidationError("Break must be within shift hours")
        
        return cleaned_data


class HolidayForm(forms.ModelForm):
    """Form for holiday management"""
    date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    class Meta:
        model = Holiday
        fields = ['name', 'date', 'holiday_type', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'holiday_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_date(self):
        date = self.cleaned_data['date']
        if date < date.today():
            raise ValidationError("Cannot create holiday for past dates")
        return date


class AttendancePolicyForm(forms.ModelForm):
    """Form for attendance policy configuration"""
    class Meta:
        model = AttendancePolicy
        fields = [
            'name', 'grace_period_minutes', 'half_day_threshold_hours',
            'full_day_threshold_hours', 'overtime_threshold_hours',
            'break_duration_minutes', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'grace_period_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'half_day_threshold_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'full_day_threshold_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'overtime_threshold_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'break_duration_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TimeSheetForm(forms.ModelForm):
    """Form for timesheet management"""
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    class Meta:
        model = TimeSheet
        fields = [
            'employee', 'period_type', 'start_date', 'end_date',
            'notes', 'is_submitted', 'is_approved'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'period_type': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_submitted': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_approved': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if end_date <= start_date:
                raise ValidationError("End date must be after start date")
            
            # Check period type constraints
            period_type = cleaned_data.get('period_type')
            if period_type == 'weekly':
                days_diff = (end_date - start_date).days
                if days_diff > 7:
                    raise ValidationError("Weekly timesheet cannot exceed 7 days")
            elif period_type == 'monthly':
                days_diff = (end_date - start_date).days
                if days_diff > 31:
                    raise ValidationError("Monthly timesheet cannot exceed 31 days")
        
        return cleaned_data


class AttendanceReportForm(forms.Form):
    """Form for generating attendance reports"""
    REPORT_TYPES = [
        ('daily', 'Daily Attendance'),
        ('weekly', 'Weekly Summary'),
        ('monthly', 'Monthly Summary'),
        ('late_arrival', 'Late Arrival Report'),
        ('overtime', 'Overtime Report'),
        ('department', 'Department-wise Attendance'),
        ('custom', 'Custom Period'),
    ]
    
    name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    report_type = forms.ChoiceField(
        choices=REPORT_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(status='active'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    include_breaks = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    include_overtime = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    export_format = forms.ChoiceField(
        choices=[('excel', 'Excel'), ('pdf', 'PDF'), ('csv', 'CSV')],
        initial='excel',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if end_date < start_date:
                raise ValidationError("End date cannot be before start date")
            
            # Limit report period to 1 year
            days_diff = (end_date - start_date).days
            if days_diff > 365:
                raise ValidationError("Report period cannot exceed 1 year")
        
        return cleaned_data


class AttendanceSearchForm(forms.Form):
    """Form for searching attendance records"""
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(status='active'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + Attendance.ATTENDANCE_STATUS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    shift = forms.ModelChoiceField(
        queryset=Shift.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    is_late = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    has_overtime = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class PunchInOutForm(forms.Form):
    """Form for employee punch-in/out"""
    action = forms.ChoiceField(
        choices=[('check_in', 'Check In'), ('check_out', 'Check Out')],
        widget=forms.HiddenInput()
    )
    location = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.HiddenInput()
    )
    latitude = forms.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        widget=forms.HiddenInput()
    )
    longitude = forms.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        widget=forms.HiddenInput()
    )
    notes = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional notes...'})
    )


class AttendanceAlertForm(forms.ModelForm):
    """Form for attendance alerts"""
    class Meta:
        model = AttendanceAlert
        fields = [
            'employee', 'alert_type', 'severity', 'date', 'title',
            'description', 'is_resolved', 'resolution_notes'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'alert_type': forms.Select(attrs={'class': 'form-select'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_resolved': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'resolution_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# Custom widgets and form utilities
class TimeInput(forms.TimeInput):
    """Custom time input widget"""
    input_type = 'time'
    
    def __init__(self, attrs=None):
        if attrs is None:
            attrs = {}
        attrs.update({'class': 'form-control'})
        super().__init__(attrs)


class DateInput(forms.DateInput):
    """Custom date input widget"""
    input_type = 'date'
    
    def __init__(self, attrs=None):
        if attrs is None:
            attrs = {}
        attrs.update({'class': 'form-control'})
        super().__init__(attrs)


class DateTimeInput(forms.DateTimeInput):
    """Custom datetime input widget"""
    input_type = 'datetime-local'
    
    def __init__(self, attrs=None):
        if attrs is None:
            attrs = {}
        attrs.update({'class': 'form-control'})
        super().__init__(attrs) 