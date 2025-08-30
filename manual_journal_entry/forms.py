from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from .models import JournalEntry, JournalEntryLine
from chart_of_accounts.models import ChartOfAccount
from company.company_model import Company
from multi_currency.models import Currency
from fiscal_year.models import FiscalYear


class JournalEntryForm(forms.ModelForm):
    """Form for creating/editing journal entries"""
    
    class Meta:
        model = JournalEntry
        fields = ['date', 'reference_number', 'narration', 'currency', 'fiscal_year']
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'reference_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter reference number (optional)'
            }),
            'narration': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter narration for this journal entry'
            }),
            'currency': forms.Select(attrs={
                'class': 'form-control'
            }),
            'fiscal_year': forms.Select(attrs={
                'class': 'form-control'
            })
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter fiscal years to active ones
        self.fields['fiscal_year'].queryset = FiscalYear.objects.filter(status='active')
        
        # Set default currency to AED
        if not self.instance.pk:
            try:
                aed_currency = Currency.objects.get(code='AED')
                self.fields['currency'].initial = aed_currency
            except Currency.DoesNotExist:
                pass
        
        # Set default fiscal year to current active one
        if not self.instance.pk:
            try:
                current_fiscal_year = FiscalYear.objects.filter(status='active').first()
                if current_fiscal_year:
                    self.fields['fiscal_year'].initial = current_fiscal_year
            except:
                pass


class JournalEntryLineForm(forms.ModelForm):
    """Form for individual journal entry lines"""
    
    class Meta:
        model = JournalEntryLine
        fields = ['account', 'description', 'debit', 'credit']
        widgets = {
            'account': forms.Select(attrs={
                'class': 'form-control account-select',
                'required': True
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter description (optional)'
            }),
            'debit': forms.NumberInput(attrs={
                'class': 'form-control debit-amount',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'credit': forms.NumberInput(attrs={
                'class': 'form-control credit-amount',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter accounts to active ones
        self.fields['account'].queryset = ChartOfAccount.objects.filter(is_active=True)
        
        # Add custom validation
        self.fields['debit'].widget.attrs.update({
            'onchange': 'validateLineAmount(this)',
            'onblur': 'calculateTotals()'
        })
        self.fields['credit'].widget.attrs.update({
            'onchange': 'validateLineAmount(this)',
            'onblur': 'calculateTotals()'
        })
    
    def clean(self):
        cleaned_data = super().clean()
        debit = cleaned_data.get('debit', 0)
        credit = cleaned_data.get('credit', 0)
        
        # Ensure at least one amount is provided
        if debit == 0 and credit == 0:
            raise ValidationError("Either debit or credit amount must be provided")
        
        # Ensure not both debit and credit have values
        if debit > 0 and credit > 0:
            raise ValidationError("A line item cannot have both debit and credit amounts")
        
        return cleaned_data


# Create formset for journal entry lines
JournalEntryLineFormSet = inlineformset_factory(
    JournalEntry,
    JournalEntryLine,
    form=JournalEntryLineForm,
    extra=2,  # Start with 2 empty rows
    min_num=2,  # Minimum 2 lines required
    max_num=50,  # Maximum 50 lines
    can_delete=True,
    validate_min=True,
    validate_max=True
)


class JournalEntryLineFormSetHelper:
    """Helper class for formset validation and processing"""
    
    @staticmethod
    def clean_formset(formset):
        """Clean and validate the entire formset"""
        if formset.is_valid():
            # Check if at least 2 lines have data
            lines_with_data = 0
            total_debit = 0
            total_credit = 0
            
            for form in formset.forms:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    lines_with_data += 1
                    debit = form.cleaned_data.get('debit', 0) or 0
                    credit = form.cleaned_data.get('credit', 0) or 0
                    total_debit += debit
                    total_credit += credit
            
            if lines_with_data < 2:
                raise ValidationError("At least 2 line items are required")
            
            if total_debit != total_credit:
                raise ValidationError(
                    f"Total debit ({total_debit}) must equal total credit ({total_credit})"
                )
            
            return True
        return False 