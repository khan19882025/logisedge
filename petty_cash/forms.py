from django import forms
from django.forms import ModelForm, inlineformset_factory
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
from .models import PettyCashDay, PettyCashEntry, PettyCashBalance


class PettyCashDayForm(ModelForm):
    """Form for petty cash day management"""
    
    class Meta:
        model = PettyCashDay
        fields = ['entry_date', 'opening_balance', 'notes']
        widgets = {
            'entry_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                    'placeholder': 'Select Date'
                }
            ),
            'opening_balance': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '0.01',
                    'step': '0.01',
                    'placeholder': 'Enter opening balance'
                }
            ),
            'notes': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Additional notes (optional)'
                }
            ),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set default date to today if not editing
        if not self.instance.pk:
            self.fields['entry_date'].initial = timezone.now().date()
    
    def clean_entry_date(self):
        entry_date = self.cleaned_data['entry_date']
        
        # Check if date is not in the future
        if entry_date > timezone.now().date():
            raise forms.ValidationError("Cannot create entries for future dates.")
        
        # Check for duplicate date (only if not editing)
        if not self.instance.pk:
            if PettyCashDay.objects.filter(entry_date=entry_date).exists():
                raise forms.ValidationError("An entry for this date already exists.")
        
        return entry_date
    
    def clean_opening_balance(self):
        opening_balance = self.cleaned_data['opening_balance']
        
        if opening_balance < 0:
            raise forms.ValidationError("Opening balance cannot be negative.")
        
        return opening_balance


class PettyCashEntryForm(ModelForm):
    """Form for individual petty cash entries"""
    
    class Meta:
        model = PettyCashEntry
        fields = ['job_no', 'description', 'amount', 'notes']
        widgets = {
            'job_no': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Job No.'
                }
            ),
            'description': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Description'
                }
            ),
            'amount': forms.NumberInput(
                attrs={
                    'class': 'form-control amount-input',
                    'placeholder': '0.00',
                    'step': '0.01',
                    'min': '0.01'
                }
            ),
            'notes': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Notes (optional)'
                }
            )
        }
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        
        # Allow None/empty amounts for empty forms
        if amount is None:
            return amount
            
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        
        return amount
    
    def clean_description(self):
        description = self.cleaned_data.get('description', '').strip()
        amount = self.cleaned_data.get('amount')
        
        # Only require description if amount is provided
        if amount and amount > 0 and not description:
            raise forms.ValidationError("Description is required when amount is provided.")
        
        return description
    
    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get('amount')
        description = cleaned_data.get('description', '').strip()
        
        # Skip validation for completely empty forms
        if not amount and not description:
            # Mark this form for deletion if it's empty
            cleaned_data['DELETE'] = True
        
        return cleaned_data


# Inline formset for entries
PettyCashEntryFormSet = inlineformset_factory(
    PettyCashDay,
    PettyCashEntry,
    form=PettyCashEntryForm,
    extra=1,
    can_delete=True,
    fields=['job_no', 'description', 'amount', 'notes'],
    validate_min=False,
    min_num=0
)


class PettyCashBalanceForm(ModelForm):
    """Form for managing petty cash balance"""
    
    class Meta:
        model = PettyCashBalance
        fields = ['location', 'currency', 'current_balance']
        widgets = {
            'location': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter location name'
                }
            ),
            'currency': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),
            'current_balance': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '0.01',
                    'step': '0.01',
                    'placeholder': 'Enter current balance'
                }
            ),
        }
    
    def clean_current_balance(self):
        balance = self.cleaned_data['current_balance']
        
        if balance < 0:
            raise forms.ValidationError("Balance cannot be negative.")
        
        return balance


class PettyCashFilterForm(forms.Form):
    """Form for filtering petty cash entries"""
    
    STATUS_CHOICES = [('', 'All Statuses'), ('draft', 'Draft'), ('submitted', 'Submitted'), 
                     ('approved', 'Approved'), ('locked', 'Locked')]
    
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
                'class': 'form-select'
            }
        )
    )
    paid_by = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Search by paid by'
            }
        )
    )
    search = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Search by description'
            }
        )
    )


class QuickEntryForm(forms.Form):
    """Quick entry form for adding single entries"""
    
    description = forms.CharField(
        max_length=255,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter expense description'
            }
        )
    )
    amount = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(
            attrs={
                'class': 'form-control',
                'min': '0.01',
                'step': '0.01',
                'placeholder': 'Enter amount'
            }
        )
    )
    paid_by = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Who paid for this expense?'
            }
        )
    )
    notes = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Additional notes (optional)'
            }
        )
    )