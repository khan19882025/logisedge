from django import forms
from django.utils import timezone
from django.db.models import Q
from .models import StorageInvoice, StorageInvoiceItem
from customer.models import Customer
from facility.models import FacilityLocation
from items.models import Item

class StorageInvoiceSearchForm(forms.Form):
    """Form for searching and filtering storage invoices"""
    invoice_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Invoice Number'
        }),
        label="Invoice Number"
    )
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
        required=False,
        empty_label="All Customers",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Customer"
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + StorageInvoice.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Status"
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'From Date'
        }),
        label="From Date"
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'To Date'
        }),
        label="To Date"
    )
    amount_min = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Min Amount',
            'step': '0.01'
        }),
        label="Min Amount"
    )
    amount_max = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Max Amount',
            'step': '0.01'
        }),
        label="Max Amount"
    )

class GenerateInvoiceForm(forms.Form):
    """Form for generating storage invoices"""
    CUSTOMER_CHOICES = [
        ('all', 'All Customers'),
        ('specific', 'Specific Customer'),
    ]
    
    customer = forms.ChoiceField(
        choices=CUSTOMER_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'customer-selection'
        }),
        label="Customer Selection"
    )
    specific_customer = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
        required=False,
        empty_label="Select a customer",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Specific Customer"
    )
    storage_period_from = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'required': 'required'
        }),
        label="Storage Period From"
    )
    storage_period_to = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'required': 'required'
        }),
        label="Storage Period To"
    )
    invoice_date = forms.DateField(
        initial=timezone.now().date,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'required': 'required'
        }),
        label="Invoice Date"
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Optional notes for the generated invoices'
        }),
        label="Notes"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial values
        self.initial['storage_period_from'] = timezone.now().replace(day=1).date()
        self.initial['storage_period_to'] = timezone.now().date()
    
    def clean(self):
        cleaned_data = super().clean()
        customer = cleaned_data.get('customer')
        specific_customer = cleaned_data.get('specific_customer')
        storage_period_from = cleaned_data.get('storage_period_from')
        storage_period_to = cleaned_data.get('storage_period_to')
        
        # Validate customer selection
        if customer == 'specific' and not specific_customer:
            raise forms.ValidationError("Please select a specific customer when 'Specific Customer' is chosen.")
        
        # Validate date range
        if storage_period_from and storage_period_to:
            if storage_period_from > storage_period_to:
                raise forms.ValidationError("Storage period 'from' date must be before 'to' date.")
            
            if storage_period_to > timezone.now().date():
                raise forms.ValidationError("Storage period 'to' date cannot be in the future.")
        
        return cleaned_data

class StorageInvoiceForm(forms.ModelForm):
    """Form for creating/editing storage invoices"""
    class Meta:
        model = StorageInvoice
        fields = [
            'invoice_number', 'customer', 'invoice_date', 'storage_period_from',
            'storage_period_to', 'notes', 'terms_conditions'
        ]
        widgets = {
            'invoice_number': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly'
            }),
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'invoice_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'storage_period_from': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'storage_period_to': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'terms_conditions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default due date to 30 days from invoice date
        if not self.instance.pk:  # Only for new invoices
            self.initial['invoice_date'] = timezone.now().date()
            self.initial['due_date'] = (timezone.now() + timezone.timedelta(days=30)).date()

class StorageInvoiceItemForm(forms.ModelForm):
    """Form for storage invoice line items"""
    class Meta:
        model = StorageInvoiceItem
        fields = [
            'item', 'pallet_id', 'location', 'quantity', 'weight', 'volume',
            'storage_days', 'charge_type', 'rate', 'description'
        ]
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select'}),
            'pallet_id': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'volume': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'storage_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'charge_type': forms.Select(attrs={'class': 'form-select'}),
            'rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }

class MonthSelectionForm(forms.Form):
    """Form for selecting month for invoice listing"""
    month = forms.DateField(
        initial=timezone.now().replace(day=1).date,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'month'
        }),
        label="Select Month"
    )

class BulkInvoiceForm(forms.Form):
    """Form for bulk invoice operations"""
    action = forms.ChoiceField(
        choices=[
            ('finalize', 'Finalize Selected'),
            ('cancel', 'Cancel Selected'),
            ('delete', 'Delete Selected'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Action"
    )
    invoice_ids = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    ) 