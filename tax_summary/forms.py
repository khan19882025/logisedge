from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import TaxSummaryReport, TaxSummaryTransaction


class TaxSummaryReportForm(forms.ModelForm):
    """Form for creating and editing tax summary reports"""
    
    class Meta:
        model = TaxSummaryReport
        fields = [
            'report_name', 'report_type', 'start_date', 'end_date', 'currency'
        ]
        widgets = {
            'report_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter report name'
            }),
            'report_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'currency': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date >= end_date:
                raise ValidationError("End date must be after start date.")
            
            # Check if date range is not more than 1 year
            if (end_date - start_date).days > 365:
                raise ValidationError("Date range cannot exceed 1 year.")
        
        return cleaned_data


class TaxSummaryFilterForm(forms.Form):
    """Form for filtering tax summary reports"""
    
    # Date range filters
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    # Party filters
    party_name = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by party name'
        })
    )
    vat_number = forms.CharField(
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by VAT number'
        })
    )
    
    # Transaction type filters
    transaction_type = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Types'),
            ('input', 'Input Tax'),
            ('output', 'Output Tax'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    # Tax rate filters
    vat_percentage = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Rates'),
            ('0', '0%'),
            ('5', '5%'),
            ('12', '12%'),
            ('18', '18%'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    # Currency filter
    currency = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Currencies'),
            ('AED', 'AED'),
            ('USD', 'USD'),
            ('EUR', 'EUR'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    # Amount range filters
    min_amount = forms.DecimalField(
        required=False,
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Min amount',
            'step': '0.01'
        })
    )
    max_amount = forms.DecimalField(
        required=False,
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Max amount',
            'step': '0.01'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        min_amount = cleaned_data.get('min_amount')
        max_amount = cleaned_data.get('max_amount')
        
        if start_date and end_date and start_date >= end_date:
            raise ValidationError("End date must be after start date.")
        
        if min_amount and max_amount and min_amount > max_amount:
            raise ValidationError("Minimum amount cannot be greater than maximum amount.")
        
        return cleaned_data


class TaxSummaryExportForm(forms.Form):
    """Form for exporting tax summary reports"""
    
    EXPORT_FORMATS = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    ]
    
    export_format = forms.ChoiceField(
        choices=EXPORT_FORMATS,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    include_summary = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    include_transactions = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    include_filters = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )


class TaxSummarySearchForm(forms.Form):
    """Form for searching tax summary reports"""
    
    search = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search reports...'
        })
    )
    
    report_type = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Types'),
            ('input_output', 'Input/Output Tax Summary'),
            ('vat_summary', 'VAT Summary'),
            ('detailed', 'Detailed Tax Report'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Status'),
            ('draft', 'Draft'),
            ('generated', 'Generated'),
            ('exported', 'Exported'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
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
