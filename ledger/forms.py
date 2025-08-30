from django import forms
from django.contrib.auth.models import User
from .models import Ledger, LedgerBatch
from chart_of_accounts.models import ChartOfAccount as Account
from company.company_model import Company
from fiscal_year.models import FiscalYear
from django.core.exceptions import ValidationError
from decimal import Decimal


class LedgerForm(forms.ModelForm):
    """Form for creating and editing ledger entries"""
    
    class Meta:
        model = Ledger
        fields = [
            'entry_date', 'reference', 'description', 'account', 'entry_type', 
            'amount', 'voucher_number', 'cheque_number', 'bank_reference', 'payment_source'
        ]
        widgets = {
            'entry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter reference number'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter detailed description'
            }),
            'account': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'entry_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': 'Enter amount (optional)'
            }),
            'voucher_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter voucher number'
            }),
            'cheque_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter cheque number'
            }),
            'bank_reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter bank reference'
            }),
            'payment_source': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Select payment source'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user and user.is_authenticated:
            # Filter accounts by user's company
            try:
                company = Company.objects.filter(is_active=True).first()
                if company:
                    self.fields['account'].queryset = Account.objects.filter(
                        company=company,
                        is_active=True
                    ).order_by('account_code', 'name')
            except:
                self.fields['account'].queryset = Account.objects.filter(is_active=True).order_by('account_code', 'name')
    
    def clean_amount(self):
        """Validate amount field"""
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise ValidationError("Amount must be greater than zero.")
        return amount
    
    def clean(self):
        """Additional validation"""
        cleaned_data = super().clean()
        entry_type = cleaned_data.get('entry_type')
        amount = cleaned_data.get('amount')
        
        if entry_type and amount:
            # Additional business logic validation can be added here
            pass
        
        return cleaned_data


class LedgerBatchForm(forms.ModelForm):
    """Form for creating and editing ledger batches"""
    
    class Meta:
        model = LedgerBatch
        fields = ['batch_type', 'description']
        widgets = {
            'batch_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter batch description'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set initial values if needed
        if not self.instance.pk:
            self.fields['batch_type'].initial = 'JOURNAL'


class LedgerSearchForm(forms.Form):
    """Form for searching ledger entries"""
    
    SEARCH_BY_CHOICES = [
        ('ledger_number', 'Ledger Number'),
        ('reference', 'Reference'),
        ('description', 'Description'),
        ('voucher_number', 'Voucher Number'),
        ('cheque_number', 'Cheque Number'),
        ('bank_reference', 'Bank Reference'),
    ]
    
    ENTRY_TYPE_CHOICES = [
        ('', 'All Entry Types'),
        ('DR', 'Debit'),
        ('CR', 'Credit'),
    ]
    
    STATUS_CHOICES = [
        ('', 'All Status'),
        ('DRAFT', 'Draft'),
        ('POSTED', 'Posted'),
        ('VOID', 'Void'),
    ]
    
    # Search fields
    search_term = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search ledger entries...'
        })
    )
    
    search_by = forms.ChoiceField(
        choices=SEARCH_BY_CHOICES,
        initial='ledger_number',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Filter fields
    account = forms.ModelChoiceField(
        queryset=Account.objects.none(),
        required=False,
        empty_label="All Accounts",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    entry_type = forms.ChoiceField(
        choices=ENTRY_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
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
    
    amount_min = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Min amount'
        })
    )
    
    amount_max = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Max amount'
        })
    )
    
    is_reconciled = forms.ChoiceField(
        choices=[
            ('', 'All'),
            ('True', 'Reconciled'),
            ('False', 'Not Reconciled'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user and user.is_authenticated:
            # Filter accounts by user's company
            try:
                company = Company.objects.filter(is_active=True).first()
                if company:
                    self.fields['account'].queryset = Account.objects.filter(
                        company=company,
                        is_active=True
                    ).order_by('account_code', 'name')
            except:
                self.fields['account'].queryset = Account.objects.filter(is_active=True).order_by('account_code', 'name')
    
    def clean(self):
        """Validate date range and amount range"""
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        amount_min = cleaned_data.get('amount_min')
        amount_max = cleaned_data.get('amount_max')
        
        # Validate date range
        if date_from and date_to and date_from > date_to:
            raise ValidationError("Date from cannot be after date to.")
        
        # Validate amount range
        if amount_min and amount_max and amount_min > amount_max:
            raise ValidationError("Minimum amount cannot be greater than maximum amount.")
        
        return cleaned_data


class LedgerImportForm(forms.Form):
    """Form for importing ledger entries from CSV/Excel"""
    
    file = forms.FileField(
        label="Select File",
        help_text="Upload CSV or Excel file with ledger entries",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls'
        })
    )
    
    batch_type = forms.ChoiceField(
        choices=LedgerBatch.BATCH_TYPES,
        initial='JOURNAL',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    description = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Batch description for imported entries'
        })
    )
    
    skip_first_row = forms.BooleanField(
        required=False,
        initial=True,
        label="Skip first row (headers)",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def clean_file(self):
        """Validate uploaded file"""
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (max 5MB)
            if file.size > 5 * 1024 * 1024:
                raise ValidationError("File size must be less than 5MB.")
            
            # Check file extension
            allowed_extensions = ['.csv', '.xlsx', '.xls']
            file_extension = file.name.lower()
            if not any(file_extension.endswith(ext) for ext in allowed_extensions):
                raise ValidationError("Please upload a CSV or Excel file.")
        
        return file


class LedgerReconciliationForm(forms.Form):
    """Form for reconciling ledger entries"""
    
    reconciliation_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'required': True
        })
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter reconciliation notes'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default reconciliation date to today
        from django.utils import timezone
        self.fields['reconciliation_date'].initial = timezone.now().date() 