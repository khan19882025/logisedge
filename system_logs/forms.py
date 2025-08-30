from django import forms
from django.contrib.auth.models import User
from .models import SystemLog, ErrorPattern, DebugSession, LogRetentionPolicy, LogExport


class SystemLogSearchForm(forms.Form):
    """
    Form for searching and filtering system logs
    """
    # Date range filters
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    # Core filters
    log_type = forms.ChoiceField(
        choices=[('', 'All Types')] + SystemLog.LOG_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    severity = forms.ChoiceField(
        choices=[('', 'All Severities')] + SystemLog.SEVERITY_LEVELS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + SystemLog.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Context filters
    module = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Module name'})
    )
    function = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Function name'})
    )
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        empty_label="All Users",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Error details
    error_type = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Error type'})
    )
    error_message = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Error message'})
    )
    
    # Performance filters
    execution_time_min = forms.DecimalField(
        max_digits=10,
        decimal_places=6,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Min execution time (s)'})
    )
    execution_time_max = forms.DecimalField(
        max_digits=10,
        decimal_places=6,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Max execution time (s)'})
    )
    
    # Tags and context
    tags = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tags (comma-separated)'})
    )
    environment = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Environment'})
    )
    
    # Advanced filters
    has_stack_trace = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    has_context_data = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    is_resolved = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError("Start date cannot be after end date")
        
        return cleaned_data


