from django import forms
from django.forms import ModelForm, Form
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from .models import CashTransaction
from chart_of_accounts.models import ChartOfAccount
from multi_currency.models import Currency

class CashTransactionForm(ModelForm):
    """Form for creating and editing cash transactions"""
    
    class Meta:
        model = CashTransaction
        fields = ['transaction_date', 'transaction_type', 'category', 'from_account', 'to_account', 
                 'amount', 'currency', 'location', 'reference_number', 'narration', 'attachment']
        widgets = {
            'transaction_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                    'value': timezone.now().date()
                }
            ),
            'transaction_type': forms.Select(
                attrs={
                    'class': 'form-select',
                    'data-placeholder': 'Select Transaction Type'
                }
            ),
            'category': forms.Select(
                attrs={
                    'class': 'form-select',
                    'data-placeholder': 'Select Category'
                }
            ),
            'from_account': forms.Select(
                attrs={
                    'class': 'form-select',
                    'data-placeholder': 'Select From Account'
                }
            ),
            'to_account': forms.Select(
                attrs={
                    'class': 'form-select',
                    'data-placeholder': 'Select To Account'
                }
            ),
            'amount': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'step': '0.01',
                    'min': '0.01',
                    'placeholder': 'Enter amount'
                }
            ),
            'currency': forms.Select(
                attrs={
                    'class': 'form-select',
                    'data-placeholder': 'Select Currency'
                }
            ),
            'location': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter location or branch'
                }
            ),
            'reference_number': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter reference number'
                }
            ),
            'narration': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Enter transaction details'
                }
            ),
            'attachment': forms.FileInput(
                attrs={
                    'class': 'form-control',
                    'accept': '.pdf,.jpg,.jpeg,.png,.doc,.docx'
                }
            ),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set default currency to AED
        if not self.instance.pk:
            self.fields['currency'].initial = 3  # AED
        
        # Filter accounts based on transaction type
        self.fields['from_account'].queryset = ChartOfAccount.objects.filter(is_active=True).order_by('account_code')
        self.fields['to_account'].queryset = ChartOfAccount.objects.filter(is_active=True).order_by('account_code')
    
    def clean(self):
        cleaned_data = super().clean()
        transaction_type = cleaned_data.get('transaction_type')
        from_account = cleaned_data.get('from_account')
        to_account = cleaned_data.get('to_account')
        amount = cleaned_data.get('amount')
        
        # Validate amount
        if amount and amount <= 0:
            raise ValidationError("Amount must be greater than zero.")
        
        # Validate that at least one account is selected
        if not from_account and not to_account:
            raise ValidationError("Either From Account or To Account must be selected.")
        
        # Validate that from and to accounts are different if both are selected
        if from_account and to_account and from_account == to_account:
            raise ValidationError("From and To accounts must be different.")
        
        # Validate transaction type specific rules
        if transaction_type == 'cash_in':
            if not to_account:
                raise ValidationError("To Account is required for Cash In transactions.")
        elif transaction_type == 'cash_out':
            if not from_account:
                raise ValidationError("From Account is required for Cash Out transactions.")
        
        return cleaned_data


class CashTransactionFilterForm(Form):
    """Form for filtering cash transactions in list view"""
    
    STATUS_CHOICES = [('', 'All Statuses'), ('draft', 'Draft'), ('posted', 'Posted'), ('cancelled', 'Cancelled')]
    TRANSACTION_TYPE_CHOICES = [('', 'All Types'), ('cash_in', 'Cash In'), ('cash_out', 'Cash Out')]
    CATEGORY_CHOICES = [('', 'All Categories'), ('petty_expense', 'Petty Expense'), ('cash_sale', 'Cash Sale'), 
                       ('staff_advance', 'Staff Advance'), ('reimbursement', 'Reimbursement'), 
                       ('cash_purchase', 'Cash Purchase'), ('cash_receipt', 'Cash Receipt'), 
                       ('cash_payment', 'Cash Payment'), ('other', 'Other')]
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control',
                'placeholder': 'From Date'
            }
        )
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control',
                'placeholder': 'To Date'
            }
        )
    )
    status = forms.ChoiceField(
        required=False,
        choices=STATUS_CHOICES,
        widget=forms.Select(
            attrs={
                'class': 'form-select'
            }
        )
    )
    transaction_type = forms.ChoiceField(
        required=False,
        choices=TRANSACTION_TYPE_CHOICES,
        widget=forms.Select(
            attrs={
                'class': 'form-select'
            }
        )
    )
    category = forms.ChoiceField(
        required=False,
        choices=CATEGORY_CHOICES,
        widget=forms.Select(
            attrs={
                'class': 'form-select'
            }
        )
    )
    from_account = forms.ModelChoiceField(
        required=False,
        queryset=ChartOfAccount.objects.filter(is_active=True).order_by('account_code'),
        widget=forms.Select(
            attrs={
                'class': 'form-select',
                'data-placeholder': 'All From Accounts'
            }
        )
    )
    to_account = forms.ModelChoiceField(
        required=False,
        queryset=ChartOfAccount.objects.filter(is_active=True).order_by('account_code'),
        widget=forms.Select(
            attrs={
                'class': 'form-select',
                'data-placeholder': 'All To Accounts'
            }
        )
    )
    currency = forms.ModelChoiceField(
        required=False,
        queryset=Currency.objects.filter(is_active=True).order_by('name'),
        widget=forms.Select(
            attrs={
                'class': 'form-select',
                'data-placeholder': 'All Currencies'
            }
        )
    )
    location = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Search by location'
            }
        )
    )
    search = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Search by transaction number or reference'
            }
        )
    )


class QuickCashTransactionForm(Form):
    """Quick cash transaction form for simple transactions"""
    
    transaction_type = forms.ChoiceField(
        choices=[('cash_in', 'Cash In'), ('cash_out', 'Cash Out')],
        widget=forms.Select(
            attrs={
                'class': 'form-select',
                'data-placeholder': 'Select Transaction Type'
            }
        )
    )
    category = forms.ChoiceField(
        choices=[('petty_expense', 'Petty Expense'), ('cash_sale', 'Cash Sale'), 
                ('staff_advance', 'Staff Advance'), ('reimbursement', 'Reimbursement'), 
                ('cash_purchase', 'Cash Purchase'), ('cash_receipt', 'Cash Receipt'), 
                ('cash_payment', 'Cash Payment'), ('other', 'Other')],
        widget=forms.Select(
            attrs={
                'class': 'form-select',
                'data-placeholder': 'Select Category'
            }
        )
    )
    account = forms.ModelChoiceField(
        queryset=ChartOfAccount.objects.filter(is_active=True).order_by('account_code'),
        widget=forms.Select(
            attrs={
                'class': 'form-select',
                'data-placeholder': 'Select Account'
            }
        )
    )
    amount = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(
            attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': 'Enter amount'
            }
        )
    )
    location = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Location (optional)'
            }
        )
    )
    narration = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Brief description (optional)'
            }
        )
    )
    
    def clean(self):
        cleaned_data = super().clean()
        transaction_type = cleaned_data.get('transaction_type')
        account = cleaned_data.get('account')
        amount = cleaned_data.get('amount')
        
        if amount and amount <= 0:
            raise ValidationError("Amount must be greater than zero.")
        
        if not account:
            raise ValidationError("Account is required.")
        
        return cleaned_data 