from django import forms
from .models import DunningLetter

class DunningLetterForm(forms.ModelForm):
    customer = forms.ChoiceField(
        choices=[('', 'Select Customer')],
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'customer-select'
        })
    )
    
    class Meta:
        model = DunningLetter
        fields = ['customer', 'level', 'subject', 'content', 'status']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email subject'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Enter letter content'
            }),
            'level': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            })
        }

class DunningLetterFilterForm(forms.Form):
    customer = forms.ChoiceField(
        choices=[('', 'All Customers')],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    level = forms.ChoiceField(
        choices=[('', 'All Levels')] + DunningLetter.LEVEL_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + DunningLetter.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
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
    
    overdue_days_min = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Min overdue days'
        })
    )
    
    overdue_days_max = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Max overdue days'
        })
    ) 