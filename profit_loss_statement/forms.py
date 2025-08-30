from django import forms
from django.utils import timezone
from datetime import datetime, timedelta
from company.company_model import Company
from chart_of_accounts.models import ChartOfAccount, AccountType


class ProfitLossReportForm(forms.Form):
    """Form for generating Profit & Loss reports"""
    
    # Date range
    from_date = forms.DateField(
        label='From Date',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        initial=timezone.now().replace(day=1).date(),
        required=False
    )
    
    to_date = forms.DateField(
        label='To Date',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        initial=timezone.now().date(),
        required=False
    )
    
    # Company selection
    company = forms.ModelChoiceField(
        queryset=Company.objects.all(),
        required=False,
        empty_label="All Companies",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'company-select'
        })
    )
    
    # Report period type
    report_period = forms.ChoiceField(
        choices=[
            ('custom', 'Custom Period'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('yearly', 'Yearly'),
        ],
        initial='custom',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'report-period'
        })
    )
    
    # Comparison options
    comparison_type = forms.ChoiceField(
        choices=[
            ('none', 'No Comparison'),
            ('previous_period', 'Previous Period'),
            ('previous_year', 'Previous Year'),
            ('budget', 'Budget Comparison'),
        ],
        initial='none',
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'comparison-type'
        })
    )
    
    # Account type filters
    revenue_accounts = forms.ModelMultipleChoiceField(
        queryset=AccountType.objects.filter(name__icontains='income').exclude(name__icontains='other'),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        help_text="Select revenue account types to include"
    )
    
    cogs_accounts = forms.ModelMultipleChoiceField(
        queryset=AccountType.objects.filter(name__icontains='cost').exclude(name__icontains='other'),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        help_text="Select cost of goods sold account types"
    )
    
    expense_accounts = forms.ModelMultipleChoiceField(
        queryset=AccountType.objects.filter(name__icontains='expense').exclude(name__icontains='cost'),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        help_text="Select operating expense account types"
    )
    
    # Display options
    include_zero_balances = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'include-zero-balances'
        }),
        help_text="Include accounts with zero balances"
    )
    
    group_by_department = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'group-by-department'
        }),
        help_text="Group accounts by department"
    )
    
    show_percentages = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'show-percentages'
        }),
        help_text="Show percentages of total revenue"
    )
    
    # Export options
    include_headers = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    include_totals = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    include_comparison = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set initial date range to current month
        today = timezone.now().date()
        first_day = today.replace(day=1)
        
        # Set initial values on the fields themselves
        if not self.is_bound:
            self.fields['from_date'].initial = first_day
            self.fields['to_date'].initial = today
    
    def clean(self):
        cleaned_data = super().clean()
        from_date = cleaned_data.get('from_date')
        to_date = cleaned_data.get('to_date')
        
        if from_date and to_date and from_date > to_date:
            raise forms.ValidationError("From date cannot be after to date.")
        
        return cleaned_data


class ExportForm(forms.Form):
    """Form for export options"""
    
    export_format = forms.ChoiceField(
        choices=[
            ('pdf', 'PDF'),
            ('excel', 'Excel'),
            ('csv', 'CSV'),
        ],
        initial='pdf',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'export-format'
        })
    )
    
    include_headers = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    include_totals = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    include_comparison = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    include_percentages = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )