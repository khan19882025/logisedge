from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Customer, CustomerType
from django.core.exceptions import ValidationError
import re

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = '__all__'
        exclude = ['customer_code', 'created_by', 'updated_by', 'created_at', 'updated_at']
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter customer name'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter contact person'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter mobile number'}),
            'fax': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter fax number'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Enter website URL'}),
            'customer_types': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            'industry': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter industry'}),
            'tax_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter tax number'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter registration number'}),
            
            # Addresses
            'billing_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter billing address'}),
            'billing_city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter billing city'}),
            'billing_state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter billing state'}),
            'billing_country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter billing country'}),
            'billing_postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter billing postal code'}),
            
            'shipping_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter shipping address'}),
            'shipping_city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter shipping city'}),
            'shipping_state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter shipping state'}),
            'shipping_country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter shipping country'}),
            'shipping_postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter shipping postal code'}),
            
            # Financial
            'credit_limit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Enter credit limit'}),
            'payment_terms': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter payment terms'}),
            'currency': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter currency code'}),
            'tax_exempt': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Enter tax rate'}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Enter discount percentage'}),
            
            # Customer Portal
            'portal_username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter portal username'}),
            'portal_password': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter portal password'}),
            'portal_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            
            # System fields
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter notes'}),
            'salesman': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make customer_types required
        self.fields['customer_types'].required = True
        self.fields['customer_types'].queryset = CustomerType.objects.filter(is_active=True)
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Remove all non-digit characters
            phone_clean = re.sub(r'\D', '', phone)
            if len(phone_clean) < 7:
                raise ValidationError("Phone number must be at least 7 digits.")
        return phone
    
    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile')
        if mobile:
            # Remove all non-digit characters
            mobile_clean = re.sub(r'\D', '', mobile)
            if len(mobile_clean) < 10:
                raise ValidationError("Mobile number must be at least 10 digits.")
        return mobile
    
    def clean_portal_username(self):
        portal_username = self.cleaned_data.get('portal_username')
        if portal_username and portal_username.strip():  # Only validate if username is provided and not empty
            portal_username = portal_username.strip()
            # Check if portal username already exists (excluding current instance if editing)
            instance = getattr(self, 'instance', None)
            if Customer.objects.filter(portal_username=portal_username).exclude(pk=instance.pk if instance else None).exists():
                raise ValidationError("Portal username already exists.")
            
            # Validate username format
            if not re.match(r'^[a-zA-Z0-9_]+$', portal_username):
                raise ValidationError("Portal username can only contain letters, numbers, and underscores.")
            
            return portal_username
        
        return None  # Return None if empty (will be stored as NULL in database)

class CustomerSearchForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by customer code, name, or contact person...'
        })
    )
    customer_type = forms.ModelChoiceField(
        queryset=CustomerType.objects.filter(is_active=True),
        required=False,
        empty_label="All Types",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    is_active = forms.ChoiceField(
        choices=[('', 'All'), ('True', 'Active'), ('False', 'Inactive')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    ) 