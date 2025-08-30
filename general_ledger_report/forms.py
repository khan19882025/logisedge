from django import forms
from django.contrib.auth.models import User
from chart_of_accounts.models import ChartOfAccount
from company.company_model import Company
from fiscal_year.models import FiscalYear
from .models import GeneralLedgerReport, ReportTemplate
from django.utils import timezone
from datetime import datetime, timedelta


class GeneralLedgerReportForm(forms.ModelForm):
    """Form for creating and editing General Ledger Reports"""
    
    # Date range fields
    from_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'placeholder': 'From Date'
        }),
        required=True,
        initial=timezone.now().date() - timedelta(days=30)
    )
    
    to_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'placeholder': 'To Date'
        }),
        required=True,
        initial=timezone.now().date()
    )
    
    # Account selection
    account = forms.ModelChoiceField(
        queryset=ChartOfAccount.objects.filter(is_active=True, is_group=False),
        required=False,
        empty_label="All Accounts",
        widget=forms.Select(attrs={
            'class': 'form-control select2',
            'data-placeholder': 'Select Account'
        })
    )
    
    # Amount filters
    min_amount = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Minimum Amount',
            'step': '0.01',
            'min': '0'
        })
    )
    
    max_amount = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Maximum Amount',
            'step': '0.01',
            'min': '0'
        })
    )
    
    # Report type
    report_type = forms.ChoiceField(
        choices=GeneralLedgerReport.REPORT_TYPES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    # Export format
    export_format = forms.ChoiceField(
        choices=GeneralLedgerReport.EXPORT_FORMATS,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    class Meta:
        model = GeneralLedgerReport
        fields = [
            'name', 'report_type', 'from_date', 'to_date', 'account',
            'include_sub_accounts', 'min_amount', 'max_amount',
            'include_reconciled_only', 'include_unreconciled_only',
            'export_format', 'include_opening_balance', 'include_closing_balance'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Report Name'
            }),
            'include_sub_accounts': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'include_reconciled_only': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'include_unreconciled_only': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'include_opening_balance': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'include_closing_balance': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        # Filter accounts by company if provided
        if company:
            self.fields['account'].queryset = ChartOfAccount.objects.filter(
                is_active=True,
                is_group=False,
                company=company
            )
        
        # Set initial values
        if not self.instance.pk:
            # Set default name
            if not self.initial.get('name'):
                self.initial['name'] = f"General Ledger Report - {timezone.now().strftime('%d/%m/%Y')}"
    
    def clean(self):
        cleaned_data = super().clean()
        from_date = cleaned_data.get('from_date')
        to_date = cleaned_data.get('to_date')
        min_amount = cleaned_data.get('min_amount')
        max_amount = cleaned_data.get('max_amount')
        include_reconciled_only = cleaned_data.get('include_reconciled_only')
        include_unreconciled_only = cleaned_data.get('include_unreconciled_only')
        
        # Validate date range
        if from_date and to_date and from_date > to_date:
            raise forms.ValidationError("From date cannot be after to date.")
        
        # Validate amount range
        if min_amount and max_amount and min_amount > max_amount:
            raise forms.ValidationError("Minimum amount cannot be greater than maximum amount.")
        
        # Validate reconciliation filters
        if include_reconciled_only and include_unreconciled_only:
            raise forms.ValidationError("Cannot select both 'Reconciled Only' and 'Unreconciled Only'.")
        
        return cleaned_data


class QuickReportForm(forms.Form):
    """Quick report form for simple filtering"""
    
    # Date presets
    DATE_PRESETS = [
        ('today', 'Today'),
        ('yesterday', 'Yesterday'),
        ('this_week', 'This Week'),
        ('last_week', 'Last Week'),
        ('this_month', 'This Month'),
        ('last_month', 'Last Month'),
        ('this_quarter', 'This Quarter'),
        ('last_quarter', 'Last Quarter'),
        ('this_year', 'This Year'),
        ('last_year', 'Last Year'),
        ('custom', 'Custom Range'),
    ]
    
    date_preset = forms.ChoiceField(
        choices=DATE_PRESETS,
        initial='this_month',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'date-preset'
        })
    )
    
    from_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'id': 'from-date'
        })
    )
    
    to_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'id': 'to-date'
        })
    )
    
    account = forms.ModelChoiceField(
        queryset=ChartOfAccount.objects.filter(is_active=True, is_group=False),
        required=False,
        empty_label="All Accounts",
        widget=forms.Select(attrs={
            'class': 'form-control select2',
            'data-placeholder': 'Select Account'
        })
    )
    
    include_sub_accounts = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        if company:
            self.fields['account'].queryset = ChartOfAccount.objects.filter(
                is_active=True,
                is_group=False,
                company=company
            )
    
    def clean(self):
        cleaned_data = super().clean()
        date_preset = cleaned_data.get('date_preset')
        from_date = cleaned_data.get('from_date')
        to_date = cleaned_data.get('to_date')
        
        # Set dates based on preset
        if date_preset != 'custom':
            today = timezone.now().date()
            
            if date_preset == 'today':
                cleaned_data['from_date'] = today
                cleaned_data['to_date'] = today
            elif date_preset == 'yesterday':
                yesterday = today - timedelta(days=1)
                cleaned_data['from_date'] = yesterday
                cleaned_data['to_date'] = yesterday
            elif date_preset == 'this_week':
                # Start of week (Monday)
                start_of_week = today - timedelta(days=today.weekday())
                cleaned_data['from_date'] = start_of_week
                cleaned_data['to_date'] = today
            elif date_preset == 'last_week':
                # Previous week
                start_of_week = today - timedelta(days=today.weekday())
                start_of_last_week = start_of_week - timedelta(days=7)
                end_of_last_week = start_of_week - timedelta(days=1)
                cleaned_data['from_date'] = start_of_last_week
                cleaned_data['to_date'] = end_of_last_week
            elif date_preset == 'this_month':
                # Start of month
                start_of_month = today.replace(day=1)
                cleaned_data['from_date'] = start_of_month
                cleaned_data['to_date'] = today
            elif date_preset == 'last_month':
                # Previous month
                if today.month == 1:
                    last_month = today.replace(year=today.year-1, month=12)
                else:
                    last_month = today.replace(month=today.month-1)
                start_of_last_month = last_month.replace(day=1)
                if today.month == 1:
                    end_of_last_month = today.replace(day=1) - timedelta(days=1)
                else:
                    end_of_last_month = today.replace(day=1) - timedelta(days=1)
                cleaned_data['from_date'] = start_of_last_month
                cleaned_data['to_date'] = end_of_last_month
            elif date_preset == 'this_quarter':
                # Current quarter
                quarter_start_month = ((today.month - 1) // 3) * 3 + 1
                start_of_quarter = today.replace(month=quarter_start_month, day=1)
                cleaned_data['from_date'] = start_of_quarter
                cleaned_data['to_date'] = today
            elif date_preset == 'last_quarter':
                # Previous quarter
                quarter_start_month = ((today.month - 1) // 3) * 3 + 1
                if quarter_start_month == 1:
                    last_quarter_start_month = 10
                    last_quarter_year = today.year - 1
                else:
                    last_quarter_start_month = quarter_start_month - 3
                    last_quarter_year = today.year
                start_of_last_quarter = today.replace(year=last_quarter_year, month=last_quarter_start_month, day=1)
                end_of_last_quarter = start_of_quarter - timedelta(days=1)
                cleaned_data['from_date'] = start_of_last_quarter
                cleaned_data['to_date'] = end_of_last_quarter
            elif date_preset == 'this_year':
                # Start of year
                start_of_year = today.replace(month=1, day=1)
                cleaned_data['from_date'] = start_of_year
                cleaned_data['to_date'] = today
            elif date_preset == 'last_year':
                # Previous year
                start_of_last_year = today.replace(year=today.year-1, month=1, day=1)
                end_of_last_year = today.replace(month=1, day=1) - timedelta(days=1)
                cleaned_data['from_date'] = start_of_last_year
                cleaned_data['to_date'] = end_of_last_year
        
        return cleaned_data


class ReportTemplateForm(forms.ModelForm):
    """Form for creating and editing report templates"""
    
    class Meta:
        model = ReportTemplate
        fields = [
            'name', 'description', 'template_type', 'default_from_date',
            'default_to_date', 'default_account_codes', 'include_sub_accounts',
            'include_opening_balance', 'include_closing_balance',
            'default_export_format', 'is_public'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Template Name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Template Description'
            }),
            'template_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'default_from_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'default_to_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'default_account_codes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter account codes separated by commas'
            }),
            'include_sub_accounts': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'include_opening_balance': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'include_closing_balance': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'default_export_format': forms.Select(attrs={
                'class': 'form-control'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }