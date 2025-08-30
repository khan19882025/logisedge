from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import ChequeRegister, ChequeStatusHistory
from chart_of_accounts.models import ChartOfAccount
from customer.models import Customer
from company.company_model import Company


class ChequeRegisterForm(forms.ModelForm):
    """Form for creating and editing cheque register entries"""
    
    class Meta:
        model = ChequeRegister
        fields = [
            'cheque_number', 'cheque_date', 'cheque_type', 'party_type',
            'customer', 'supplier', 'amount', 'bank_account',
            'related_transaction', 'transaction_reference', 'status',
            'clearing_date', 'remarks'
        ]
        widgets = {
            'cheque_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter cheque number',
                'required': True
            }),
            'cheque_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'cheque_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'party_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'customer': forms.Select(attrs={
                'class': 'form-select',
                'required': False
            }),
            'supplier': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter supplier name',
                'required': False
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00',
                'required': True
            }),
            'bank_account': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'related_transaction': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Related transaction reference'
            }),
            'transaction_reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Transaction reference number'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'clearing_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'remarks': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional remarks or notes'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter bank accounts - look for accounts with 'bank' in the name
        # or use all active accounts if no bank accounts found
        bank_accounts = ChartOfAccount.objects.filter(
            name__icontains='bank',
            is_active=True
        )
        if not bank_accounts.exists():
            bank_accounts = ChartOfAccount.objects.filter(is_active=True)
        
        self.fields['bank_account'].queryset = bank_accounts.order_by('name')
        
        # Filter customers
        self.fields['customer'].queryset = Customer.objects.filter(is_active=True).order_by('customer_name')
        
        # Set default cheque date to today
        if not self.instance.pk:
            self.fields['cheque_date'].initial = timezone.now().date()
        
        # Add dynamic field dependencies
        self.fields['customer'].widget.attrs.update({'style': 'display: none;'})
        self.fields['supplier'].widget.attrs.update({'style': 'display: none;'})
    
    def clean(self):
        cleaned_data = super().clean()
        party_type = cleaned_data.get('party_type')
        customer = cleaned_data.get('customer')
        supplier = cleaned_data.get('supplier')
        
        # Validate party selection
        if party_type == 'customer' and not customer:
            raise ValidationError(_('Please select a customer.'))
        elif party_type == 'supplier' and not supplier:
            raise ValidationError(_('Please enter a supplier name.'))
        
        return cleaned_data

    def save(self, commit=True):
        cheque = super().save(commit=False)
        
        # Set company from bank account if not already set
        if not cheque.company and cheque.bank_account:
            try:
                cheque.company = cheque.bank_account.company
            except Exception as e:
                # If bank account doesn't have company, get first active company
                from company.company_model import Company
                company = Company.objects.filter(is_active=True).first()
                if company:
                    cheque.company = company
        
        # Validate cheque number uniqueness after company is set
        if cheque.cheque_number and cheque.bank_account and cheque.company:
            existing_cheque = ChequeRegister.objects.filter(
                cheque_number=cheque.cheque_number,
                bank_account=cheque.bank_account,
                company=cheque.company
            )
            if self.instance.pk:
                existing_cheque = existing_cheque.exclude(pk=self.instance.pk)
            
            if existing_cheque.exists():
                raise ValidationError(_('A cheque with this number already exists for this bank account.'))
        
        if commit:
            cheque.save()
        
        return cheque


class ChequeFilterForm(forms.Form):
    """Form for filtering cheque register entries"""
    
    # Search
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search cheque number or party name...'
        })
    )
    
    # Filters
    cheque_type = forms.ChoiceField(
        choices=[('', 'All Types')] + ChequeRegister.CHEQUE_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + ChequeRegister.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    party_type = forms.ChoiceField(
        choices=[('', 'All Parties')] + [('customer', 'Customer'), ('supplier', 'Supplier')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    bank_account = forms.ModelChoiceField(
        queryset=ChartOfAccount.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="All Bank Accounts"
    )
    
    # Date Range
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
    
    # Amount Range
    amount_min = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Min amount'
        })
    )
    
    amount_max = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Max amount'
        })
    )
    
    # Special Filters
    is_post_dated = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Post-dated Cheques Only"
    )
    
    is_overdue = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Overdue Cheques Only"
    )


class BulkStatusUpdateForm(forms.Form):
    """Form for bulk status updates"""
    
    STATUS_CHOICES = [
        ('cleared', 'Mark as Cleared'),
        ('bounced', 'Mark as Bounced'),
        ('cancelled', 'Mark as Cancelled'),
        ('stopped', 'Mark as Stopped'),
    ]
    
    new_status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Select new status for selected cheques"
    )
    
    clearing_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        help_text="Clearing date (required if marking as cleared)"
    )
    
    remarks = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Remarks for status change'
        }),
        help_text="Optional remarks for the status change"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        new_status = cleaned_data.get('new_status')
        clearing_date = cleaned_data.get('clearing_date')
        
        if new_status == 'cleared' and not clearing_date:
            raise ValidationError(_('Clearing date is required when marking cheques as cleared.'))
        
        return cleaned_data


class ChequeStatusChangeForm(forms.Form):
    """Form for changing individual cheque status"""
    
    new_status = forms.ChoiceField(
        choices=ChequeRegister.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    clearing_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    remarks = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Remarks for status change'
        })
    )
    
    def __init__(self, *args, **kwargs):
        current_status = kwargs.pop('current_status', None)
        super().__init__(*args, **kwargs)
        
        # Filter out current status from choices
        if current_status:
            choices = [(k, v) for k, v in ChequeRegister.STATUS_CHOICES if k != current_status]
            self.fields['new_status'].choices = choices 