from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from .restore_models import RestoreRequest, RestoreExecution, RestoreApprovalWorkflow, RestoreNotification
from .models import BackupExecution, BackupType, BackupScope, StorageLocation
import json

class RestoreRequestForm(forms.ModelForm):
    """Form for creating and editing restore requests"""
    
    # Custom fields for better UX
    restore_type_display = forms.ChoiceField(
        choices=[
            ('full_database', 'Full Database Restore'),
            ('module_specific', 'Module-Specific Restore'),
            ('point_in_time', 'Point-in-Time Recovery'),
            ('selective_records', 'Selective Records Restore'),
            ('staging_test', 'Staging/Test Environment Restore'),
        ],
        widget=forms.RadioSelect,
        label="Restore Type"
    )
    
    # Source selection
    source_type = forms.ChoiceField(
        choices=[
            ('backup_execution', 'From Existing Backup'),
            ('file_upload', 'Upload Backup File'),
            ('cloud_storage', 'From Cloud Storage'),
        ],
        widget=forms.RadioSelect,
        label="Source Type"
    )
    
    # File upload
    backup_file = forms.FileField(
        required=False,
        help_text="Upload a backup file (.sql, .bak, .zip)",
        widget=forms.FileInput(attrs={'accept': '.sql,.bak,.zip,.tar.gz'})
    )
    
    # Scheduling
    schedule_type = forms.ChoiceField(
        choices=[
            ('immediate', 'Execute Immediately'),
            ('scheduled', 'Schedule for Later'),
        ],
        widget=forms.RadioSelect,
        label="Execution Schedule"
    )
    
    # Safety options
    safety_options = forms.MultipleChoiceField(
        choices=[
            ('backup_before_restore', 'Create backup before restore'),
            ('dry_run', 'Perform dry run first'),
            ('validate_after_restore', 'Validate data after restore'),
            ('rollback_plan', 'Create rollback plan'),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Safety Options"
    )
    
    class Meta:
        model = RestoreRequest
        fields = [
            'title', 'description', 'restore_type', 'target_environment',
            'source_backup', 'restore_modules', 'restore_tables', 'restore_records',
            'target_timestamp', 'scheduled_at', 'estimated_duration',
            'priority', 'requires_approval', 'rollback_plan'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter restore request title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe the restore operation'}),
            'restore_type': forms.Select(attrs={'class': 'form-control'}),
            'target_environment': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('production', 'Production'),
                ('staging', 'Staging'),
                ('test', 'Test'),
                ('development', 'Development'),
            ]),
            'source_backup': forms.Select(attrs={'class': 'form-control'}),
            'restore_modules': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'restore_tables': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter table names, one per line'}),
            'restore_records': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter record filters in JSON format'}),
            'target_timestamp': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'scheduled_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'estimated_duration': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 1440}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'requires_approval': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'rollback_plan': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe rollback procedures'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Store user for later use in save method
        self.user = user
        
        # Populate source backup choices
        self.fields['source_backup'].queryset = BackupExecution.objects.filter(
            status='completed'
        ).order_by('-created_at')
        
        # Populate restore modules from backup scope choices
        self.fields['restore_modules'].choices = [
            ('customers', 'Customers'),
            ('items', 'Items'),
            ('transactions', 'Transactions'),
            ('financial_data', 'Financial Data'),
            ('documents', 'Documents'),
            ('users', 'Users'),
            ('settings', 'System Settings'),
        ]
        
        # Set default values
        self.fields['target_environment'].initial = 'staging'
        self.fields['priority'].initial = 'normal'
        self.fields['requires_approval'].initial = True
        
        # Add form-control class to all fields
        for field_name, field in self.fields.items():
            if hasattr(field.widget, 'attrs'):
                field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' form-control'
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate restore type and source compatibility
        restore_type = cleaned_data.get('restore_type')
        source_type = cleaned_data.get('source_type')
        source_backup = cleaned_data.get('source_backup')
        backup_file = cleaned_data.get('backup_file')
        
        if source_type == 'backup_execution' and not source_backup:
            raise ValidationError("Please select a source backup when using existing backup.")
        
        if source_type == 'file_upload' and not backup_file:
            raise ValidationError("Please upload a backup file.")
        
        # Validate point-in-time recovery
        if restore_type == 'point_in_time':
            target_timestamp = cleaned_data.get('target_timestamp')
            if not target_timestamp:
                raise ValidationError("Target timestamp is required for point-in-time recovery.")
            
            if target_timestamp > timezone.now():
                raise ValidationError("Target timestamp cannot be in the future.")
        
        # Validate scheduling
        schedule_type = cleaned_data.get('schedule_type')
        scheduled_at = cleaned_data.get('scheduled_at')
        
        if schedule_type == 'scheduled' and not scheduled_at:
            raise ValidationError("Please specify a scheduled time.")
        
        if scheduled_at and scheduled_at <= timezone.now():
            raise ValidationError("Scheduled time must be in the future.")
        
        # Validate restore modules and tables
        restore_modules = cleaned_data.get('restore_modules')
        restore_tables = cleaned_data.get('restore_tables')
        
        if restore_type == 'module_specific' and not restore_modules:
            raise ValidationError("Please select at least one module to restore.")
        
        if restore_tables:
            try:
                # Convert textarea input to list
                table_list = [table.strip() for table in restore_tables.split('\n') if table.strip()]
                cleaned_data['restore_tables'] = table_list
            except:
                raise ValidationError("Invalid table format. Please enter one table name per line.")
        
        # Validate restore records JSON
        restore_records = cleaned_data.get('restore_records')
        if restore_records:
            try:
                if isinstance(restore_records, str):
                    json.loads(restore_records)
                cleaned_data['restore_records'] = restore_records
            except json.JSONDecodeError:
                raise ValidationError("Invalid JSON format for record filters.")
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if hasattr(self, 'user') and self.user:
            instance.created_by = self.user
        if commit:
            instance.save()
        return instance

