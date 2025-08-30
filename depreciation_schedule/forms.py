from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from .models import DepreciationSchedule, DepreciationEntry, DepreciationSettings
from asset_register.models import Asset, AssetCategory
from chart_of_accounts.models import ChartOfAccount


class DepreciationScheduleForm(forms.ModelForm):
    """Form for creating and updating depreciation schedules"""
    
    class Meta:
        model = DepreciationSchedule
        fields = [
            'name', 'description', 'start_date', 'end_date',
            'depreciation_expense_account', 'accumulated_depreciation_account'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter schedule name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter description'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'depreciation_expense_account': forms.Select(attrs={
                'class': 'form-control'
            }),
            'accumulated_depreciation_account': forms.Select(attrs={
                'class': 'form-control'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter accounts for depreciation expense (expense accounts)
        expense_accounts = ChartOfAccount.objects.filter(
            account_type__category='EXPENSE',
            is_active=True
        ).order_by('account_code')
        
        # Filter accounts for accumulated depreciation (asset accounts)
        asset_accounts = ChartOfAccount.objects.filter(
            account_type__category='ASSET',
            is_active=True
        ).order_by('account_code')
        
        self.fields['depreciation_expense_account'].queryset = expense_accounts
        self.fields['accumulated_depreciation_account'].queryset = asset_accounts
        
        # Set default dates if not provided
        if not self.instance.pk:
            today = date.today()
            self.fields['start_date'].initial = today.replace(day=1)
            self.fields['end_date'].initial = today.replace(day=1) + relativedelta(months=1, days=-1)
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date >= end_date:
                raise ValidationError("End date must be after start date")
            
            # Check if the date range is reasonable (not more than 12 months)
            months_diff = (end_date.year - start_date.year) * 12 + end_date.month - start_date.month
            if months_diff > 12:
                raise ValidationError("Date range cannot exceed 12 months")
        
        return cleaned_data


class DepreciationScheduleFilterForm(forms.Form):
    """Form for filtering depreciation schedules"""
    
    STATUS_CHOICES = [
        ('', 'All Statuses'),
        ('draft', 'Draft'),
        ('calculated', 'Calculated'),
        ('posted', 'Posted'),
        ('cancelled', 'Cancelled'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    start_date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'From Date'
        })
    )
    
    start_date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'To Date'
        })
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, description, or schedule number'
        })
    )


class DepreciationEntryFilterForm(forms.Form):
    """Form for filtering depreciation entries"""
    
    asset_category = forms.ModelChoiceField(
        queryset=AssetCategory.objects.all(),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    asset_search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by asset code or name'
        })
    )
    
    period_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'From Period'
        })
    )
    
    period_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'To Period'
        })
    )


class DepreciationSettingsForm(forms.ModelForm):
    """Form for depreciation settings"""
    
    class Meta:
        model = DepreciationSettings
        fields = [
            'default_depreciation_expense_account',
            'default_accumulated_depreciation_account',
            'auto_post_to_gl',
            'require_approval',
            'minimum_depreciation_amount'
        ]
        widgets = {
            'default_depreciation_expense_account': forms.Select(attrs={
                'class': 'form-control'
            }),
            'default_accumulated_depreciation_account': forms.Select(attrs={
                'class': 'form-control'
            }),
            'auto_post_to_gl': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'require_approval': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'minimum_depreciation_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter accounts for depreciation expense (expense accounts)
        expense_accounts = ChartOfAccount.objects.filter(
            account_type__category='EXPENSE',
            is_active=True
        ).order_by('account_code')
        
        # Filter accounts for accumulated depreciation (asset accounts)
        asset_accounts = ChartOfAccount.objects.filter(
            account_type__category='ASSET',
            is_active=True
        ).order_by('account_code')
        
        self.fields['default_depreciation_expense_account'].queryset = expense_accounts
        self.fields['default_accumulated_depreciation_account'].queryset = asset_accounts


class DepreciationCalculationForm(forms.Form):
    """Form for triggering depreciation calculations"""
    
    confirm_calculation = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text="I confirm that I want to calculate depreciation for the selected period"
    )
    
    include_disposed_assets = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text="Include assets that were disposed during the period"
    )
    
    recalculate_existing = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text="Recalculate depreciation for assets that already have entries in this period"
    )


class DepreciationPostingForm(forms.Form):
    """Form for posting depreciation to general ledger"""
    
    confirm_posting = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text="I confirm that I want to post depreciation to the general ledger"
    )
    
    post_date = forms.DateField(
        required=True,
        initial=date.today,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        help_text="Date for the journal entry"
    )
    
    reference = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Optional reference for the journal entry'
        })
    )
    
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Optional description for the journal entry'
        })
    )


class DepreciationExportForm(forms.Form):
    """Form for exporting depreciation data"""
    
    EXPORT_FORMATS = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    ]
    
    export_format = forms.ChoiceField(
        choices=EXPORT_FORMATS,
        initial='pdf',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    include_details = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text="Include individual asset details"
    )
    
    include_summary = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text="Include summary totals"
    )
    
    include_charts = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text="Include charts and graphs (PDF only)"
    )


class AssetDepreciationForm(forms.Form):
    """Form for calculating depreciation for specific assets"""
    
    assets = forms.ModelMultipleChoiceField(
        queryset=Asset.objects.filter(
            is_deleted=False,
            disposal_date__isnull=True,
            purchase_value__gt=0,
            useful_life_years__gt=0
        ),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control',
            'size': '8'
        }),
        help_text="Select assets to calculate depreciation for"
    )
    
    start_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    end_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    depreciation_method = forms.ChoiceField(
        choices=[
            ('straight_line', 'Straight-line'),
            ('declining_balance', 'Declining Balance'),
        ],
        initial='straight_line',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set default dates
        today = date.today()
        self.fields['start_date'].initial = today.replace(day=1)
        self.fields['end_date'].initial = today.replace(day=1) + relativedelta(months=1, days=-1)
        
        # Improve the assets field queryset ordering
        self.fields['assets'].queryset = Asset.objects.filter(
            is_deleted=False,
            disposal_date__isnull=True,
            purchase_value__gt=0,
            useful_life_years__gt=0
        ).order_by('asset_code')
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date >= end_date:
                raise ValidationError("End date must be after start date")
        
        return cleaned_data
