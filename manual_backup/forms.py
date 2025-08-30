from django import forms
from django.contrib.auth.models import User
from .models import (
    BackupConfiguration, BackupSession, BackupStep, 
    BackupAuditLog, BackupStorageLocation, BackupRetentionPolicy
)


class BackupConfigurationForm(forms.ModelForm):
    """Form for creating and editing backup configurations"""
    
    class Meta:
        model = BackupConfiguration
        fields = [
            'name', 'backup_type', 'compression_level', 'encryption_type',
            'retention_days', 'include_media', 'include_static', 
            'include_database', 'include_config', 'exclude_patterns'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter configuration name'
            }),
            'backup_type': forms.Select(attrs={'class': 'form-control'}),
            'compression_level': forms.Select(attrs={'class': 'form-control'}),
            'encryption_type': forms.Select(attrs={'class': 'form-control'}),
            'retention_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '3650'
            }),
            'exclude_patterns': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '4',
                'placeholder': 'Enter file patterns to exclude (one per line)\nExample:\n*.tmp\n*.log\nnode_modules/'
            })
        }
    
    def clean_name(self):
        name = self.cleaned_data['name']
        if BackupConfiguration.objects.filter(name=name).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise forms.ValidationError('A configuration with this name already exists.')
        return name
    
    def clean_retention_days(self):
        days = self.cleaned_data['retention_days']
        if days < 1:
            raise forms.ValidationError('Retention period must be at least 1 day.')
        if days > 3650:  # 10 years
            raise forms.ValidationError('Retention period cannot exceed 10 years.')
        return days


class BackupSessionForm(forms.ModelForm):
    """Form for initiating backup sessions"""
    
    # Additional fields for backup initiation
    backup_type = forms.ChoiceField(
        choices=BackupConfiguration.BACKUP_TYPES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='full'
    )
    
    compression_level = forms.ChoiceField(
        choices=BackupConfiguration.COMPRESSION_LEVELS,
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='balanced'
    )
    
    encryption_type = forms.ChoiceField(
        choices=BackupConfiguration.ENCRYPTION_TYPES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='aes256'
    )
    
    retention_days = forms.IntegerField(
        min_value=1,
        max_value=3650,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '30'
        }),
        initial=30
    )
    
    include_media = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    include_static = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    include_database = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    include_config = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    notify_emails = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'email1@company.com, email2@company.com'
        }),
        help_text='Comma-separated list of email addresses to notify'
    )
    
    class Meta:
        model = BackupSession
        fields = ['reason', 'description', 'priority', 'configuration']
        widgets = {
            'reason': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': 'Provide additional details about this backup...'
            }),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'configuration': forms.Select(attrs={'class': 'form-control'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make configuration field optional
        self.fields['configuration'].required = False
        self.fields['configuration'].empty_label = "Use custom settings (below)"
        
        # Set initial values for custom fields
        if self.instance.pk and self.instance.configuration:
            config = self.instance.configuration
            self.fields['backup_type'].initial = config.backup_type
            self.fields['compression_level'].initial = config.compression_level
            self.fields['encryption_type'].initial = config.encryption_type
            self.fields['retention_days'].initial = config.retention_days
            self.fields['include_media'].initial = config.include_media
            self.fields['include_static'].initial = config.include_static
            self.fields['include_database'].initial = config.include_database
            self.fields['include_config'].initial = config.include_config
    
    def clean_notify_emails(self):
        emails = self.cleaned_data['notify_emails']
        if emails:
            email_list = [email.strip() for email in emails.split(',')]
            for email in email_list:
                if email and not forms.EmailField().clean(email):
                    raise forms.ValidationError(f'Invalid email address: {email}')
        return emails
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate that at least one backup component is selected
        include_media = cleaned_data.get('include_media', False)
        include_static = cleaned_data.get('include_static', False)
        include_database = cleaned_data.get('include_database', False)
        include_config = cleaned_data.get('include_config', False)
        
        if not any([include_media, include_static, include_database, include_config]):
            raise forms.ValidationError(
                'At least one backup component must be selected (media, static, database, or config).'
            )
        
        return cleaned_data


class BackupSessionUpdateForm(forms.ModelForm):
    """Form for updating backup session details"""
    
    class Meta:
        model = BackupSession
        fields = ['status', 'description', 'priority']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3'
            }),
            'priority': forms.Select(attrs={'class': 'form-control'})
        }
    
    def clean_status(self):
        status = self.cleaned_data['status']
        current_status = self.instance.status if self.instance else None
        
        # Prevent status changes that don't make sense
        if current_status == 'completed' and status in ['pending', 'in_progress']:
            raise forms.ValidationError('Cannot change status from completed to pending or in progress.')
        
        if current_status == 'failed' and status == 'in_progress':
            raise forms.ValidationError('Cannot change status from failed to in progress.')
        
        return status


