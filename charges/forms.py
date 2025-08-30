from django import forms
from django.utils import timezone
from django.db.models import Q
from .models import Charge
from customer.models import Customer
from items.models import Item

class ChargeSearchForm(forms.Form):
    """Form for searching and filtering charges"""
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
        required=False,
        empty_label="All Customers",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Customer"
    )
    item = forms.ModelChoiceField(
        queryset=Item.objects.all(),
        required=False,
        empty_label="All Items",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Item"
    )
    charge_type = forms.ChoiceField(
        choices=[('', 'All Types')] + Charge.CHARGE_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Charge Type"
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + Charge.STATUS_CHOICES,
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
    rate_min = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Min Rate',
            'step': '0.01'
        }),
        label="Min Rate"
    )
    rate_max = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Max Rate',
            'step': '0.01'
        }),
        label="Max Rate"
    )

class ChargeForm(forms.ModelForm):
    """Form for creating and editing charges"""
    class Meta:
        model = Charge
        fields = [
            'customer', 'item', 'charge_type', 'rate', 'effective_date', 
            'status', 'remarks'
        ]
        widgets = {
            'customer': forms.Select(attrs={
                'class': 'form-select',
                'required': 'required'
            }),
            'item': forms.Select(attrs={
                'class': 'form-select',
                'required': 'required'
            }),
            'charge_type': forms.Select(attrs={
                'class': 'form-select',
                'required': 'required'
            }),
            'rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'required': 'required'
            }),
            'effective_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': 'required'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
                'required': 'required'
            }),
            'remarks': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter any additional remarks...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default effective date to today
        if not self.instance.pk:  # Only for new charges
            self.initial['effective_date'] = timezone.now().date()
    
    def clean(self):
        cleaned_data = super().clean()
        customer = cleaned_data.get('customer')
        item = cleaned_data.get('item')
        charge_type = cleaned_data.get('charge_type')
        effective_date = cleaned_data.get('effective_date')
        
        # Check for duplicate charges
        if customer and item and charge_type and effective_date:
            existing_charge = Charge.objects.filter(
                customer=customer,
                item=item,
                charge_type=charge_type,
                effective_date=effective_date
            )
            
            if self.instance.pk:
                existing_charge = existing_charge.exclude(pk=self.instance.pk)
            
            if existing_charge.exists():
                raise forms.ValidationError(
                    f"A charge already exists for {customer.customer_name} - {item.item_name} "
                    f"with type {self.fields['charge_type'].choices[dict(self.fields['charge_type'].choices)[charge_type]]} "
                    f"on {effective_date}."
                )
        
        return cleaned_data

class BulkChargeForm(forms.Form):
    """Form for bulk charge operations"""
    action = forms.ChoiceField(
        choices=[
            ('activate', 'Activate Selected'),
            ('deactivate', 'Deactivate Selected'),
            ('delete', 'Delete Selected'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Action"
    )
    charge_ids = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    ) 