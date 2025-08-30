from django import forms
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
from .models import LogHistory, LogCategory, LogFilter, LogExport, LogRetentionPolicy


class LogHistorySearchForm(forms.Form):
    """
    Advanced search form for log history entries
    """
    
    # Date Range
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'placeholder': 'From Date'
        }),
        label='From Date'
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'placeholder': 'To Date'
        }),
        label='To Date'
    )
    
    # Action and Severity
    action_type = forms.ChoiceField(
        choices=[('', 'All Actions')] + LogHistory.ACTION_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'placeholder': 'Action Type'
        }),
        label='Action Type'
    )
    
    severity = forms.ChoiceField(
        choices=[('', 'All Severities')] + LogHistory.SEVERITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'placeholder': 'Severity'
        }),
        label='Severity'
    )
    
    # User and Object
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True).order_by('username'),
        required=False,
        empty_label='All Users',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'placeholder': 'User'
        }),
        label='User'
    )
    
    object_type = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Object Type (e.g., User, Order)'
        }),
        label='Object Type'
    )
    
    object_name = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Object Name'
        }),
        label='Object Name'
    )
    
    # Module and Function
    module = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Module'
        }),
        label='Module'
    )
    
    function = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Function'
        }),
        label='Function'
    )
    
    # Description and Details
    description = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search in description'
        }),
        label='Description'
    )
    
    # Tags
    tags = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tags (comma-separated)'
        }),
        label='Tags'
    )
    
    # Quick Date Presets
    QUICK_DATE_CHOICES = [
        ('', 'Custom Range'),
        ('today', 'Today'),
        ('yesterday', 'Yesterday'),
        ('last_7_days', 'Last 7 Days'),
        ('last_30_days', 'Last 30 Days'),
        ('last_90_days', 'Last 90 Days'),
        ('this_month', 'This Month'),
        ('last_month', 'Last Month'),
        ('this_year', 'This Year'),
        ('last_year', 'Last Year'),
    ]
    
    quick_date = forms.ChoiceField(
        choices=QUICK_DATE_CHOICES,
        required=False,
        initial='',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'onchange': 'handleQuickDateChange(this.value)'
        }),
        label='Quick Date Selection'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default date range to last 30 days
        if not self.data:
            self.fields['date_from'].initial = (timezone.now() - timedelta(days=30)).date()
            self.fields['date_to'].initial = timezone.now().date()
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError("From date cannot be after to date.")
        
        return cleaned_data


class LogHistoryExportForm(forms.Form):
    """
    Form for exporting log history data
    """
    
    EXPORT_FORMAT_CHOICES = [
        ('CSV', 'CSV'),
        ('JSON', 'JSON'),
        ('XML', 'XML'),
        ('PDF', 'PDF'),
    ]
    
    export_format = forms.ChoiceField(
        choices=EXPORT_FORMAT_CHOICES,
        initial='CSV',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'export-format'
        }),
        label='Export Format'
    )
    
    include_headers = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'include-headers'
        }),
        label='Include Headers'
    )
    
    include_metadata = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'include-metadata'
        }),
        label='Include Metadata'
    )
    
    max_records = forms.IntegerField(
        min_value=1,
        max_value=100000,
        initial=10000,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'id': 'max-records',
            'placeholder': 'Maximum records to export'
        }),
        label='Maximum Records',
        help_text='Maximum number of records to export (1-100,000)'
    )
    
    filename_prefix = forms.CharField(
        max_length=100,
        initial='log_history',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'filename-prefix',
            'placeholder': 'Filename prefix'
        }),
        label='Filename Prefix'
    )


class LogFilterForm(forms.ModelForm):
    """
    Form for creating and editing saved log filters
    """
    
    class Meta:
        model = LogFilter
        fields = ['name', 'description', 'filter_criteria', 'is_default', 'is_public']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Filter name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Filter description'
            }),
            'filter_criteria': forms.HiddenInput(),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['user'].initial = self.user
            self.fields['user'].widget = forms.HiddenInput()


class LogCategoryForm(forms.ModelForm):
    """
    Form for creating and editing log categories
    """
    
    class Meta:
        model = LogCategory
        fields = ['name', 'description', 'color', 'icon', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Category name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Category description'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'placeholder': '#007bff'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Icon class (e.g., fas fa-folder)'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class LogRetentionPolicyForm(forms.ModelForm):
    """
    Form for creating and editing log retention policies
    """
    
    class Meta:
        model = LogRetentionPolicy
        fields = ['name', 'description', 'action_type', 'severity', 'module', 'retention_period', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Policy name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Policy description'
            }),
            'action_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'severity': forms.Select(attrs={
                'class': 'form-select'
            }),
            'module': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Module name'
            }),
            'retention_period': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add empty choice for action_type and severity
        self.fields['action_type'].choices = [('', 'All Actions')] + LogHistory.ACTION_CHOICES
        self.fields['severity'].choices = [('', 'All Severities')] + LogHistory.SEVERITY_CHOICES


class BulkActionForm(forms.Form):
    """
    Form for bulk actions on log entries
    """
    
    ACTION_CHOICES = [
        ('', 'Select Action'),
        ('archive', 'Archive Selected'),
        ('delete', 'Delete Selected'),
        ('export', 'Export Selected'),
        ('tag', 'Add Tags'),
        ('untag', 'Remove Tags'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'bulk-action'
        }),
        label='Bulk Action'
    )
    
    selected_logs = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )
    
    tags = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tags (comma-separated)',
            'id': 'bulk-tags'
        }),
        label='Tags',
        help_text='Required when adding/removing tags'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        tags = cleaned_data.get('tags')
        
        if action in ['tag', 'untag'] and not tags:
            raise forms.ValidationError("Tags are required when adding or removing tags.")
        
        return cleaned_data


class LogHistoryDetailForm(forms.Form):
    """
    Form for viewing detailed log entry information
    """
    
    # This form is read-only and used for displaying log details
    # All fields are disabled to prevent editing
    
    timestamp = forms.DateTimeField(
        disabled=True,
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'readonly': 'readonly'
        })
    )
    
    action_type = forms.CharField(
        disabled=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'readonly': 'readonly'
        })
    )
    
    severity = forms.CharField(
        disabled=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'readonly': 'readonly'
        })
    )
    
    user = forms.CharField(
        disabled=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'readonly': 'readonly'
        })
    )
    
    description = forms.CharField(
        disabled=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'readonly': 'readonly'
        })
    )
    
    details = forms.CharField(
        disabled=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'readonly': 'readonly'
        })
    )
    
    before_values = forms.CharField(
        disabled=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'readonly': 'readonly'
        })
    )
    
    after_values = forms.CharField(
        disabled=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'readonly': 'readonly'
        })
    )
