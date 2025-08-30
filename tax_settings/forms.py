from django import forms
from django.forms import ModelForm, inlineformset_factory
from django.contrib.auth.models import User
from .models import (
    TaxJurisdiction, TaxType, TaxRate, ProductTaxCategory,
    CustomerTaxProfile, SupplierTaxProfile, VATReport
)
from customer.models import Customer
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils import timezone


class TaxJurisdictionForm(ModelForm):
    """Form for Tax Jurisdiction"""
    class Meta:
        model = TaxJurisdiction
        fields = ['name', 'code', 'jurisdiction_type', 'parent_jurisdiction', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter jurisdiction name'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter jurisdiction code'}),
            'jurisdiction_type': forms.Select(attrs={'class': 'form-control'}),
            'parent_jurisdiction': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_code(self):
        code = self.cleaned_data['code']
        if not code.isalnum():
            raise ValidationError("Code must contain only letters and numbers.")
        return code.upper()


class TaxTypeForm(ModelForm):
    """Form for Tax Type"""
    class Meta:
        model = TaxType
        fields = ['name', 'code', 'tax_type', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter tax type name'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter tax type code'}),
            'tax_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter description'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_code(self):
        code = self.cleaned_data['code']
        if not code.replace('_', '').isalnum():
            raise ValidationError("Code must contain only letters, numbers, and underscores.")
        return code.upper()


class TaxRateForm(ModelForm):
    """Form for Tax Rate"""
    class Meta:
        model = TaxRate
        fields = [
            'name', 'rate_percentage', 'tax_type', 'jurisdiction', 
            'effective_from', 'effective_to', 'rounding_method', 
            'is_active', 'description'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter tax rate name'}),
            'rate_percentage': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'tax_type': forms.Select(attrs={'class': 'form-control'}),
            'jurisdiction': forms.Select(attrs={'class': 'form-control'}),
            'effective_from': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'effective_to': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'rounding_method': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter description'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        effective_from = cleaned_data.get('effective_from')
        effective_to = cleaned_data.get('effective_to')
        tax_type = cleaned_data.get('tax_type')
        jurisdiction = cleaned_data.get('jurisdiction')

        if effective_from and effective_to and effective_from >= effective_to:
            raise ValidationError("Effective from date must be before effective to date.")

        if effective_from and effective_from < timezone.now().date():
            raise ValidationError("Effective from date cannot be in the past.")

        # Check for overlapping tax rates
        if tax_type and jurisdiction and effective_from:
            overlapping_rates = TaxRate.objects.filter(
                tax_type=tax_type,
                jurisdiction=jurisdiction,
                is_active=True
            )
            
            if self.instance.pk:
                overlapping_rates = overlapping_rates.exclude(pk=self.instance.pk)
            
            for rate in overlapping_rates:
                if (rate.effective_from <= effective_from and 
                    (rate.effective_to is None or rate.effective_to >= effective_from)):
                    raise ValidationError(
                        f"Tax rate overlaps with existing rate '{rate.name}' "
                        f"({rate.effective_from} to {rate.effective_to or 'No end date'})"
                    )

        return cleaned_data


class ProductTaxCategoryForm(ModelForm):
    """Form for Product Tax Category"""
    class Meta:
        model = ProductTaxCategory
        fields = ['name', 'code', 'description', 'default_tax_rate', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter category name'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter category code'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter description'}),
            'default_tax_rate': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active tax rates
        self.fields['default_tax_rate'].queryset = TaxRate.objects.filter(is_active=True)


class CustomerTaxProfileForm(ModelForm):
    """Form for Customer Tax Profile"""
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select a customer"
    )

    class Meta:
        model = CustomerTaxProfile
        fields = [
            'customer', 'tax_registration_number', 'tax_exemption_number',
            'default_tax_rate', 'is_tax_exempt', 'tax_exemption_reason'
        ]
        widgets = {
            'tax_registration_number': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter tax registration number'
            }),
            'tax_exemption_number': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter tax exemption number'
            }),
            'default_tax_rate': forms.Select(attrs={'class': 'form-control'}),
            'is_tax_exempt': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tax_exemption_reason': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Enter tax exemption reason'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active tax rates
        self.fields['default_tax_rate'].queryset = TaxRate.objects.filter(is_active=True)
        
        # Exclude customers that already have tax profiles
        existing_customers = CustomerTaxProfile.objects.values_list('customer_id', flat=True)
        if self.instance.pk:
            existing_customers = existing_customers.exclude(customer_id=self.instance.customer_id)
        self.fields['customer'].queryset = Customer.objects.exclude(id__in=existing_customers)


