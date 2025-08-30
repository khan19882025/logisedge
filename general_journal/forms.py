from django import forms
from django.contrib.auth.models import User
from .models import JournalEntry
from chart_of_accounts.models import ChartOfAccount


class CustomJournalEntryForm(forms.Form):
    """Custom form for creating journal entries - completely separate from ModelForm"""
    
    date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    reference = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter reference number'
        })
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter description'
        })
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Enter notes (optional)'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.instance = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)
        
        # If we have an instance, populate the form
        if self.instance:
            self.fields['date'].initial = self.instance.date
            self.fields['reference'].initial = self.instance.reference
            self.fields['description'].initial = self.instance.description
            self.fields['notes'].initial = self.instance.notes
    
    def save(self, company, fiscal_year, user):
        """Save the form data to create or update a journal entry"""
        if self.instance:
            # Update existing instance
            self.instance.date = self.cleaned_data['date']
            self.instance.reference = self.cleaned_data['reference']
            self.instance.description = self.cleaned_data['description']
            self.instance.notes = self.cleaned_data['notes']
            self.instance.save()
            return self.instance
        else:
            # Create new instance
            return JournalEntry.objects.create(
                date=self.cleaned_data['date'],
                reference=self.cleaned_data['reference'],
                description=self.cleaned_data['description'],
                notes=self.cleaned_data['notes'],
                company=company,
                fiscal_year=fiscal_year,
                created_by=user
            )


# Keep the old form for backward compatibility
JournalEntryForm = CustomJournalEntryForm


class JournalEntrySearchForm(forms.Form):
    """Form for searching and filtering journal entries"""
    
    SEARCH_TYPE_CHOICES = [
        ('journal_number', 'Journal Number'),
        ('reference', 'Reference'),
        ('description', 'Description'),
        ('account', 'Account'),
    ]
    
    STATUS_CHOICES = [
        ('', 'All Statuses'),
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancelled', 'Cancelled'),
    ]
    
    search_type = forms.ChoiceField(
        choices=SEARCH_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    search_query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter search term'
        })
    )
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
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
    account = forms.ModelChoiceField(
        queryset=ChartOfAccount.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        if self.company:
            self.fields['account'].queryset = ChartOfAccount.objects.filter(
                company=self.company,
                is_active=True,
                is_group=False
            ).order_by('name') 