class SystemLogExportForm(forms.Form):
    """
    Form for exporting system logs
    """
    EXPORT_FORMATS = [
        ('CSV', 'CSV'),
        ('JSON', 'JSON'),
        ('XML', 'XML'),
        ('PDF', 'PDF'),
        ('EXCEL', 'Excel'),
    ]
    
    export_format = forms.ChoiceField(
        choices=EXPORT_FORMATS,
        initial='CSV',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    include_headers = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    include_metadata = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    include_stack_trace = forms.BooleanField(
        initial=False,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    include_context_data = forms.BooleanField(
        initial=False,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    max_records = forms.IntegerField(
        min_value=1,
        max_value=100000,
        initial=10000,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    filename_prefix = forms.CharField(
        max_length=100,
        initial='system_logs_export',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    # Field selection
    fields_to_include = forms.MultipleChoiceField(
        choices=[
            ('timestamp', 'Timestamp'),
            ('log_type', 'Log Type'),
            ('severity', 'Severity'),
            ('status', 'Status'),
            ('error_message', 'Error Message'),
            ('error_type', 'Error Type'),
            ('module', 'Module'),
            ('function', 'Function'),
            ('user', 'User'),
            ('execution_time', 'Execution Time'),
            ('tags', 'Tags'),
            ('environment', 'Environment'),
        ],
        initial=['timestamp', 'log_type', 'severity', 'error_message', 'module', 'user'],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )


class ErrorPatternForm(forms.ModelForm):
    """
    Form for creating and editing error patterns
    """
    class Meta:
        model = ErrorPattern
        fields = [
            'pattern_type', 'error_signature', 'error_type', 'module', 'function',
            'is_resolved', 'resolution_notes'
        ]
        widgets = {
            'pattern_type': forms.Select(attrs={'class': 'form-select'}),
            'error_signature': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'error_type': forms.TextInput(attrs={'class': 'form-control'}),
            'module': forms.TextInput(attrs={'class': 'form-control'}),
            'function': forms.TextInput(attrs={'class': 'form-control'}),
            'is_resolved': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'resolution_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class DebugSessionForm(forms.ModelForm):
    """
    Form for creating and editing debug sessions
    """
    class Meta:
        model = DebugSession
        fields = [
            'session_name', 'session_type', 'description', 'environment', 'version', 'tags'
        ]
        widgets = {
            'session_name': forms.TextInput(attrs={'class': 'form-control'}),
            'session_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'environment': forms.TextInput(attrs={'class': 'form-control'}),
            'version': forms.TextInput(attrs={'class': 'form-control'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tags (comma-separated)'}),
        }
    
    def clean_tags(self):
        tags = self.cleaned_data.get('tags')
        if tags:
            # Convert comma-separated tags to list
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            return tag_list
        return []


class LogRetentionPolicyForm(forms.ModelForm):
    """
    Form for creating and editing log retention policies
    """
    class Meta:
        model = LogRetentionPolicy
        fields = [
            'name', 'description', 'retention_type', 'retention_value', 'action_type',
            'severity_levels', 'log_types', 'modules', 'tags', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'retention_type': forms.Select(attrs={'class': 'form-select'}),
            'retention_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'action_type': forms.Select(attrs={'class': 'form-select'}),
            'severity_levels': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'log_types': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'modules': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Modules (comma-separated)'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tags (comma-separated)'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['severity_levels'].choices = SystemLog.SEVERITY_LEVELS
        self.fields['log_types'].choices = SystemLog.LOG_TYPES
    
    def clean_modules(self):
        modules = self.cleaned_data.get('modules')
        if modules:
            module_list = [module.strip() for module in modules.split(',') if module.strip()]
            return module_list
        return []
    
    def clean_tags(self):
        tags = self.cleaned_data.get('tags')
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            return tag_list
        return []


class BulkActionForm(forms.Form):
    """
    Form for bulk actions on system logs
    """
    ACTION_CHOICES = [
        ('resolve', 'Mark as Resolved'),
        ('ignore', 'Mark as Ignored'),
        ('escalate', 'Escalate'),
        ('archive', 'Archive'),
        ('delete', 'Delete'),
        ('export', 'Export Selected'),
        ('add_tags', 'Add Tags'),
        ('remove_tags', 'Remove Tags'),
        ('assign_user', 'Assign to User'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    selected_logs = forms.CharField(
        widget=forms.HiddenInput()
    )
    
    tags = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tags (comma-separated)'})
    )
    
    assign_user = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        empty_label="Select User",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    resolution_notes = forms.CharField(
        max_length=1000,
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Resolution notes'})
    )
    
    escalation_level = forms.IntegerField(
        min_value=1,
        max_value=5,
        initial=1,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )


class SystemLogDetailForm(forms.ModelForm):
    """
    Form for viewing and editing system log details
    """
    class Meta:
        model = SystemLog
        fields = [
            'status', 'tags', 'resolution_notes', 'escalation_level'
        ]
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tags (comma-separated)'}),
            'resolution_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'escalation_level': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 5}),
        }
    
    def clean_tags(self):
        tags = self.cleaned_data.get('tags')
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            return tag_list
        return []


class LogExportForm(forms.ModelForm):
    """
    Form for creating log exports
    """
    class Meta:
        model = LogExport
        fields = [
            'name', 'description', 'export_format', 'filter_criteria', 'include_metadata', 'max_records'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'export_format': forms.Select(attrs={'class': 'form-select'}),
            'filter_criteria': forms.HiddenInput(),
            'include_metadata': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'max_records': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class PerformanceFilterForm(forms.Form):
    """
    Form for filtering logs by performance metrics
    """
    execution_time_threshold = forms.DecimalField(
        max_digits=10,
        decimal_places=6,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Execution time threshold (s)'})
    )
    
    memory_usage_threshold = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Memory usage threshold'})
    )
    
    cpu_usage_threshold = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'CPU usage threshold (%)'})
    )
    
    performance_impact = forms.ChoiceField(
        choices=[
            ('', 'All Impact Levels'),
            ('LOW', 'Low Impact'),
            ('MEDIUM', 'Medium Impact'),
            ('HIGH', 'High Impact'),
            ('CRITICAL', 'Critical Impact'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class SecurityFilterForm(forms.Form):
    """
    Form for filtering security-related logs
    """
    security_level = forms.ChoiceField(
        choices=[
            ('', 'All Security Levels'),
            ('LOW', 'Low Risk'),
            ('MEDIUM', 'Medium Risk'),
            ('HIGH', 'High Risk'),
            ('CRITICAL', 'Critical Risk'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    security_category = forms.ChoiceField(
        choices=[
            ('', 'All Categories'),
            ('AUTHENTICATION', 'Authentication'),
            ('AUTHORIZATION', 'Authorization'),
            ('DATA_ACCESS', 'Data Access'),
            ('INPUT_VALIDATION', 'Input Validation'),
            ('CONFIGURATION', 'Configuration'),
            ('NETWORK', 'Network'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    has_security_impact = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    affected_data = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Affected data or resources'})
    )
