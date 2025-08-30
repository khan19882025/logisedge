from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from .models import AdjustmentEntry, AdjustmentEntryDetail


class AdjustmentEntryForm(forms.ModelForm):
    """Form for creating and editing adjustment entries"""
    
    class Meta:
        model = AdjustmentEntry
        fields = ['date', 'narration', 'reference_number', 'adjustment_type']
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'required': True
            }),
            'narration': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter narration for this adjustment entry...'
            }),
            'reference_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Optional reference number'
            }),
            'adjustment_type': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default date to today
        if not self.instance.pk:
            self.fields['date'].initial = timezone.now().date()
    
    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        
        if date and date > timezone.now().date():
            raise ValidationError('Adjustment entry date cannot be in the future.')
        
        return cleaned_data


class AdjustmentEntryDetailForm(forms.ModelForm):
    """Form for individual adjustment entry details"""
    
    class Meta:
        model = AdjustmentEntryDetail
        fields = ['account', 'debit', 'credit']
        widgets = {
            'account': forms.Select(attrs={
                'class': 'form-control account-select',
                'required': True
            }),
            'debit': forms.NumberInput(attrs={
                'class': 'form-control debit-amount',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00'
            }),
            'credit': forms.NumberInput(attrs={
                'class': 'form-control credit-amount',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00'
            })
        }
    
    def clean(self):
        cleaned_data = super().clean()
        debit = cleaned_data.get('debit')
        credit = cleaned_data.get('credit')
        
        # Ensure either debit or credit is provided, but not both
        if debit and credit:
            raise ValidationError('An entry cannot have both debit and credit amounts.')
        
        if not debit and not credit:
            raise ValidationError('Either debit or credit amount must be provided.')
        
        # Ensure amounts are positive
        if debit and debit <= 0:
            raise ValidationError('Debit amount must be greater than zero.')
        
        if credit and credit <= 0:
            raise ValidationError('Credit amount must be greater than zero.')
        
        return cleaned_data


class AdjustmentEntryDetailFormSet(BaseInlineFormSet):
    """Formset for adjustment entry details with validation"""
    
    def clean(self):
        super().clean()
        
        if not self.is_valid():
            return
        
        # Check if we have at least 2 entries
        if len(self.forms) < 2:
            raise ValidationError('An adjustment entry must have at least two entries (one debit, one credit).')
        
        # Calculate totals
        total_debit = Decimal('0.00')
        total_credit = Decimal('0.00')
        valid_forms = 0
        
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                debit = form.cleaned_data.get('debit')
                credit = form.cleaned_data.get('credit')
                
                if debit:
                    total_debit += debit
                if credit:
                    total_credit += credit
                
                valid_forms += 1
        
        # Check if we have at least 2 valid entries
        if valid_forms < 2:
            raise ValidationError('An adjustment entry must have at least two entries (one debit, one credit).')
        
        # Check if debit equals credit
        if total_debit != total_credit:
            raise ValidationError(
                f'Total debit ({total_debit}) must equal total credit ({total_credit}). '
                f'Difference: {abs(total_debit - total_credit)}'
            )
        
        # Check if we have at least one debit and one credit
        has_debit = any(
            form.cleaned_data.get('debit') 
            for form in self.forms 
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False)
        )
        has_credit = any(
            form.cleaned_data.get('credit') 
            for form in self.forms 
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False)
        )
        
        if not has_debit:
            raise ValidationError('At least one debit entry is required.')
        
        if not has_credit:
            raise ValidationError('At least one credit entry is required.')


# Create the inline formset
AdjustmentEntryDetailInlineFormSet = inlineformset_factory(
    AdjustmentEntry,
    AdjustmentEntryDetail,
    form=AdjustmentEntryDetailForm,
    formset=AdjustmentEntryDetailFormSet,
    extra=2,  # Start with 2 empty forms
    min_num=2,  # Minimum 2 entries required
    max_num=20,  # Maximum 20 entries
    can_delete=True,
    validate_min=True,
    validate_max=True
)


class AdjustmentEntrySearchForm(forms.Form):
    """Form for searching adjustment entries"""
    
    SEARCH_CHOICES = [
        ('voucher_number', 'Voucher Number'),
        ('narration', 'Narration'),
        ('reference_number', 'Reference Number'),
        ('account', 'Account'),
    ]
    
    STATUS_CHOICES = [
        ('', 'All Statuses'),
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancelled', 'Cancelled'),
    ]
    
    ADJUSTMENT_TYPE_CHOICES = [
        ('', 'All Types'),
        ('prepaid_expense', 'Prepaid Expense'),
        ('accrued_expense', 'Accrued Expense'),
        ('accrued_income', 'Accrued Income'),
        ('depreciation', 'Depreciation'),
        ('reclassification', 'Reclassification'),
        ('others', 'Others'),
    ]
    
    search_type = forms.ChoiceField(
        choices=SEARCH_CHOICES,
        initial='voucher_number',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    search_term = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter search term...'
        })
    )
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    adjustment_type = forms.ChoiceField(
        choices=ADJUSTMENT_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    ) 