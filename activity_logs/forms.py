from django import forms
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from .models import (
    ActivityLog, AuditTrail, SecurityEvent, ComplianceReport, 
    RetentionPolicy, AlertRule
)


class ActivityLogSearchForm(forms.Form):
    """
    Form for searching and filtering activity logs
    """
    # Date range
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    # User and activity filters
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        empty_label="All Users",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    activity_type = forms.ChoiceField(
        choices=[('', 'All Types')] + ActivityLog.ACTIVITY_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    log_level = forms.ChoiceField(
        choices=[('', 'All Levels')] + ActivityLog.LOG_LEVELS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Module and action filters
    module = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Module name'})
    )
    action = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Action description'})
    )
    
    # Security and compliance filters
    is_sensitive = forms.ChoiceField(
        choices=[('', 'All'), ('True', 'Sensitive Only'), ('False', 'Non-Sensitive Only')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    compliance_category = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Compliance category'})
    )
    
    # IP address filter
    user_ip = forms.GenericIPAddressField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'IP Address'})
    )
    
    # Tags filter
    tags = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tags (comma-separated)'})
    )


class AuditTrailSearchForm(forms.Form):
    """
    Form for searching and filtering audit trails
    """
    # Trail identification
    trail_name = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Trail name'})
    )
    trail_type = forms.ChoiceField(
        choices=[('', 'All Types')] + AuditTrail.TRAIL_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Date range
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    # Object filters
    content_type = forms.ModelChoiceField(
        queryset=ContentType.objects.all(),
        required=False,
        empty_label="All Content Types",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    object_id = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Object ID'})
    )
    
    # Compliance filters
    compliance_category = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Compliance category'})
    )


