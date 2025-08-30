from django import forms
from django.forms import ModelForm, Form
from .models import DepositSlip, DepositSlipItem
from receipt_voucher.models import ReceiptVoucher
from chart_of_accounts.models import ChartOfAccount
from django.utils import timezone
from datetime import date

class DepositSlipForm(ModelForm):
    """Form for creating and editing deposit slips"""
    
    class Meta:
        model = DepositSlip
        fields = ['deposit_date', 'deposit_to', 'reference_number', 'narration']
        widgets = {
            'deposit_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                    'value': timezone.now().date().isoformat()
                }
            ),
            'deposit_to': forms.Select(
                attrs={
                    'class': 'form-control select2',
                    'data-placeholder': 'Select Bank Account'
                }
            ),
            'reference_number': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter deposit reference or slip number'
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
        self.fields['deposit_to'].queryset = ChartOfAccount.objects.filter(
            account_type__category='ASSET',
            is_active=True
        ).order_by('account_code')


class ReceiptVoucherSelectionForm(Form):
    """Form for selecting receipt vouchers to include in deposit slip"""
    
    # Filter fields
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
    payer_name = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Search by payer name'
            }
        )
    )
    receipt_mode = forms.ChoiceField(
        required=False,
        choices=[('', 'All Payment Modes')] + ReceiptVoucher.RECEIPT_MODES,
        widget=forms.Select(
            attrs={
                'class': 'form-control'
            }
        )
    )
    
    # Selection field
    selected_vouchers = forms.MultipleChoiceField(
        choices=[],
        required=False,
        widget=forms.CheckboxSelectMultiple(
            attrs={
                'class': 'voucher-checkbox'
            }
        )
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_voucher_choices()
    
    def update_voucher_choices(self):
        """Update the choices for selected_vouchers based on current filters"""
        queryset = ReceiptVoucher.objects.filter(
            status='received',
            deposit_slip_items__isnull=True  # Only unlinked vouchers
        ).order_by('-voucher_date', '-created_at')
        
        choices = []
        for voucher in queryset:
            choice_text = f"{voucher.voucher_number} - {voucher.payer_name} - {voucher.get_receipt_mode_display()} - {voucher.amount}"
            choices.append((voucher.id, choice_text))
        
        self.fields['selected_vouchers'].choices = choices


class DepositSlipItemForm(ModelForm):
    """Form for individual deposit slip items"""
    
    class Meta:
        model = DepositSlipItem
        fields = ['receipt_voucher', 'amount']
        widgets = {
            'receipt_voucher': forms.Select(
                attrs={
                    'class': 'form-control select2',
                    'data-placeholder': 'Select Receipt Voucher'
                }
            ),
            'amount': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'step': '0.01',
                    'min': '0.01'
                }
            ),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter only unlinked receipt vouchers
        self.fields['receipt_voucher'].queryset = ReceiptVoucher.objects.filter(
            status='received',
            deposit_slip_items__isnull=True
        ).order_by('-voucher_date', '-created_at')


class DepositSlipFilterForm(Form):
    """Form for filtering deposit slips in list view"""
    
    STATUS_CHOICES = [('', 'All Statuses')] + DepositSlip.STATUS_CHOICES
    
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
    deposit_to = forms.ModelChoiceField(
        required=False,
        queryset=ChartOfAccount.objects.filter(
            account_type__category='ASSET',
            is_active=True
        ).order_by('account_code'),
        widget=forms.Select(
            attrs={
                'class': 'form-control select2',
                'data-placeholder': 'All Bank Accounts'
            }
        )
    )
    search = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Search by slip number or reference'
            }
        )
    ) 