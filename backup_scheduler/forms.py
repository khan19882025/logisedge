from django import forms
from django.contrib.auth.models import User
from .models import (
    BackupType, BackupScope, StorageLocation, BackupSchedule, 
    BackupExecution, BackupRetentionPolicy, BackupAlert,
    DisasterRecoveryPlan
)
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, time, date

class BackupTypeForm(forms.ModelForm):
    """Form for creating/editing backup types"""
    
    class Meta:
        model = BackupType
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class BackupScopeForm(forms.ModelForm):
    """Form for creating/editing backup scopes"""
    
    class Meta:
        model = BackupScope
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class StorageLocationForm(forms.ModelForm):
    """Form for creating/editing storage locations"""
    
    class Meta:
        model = StorageLocation
        fields = [
            'name', 'storage_type', 'path', 'credentials', 
            'is_active', 'max_capacity_gb'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'storage_type': forms.Select(attrs={'class': 'form-control'}),
            'path': forms.TextInput(attrs={'class': 'form-control'}),
            'credentials': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'max_capacity_gb': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    
    def clean_path(self):
        path = self.cleaned_data['path']
        storage_type = self.cleaned_data.get('storage_type')
        
        if storage_type == 'local':
            # Validate local path exists and is writable
            import os
            if not os.path.exists(path):
                raise ValidationError("Local path does not exist")
            if not os.access(path, os.W_OK):
                raise ValidationError("Local path is not writable")
        
        return path

class BackupScheduleForm(forms.ModelForm):
    """Form for creating/editing backup schedules"""
    
    class Meta:
        model = BackupSchedule
        fields = [
            'name', 'description', 'backup_type', 'backup_scope', 'storage_location',
            'frequency', 'start_time', 'start_date', 'is_active', 'weekday',
            'day_of_month', 'cron_expression', 'retention_days', 'max_backups',
            'allow_parallel'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'backup_type': forms.Select(attrs={'class': 'form-control'}),
            'backup_scope': forms.Select(attrs={'class': 'form-control'}),
            'storage_location': forms.Select(attrs={'class': 'form-control'}),
            'frequency': forms.Select(attrs={'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'weekday': forms.Select(attrs={'class': 'form-control'}),
            'day_of_month': forms.NumberInput(attrs={'class': 'form-control'}),
            'cron_expression': forms.TextInput(attrs={'class': 'form-control'}),
            'retention_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_backups': forms.NumberInput(attrs={'class': 'form-control'}),
            'allow_parallel': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default start date to today
        if not self.instance.pk:
            self.fields['start_date'].initial = timezone.now().date()
            self.fields['start_time'].initial = time(2, 0)  # 2:00 AM default
    
    def clean(self):
        cleaned_data = super().clean()
        frequency = cleaned_data.get('frequency')
        weekday = cleaned_data.get('weekday')
        day_of_month = cleaned_data.get('day_of_month')
        cron_expression = cleaned_data.get('cron_expression')
        
        # Validate frequency-specific fields
        if frequency == 'weekly' and weekday is None:
            raise ValidationError("Weekday is required for weekly schedules")
        
        if frequency == 'monthly' and day_of_month is None:
            raise ValidationError("Day of month is required for monthly schedules")
        
        if frequency == 'custom' and not cron_expression:
            raise ValidationError("Cron expression is required for custom schedules")
        
        # Validate start date is not in the past
        start_date = cleaned_data.get('start_date')
        if start_date and start_date < timezone.now().date():
            raise ValidationError("Start date cannot be in the past")
        
        return cleaned_data

class ManualBackupForm(forms.ModelForm):
    """Form for triggering manual backups"""
    
    class Meta:
        model = BackupExecution
        fields = ['backup_type', 'backup_scope', 'storage_location']
        widgets = {
            'backup_type': forms.Select(attrs={'class': 'form-control'}),
            'backup_scope': forms.Select(attrs={'class': 'form-control'}),
            'storage_location': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active backup types, scopes, and storage locations
        self.fields['backup_type'].queryset = BackupType.objects.filter(is_active=True)
        self.fields['backup_scope'].queryset = BackupScope.objects.filter(is_active=True)
        self.fields['storage_location'].queryset = StorageLocation.objects.filter(is_active=True)

class BackupRetentionPolicyForm(forms.ModelForm):
    """Form for creating/editing retention policies"""
    
    class Meta:
        model = BackupRetentionPolicy
        fields = ['name', 'backup_type', 'retention_days', 'retention_count', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'backup_type': forms.Select(attrs={'class': 'form-control'}),
            'retention_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'retention_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        retention_days = cleaned_data.get('retention_days')
        retention_count = cleaned_data.get('retention_count')
        
        if retention_days and retention_days < 1:
            raise ValidationError("Retention days must be at least 1")
        
        if retention_count and retention_count < 1:
            raise ValidationError("Retention count must be at least 1")
        
        return cleaned_data

class BackupAlertForm(forms.ModelForm):
    """Form for creating/editing backup alerts"""
    
    class Meta:
        model = BackupAlert
        fields = ['name', 'alert_type', 'channel', 'recipients', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'alert_type': forms.Select(attrs={'class': 'form-control'}),
            'channel': forms.Select(attrs={'class': 'form-control'}),
            'recipients': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_recipients(self):
        recipients = self.cleaned_data['recipients']
        channel = self.cleaned_data.get('channel')
        
        if channel == 'email':
            # Validate email addresses
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            for recipient in recipients:
                if not re.match(email_pattern, recipient):
                    raise ValidationError(f"Invalid email address: {recipient}")
        
        elif channel == 'sms':
            # Validate phone numbers
            import re
            phone_pattern = r'^\+?1?\d{9,15}$'
            for recipient in recipients:
                if not re.match(phone_pattern, recipient):
                    raise ValidationError(f"Invalid phone number: {recipient}")
        
        return recipients

class DisasterRecoveryPlanForm(forms.ModelForm):
    """Form for creating/editing disaster recovery plans"""
    
    class Meta:
        model = DisasterRecoveryPlan
        fields = ['name', 'description', 'backup_execution', 'recovery_procedures', 'test_schedule', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'backup_execution': forms.Select(attrs={'class': 'form-control'}),
            'recovery_procedures': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'test_schedule': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_test_schedule(self):
        test_schedule = self.cleaned_data['test_schedule']
        # Basic cron expression validation
        if test_schedule:
            import re
            cron_pattern = r'^(\*|[0-9]{1,2})(\/[0-9]{1,2})?(\s+(\*|[0-9]{1,2})(\/[0-9]{1,2})?){4}$'
            if not re.match(cron_pattern, test_schedule):
                raise ValidationError("Invalid cron expression format")
        return test_schedule

class BackupFilterForm(forms.Form):
    """Form for filtering backup executions"""
    
    STATUS_CHOICES = [('', 'All Statuses')] + BackupExecution.STATUS_CHOICES
    TYPE_CHOICES = [('', 'All Types')] + BackupType.BACKUP_TYPES
    SCOPE_CHOICES = [('', 'All Scopes')] + BackupScope.SCOPE_CHOICES
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    backup_type = forms.ChoiceField(
        choices=TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    backup_scope = forms.ChoiceField(
        choices=SCOPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    is_manual = forms.ChoiceField(
        choices=[('', 'All'), ('True', 'Manual'), ('False', 'Scheduled')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class BackupScheduleFilterForm(forms.Form):
    """Form for filtering backup schedules"""
    
    FREQUENCY_CHOICES = [('', 'All Frequencies')] + BackupSchedule.FREQUENCY_CHOICES
    
    frequency = forms.ChoiceField(
        choices=FREQUENCY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    is_active = forms.ChoiceField(
        choices=[('', 'All'), ('True', 'Active'), ('False', 'Inactive')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    storage_location = forms.ModelChoiceField(
        queryset=StorageLocation.objects.filter(is_active=True),
        required=False,
        empty_label="All Storage Locations",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
