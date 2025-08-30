from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import (
    BankReconciliationSession, ERPTransaction, BankStatementEntry, 
    MatchedEntry, ReconciliationReport
)
from bank_accounts.models import BankAccount
from chart_of_accounts.models import ChartOfAccount
import csv
import io


class BankReconciliationSessionForm(forms.ModelForm):
    """Form for creating and editing reconciliation sessions"""
    
    class Meta:
        model = BankReconciliationSession
        fields = [
            'bank_account', 'session_name', 'reconciliation_date',
            'tolerance_amount', 'opening_balance_erp', 'opening_balance_bank'
        ]
        widgets = {
            'bank_account': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'session_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter session name (e.g., January 2024 Reconciliation)',
                'required': True
            }),
            'reconciliation_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'tolerance_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.01'
            }),
            'opening_balance_erp': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'opening_balance_bank': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter bank accounts to active ones
        self.fields['bank_account'].queryset = BankAccount.objects.filter(
            status='active'
        ).order_by('bank_name')
        
        # Set default reconciliation date to today
        if not self.instance.pk:
            self.fields['reconciliation_date'].initial = timezone.now().date()
    
    def clean(self):
        cleaned_data = super().clean()
        bank_account = cleaned_data.get('bank_account')
        reconciliation_date = cleaned_data.get('reconciliation_date')
        
        # Check if there's already an open session for this account and date
        if bank_account and reconciliation_date:
            existing_session = BankReconciliationSession.objects.filter(
                bank_account=bank_account,
                reconciliation_date=reconciliation_date,
                status__in=['open', 'in_progress']
            )
            if self.instance.pk:
                existing_session = existing_session.exclude(pk=self.instance.pk)
            
            if existing_session.exists():
                raise ValidationError(
                    _('A reconciliation session already exists for this bank account and date.')
                )
        
        return cleaned_data


class BankStatementImportForm(forms.Form):
    """Form for importing bank statements"""
    
    IMPORT_FORMATS = [
        ('csv', 'CSV File'),
        ('excel', 'Excel File'),
    ]
    
    reconciliation_session = forms.ModelChoiceField(
        queryset=BankReconciliationSession.objects.filter(status__in=['open', 'in_progress']),
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Select the reconciliation session to import into"
    )
    
    import_file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls'
        }),
        help_text="Upload CSV or Excel file with bank statement data"
    )
    
    import_format = forms.ChoiceField(
        choices=IMPORT_FORMATS,
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='csv'
    )
    
    # CSV Column Mapping
    date_column = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        initial='Date',
        help_text="Column name for transaction date"
    )
    
    description_column = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        initial='Description',
        help_text="Column name for transaction description"
    )
    
    reference_column = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        initial='Reference',
        help_text="Column name for reference number"
    )
    
    debit_column = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        initial='Debit',
        help_text="Column name for debit amount"
    )
    
    credit_column = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        initial='Credit',
        help_text="Column name for credit amount"
    )
    
    # Import Options
    skip_first_row = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Skip the first row (header row)"
    )
    
    date_format = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        initial='%Y-%m-%d',
        help_text="Date format (e.g., %Y-%m-%d, %d/%m/%Y)"
    )
    
    def clean_import_file(self):
        file = self.cleaned_data['import_file']
        import_format = self.cleaned_data.get('import_format', 'csv')
        
        if file:
            # Check file size (max 10MB)
            if file.size > 10 * 1024 * 1024:
                raise ValidationError(_('File size must be less than 10MB.'))
            
            # Check file extension
            file_extension = file.name.split('.')[-1].lower()
            if import_format == 'csv' and file_extension != 'csv':
                raise ValidationError(_('Please upload a CSV file.'))
            elif import_format == 'excel' and file_extension not in ['xlsx', 'xls']:
                raise ValidationError(_('Please upload an Excel file (.xlsx or .xls).'))
        
        return file


