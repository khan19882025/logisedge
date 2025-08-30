from django import forms
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q
from .models import (
    Customer, CargoType, Incoterm, ChargeType, FreightQuotation,
    QuotationCharge, QuotationAttachment
)


class CustomerForm(forms.ModelForm):
    """Form for creating and editing customers"""
    class Meta:
        model = Customer
        fields = ['name', 'email', 'phone', 'address', 'country', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CargoTypeForm(forms.ModelForm):
    """Form for creating and editing cargo types"""
    class Meta:
        model = CargoType
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class IncotermForm(forms.ModelForm):
    """Form for creating and editing incoterms"""
    class Meta:
        model = Incoterm
        fields = ['code', 'name', 'description', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ChargeTypeForm(forms.ModelForm):
    """Form for creating and editing charge types"""
    class Meta:
        model = ChargeType
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class FreightQuotationForm(forms.ModelForm):
    """Form for creating and editing freight quotations"""
    class Meta:
        model = FreightQuotation
        fields = [
            'customer', 'mode_of_transport', 'origin', 'destination',
            'transit_time_estimate', 'cargo_type', 'cargo_details',
            'weight', 'volume', 'packages', 'incoterm', 'remarks',
            'internal_notes', 'validity_date', 'currency', 'vat_percentage'
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'mode_of_transport': forms.Select(attrs={'class': 'form-select'}),
            'origin': forms.TextInput(attrs={'class': 'form-control'}),
            'destination': forms.TextInput(attrs={'class': 'form-control'}),
            'transit_time_estimate': forms.TextInput(attrs={'class': 'form-control'}),
            'cargo_type': forms.Select(attrs={'class': 'form-select'}),
            'cargo_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'volume': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'packages': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'incoterm': forms.Select(attrs={'class': 'form-select'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'internal_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'validity_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'currency': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('AED', 'AED - UAE Dirham'),
                ('USD', 'USD - US Dollar'),
                ('EUR', 'EUR - Euro'),
                ('GBP', 'GBP - British Pound'),
            ]),
            'vat_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter only active records
        self.fields['customer'].queryset = Customer.objects.filter(is_active=True)
        self.fields['cargo_type'].queryset = CargoType.objects.filter(is_active=True)
        self.fields['incoterm'].queryset = Incoterm.objects.filter(is_active=True)
        
        # Set empty labels
        self.fields['incoterm'].empty_label = "Select Incoterm (Optional)"

    def clean(self):
        cleaned_data = super().clean()
        validity_date = cleaned_data.get('validity_date')
        
        if validity_date and validity_date < timezone.now().date():
            raise forms.ValidationError("Validity date cannot be in the past.")
        
        return cleaned_data


class QuotationChargeForm(forms.ModelForm):
    """Form for creating and editing quotation charges"""
    class Meta:
        model = QuotationCharge
        fields = ['charge_type', 'description', 'currency', 'rate', 'unit', 'quantity']
        widgets = {
            'charge_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'currency': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('AED', 'AED - UAE Dirham'),
                ('USD', 'USD - US Dollar'),
                ('EUR', 'EUR - Euro'),
                ('GBP', 'GBP - British Pound'),
            ]),
            'rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['charge_type'].queryset = ChargeType.objects.filter(is_active=True)


class QuotationAttachmentForm(forms.ModelForm):
    """Form for uploading quotation attachments"""
    class Meta:
        model = QuotationAttachment
        fields = ['file', 'description']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (max 10MB)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError("File size must be under 10MB.")
            
            # Check file extension
            allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']
            file_extension = file.name.lower()
            if not any(file_extension.endswith(ext) for ext in allowed_extensions):
                raise forms.ValidationError("Only PDF, JPG, PNG, and DOC files are allowed.")
        
        return file


class QuotationSearchForm(forms.Form):
    """Form for searching quotations"""
    quotation_number = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Quotation Number'
    }))
    customer = forms.ModelChoiceField(queryset=Customer.objects.filter(is_active=True), 
                                    required=False, empty_label="All Customers",
                                    widget=forms.Select(attrs={'class': 'form-select'}))
    status = forms.ChoiceField(choices=[('', 'All Statuses')] + FreightQuotation.STATUS_CHOICES,
                              required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    mode_of_transport = forms.ChoiceField(choices=[('', 'All Modes')] + FreightQuotation.MODE_CHOICES,
                                        required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={
        'class': 'form-control', 'type': 'date'
    }))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={
        'class': 'form-control', 'type': 'date'
    }))

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError("Start date cannot be after end date.")
        
        return cleaned_data


class QuotationStatusForm(forms.Form):
    """Form for changing quotation status"""
    status = forms.ChoiceField(choices=FreightQuotation.STATUS_CHOICES,
                              widget=forms.Select(attrs={'class': 'form-select'}))
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={
        'class': 'form-control', 'rows': 3, 'placeholder': 'Add notes about this status change...'
    })) 