class SupplierTaxProfileForm(ModelForm):
    """Form for Supplier Tax Profile"""

    class Meta:
        model = SupplierTaxProfile
        fields = [
            'supplier_name', 'supplier_code', 'tax_registration_number', 'tax_exemption_number',
            'default_tax_rate', 'is_tax_exempt', 'tax_exemption_reason'
        ]
        widgets = {
            'supplier_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter supplier name'
            }),
            'supplier_code': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter supplier code'
            }),
            'tax_registration_number': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter tax registration number'
            }),
            'tax_exemption_number': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter tax exemption number'
            }),
            'default_tax_rate': forms.Select(attrs={'class': 'form-control'}),
            'is_tax_exempt': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tax_exemption_reason': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Enter tax exemption reason'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active tax rates
        self.fields['default_tax_rate'].queryset = TaxRate.objects.filter(is_active=True)


class VATReportForm(ModelForm):
    """Form for VAT Report"""
    class Meta:
        model = VATReport
        fields = [
            'report_name', 'report_period', 'start_date', 'end_date', 
            'currency', 'is_filed'
        ]
        widgets = {
            'report_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter report name'
            }),
            'report_period': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'currency': forms.Select(attrs={'class': 'form-control'}),
            'is_filed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date >= end_date:
            raise ValidationError("Start date must be before end date.")

        return cleaned_data


class TaxCalculationForm(forms.Form):
    """Form for tax calculation"""
    taxable_amount = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01',
            'min': '0'
        })
    )
    tax_rate = forms.ModelChoiceField(
        queryset=TaxRate.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select tax rate"
    )
    currency = forms.ChoiceField(
        choices=[('AED', 'AED'), ('USD', 'USD'), ('EUR', 'EUR')],
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='AED'
    )

    def calculate_tax(self):
        """Calculate tax amount based on taxable amount and tax rate"""
        if self.is_valid():
            taxable_amount = self.cleaned_data['taxable_amount']
            tax_rate = self.cleaned_data['tax_rate']
            
            # Calculate tax amount
            tax_amount = (taxable_amount * tax_rate.rate_percentage) / 100
            
            # Apply rounding based on tax rate setting
            if tax_rate.rounding_method == 'nearest_001':
                tax_amount = round(tax_amount, 2)
            elif tax_rate.rounding_method == 'nearest_005':
                tax_amount = round(tax_amount * 20) / 20
            elif tax_rate.rounding_method == 'nearest_010':
                tax_amount = round(tax_amount * 10) / 10
            elif tax_rate.rounding_method == 'round_up':
                tax_amount = (tax_amount * 100).__ceil__() / 100
            elif tax_rate.rounding_method == 'round_down':
                tax_amount = (tax_amount * 100).__floor__() / 100
            
            total_amount = taxable_amount + tax_amount
            
            return {
                'taxable_amount': taxable_amount,
                'tax_rate': tax_rate,
                'tax_amount': tax_amount,
                'total_amount': total_amount,
                'currency': self.cleaned_data['currency']
            }
        return None


class TaxSettingsSearchForm(forms.Form):
    """Form for searching tax settings"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search...'
        })
    )
    jurisdiction = forms.ModelChoiceField(
        queryset=TaxJurisdiction.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="All Jurisdictions"
    )
    tax_type = forms.ModelChoiceField(
        queryset=TaxType.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="All Tax Types"
    )
    is_active = forms.ChoiceField(
        choices=[('', 'All'), ('True', 'Active'), ('False', 'Inactive')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
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


class VATReportGenerationForm(forms.Form):
    """Form for generating VAT reports"""
    report_period = forms.ChoiceField(
        choices=VATReport.REPORT_PERIODS,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    currency = forms.ChoiceField(
        choices=[('AED', 'AED'), ('USD', 'USD'), ('EUR', 'EUR')],
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='AED'
    )
    include_zero_rated = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    include_exempt = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date >= end_date:
            raise ValidationError("Start date must be before end date.")

        return cleaned_data