class RestoreApprovalForm(forms.ModelForm):
    """Form for approving or rejecting restore requests"""
    
    action = forms.ChoiceField(
        choices=[
            ('approve', 'Approve'),
            ('reject', 'Reject'),
        ],
        widget=forms.RadioSelect,
        label="Action"
    )
    
    approval_notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        required=False,
        label="Approval Notes"
    )
    
    class Meta:
        model = RestoreRequest
        fields = ['approval_notes']
    
    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        approval_notes = cleaned_data.get('approval_notes')
        
        if action == 'reject' and not approval_notes:
            raise ValidationError("Please provide a reason for rejection.")
        
        return cleaned_data

class RestoreExecutionForm(forms.ModelForm):
    """Form for executing restore requests"""
    
    execution_notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False,
        label="Execution Notes"
    )
    
    confirm_execution = forms.BooleanField(
        required=True,
        label="I confirm that I want to execute this restore operation",
        help_text="This action cannot be undone. Please ensure all safety measures are in place."
    )
    
    class Meta:
        model = RestoreExecution
        fields = ['execution_notes']
    
    def clean_confirm_execution(self):
        confirmed = self.cleaned_data.get('confirm_execution')
        if not confirmed:
            raise ValidationError("You must confirm the execution to proceed.")
        return confirmed

class RestoreValidationForm(forms.Form):
    """Form for running validation checks on restore operations"""
    
    validation_rules = forms.MultipleChoiceField(
        choices=[],
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Select Validation Rules"
    )
    
    custom_validation = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        required=False,
        label="Custom Validation Query",
        help_text="Enter a custom SQL query or validation logic"
    )
    
    expected_result = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False,
        label="Expected Result",
        help_text="What result do you expect from the validation?"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate validation rules choices
        self.fields['validation_rules'].choices = [
            ('data_integrity', 'Data Integrity Check'),
            ('referential_integrity', 'Referential Integrity Check'),
            ('business_logic', 'Business Logic Validation'),
            ('record_count', 'Record Count Verification'),
            ('checksum_verification', 'Checksum Verification'),
        ]

class RestoreSearchForm(forms.Form):
    """Form for searching and filtering restore requests"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search restore requests...'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + RestoreRequest.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    priority = forms.ChoiceField(
        choices=[('', 'All Priorities')] + RestoreRequest.PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    restore_type = forms.ChoiceField(
        choices=[('', 'All Types')] + RestoreRequest.RESTORE_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    created_by = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        empty_label="All Users",
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

class RestoreNotificationForm(forms.ModelForm):
    """Form for configuring restore notifications"""
    
    notification_channels = forms.MultipleChoiceField(
        choices=[
            ('email', 'Email'),
            ('sms', 'SMS'),
            ('webhook', 'Webhook'),
            ('dashboard', 'Dashboard'),
            ('slack', 'Slack'),
            ('teams', 'Microsoft Teams'),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Notification Channels"
    )
    
    notification_events = forms.MultipleChoiceField(
        choices=[
            ('request_created', 'Request Created'),
            ('approval_required', 'Approval Required'),
            ('approved', 'Request Approved'),
            ('rejected', 'Request Rejected'),
            ('execution_started', 'Execution Started'),
            ('execution_completed', 'Execution Completed'),
            ('execution_failed', 'Execution Failed'),
            ('validation_failed', 'Validation Failed'),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Notification Events"
    )
    
    class Meta:
        model = RestoreNotification
        fields = ['recipients', 'user_groups', 'subject', 'message_template']
        widgets = {
            'recipients': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter email addresses, one per line'}),
            'user_groups': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'message_template': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }
