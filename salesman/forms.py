from django import forms
from .models import Salesman

COUNTRY_CHOICES = [
    ('', 'Select Country'),
    ('AE', 'United Arab Emirates'),
    ('SA', 'Saudi Arabia'),
    ('IN', 'India'),
    ('US', 'United States'),
    ('CN', 'China'),
    ('GB', 'United Kingdom'),
    ('DE', 'Germany'),
    ('FR', 'France'),
    ('SG', 'Singapore'),
    ('JP', 'Japan'),
]

class SalesmanForm(forms.ModelForm):
    country = forms.ChoiceField(choices=COUNTRY_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter phone number'
        })
    )
    
    class Meta:
        model = Salesman
        fields = [
            'salesman_code', 'first_name', 'last_name', 'email', 'phone',
            'date_of_birth', 'gender', 'address', 'city', 'state', 'country', 'postal_code',
            'hire_date', 'status', 'department', 'position', 'manager',
            'commission_rate', 'target_amount', 'notes'
        ]
        widgets = {
            'salesman_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter salesman code (e.g., SAL001)'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter last name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email address'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter address'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter city'
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter state/province'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter postal code'
            }),
            'hire_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter department'
            }),
            'position': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter position/title'
            }),
            'manager': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Select manager (optional)'
            }),
            'commission_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': 'Enter commission rate (%)'
            }),
            'target_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Enter monthly target amount'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter additional notes'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter manager choices to only active salesmen
        self.fields['manager'].queryset = Salesman.objects.filter(status='active')
        self.fields['manager'].empty_label = "Select manager (optional)" 