class BankStatementEntryForm(forms.ModelForm):
    """Form for manually adding bank statement entries"""
    
    class Meta:
        model = BankStatementEntry
        fields = ['transaction_date', 'description', 'reference_number', 'debit_amount', 'credit_amount']
        widgets = {
            'transaction_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
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
            'debit_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'credit_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        debit_amount = cleaned_data.get('debit_amount', 0)
        credit_amount = cleaned_data.get('credit_amount', 0)
        
        # Ensure only one amount is provided
        if debit_amount > 0 and credit_amount > 0:
            raise ValidationError(_('Please provide either a debit or credit amount, not both.'))
        
        if debit_amount == 0 and credit_amount == 0:
            raise ValidationError(_('Please provide either a debit or credit amount.'))
        
        return cleaned_data


class ReconciliationFilterForm(forms.Form):
    """Form for filtering reconciliation entries"""
    
    # Date Range
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    # Search
    search_term = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search description, reference, or amount...'
        })
    )
    
    # Amount Range
    min_amount = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Min amount'
        })
    )
    
    max_amount = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Max amount'
        })
    )
    
    # Status Filters
    match_status = forms.ChoiceField(
        choices=[
            ('', 'All Entries'),
            ('matched', 'Matched Only'),
            ('unmatched', 'Unmatched Only'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    transaction_type = forms.ChoiceField(
        choices=[
            ('', 'All Types'),
            ('credit', 'Credits Only'),
            ('debit', 'Debits Only'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class ManualMatchForm(forms.Form):
    """Form for manually matching ERP and Bank entries"""
    
    erp_entry = forms.ModelChoiceField(
        queryset=ERPTransaction.objects.filter(is_matched=False),
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Select ERP transaction to match"
    )
    
    bank_entry = forms.ModelChoiceField(
        queryset=BankStatementEntry.objects.filter(is_matched=False),
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Select Bank statement entry to match"
    )
    
    match_type = forms.ChoiceField(
        choices=[
            ('exact', 'Exact Match'),
            ('partial', 'Partial Match'),
            ('manual', 'Manual Match'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='manual'
    )
    
    notes = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Add notes about this match (optional)'
        })
    )
    
    def __init__(self, *args, **kwargs):
        reconciliation_session = kwargs.pop('reconciliation_session', None)
        super().__init__(*args, **kwargs)
        
        if reconciliation_session:
            self.fields['erp_entry'].queryset = ERPTransaction.objects.filter(
                reconciliation_session=reconciliation_session,
                is_matched=False
            )
            self.fields['bank_entry'].queryset = BankStatementEntry.objects.filter(
                reconciliation_session=reconciliation_session,
                is_matched=False
            )
    
    def clean(self):
        cleaned_data = super().clean()
        erp_entry = cleaned_data.get('erp_entry')
        bank_entry = cleaned_data.get('bank_entry')
        
        if erp_entry and bank_entry:
            # Check if entries are from the same session
            if erp_entry.reconciliation_session != bank_entry.reconciliation_session:
                raise ValidationError(_('ERP and Bank entries must be from the same reconciliation session.'))
            
            # Check if entries are already matched
            if erp_entry.is_matched:
                raise ValidationError(_('ERP entry is already matched.'))
            
            if bank_entry.is_matched:
                raise ValidationError(_('Bank entry is already matched.'))
        
        return cleaned_data


class BulkMatchForm(forms.Form):
    """Form for bulk matching operations"""
    
    MATCH_CRITERIA = [
        ('amount_date', 'Amount + Date'),
        ('amount_only', 'Amount Only'),
        ('reference', 'Reference Number'),
        ('description', 'Description Similarity'),
    ]
    
    match_criteria = forms.ChoiceField(
        choices=MATCH_CRITERIA,
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='amount_date',
        help_text="Select criteria for automatic matching"
    )
    
    date_tolerance = forms.IntegerField(
        min_value=0,
        max_value=30,
        initial=3,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text="Date tolerance in days"
    )
    
    amount_tolerance = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        initial=0.01,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text="Amount tolerance for partial matches"
    )
    
    description_similarity = forms.IntegerField(
        min_value=50,
        max_value=100,
        initial=80,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text="Minimum similarity percentage for description matching"
    )
    
    auto_confirm_matches = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Automatically confirm matches without manual review"
    )


class ReconciliationReportForm(forms.Form):
    """Form for generating reconciliation reports"""
    
    REPORT_TYPES = [
        ('summary', 'Summary Report'),
        ('detailed', 'Detailed Report'),
        ('unmatched', 'Unmatched Entries Report'),
        ('reconciliation_statement', 'Reconciliation Statement'),
    ]
    
    report_type = forms.ChoiceField(
        choices=REPORT_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='summary'
    )
    
    include_matched_entries = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    include_unmatched_entries = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    include_notes = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    export_format = forms.ChoiceField(
        choices=[
            ('pdf', 'PDF'),
            ('excel', 'Excel'),
            ('csv', 'CSV'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='pdf'
    ) 