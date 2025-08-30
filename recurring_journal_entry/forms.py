from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from .models import RecurringEntry, RecurringEntryLine
from chart_of_accounts.models import ChartOfAccount
from company.company_model import Company
from multi_currency.models import Currency
from fiscal_year.models import FiscalYear
from datetime import date


class RecurringEntryForm(forms.ModelForm):
    """Form for creating/editing recurring entries"""
    
    class Meta:
        model = RecurringEntry
        fields = [
            'template_name', 'journal_type', 'narration', 'start_date', 
            'end_date', 'number_of_occurrences', 'frequency', 'posting_day', 
            'custom_day', 'currency', 'fiscal_year', 'auto_post'
        ]
        widgets = {
            'template_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter template name (e.g., Monthly Rent, Depreciation)'
            }),
            'journal_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'narration': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter description for this recurring entry'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'number_of_occurrences': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '999',
                'placeholder': 'Leave empty for unlimited'
            }),
            'frequency': forms.Select(attrs={
                'class': 'form-control'
            }),
            'posting_day': forms.Select(attrs={
                'class': 'form-control'
            }),
            'custom_day': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '31',
                'placeholder': 'Day of month (1-31)'
            }),
            'currency': forms.Select(attrs={
                'class': 'form-control'
            }),
            'fiscal_year': forms.Select(attrs={
                'class': 'form-control'
            }),
            'auto_post': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
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
        
        # Set default start date to today
        if not self.instance.pk:
            self.fields['start_date'].initial = date.today()
        
        # Add JavaScript for dynamic behavior
        self.fields['posting_day'].widget.attrs.update({
            'onchange': 'toggleCustomDay()'
        })
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        number_of_occurrences = cleaned_data.get('number_of_occurrences')
        posting_day = cleaned_data.get('posting_day')
        custom_day = cleaned_data.get('custom_day')
        
        # Validate dates
        if start_date and end_date and start_date >= end_date:
            raise ValidationError("End date must be after start date")
        
        # Validate that either end_date or number_of_occurrences is provided
        if not end_date and not number_of_occurrences:
            raise ValidationError("Either end date or number of occurrences must be specified")
        
        # Validate custom day
        if posting_day == 'CUSTOM' and not custom_day:
            raise ValidationError("Custom day is required when posting day is set to 'Custom'")
        
        if custom_day and (custom_day < 1 or custom_day > 31):
            raise ValidationError("Custom day must be between 1 and 31")
        
        return cleaned_data


class RecurringEntryLineForm(forms.ModelForm):
    """Form for individual recurring entry lines"""
    
    class Meta:
        model = RecurringEntryLine
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


# Create formset for recurring entry lines
RecurringEntryLineFormSet = inlineformset_factory(
    RecurringEntry,
    RecurringEntryLine,
    form=RecurringEntryLineForm,
    extra=2,  # Start with 2 empty rows
    min_num=2,  # Minimum 2 lines required
    max_num=50,  # Maximum 50 lines
    can_delete=True,
    validate_min=True,
    validate_max=True
)


class RecurringEntryLineFormSetHelper:
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


class GenerateEntriesForm(forms.Form):
    """Form for manually generating entries from a recurring template"""
    posting_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'required': True
        }),
        help_text="Date for the journal entry to be generated"
    )
    
    auto_post = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text="Automatically post the generated entry"
    )
    
    def __init__(self, recurring_entry, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.recurring_entry = recurring_entry
        
        # Set default posting date to next scheduled date
        if recurring_entry:
            next_date = recurring_entry.get_next_posting_date()
            if next_date:
                self.fields['posting_date'].initial = next_date
    
    def clean_posting_date(self):
        posting_date = self.cleaned_data['posting_date']
        
        # Check if entry already exists for this date
        if self.recurring_entry.generated_entries.filter(posting_date=posting_date).exists():
            raise ValidationError("An entry for this date has already been generated")
        
        # Check if date is within the recurring entry's date range
        if posting_date < self.recurring_entry.start_date:
            raise ValidationError("Posting date cannot be before the start date")
        
        if self.recurring_entry.end_date and posting_date > self.recurring_entry.end_date:
            raise ValidationError("Posting date cannot be after the end date")
        
        return posting_date 