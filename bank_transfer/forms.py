from django import forms
from django.forms import ModelForm, Form
from .models import BankTransfer, BankTransferTemplate
from chart_of_accounts.models import ChartOfAccount
from multi_currency.models import Currency
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal

class BankTransferForm(ModelForm):
    """Form for creating and editing bank transfers"""
    
    class Meta:
        model = BankTransfer
        fields = ['transfer_date', 'transfer_type', 'from_account', 'to_account', 'amount', 
                 'currency', 'exchange_rate', 'reference_number', 'narration']
        widgets = {
            'transfer_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                    'value': timezone.now().date().isoformat()
                }
            ),
            'transfer_type': forms.Select(
                attrs={
                    'class': 'form-select',
                    'data-placeholder': 'Select Transfer Type'
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
                    'placeholder': 'Enter transfer amount'
                }
            ),
            'currency': forms.Select(
                attrs={
                    'class': 'form-select',
                    'data-placeholder': 'Select Currency'
                }
            ),
            'exchange_rate': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'step': '0.000001',
                    'min': '0.000001',
                    'placeholder': '1.000000'
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
                    'placeholder': 'Enter narration or notes'
                }
            ),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter bank accounts only
        bank_accounts = ChartOfAccount.objects.filter(
            account_type__category='ASSET',
            is_active=True
        ).order_by('account_code')
        
        self.fields['from_account'].queryset = bank_accounts
        self.fields['to_account'].queryset = bank_accounts
        
        # Set default currency to AED
        if not self.instance.pk:
            self.fields['currency'].initial = 3  # AED
            self.fields['exchange_rate'].initial = 1.000000
    
    def clean(self):
        cleaned_data = super().clean()
        from_account = cleaned_data.get('from_account')
        to_account = cleaned_data.get('to_account')
        amount = cleaned_data.get('amount')
        currency = cleaned_data.get('currency')
        exchange_rate = cleaned_data.get('exchange_rate')
        reference_number = cleaned_data.get('reference_number')
        
        # Validate that from and to accounts are different
        if from_account and to_account and from_account == to_account:
            raise ValidationError("From and To accounts must be different.")
        
        # Validate amount
        if amount and amount <= 0:
            raise ValidationError("Transfer amount must be greater than zero.")
        
        # Validate exchange rate for multi-currency transfers
        if currency and exchange_rate:
            if exchange_rate <= 0:
                raise ValidationError("Exchange rate must be greater than zero.")
        
        # Validate reference number uniqueness
        if reference_number:
            existing_transfer = BankTransfer.objects.filter(
                reference_number=reference_number
            ).exclude(pk=self.instance.pk if self.instance.pk else None)
            
            if existing_transfer.exists():
                raise ValidationError("A transfer with this reference number already exists.")
        
        return cleaned_data


class BankTransferFilterForm(Form):
    """Form for filtering bank transfers in list view"""
    
    STATUS_CHOICES = [('', 'All Statuses')] + BankTransfer.STATUS_CHOICES
    TRANSFER_TYPE_CHOICES = [('', 'All Types')] + BankTransfer.TRANSFER_TYPES
    
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
                'class': 'form-control'
            }
        )
    )
    transfer_type = forms.ChoiceField(
        required=False,
        choices=TRANSFER_TYPE_CHOICES,
        widget=forms.Select(
            attrs={
                'class': 'form-control'
            }
        )
    )
    from_account = forms.ModelChoiceField(
        required=False,
        queryset=ChartOfAccount.objects.filter(
            account_type__category='ASSET',
            is_active=True
        ).order_by('account_code'),
        widget=forms.Select(
            attrs={
                'class': 'form-select',
                'data-placeholder': 'All From Accounts'
            }
        )
    )
    to_account = forms.ModelChoiceField(
        required=False,
        queryset=ChartOfAccount.objects.filter(
            account_type__category='ASSET',
            is_active=True
        ).order_by('account_code'),
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
    search = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Search by transfer number or reference'
            }
        )
    )


class BankTransferTemplateForm(ModelForm):
    """Form for creating and editing bank transfer templates"""
    
    class Meta:
        model = BankTransferTemplate
        fields = ['name', 'description', 'from_account', 'to_account', 'default_amount', 
                 'default_currency', 'default_narration']
        widgets = {
            'name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter template name'
                }
            ),
            'description': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 2,
                    'placeholder': 'Enter template description'
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
            'default_amount': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'step': '0.01',
                    'min': '0.00',
                    'placeholder': 'Default amount'
                }
            ),
            'default_currency': forms.Select(
                attrs={
                    'class': 'form-select',
                    'data-placeholder': 'Select Currency'
                }
            ),
            'default_narration': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Default narration'
                }
            ),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter bank accounts only
        bank_accounts = ChartOfAccount.objects.filter(
            account_type__category='ASSET',
            is_active=True
        ).order_by('account_code')
        
        self.fields['from_account'].queryset = bank_accounts
        self.fields['to_account'].queryset = bank_accounts
        
        # Set default currency to AED
        if not self.instance.pk:
            self.fields['default_currency'].initial = 3  # AED
    
    def clean(self):
        cleaned_data = super().clean()
        from_account = cleaned_data.get('from_account')
        to_account = cleaned_data.get('to_account')
        
        # Validate that from and to accounts are different
        if from_account and to_account and from_account == to_account:
            raise ValidationError("From and To accounts must be different.")
        
        return cleaned_data


class QuickTransferForm(Form):
    """Quick transfer form for simple transfers"""
    
    from_account = forms.ModelChoiceField(
        queryset=ChartOfAccount.objects.filter(
            account_type__category='ASSET',
            is_active=True
        ).order_by('account_code'),
        widget=forms.Select(
            attrs={
                'class': 'form-select',
                'data-placeholder': 'Select From Account'
            }
        )
    )
    to_account = forms.ModelChoiceField(
        queryset=ChartOfAccount.objects.filter(
            account_type__category='ASSET',
            is_active=True
        ).order_by('account_code'),
        widget=forms.Select(
            attrs={
                'class': 'form-select',
                'data-placeholder': 'Select To Account'
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
        from_account = cleaned_data.get('from_account')
        to_account = cleaned_data.get('to_account')
        
        if from_account and to_account and from_account == to_account:
            raise ValidationError("From and To accounts must be different.")
        
        return cleaned_data 