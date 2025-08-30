from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import BankAccount, BankAccountTransaction
from chart_of_accounts.models import ChartOfAccount
from multi_currency.models import Currency
from company.company_model import Company
from django.utils import timezone


class BankAccountForm(forms.ModelForm):
    """Form for creating and editing bank accounts"""
    
    class Meta:
        model = BankAccount
        fields = [
            'bank_name', 'account_number', 'account_type', 'branch_name', 
            'ifsc_code', 'currency', 'opening_balance', 'chart_account',
            'status', 'is_default_for_payments', 'is_default_for_receipts', 'notes'
        ]
        widgets = {
            'bank_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter bank name',
                'required': True
            }),
            'account_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter account number',
                'required': True
            }),
            'account_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'branch_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter branch name'
            }),
            'ifsc_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter IFSC/SWIFT code'
            }),
            'currency': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'opening_balance': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'chart_account': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'is_default_for_payments': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_default_for_receipts': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter additional notes (optional)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter currencies to active ones
        self.fields['currency'].queryset = Currency.objects.filter(is_active=True)
        
        # Filter chart accounts to bank-type ledgers only
        self.fields['chart_account'].queryset = ChartOfAccount.objects.filter(
            account_type__category='ASSET',
            is_active=True
        ).order_by('account_code', 'name')
        
        # Set initial currency to AED if available
        if not self.instance.pk:
            try:
                aed_currency = Currency.objects.filter(code='AED').first()
                if aed_currency:
                    self.fields['currency'].initial = aed_currency
            except:
                pass
    
    def clean_account_number(self):
        account_number = self.cleaned_data.get('account_number')
        company = Company.objects.filter(is_active=True).first()
        
        if account_number and company:
            # Check if account number already exists for this company
            existing = BankAccount.objects.filter(
                account_number=account_number,
                company=company
            )
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError(_('An account with this number already exists for this company.'))
        
        return account_number
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Ensure only one default account for payments/receipts
        is_default_payments = cleaned_data.get('is_default_for_payments')
        is_default_receipts = cleaned_data.get('is_default_for_receipts')
        
        if is_default_payments or is_default_receipts:
            company = Company.objects.filter(is_active=True).first()
            if company:
                existing_accounts = BankAccount.objects.filter(company=company)
                if self.instance.pk:
                    existing_accounts = existing_accounts.exclude(pk=self.instance.pk)
                
                if is_default_payments:
                    existing_payments = existing_accounts.filter(is_default_for_payments=True)
                    if existing_payments.exists():
                        self.add_error('is_default_for_payments', 
                                     _('Another account is already set as default for payments.'))
                
                if is_default_receipts:
                    existing_receipts = existing_accounts.filter(is_default_for_receipts=True)
                    if existing_receipts.exists():
                        self.add_error('is_default_for_receipts', 
                                     _('Another account is already set as default for receipts.'))
        
        return cleaned_data


class BankAccountSearchForm(forms.Form):
    """Form for searching and filtering bank accounts"""
    
    SEARCH_CHOICES = [
        ('bank_name', 'Bank Name'),
        ('account_number', 'Account Number'),
        ('branch_name', 'Branch Name'),
    ]
    
    search_term = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search bank accounts...'
        })
    )
    
    search_by = forms.ChoiceField(
        choices=SEARCH_CHOICES,
        initial='bank_name',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    account_type = forms.ChoiceField(
        choices=[('', 'All Types')] + BankAccount.ACCOUNT_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    currency = forms.ModelChoiceField(
        queryset=Currency.objects.filter(is_active=True),
        required=False,
        empty_label="All Currencies",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + BankAccount.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    is_default = forms.ChoiceField(
        choices=[
            ('', 'All Accounts'),
            ('payments', 'Default for Payments'),
            ('receipts', 'Default for Receipts'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class BankAccountTransactionForm(forms.ModelForm):
    """Form for adding transactions to bank accounts"""
    
    class Meta:
        model = BankAccountTransaction
        fields = ['transaction_date', 'transaction_type', 'amount', 'description', 'reference_number']
        widgets = {
            'transaction_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'transaction_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'required': True
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter transaction description',
                'required': True
            }),
            'reference_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter reference number (optional)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.bank_account = kwargs.pop('bank_account', None)
        super().__init__(*args, **kwargs)
        
        if self.bank_account:
            # Set initial transaction date to today
            self.fields['transaction_date'].initial = timezone.now().date()
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise ValidationError(_('Amount must be greater than zero.'))
        return amount


class BankAccountBulkActionForm(forms.Form):
    """Form for bulk actions on bank accounts"""
    
    ACTION_CHOICES = [
        ('activate', 'Activate Selected'),
        ('deactivate', 'Deactivate Selected'),
        ('export_excel', 'Export to Excel'),
        ('export_pdf', 'Export to PDF'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    account_ids = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    ) 