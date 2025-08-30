from django import forms
from .models import AccountType


class AccountTypeForm(forms.ModelForm):
    """Form for creating and editing account types"""
    
    class Meta:
        model = AccountType
        fields = ['name', 'category', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter account type name',
                'required': True
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter description (optional)'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def clean_name(self):
        """Validate account type name uniqueness"""
        name = self.cleaned_data.get('name')
        if name:
            # Check if name already exists (excluding current instance if editing)
            existing = AccountType.objects.filter(name__iexact=name)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise forms.ValidationError("An account type with this name already exists.")
        
        return name
    
    def clean(self):
        """Additional validation"""
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        category = cleaned_data.get('category')
        
        if name and category:
            # Additional business logic validation can be added here
            pass
        
        return cleaned_data 