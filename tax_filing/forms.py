from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import TaxFilingReport, TaxFilingTransaction, TaxFilingValidation, TaxFilingExport, TaxFilingSettings


class TaxFilingReportForm(forms.ModelForm):
    """Form for creating and editing tax filing reports"""
    
    class Meta:
        model = TaxFilingReport
        fields = [
            'report_name', 'filing_period', 'start_date', 'end_date', 'currency', 'notes'
        ]
        widgets = {
            'report_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter report name (e.g., VAT Filing Q1 2024)'
            }),
            'filing_period': forms.Select(attrs={
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
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes for this filing report...'
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
            
            # Check if dates are in the past
            today = timezone.now().date()
            if end_date > today:
                raise ValidationError("End date cannot be in the future.")
        
        return cleaned_data


class TaxFilingFilterForm(forms.Form):
    """Form for filtering tax filing reports"""
    
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
            ('output', 'Output Tax (Sales)'),
            ('input', 'Input Tax (Purchases)'),
            ('adjustment', 'Adjustment'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    # Adjustment type filters
    adjustment_type = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Adjustments'),
            ('credit_note', 'Credit Note'),
            ('debit_note', 'Debit Note'),
            ('refund', 'Refund'),
            ('write_off', 'Write-off'),
            ('correction', 'Correction'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    # VAT rate filters
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
    
    # Validation filters
    has_validation_issues = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
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


class TaxFilingExportForm(forms.Form):
    """Form for exporting tax filing reports"""
    
    EXPORT_FORMATS = [
        ('pdf', 'PDF (For Filing Submission)'),
        ('excel', 'Excel (For Review)'),
        ('csv', 'CSV (For Analysis)'),
        ('xml', 'XML (For System Integration)'),
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
    
    include_validations = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    date_format = forms.ChoiceField(
        required=False,
        choices=[
            ('dd/mm/yyyy', 'DD/MM/YYYY'),
            ('mm/dd/yyyy', 'MM/DD/YYYY'),
            ('yyyy-mm-dd', 'YYYY-MM-DD'),
        ],
        initial='dd/mm/yyyy',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    number_format = forms.ChoiceField(
        required=False,
        choices=[
            ('comma', '1,234.56'),
            ('dot', '1.234,56'),
            ('space', '1 234.56'),
        ],
        initial='comma',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    notes = forms.CharField(
        required=False,
        max_length=500,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Export notes (optional)'
        })
    )


class TaxFilingSearchForm(forms.Form):
    """Form for searching tax filing reports"""
    
    search = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search reports...'
        })
    )
    
    filing_period = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Periods'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('yearly', 'Yearly'),
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
            ('reviewed', 'Reviewed'),
            ('submitted', 'Submitted'),
            ('filed', 'Filed'),
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


class TaxFilingValidationForm(forms.ModelForm):
    """Form for managing tax filing validations"""
    
    class Meta:
        model = TaxFilingValidation
        fields = ['validation_type', 'severity', 'description', 'field_name', 'expected_value', 'actual_value', 'is_resolved']
        widgets = {
            'validation_type': forms.Select(attrs={'class': 'form-control'}),
            'severity': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'field_name': forms.TextInput(attrs={'class': 'form-control'}),
            'expected_value': forms.TextInput(attrs={'class': 'form-control'}),
            'actual_value': forms.TextInput(attrs={'class': 'form-control'}),
            'is_resolved': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TaxFilingSettingsForm(forms.ModelForm):
    """Form for tax filing settings"""
    
    class Meta:
        model = TaxFilingSettings
        fields = [
            'tax_authority_name', 'tax_authority_code', 'filing_deadline_days', 
            'auto_validation', 'require_vat_numbers', 'default_currency'
        ]
        widgets = {
            'tax_authority_name': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_authority_code': forms.TextInput(attrs={'class': 'form-control'}),
            'filing_deadline_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'auto_validation': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'require_vat_numbers': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'default_currency': forms.Select(attrs={'class': 'form-control'}),
        }
