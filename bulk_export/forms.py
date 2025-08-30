from django import forms
from django.contrib.auth.models import User
from customer.models import Customer
from items.models import Item
from datetime import datetime, timedelta


class CustomerExportForm(forms.Form):
    """Form for filtering customer export data"""
    
    customer_code = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter customer code'
        })
    )
    
    customer_name = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter customer name'
        })
    )
    
    region = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter region'
        })
    )
    
    account_status = forms.ChoiceField(
        choices=[
            ('', 'All Statuses'),
            ('active', 'Active'),
            ('inactive', 'Inactive'),
            ('suspended', 'Suspended'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    registration_date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    registration_date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    export_format = forms.ChoiceField(
        choices=[
            ('excel', 'Excel (.xlsx)'),
            ('csv', 'CSV (.csv)'),
        ],
        initial='excel',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('registration_date_from')
        date_to = cleaned_data.get('registration_date_to')
        
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError("Start date cannot be after end date.")
        
        return cleaned_data


class ItemExportForm(forms.Form):
    """Form for filtering item export data"""
    
    item_code = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter item code'
        })
    )
    
    item_name = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter item name'
        })
    )
    
    category = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter category'
        })
    )
    
    brand = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter brand'
        })
    )
    
    supplier = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter supplier name'
        })
    )
    
    status = forms.ChoiceField(
        choices=[
            ('', 'All Items'),
            ('active', 'Active'),
            ('inactive', 'Inactive'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    export_format = forms.ChoiceField(
        choices=[
            ('excel', 'Excel (.xlsx)'),
            ('csv', 'CSV (.csv)'),
        ],
        initial='excel',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )


class TransactionExportForm(forms.Form):
    """Form for filtering transaction export data"""
    
    TRANSACTION_TYPES = [
        ('', 'All Types'),
        ('sale', 'Sale'),
        ('purchase', 'Purchase'),
        ('return', 'Return'),
        ('refund', 'Refund'),
        ('adjustment', 'Adjustment'),
        ('transfer', 'Transfer'),
    ]
    
    PAYMENT_STATUSES = [
        ('', 'All Statuses'),
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('partial', 'Partial'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    transaction_type = forms.ChoiceField(
        choices=TRANSACTION_TYPES,
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
    
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
        required=False,
        empty_label="All Customers",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    item = forms.ModelChoiceField(
        queryset=Item.objects.all(),
        required=False,
        empty_label="All Items",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    payment_status = forms.ChoiceField(
        choices=PAYMENT_STATUSES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    location = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter location/branch'
        })
    )
    
    export_format = forms.ChoiceField(
        choices=[
            ('excel', 'Excel (.xlsx)'),
            ('csv', 'CSV (.csv)'),
        ],
        initial='excel',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError("Start date cannot be after end date.")
        
        return cleaned_data
