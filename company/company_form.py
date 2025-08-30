from django import forms
from company.company_model import Company

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = [
            'name', 'code', 'address', 'phone', 'email', 
            'website', 'tax_number', 'registration_number',
            'bank_name', 'bank_account_number', 'bank_iban', 'bank_swift_code', 'bank_branch',
            'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter company name'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter company code'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter company address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email address'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Enter website URL'}),
            'tax_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter tax number'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter registration number'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter bank name'}),
            'bank_account_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter bank account number'}),
            'bank_iban': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter IBAN'}),
            'bank_swift_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter SWIFT/BIC code'}),
            'bank_branch': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter bank branch'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code:
            code = code.upper()
        return code 