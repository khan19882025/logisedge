from django import forms
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date
from .models import PaymentVoucher, PaymentVoucherAttachment
from customer.models import Customer, CustomerType
from chart_of_accounts.models import ChartOfAccount
from multi_currency.models import Currency
from salesman.models import Salesman


class PaymentVoucherForm(forms.ModelForm):
    """Form for creating and editing payment vouchers"""
    
    # Custom fields for better UX
    payee_search = forms.CharField(
        max_length=200, 
        required=False, 
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search payee...',
            'autocomplete': 'off'
        }),
        help_text="Search for payee by name or code"
    )
    
    manual_voucher_number = forms.CharField(
        max_length=20, 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Leave blank for auto-generation'
        }),
        help_text="Manual voucher number (optional)"
    )
    
    class Meta:
        model = PaymentVoucher
        fields = [
            'voucher_date', 'payment_mode', 'payee_type', 'payee_name', 
            'payee_id', 'amount', 'currency', 'account_to_debit', 
            'description', 'reference_invoices', 'reference_number'
        ]
        widgets = {
            'voucher_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'payment_mode': forms.Select(attrs={
                'class': 'form-control select2',
                'required': True
            }),
            'payee_type': forms.Select(attrs={
                'class': 'form-control select2',
                'required': True
            }),
            'payee_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter payee name',
                'required': True
            }),
            'payee_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Payee ID/Code (optional)'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00',
                'required': True
            }),
            'currency': forms.Select(attrs={
                'class': 'form-control select2',
                'required': True
            }),
            'account_to_debit': forms.Select(attrs={
                'class': 'form-control select2',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter description or remarks...'
            }),
            'reference_invoices': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Reference to related invoices...'
            }),
            'reference_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'External reference number'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set current date as default
        if not self.instance.pk:  # Only for new vouchers
            self.fields['voucher_date'].initial = date.today()
        
        # Filter active currencies
        self.fields['currency'].queryset = Currency.objects.filter(is_active=True)
        
        # Filter active accounts that can be debited (assets and expenses)
        self.fields['account_to_debit'].queryset = ChartOfAccount.objects.filter(
            is_active=True,
            account_type__category__in=['ASSET', 'EXPENSE']
        ).order_by('account_code')
        
        # Add validation
        self.fields['amount'].validators.append(MinValueValidator(Decimal('0.01')))
        
        # Set manual voucher number if instance exists
        if self.instance.pk and self.instance.voucher_number:
            self.fields['manual_voucher_number'].initial = self.instance.voucher_number
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise ValidationError("Amount must be greater than zero.")
        return amount
    
    def clean_voucher_date(self):
        voucher_date = self.cleaned_data.get('voucher_date')
        if voucher_date and voucher_date > date.today():
            raise ValidationError("Voucher date cannot be in the future.")
        return voucher_date
    
    def clean_manual_voucher_number(self):
        manual_number = self.cleaned_data.get('manual_voucher_number')
        if manual_number:
            # Check if voucher number already exists
            if PaymentVoucher.objects.filter(voucher_number=manual_number).exclude(pk=self.instance.pk if self.instance.pk else None).exists():
                raise ValidationError("This voucher number already exists.")
        return manual_number
    
    def clean(self):
        cleaned_data = super().clean()
        payee_type = cleaned_data.get('payee_type')
        payee_name = cleaned_data.get('payee_name')
        
        # Validate payee based on type
        if payee_type == 'vendor':
            # Check if vendor exists in customer database
            if payee_name:
                vendor_exists = Customer.objects.filter(
                    customer_name__iexact=payee_name,
                    customer_types__name__icontains='vendor'
                ).exists()
                if not vendor_exists:
                    self.add_warning('payee_name', 'Vendor not found in customer database. Please verify the name.')
        
        elif payee_type == 'employee':
            # Check if employee exists in salesman database
            if payee_name:
                employee_exists = Salesman.objects.filter(
                    first_name__icontains=payee_name.split()[0] if payee_name.split() else '',
                    last_name__icontains=payee_name.split()[-1] if len(payee_name.split()) > 1 else ''
                ).exists()
                if not employee_exists:
                    self.add_warning('payee_name', 'Employee not found in salesman database. Please verify the name.')
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set manual voucher number if provided
        manual_number = self.cleaned_data.get('manual_voucher_number')
        if manual_number:
            instance.voucher_number = manual_number
        
        if commit:
            instance.save()
        return instance


class PaymentVoucherAttachmentForm(forms.ModelForm):
    """Form for uploading payment voucher attachments"""
    
    class Meta:
        model = PaymentVoucherAttachment
        fields = ['file', 'file_type', 'description']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png,.gif,.bmp,.webp,.doc,.docx,.xls,.xlsx',
                'required': True
            }),
            'file_type': forms.Select(attrs={
                'class': 'form-control select2',
                'required': True
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief description of the attachment...'
            }),
        }
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (max 10MB)
            if file.size > 10 * 1024 * 1024:
                raise ValidationError("File size must be less than 10MB.")
            
            # Check file extension
            allowed_extensions = [
                '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
                '.doc', '.docx', '.xls', '.xlsx'
            ]
            file_extension = file.name.lower()
            if not any(file_extension.endswith(ext) for ext in allowed_extensions):
                raise ValidationError(
                    "File type not allowed. Please upload PDF, image, or document files."
                )
        
        return file


class PaymentVoucherSearchForm(forms.Form):
    """Form for searching payment vouchers"""
    
    SEARCH_FIELDS = [
        ('voucher_number', 'Voucher Number'),
        ('payee_name', 'Payee Name'),
        ('description', 'Description'),
        ('reference_number', 'Reference Number'),
    ]
    
    STATUS_CHOICES = [('', 'All Statuses')] + PaymentVoucher.STATUS_CHOICES
    PAYMENT_MODE_CHOICES = [('', 'All Payment Modes')] + PaymentVoucher.PAYMENT_MODES
    PAYEE_TYPE_CHOICES = [('', 'All Payee Types')] + PaymentVoucher.PAYEE_TYPES
    
    # Search fields
    search_field = forms.ChoiceField(
        choices=SEARCH_FIELDS,
        initial='voucher_number',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    search_query = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter search term...'
        })
    )
    
    # Filter fields
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    payment_mode = forms.ChoiceField(
        choices=PAYMENT_MODE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    payee_type = forms.ChoiceField(
        choices=PAYEE_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    currency = forms.ModelChoiceField(
        queryset=Currency.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Date range
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
    
    # Amount range
    amount_min = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Min amount'
        })
    )
    amount_max = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Max amount'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        amount_min = cleaned_data.get('amount_min')
        amount_max = cleaned_data.get('amount_max')
        
        # Validate date range
        if date_from and date_to and date_from > date_to:
            raise ValidationError("Start date cannot be after end date.")
        
        # Validate amount range
        if amount_min and amount_max and amount_min > amount_max:
            raise ValidationError("Minimum amount cannot be greater than maximum amount.")
        
        return cleaned_data


class PaymentVoucherApprovalForm(forms.Form):
    """Form for approving payment vouchers"""
    
    approval_notes = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Approval notes (optional)...'
        })
    )
    
    def __init__(self, voucher=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.voucher = voucher
    
    def clean(self):
        cleaned_data = super().clean()
        
        if self.voucher and not self.voucher.can_approve:
            raise ValidationError("This voucher cannot be approved.")
        
        return cleaned_data 