class BackupStepForm(forms.ModelForm):
    """Form for managing backup steps"""
    
    class Meta:
        model = BackupStep
        fields = ['step_type', 'step_name', 'status', 'order', 'details', 'error_message']
        widgets = {
            'step_type': forms.Select(attrs={'class': 'form-control'}),
            'step_name': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'details': forms.Textarea(attrs={'class': 'form-control', 'rows': '3'}),
            'error_message': forms.Textarea(attrs={'class': 'form-control', 'rows': '3'})
        }
    
    def clean_order(self):
        order = self.cleaned_data['order']
        backup_session = self.cleaned_data.get('backup_session')
        
        if backup_session and order:
            # Check for duplicate order within the same backup session
            existing_step = BackupStep.objects.filter(
                backup_session=backup_session,
                order=order
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if existing_step.exists():
                raise forms.ValidationError(
                    f'Step with order {order} already exists in this backup session.'
                )
        
        return order


class BackupAuditLogForm(forms.ModelForm):
    """Form for creating audit log entries"""
    
    class Meta:
        model = BackupAuditLog
        fields = ['level', 'message', 'details']
        widgets = {
            'level': forms.Select(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': 'Enter audit log message...'
            }),
            'details': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '4',
                'placeholder': 'Enter additional details in JSON format...'
            })
        }
    
    def clean_details(self):
        details = self.cleaned_data['details']
        if details:
            try:
                import json
                json.loads(details)
            except json.JSONDecodeError:
                raise forms.ValidationError('Details must be valid JSON format.')
        return details


class BackupStorageLocationForm(forms.ModelForm):
    """Form for managing backup storage locations"""
    
    class Meta:
        model = BackupStorageLocation
        fields = [
            'name', 'storage_type', 'path', 'description', 'total_capacity_bytes',
            'available_capacity_bytes', 'is_primary', 'is_active', 'encryption_required',
            'host', 'port', 'username', 'credentials_encrypted'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'storage_type': forms.Select(attrs={'class': 'form-control'}),
            'path': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': '3'}),
            'total_capacity_bytes': forms.NumberInput(attrs={'class': 'form-control'}),
            'available_capacity_bytes': forms.NumberInput(attrs={'class': 'form-control'}),
            'host': forms.TextInput(attrs={'class': 'form-control'}),
            'port': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '65535'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'credentials_encrypted': forms.Textarea(attrs={'class': 'form-control', 'rows': '3'})
        }
    
    def clean(self):
        cleaned_data = super().clean()
        storage_type = cleaned_data.get('storage_type')
        host = cleaned_data.get('host')
        port = cleaned_data.get('port')
        
        # Validate network storage requirements
        if storage_type in ['network', 'cloud']:
            if not host:
                raise forms.ValidationError('Host is required for network and cloud storage types.')
            if not port:
                raise forms.ValidationError('Port is required for network and cloud storage types.')
        
        # Validate capacity fields
        total_capacity = cleaned_data.get('total_capacity_bytes')
        available_capacity = cleaned_data.get('available_capacity_bytes')
        
        if total_capacity and available_capacity:
            if available_capacity > total_capacity:
                raise forms.ValidationError('Available capacity cannot exceed total capacity.')
        
        return cleaned_data


class BackupRetentionPolicyForm(forms.ModelForm):
    """Form for managing backup retention policies"""
    
    class Meta:
        model = BackupRetentionPolicy
        fields = [
            'name', 'description', 'keep_daily_for_days', 'keep_weekly_for_weeks',
            'keep_monthly_for_months', 'keep_yearly_for_years', 'keep_forever',
            'minimum_retention_days', 'auto_cleanup', 'cleanup_schedule'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': '3'}),
            'keep_daily_for_days': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'keep_weekly_for_weeks': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'keep_monthly_for_months': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'keep_yearly_for_years': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'minimum_retention_days': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'cleanup_schedule': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '0 2 * * 0 (Weekly on Sunday at 2 AM)'
            })
        }
    
    def clean(self):
        cleaned_data = super().clean()
        keep_forever = cleaned_data.get('keep_forever', False)
        
        if not keep_forever:
            # Validate that at least one retention period is set
            daily = cleaned_data.get('keep_daily_for_days', 0)
            weekly = cleaned_data.get('keep_weekly_for_weeks', 0)
            monthly = cleaned_data.get('keep_monthly_for_months', 0)
            yearly = cleaned_data.get('keep_yearly_for_years', 0)
            
            if not any([daily, weekly, monthly, yearly]):
                raise forms.ValidationError(
                    'At least one retention period must be set when not keeping backups forever.'
                )
        
        return cleaned_data


class BackupSearchForm(forms.Form):
    """Form for searching and filtering backup sessions"""
    
    SEARCH_FIELDS = [
        ('name', 'Backup Name'),
        ('reason', 'Backup Reason'),
        ('description', 'Description'),
        ('created_by', 'Created By'),
    ]
    
    STATUS_CHOICES = [('', 'All Statuses')] + BackupSession.STATUS_CHOICES
    REASON_CHOICES = [('', 'All Reasons')] + BackupSession.BACKUP_REASONS
    PRIORITY_CHOICES = [('', 'All Priorities')] + BackupSession.PRIORITY_LEVELS
    
    search_query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search backups...'
        })
    )
    
    search_field = forms.ChoiceField(
        choices=SEARCH_FIELDS,
        required=False,
        initial='name',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    reason = forms.ChoiceField(
        choices=REASON_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    created_by = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        empty_label="All Users",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError('Start date cannot be after end date.')
        
        return cleaned_data
