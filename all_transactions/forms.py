from django import forms
from django.contrib.auth.models import User
from chart_of_accounts.models import ChartOfAccount as Account
from .models import TransactionView


class TransactionFilterForm(forms.Form):
    """Form for filtering transactions"""
    
    # Date range filters
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'From Date'
        }),
        label='From Date'
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'To Date'
        }),
        label='To Date'
    )
    
    # Transaction type filter
    transaction_type = forms.ChoiceField(
        choices=[('', 'All Types')] + TransactionView.TRANSACTION_TYPES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'placeholder': 'Transaction Type'
        }),
        label='Transaction Type'
    )
    
    # Account filters
    debit_account = forms.ModelChoiceField(
        queryset=Account.objects.filter(is_active=True).order_by('name'),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'placeholder': 'Debit Account'
        }),
        label='Debit Account'
    )
    
    credit_account = forms.ModelChoiceField(
        queryset=Account.objects.filter(is_active=True).order_by('name'),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'placeholder': 'Credit Account'
        }),
        label='Credit Account'
    )
    
    # Amount range filters
    amount_from = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Min Amount',
            'step': '0.01'
        }),
        label='Amount From'
    )
    
    amount_to = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Max Amount',
            'step': '0.01'
        }),
        label='Amount To'
    )
    
    # User filter
    posted_by = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True).order_by('username'),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'placeholder': 'Posted By'
        }),
        label='Posted By'
    )
    
    # Status filter
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + TransactionView.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'placeholder': 'Status'
        }),
        label='Status'
    )
    
    # Search filters
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search document number, narration...'
        }),
        label='Search'
    )
    
    # Reference number filter
    reference_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Reference Number'
        }),
        label='Reference Number'
    )
    
    # Export format
    export_format = forms.ChoiceField(
        choices=[
            ('', 'No Export'),
            ('excel', 'Export to Excel'),
            ('pdf', 'Export to PDF'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Export Format'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add empty option to account choices
        self.fields['debit_account'].empty_label = "All Debit Accounts"
        self.fields['credit_account'].empty_label = "All Credit Accounts"
        self.fields['posted_by'].empty_label = "All Users"


class TransactionDetailForm(forms.ModelForm):
    """Form for viewing transaction details (read-only)"""
    
    class Meta:
        model = TransactionView
        fields = [
            'transaction_date', 'transaction_type', 'document_number', 
            'reference_number', 'debit_account', 'credit_account', 
            'amount', 'narration', 'posted_by', 'status'
        ]
        widgets = {
            'transaction_date': forms.DateInput(attrs={'class': 'form-control', 'readonly': True}),
            'transaction_type': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'document_number': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'debit_account': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'credit_account': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'readonly': True}),
            'narration': forms.Textarea(attrs={'class': 'form-control', 'readonly': True, 'rows': 3}),
            'posted_by': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'status': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
        } 