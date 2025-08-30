from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta


class TrialBalanceFilterForm(forms.Form):
    """Form for filtering trial balance data"""
    
    # Date Range
    from_date = forms.DateField(
        label='From Date',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'placeholder': 'Select start date'
        }),
        initial=date.today().replace(day=1)  # First day of current month
    )
    
    to_date = forms.DateField(
        label='To Date',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'placeholder': 'Select end date'
        }),
        initial=date.today()  # Current date
    )
    
    # Company
    company = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        label='Company',
        required=False,
        empty_label="All Companies",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'placeholder': 'Select company'
        })
    )
    
    # Additional Filters
    include_zero_balances = forms.BooleanField(
        label='Include Zero Balances',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    account_type = forms.ChoiceField(
        label='Account Type',
        required=False,
        choices=[('', 'All Types')],
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set company queryset
        try:
            from company.company_model import Company
            self.fields['company'].queryset = Company.objects.filter(is_active=True)
        except ImportError:
            # Use a dummy queryset if Company model is not available
            from django.db.models import QuerySet
            self.fields['company'].queryset = QuerySet()
        
        # Set account type choices
        try:
            from chart_of_accounts.models import AccountType
            account_types = [('', 'All Types')] + list(AccountType.objects.values_list('id', 'name'))
            self.fields['account_type'].choices = account_types
        except ImportError:
            pass
    
    def clean(self):
        cleaned_data = super().clean()
        from_date = cleaned_data.get('from_date')
        to_date = cleaned_data.get('to_date')
        
        if from_date and to_date:
            if from_date > to_date:
                raise ValidationError("From date cannot be after to date.")
            
            # Check if date range is not too large (e.g., more than 1 year)
            if (to_date - from_date).days > 365:
                raise ValidationError("Date range cannot exceed 1 year.")
        
        return cleaned_data


class ExportForm(forms.Form):
    """Form for export options"""
    
    EXPORT_FORMATS = [
        ('excel', 'Excel (.xlsx)'),
        ('pdf', 'PDF'),
        ('csv', 'CSV'),
    ]
    
    format = forms.ChoiceField(
        label='Export Format',
        choices=EXPORT_FORMATS,
        initial='excel',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )
    
    include_headers = forms.BooleanField(
        label='Include Headers',
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    include_totals = forms.BooleanField(
        label='Include Totals',
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    include_running_balance = forms.BooleanField(
        label='Include Running Balance',
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    ) 