class SecurityEventSearchForm(forms.Form):
    """
    Form for searching and filtering security events
    """
    # Event details
    event_type = forms.ChoiceField(
        choices=[('', 'All Types')] + SecurityEvent.EVENT_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    severity = forms.ChoiceField(
        choices=[('', 'All Severities')] + SecurityEvent.SEVERITY_LEVELS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Date range
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    # User and source filters
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        empty_label="All Users",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    source_ip = forms.GenericIPAddressField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Source IP'})
    )
    
    # Status filter
    is_resolved = forms.ChoiceField(
        choices=[('', 'All'), ('True', 'Resolved Only'), ('False', 'Unresolved Only')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Title and description search
    title = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Event title'})
    )
    description = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Description keywords'})
    )


class ComplianceReportForm(forms.ModelForm):
    """
    Form for creating and editing compliance reports
    """
    class Meta:
        model = ComplianceReport
        fields = [
            'report_name', 'report_type', 'start_date', 'end_date', 
            'report_summary'
        ]
        widgets = {
            'report_name': forms.TextInput(attrs={'class': 'form-control'}),
            'report_type': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'report_summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default dates
        if not self.instance.pk:
            self.fields['start_date'].initial = timezone.now().date()
            self.fields['end_date'].initial = timezone.now().date()
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("Start date cannot be after end date.")
        
        return cleaned_data


class RetentionPolicyForm(forms.ModelForm):
    """
    Form for creating and editing retention policies
    """
    class Meta:
        model = RetentionPolicy
        fields = [
            'name', 'policy_type', 'description', 'retention_period_days',
            'archive_after_days', 'delete_after_days', 'compliance_standards',
            'legal_requirements', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'policy_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'retention_period_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'archive_after_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'delete_after_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'compliance_standards': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Comma-separated standards'}),
            'legal_requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        retention_days = cleaned_data.get('retention_period_days')
        archive_days = cleaned_data.get('archive_after_days')
        delete_days = cleaned_data.get('delete_after_days')
        
        if archive_days and retention_days and archive_days >= retention_days:
            raise forms.ValidationError("Archive date must be before retention period.")
        
        if delete_days and retention_days and delete_days <= retention_days:
            raise forms.ValidationError("Delete date must be after retention period.")
        
        if archive_days and delete_days and archive_days >= delete_days:
            raise forms.ValidationError("Archive date must be before delete date.")
        
        return cleaned_data


class AlertRuleForm(forms.ModelForm):
    """
    Form for creating and editing alert rules
    """
    class Meta:
        model = AlertRule
        fields = [
            'name', 'description', 'trigger_type', 'trigger_conditions',
            'alert_type', 'recipients', 'message_template', 'threshold_value',
            'time_window_minutes', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'trigger_type': forms.Select(attrs={'class': 'form-control'}),
            'trigger_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'JSON format trigger conditions'}),
            'alert_type': forms.Select(attrs={'class': 'form-control'}),
            'recipients': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'One recipient per line'}),
            'message_template': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Alert message template'}),
            'threshold_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'time_window_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_recipients(self):
        recipients = self.cleaned_data.get('recipients')
        if recipients:
            # Convert textarea input to list
            recipient_list = [r.strip() for r in recipients.split('\n') if r.strip()]
            return recipient_list
        return []
    
    def clean_trigger_conditions(self):
        conditions = self.cleaned_data.get('trigger_conditions')
        if conditions:
            try:
                import json
                json.loads(conditions)
            except json.JSONDecodeError:
                raise forms.ValidationError("Trigger conditions must be valid JSON format.")
        return conditions


class ActivityLogExportForm(forms.Form):
    """
    Form for exporting activity logs
    """
    EXPORT_FORMATS = [
        ('csv', 'CSV'),
        ('json', 'JSON'),
        ('xml', 'XML'),
        ('pdf', 'PDF'),
    ]
    
    export_format = forms.ChoiceField(
        choices=EXPORT_FORMATS,
        initial='csv',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    include_sensitive_data = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Include sensitive data in export (requires special permissions)"
    )
    
    date_range = forms.ChoiceField(
        choices=[
            ('custom', 'Custom Range'),
            ('today', 'Today'),
            ('yesterday', 'Yesterday'),
            ('last_7_days', 'Last 7 Days'),
            ('last_30_days', 'Last 30 Days'),
            ('last_90_days', 'Last 90 Days'),
            ('this_month', 'This Month'),
            ('last_month', 'Last Month'),
            ('this_year', 'This Year'),
        ],
        initial='last_30_days',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    custom_start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    custom_end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    # Field selection for export
    export_fields = forms.MultipleChoiceField(
        choices=[
            ('timestamp', 'Timestamp'),
            ('user', 'User'),
            ('activity_type', 'Activity Type'),
            ('action', 'Action'),
            ('module', 'Module'),
            ('description', 'Description'),
            ('user_ip', 'User IP'),
            ('old_values', 'Old Values'),
            ('new_values', 'New Values'),
            ('tags', 'Tags'),
            ('compliance_category', 'Compliance Category'),
        ],
        initial=['timestamp', 'user', 'activity_type', 'action', 'module'],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        help_text="Select fields to include in export"
    )


class SecurityEventResponseForm(forms.Form):
    """
    Form for responding to security events
    """
    RESPONSE_ACTIONS = [
        ('investigate', 'Investigate Further'),
        ('escalate', 'Escalate to Security Team'),
        ('block_ip', 'Block Source IP'),
        ('disable_user', 'Disable User Account'),
        ('notify_admin', 'Notify Administrators'),
        ('mark_resolved', 'Mark as Resolved'),
        ('custom', 'Custom Action'),
    ]
    
    response_action = forms.ChoiceField(
        choices=RESPONSE_ACTIONS,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    resolution_notes = forms.CharField(
        max_length=1000,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe the response action taken...'}),
        required=False
    )
    
    custom_action = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Describe custom action...'}),
        required=False
    )
    
    notify_users = forms.MultipleChoiceField(
        choices=[],
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        help_text="Select users to notify about this response"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate user choices
        self.fields['notify_users'].choices = [
            (user.id, f"{user.get_full_name()} ({user.username})")
            for user in User.objects.filter(is_staff=True)
        ]
