from django import forms
from django.forms import inlineformset_factory
from .models import OpeningBalance, OpeningBalanceEntry
from chart_of_accounts.models import ChartOfAccount
from fiscal_year.models import FiscalYear


class OpeningBalanceForm(forms.ModelForm):
    class Meta:
        model = OpeningBalance
        fields = ['financial_year']
        widgets = {
            'financial_year': forms.Select(
                attrs={
                    'class': 'form-select',
                    'id': 'financial_year_select'
                }
            )
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active financial years
        self.fields['financial_year'].queryset = FiscalYear.objects.filter(status='active')
        self.fields['financial_year'].empty_label = "Select Financial Year"


class OpeningBalanceEntryForm(forms.ModelForm):
    class Meta:
        model = OpeningBalanceEntry
        fields = ['account', 'amount', 'balance_type', 'remarks']
        widgets = {
            'account': forms.Select(
                attrs={
                    'class': 'form-select account-select',
                    'placeholder': 'Search for an account...'
                }
            ),
            'amount': forms.NumberInput(
                attrs={
                    'class': 'form-control amount-input',
                    'step': '0.01',
                    'min': '0.01',
                    'placeholder': '0.00'
                }
            ),
            'balance_type': forms.Select(
                attrs={
                    'class': 'form-select balance-type-select'
                }
            ),
            'remarks': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': '2',
                    'placeholder': 'Optional remarks...'
                }
            )
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active accounts
        self.fields['account'].queryset = ChartOfAccount.objects.filter(is_active=True).order_by('account_code')
        self.fields['account'].empty_label = "Select Account"


# Create formset for multiple entries
BaseOpeningBalanceEntryFormSet = inlineformset_factory(
    OpeningBalance,
    OpeningBalanceEntry,
    form=OpeningBalanceEntryForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
    exclude=[],
    can_delete_extra=True
)

class CustomOpeningBalanceEntryFormSet(BaseOpeningBalanceEntryFormSet):
    def clean(self):
        super().clean()
        total_debit = 0
        total_credit = 0
        valid_entries = 0
        
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                account = form.cleaned_data.get('account')
                amount = form.cleaned_data.get('amount')
                balance_type = form.cleaned_data.get('balance_type')
                
                if account and amount and balance_type:
                    valid_entries += 1
                    if balance_type == 'debit':
                        total_debit += amount
                    elif balance_type == 'credit':
                        total_credit += amount
        
        if valid_entries > 0 and total_debit != total_credit:
            raise forms.ValidationError(
                f'Opening balance must be balanced. Total Debit: {total_debit}, Total Credit: {total_credit}'
            )

OpeningBalanceEntryFormSet = CustomOpeningBalanceEntryFormSet 