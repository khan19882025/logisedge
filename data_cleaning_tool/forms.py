from django import forms
from django.forms import ModelForm, Form
from .models import DataCleaningSession, DataCleaningRule, AutomatedCleaningSchedule


class DataCleaningSessionForm(ModelForm):
    """Form for creating and editing data cleaning sessions"""
    
    class Meta:
        model = DataCleaningSession
        fields = ['name', 'description', 'cleaning_type']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter session name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe what this cleaning session will do'
            }),
            'cleaning_type': forms.Select(attrs={
                'class': 'form-control'
            })
        }


class DataCleaningRuleForm(ModelForm):
    """Form for creating and editing data cleaning rules"""
    
    class Meta:
        model = DataCleaningRule
        fields = ['name', 'description', 'rule_type', 'target_model', 'target_field', 'rule_config', 'priority', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter rule name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe what this rule does'
            }),
            'rule_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'target_model': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., customer.Customer, invoice.Invoice'
            }),
            'target_field': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Leave blank for model-level rules'
            }),
            'priority': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }


class AutomatedCleaningScheduleForm(ModelForm):
    """Form for creating and editing automated cleaning schedules"""
    
    class Meta:
        model = AutomatedCleaningSchedule
        fields = ['name', 'description', 'cleaning_type', 'frequency', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter schedule name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe this automated schedule'
            }),
            'cleaning_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'frequency': forms.Select(attrs={
                'class': 'form-control'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }


class DataCleaningConfigurationForm(Form):
    """Form for configuring data cleaning parameters"""
    
    # Master Data Cleaning Options
    clean_customers = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    clean_vendors = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    clean_items = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    clean_chart_of_accounts = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    clean_locations = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    # Transactional Data Cleaning Options
    clean_sales = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    clean_purchases = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    clean_inventory_movements = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    clean_journal_entries = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    clean_payroll = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    # Financial Data Cleaning Options
    clean_chart_of_accounts_detailed = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    clean_journal_vouchers = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    clean_ledgers = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    clean_cost_centers = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    clean_tax_records = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    # Cleaning Actions
    auto_merge_duplicates = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    auto_fill_mandatory_fields = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    auto_standardize_formats = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    auto_archive_obsolete = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    # Validation Options
    strict_validation = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    generate_detailed_reports = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    send_notifications = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class DataCleaningFilterForm(Form):
    """Form for filtering data cleaning results"""
    
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
    severity = forms.ChoiceField(
        choices=[
            ('', 'All Severities'),
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    action_type = forms.ChoiceField(
        choices=[
            ('', 'All Actions'),
            ('record_created', 'Record Created'),
            ('record_updated', 'Record Updated'),
            ('record_deleted', 'Record Deleted'),
            ('record_merged', 'Record Merged'),
            ('field_updated', 'Field Updated'),
            ('validation_error', 'Validation Error'),
            ('warning_generated', 'Warning Generated'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    target_model = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filter by model name'
        })
    )
