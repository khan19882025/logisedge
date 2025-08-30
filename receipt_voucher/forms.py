from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import ReceiptVoucher, ReceiptVoucherAttachment
from customer.models import Customer
from salesman.models import Salesman
from chart_of_accounts.models import ChartOfAccount
from multi_currency.models import Currency


class ReceiptVoucherForm(forms.ModelForm):
    """Form for creating and editing receipt vouchers"""
    
    # Override fields for better styling and validation
    voucher_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'required': True
        }),
        initial=timezone.now().date()
    )
    
    amount = forms.DecimalField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0.01',
            'placeholder': '0.00'
        }),
        min_value=0.01
    )
    
    payer_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter payer name',
            'autocomplete': 'off'
        })
    )
    
    payer_code = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Payer code (optional)',
            'readonly': 'readonly'
        })
    )
    
    payer_contact = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contact number (optional)'
        })
    )
    
    payer_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email address (optional)'
        })
    )
    
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter description or remarks'
        })
    )
    
    reference_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Reference number (optional)'
        })
    )
    
    reference_invoices = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Enter invoice numbers separated by commas (optional)'
        }),
        help_text="Enter invoice numbers separated by commas"
    )
    
    class Meta:
        model = ReceiptVoucher
        fields = [
            'voucher_date', 'receipt_mode', 'payer_type', 'payer_name', 
            'payer_code', 'payer_contact', 'payer_email', 'amount', 
            'currency', 'account_to_credit', 'description', 
            'reference_number', 'reference_invoices'
        ]
        widgets = {
            'receipt_mode': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'payer_type': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'currency': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'account_to_credit': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set default currency to AED
        if not self.instance.pk:
            try:
                default_currency = Currency.objects.get(code='AED')
                self.fields['currency'].initial = default_currency
            except Currency.DoesNotExist:
                pass
        
        # Filter accounts to credit (only asset and income accounts)
        self.fields['account_to_credit'].queryset = ChartOfAccount.objects.filter(
            is_active=True,
            account_type__category__in=['ASSET', 'INCOME']
        ).order_by('account_code')
        
        # Filter currencies to active ones
        self.fields['currency'].queryset = Currency.objects.filter(is_active=True).order_by('code')
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise ValidationError('Amount must be greater than zero.')
        return amount
    
    def clean_payer_email(self):
        email = self.cleaned_data.get('payer_email')
        if email and '@' not in email:
            raise ValidationError('Please enter a valid email address.')
        return email


class ReceiptVoucherAttachmentForm(forms.ModelForm):
    """Form for uploading receipt voucher attachments"""
    
    class Meta:
        model = ReceiptVoucherAttachment
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png,.gif,.doc,.docx,.xls,.xlsx'
            })
        }
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (max 10MB)
            if file.size > 10 * 1024 * 1024:
                raise ValidationError('File size must be less than 10MB.')
            
            # Check file type
            allowed_types = [
                'application/pdf',
                'image/jpeg',
                'image/jpg',
                'image/png',
                'image/gif',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/vnd.ms-excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            ]
            
            if hasattr(file, 'content_type') and file.content_type not in allowed_types:
                raise ValidationError('Please upload a valid file type (PDF, Image, Word, Excel).')
        
        return file


class ReceiptVoucherSearchForm(forms.Form):
    """Form for searching and filtering receipt vouchers"""
    
    SEARCH_FIELDS = [
        ('voucher_number', 'Voucher Number'),
        ('payer_name', 'Payer Name'),
        ('description', 'Description'),
        ('reference_number', 'Reference Number'),
    ]
    
    search_field = forms.ChoiceField(
        choices=SEARCH_FIELDS,
        initial='voucher_number',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    search_query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter search term...'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + ReceiptVoucher.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    receipt_mode = forms.ChoiceField(
        choices=[('', 'All Modes')] + ReceiptVoucher.RECEIPT_MODES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    payer_type = forms.ChoiceField(
        choices=[('', 'All Types')] + ReceiptVoucher.PAYER_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    currency = forms.ModelChoiceField(
        queryset=Currency.objects.filter(is_active=True),
        required=False,
        empty_label="All Currencies",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    amount_min = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': 'Min amount'
        })
    )
    
    amount_max = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': 'Max amount'
        })
    )


class ReceiptVoucherApprovalForm(forms.Form):
    """Form for approving receipt vouchers"""
    
    approval_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter approval notes (optional)'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.voucher = kwargs.pop('voucher', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        
        if self.voucher and self.voucher.status != 'draft':
            raise ValidationError('Only draft vouchers can be approved.')
        
        return cleaned_data


class ReceiptVoucherMarkReceivedForm(forms.Form):
    """Form for marking receipt vouchers as received"""
    
    received_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter receipt notes (optional)'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.voucher = kwargs.pop('voucher', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        
        if self.voucher and self.voucher.status != 'approved':
            raise ValidationError('Only approved vouchers can be marked as received.')
        
        return cleaned_data 