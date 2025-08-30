from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Vendor, Bill
from multi_currency.models import Currency, CurrencySettings


class VendorForm(forms.ModelForm):
    """Form for creating and editing vendors"""
    
    class Meta:
        model = Vendor
        fields = ['name', 'email', 'phone', 'address', 'tax_id', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter vendor name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter address'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter tax ID'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Check if email already exists for other vendors
            existing_vendor = Vendor.objects.filter(email=email)
            if self.instance.pk:
                existing_vendor = existing_vendor.exclude(pk=self.instance.pk)
            if existing_vendor.exists():
                raise ValidationError('A vendor with this email already exists.')
        return email


class BillForm(forms.ModelForm):
    """Form for creating and editing bills"""
    
    class Meta:
        model = Bill
        fields = ['vendor', 'bill_no', 'bill_date', 'due_date', 'amount', 'currency', 'notes', 'attachment']
        widgets = {
            'vendor': forms.Select(attrs={'class': 'form-control'}),
            'bill_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter bill number'}),
            'bill_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01', 'placeholder': '0.00'}),
            'currency': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter notes (optional)'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Only show active vendors
        self.fields['vendor'].queryset = Vendor.objects.filter(is_active=True).order_by('name')
        
        # Only show active currencies
        self.fields['currency'].queryset = Currency.objects.filter(is_active=True).order_by('code')
        
        # Set default currency if available
        if not self.instance.pk:  # Only for new bills
            currency_settings = CurrencySettings.objects.first()
            if currency_settings and currency_settings.default_currency:
                self.fields['currency'].initial = currency_settings.default_currency
        
        # Set default dates
        if not self.instance.pk:
            today = timezone.now().date()
            self.fields['bill_date'].initial = today
            self.fields['due_date'].initial = today

    def clean_bill_no(self):
        bill_no = self.cleaned_data.get('bill_no')
        if bill_no:
            # Check if bill number already exists
            existing_bill = Bill.objects.filter(bill_no=bill_no)
            if self.instance.pk:
                existing_bill = existing_bill.exclude(pk=self.instance.pk)
            if existing_bill.exists():
                raise ValidationError('A bill with this number already exists.')
        return bill_no

    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        bill_date = self.cleaned_data.get('bill_date')
        
        if due_date and bill_date:
            if due_date < bill_date:
                raise ValidationError('Due date cannot be earlier than bill date.')
        
        return due_date

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise ValidationError('Amount must be greater than zero.')
        return amount


class BillFilterForm(forms.Form):
    """Form for filtering bills"""
    
    STATUS_CHOICES = [('', 'All Statuses')] + Bill.STATUS_CHOICES
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    vendor = forms.ModelChoiceField(
        queryset=Vendor.objects.filter(is_active=True).order_by('name'),
        required=False,
        empty_label='All Vendors',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by bill number or vendor name...'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    confirmed = forms.ChoiceField(
        choices=[('', 'All'), ('true', 'Confirmed'), ('false', 'Not Confirmed')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_to < date_from:
            raise ValidationError('End date cannot be earlier than start date.')
        
        return cleaned_data