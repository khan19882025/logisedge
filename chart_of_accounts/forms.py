from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import ChartOfAccount, AccountType, AccountBalance, AccountGroup, AccountTemplate, AccountTemplateItem
from company.company_model import Company
from multi_currency.models import Currency


class AccountTypeForm(forms.ModelForm):
    """Form for Account Type management"""
    class Meta:
        model = AccountType
        fields = ['name', 'category', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter account type name'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter description'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ParentAccountForm(forms.ModelForm):
    """Form for Parent Account (Group) creation"""
    auto_generate_code = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'auto_generate_code'
        }),
        help_text="Auto-generate account code based on account type"
    )
    
    class Meta:
        model = ChartOfAccount
        fields = [
            'account_code', 'name', 'description', 'account_type', 'account_nature',
            'currency', 'is_active'
        ]
        widgets = {
            'account_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 1000, 1100, 2000',
                'pattern': '[0-9]+',
                'title': 'Account code must contain only numbers',
                'id': 'account_code'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter parent account name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter parent account description'
            }),
            'account_type': forms.Select(attrs={'class': 'form-select', 'id': 'account_type'}),
            'account_nature': forms.Select(attrs={
                'class': 'form-select',
                'id': 'account_nature'
            }),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        # Filter currencies to active ones
        self.fields['currency'].queryset = Currency.objects.filter(is_active=True)
        
        # Set initial currency to AED if available
        if not self.instance.pk:
            try:
                aed_currency = Currency.objects.filter(code='AED').first()
                if aed_currency:
                    self.fields['currency'].initial = aed_currency
            except:
                pass
    
    def clean_account_code(self):
        account_code = self.cleaned_data.get('account_code')
        if account_code:
            # Check for uniqueness within the company
            existing_account = ChartOfAccount.objects.filter(
                account_code=account_code,
                company=self.company
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if existing_account.exists():
                raise ValidationError(_(f'Account code "{account_code}" already exists for this company.'))
        
        return account_code
    
    def save(self, commit=True):
        account = super().save(commit=False)
        account.is_group = True  # Always set as group for parent accounts
        account.opening_balance = 0  # Parent accounts don't have opening balance
        
        if commit:
            account.save()
        return account
    
    @staticmethod
    def generate_account_code(account_type, company):
        """Generate account code for parent account"""
        if not account_type or not company:
            return None
        
        # Get the category prefix
        category_prefixes = {
            'ASSET': '1',
            'LIABILITY': '2', 
            'EQUITY': '3',
            'REVENUE': '4',
            'EXPENSE': '5'
        }
        
        prefix = category_prefixes.get(account_type.category, '9')
        
        # Find the next available code for parent accounts
        existing_codes = ChartOfAccount.objects.filter(
            company=company,
            account_type=account_type,
            is_group=True,
            account_code__startswith=prefix
        ).values_list('account_code', flat=True)
        
        # Generate next code
        for i in range(1, 1000):
            code = f"{prefix}{i:03d}"
            if code not in existing_codes:
                return code
        
        return None


class ChartOfAccountForm(forms.ModelForm):
    """Form for Chart of Account management"""
    parent_account_code = forms.CharField(
        max_length=20, 
        required=False, 
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter parent account code (optional)',
            'id': 'parent_account_code'
        }),
        help_text="Enter the account code of the parent account"
    )
    
    auto_generate_code = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'auto_generate_code'
        }),
        help_text="Auto-generate account code based on account type"
    )
    
    class Meta:
        model = ChartOfAccount
        fields = [
            'account_code', 'name', 'description', 'account_type', 'account_nature',
            'is_group', 'currency', 'opening_balance', 'is_active'
        ]
        widgets = {
            'account_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 1000, 1100, 2000',
                'pattern': '[0-9]+',
                'title': 'Account code must contain only numbers',
                'id': 'account_code'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter account name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter account description'
            }),
            'account_type': forms.Select(attrs={'class': 'form-select', 'id': 'account_type'}),
            'account_nature': forms.Select(attrs={
                'class': 'form-select',
                'id': 'account_nature'
            }),
            'is_group': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'opening_balance': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        # Filter currencies to active ones
        self.fields['currency'].queryset = Currency.objects.filter(is_active=True)
        
        # Set initial currency to AED if available
        if not self.instance.pk:
            try:
                aed_currency = Currency.objects.filter(code='AED').first()
                if aed_currency:
                    self.fields['currency'].initial = aed_currency
            except:
                pass
        
        # Ensure auto_generate_code field is included
        if 'auto_generate_code' not in self.fields:
            self.fields['auto_generate_code'] = forms.BooleanField(
                required=False,
                initial=True,
                widget=forms.CheckboxInput(attrs={
                    'class': 'form-check-input',
                    'id': 'auto_generate_code'
                }),
                help_text="Auto-generate account code based on account type"
            )
        
        # Make account_code optional for auto-generation
        self.fields['account_code'].required = False
        self.fields['account_code'].help_text = (
            "Account code will be auto-generated based on account type. "
            "You can also enter a custom code if needed."
        )
        
        # Make account_nature optional and add better help text
        self.fields['account_nature'].required = False
        self.fields['account_nature'].help_text = (
            "Normal balance side (optional). If left blank, will be auto-determined based on account type. "
            "Use 'Both' for accounts like Cash that can have both debit and credit transactions."
        )
        
        # Add empty choice for account_nature
        self.fields['account_nature'].choices = [('', 'Auto-determine from account type')] + list(self.fields['account_nature'].choices)
    
    def clean_account_code(self):
        account_code = self.cleaned_data.get('account_code', '')
        
        # Get auto_generate_code from data (not cleaned_data since it's not a model field)
        auto_generate = self.data.get('auto_generate_code') == 'on'  # Checkbox sends 'on' when checked
        
        # If auto-generate is checked and no account code provided, don't validate here
        # Let the clean() method handle auto-generation
        if auto_generate and not account_code:
            return ''  # Return empty string, let clean() method handle it
        
        # If manual entry and no code provided, raise error
        if not auto_generate and not account_code:
            raise ValidationError(_('Account code is required when auto-generation is disabled.'))
        
        # If account code is provided, check if it already exists for this company
        if account_code and self.company:
            if ChartOfAccount.objects.filter(
                account_code=account_code,
                company=self.company
            ).exclude(pk=self.instance.pk if self.instance.pk else None).exists():
                raise ValidationError(_('Account code already exists for this company.'))
        
        return account_code
    
    def clean(self):
        """Clean the entire form and handle auto-generation and duplicate check"""
        cleaned_data = super().clean()
        auto_generate = self.data.get('auto_generate_code') == 'on'
        account_code = cleaned_data.get('account_code', '')
        account_type = cleaned_data.get('account_type')
        company = self.company or getattr(self.instance, 'company', None) or cleaned_data.get('company')

        # If no account code and auto-generate is checked, try to generate it
        if not account_code and auto_generate and account_type and company:
            try:
                generated_code = self.generate_account_code(account_type, company)
                cleaned_data['account_code'] = generated_code
                self.fields['account_code'].initial = generated_code
                # Add a success message to inform user about the generated code
                self.generated_code = generated_code
            except ValueError as e:
                self.add_error('account_code', f'Auto-generation failed: {str(e)}. Please enter a code manually or try again.')
            except Exception as e:
                self.add_error('account_code', f'Unexpected error during auto-generation: {str(e)}. Please enter a code manually.')
        elif not account_code and auto_generate:
            if not account_type:
                self.add_error('account_type', 'Account type is required for auto-generation.')
            if not company:
                self.add_error(None, 'Company information is missing for auto-generation.')
        elif not account_code and not auto_generate:
            self.add_error('account_code', 'Account code is required. Please enable auto-generation or enter a code manually.')

        # Final duplicate check (in case company is not set on form)
        if account_code and company:
            qs = ChartOfAccount.objects.filter(account_code=account_code, company=company)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error('account_code', _('Account code already exists for this company.'))

        return cleaned_data
    
    def clean_parent_account_code(self):
        parent_code = self.cleaned_data.get('parent_account_code')
        if parent_code:
            try:
                parent_account = ChartOfAccount.objects.get(
                    account_code=parent_code,
                    company=self.company,
                    is_active=True
                )
                return parent_account
            except ChartOfAccount.DoesNotExist:
                raise ValidationError(_('Parent account with this code does not exist.'))
        return None
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set company
        if self.company:
            instance.company = self.company
        
        # Set parent account
        parent_account = self.cleaned_data.get('parent_account_code')
        if parent_account:
            instance.parent_account = parent_account
        
        if commit:
            instance.save()
        return instance
    
    @staticmethod
    def generate_account_code(account_type, company):
        """Generate account code based on account type and existing accounts"""
        # Define base codes for each category
        base_codes = {
            'ASSET': '1000',
            'LIABILITY': '2000', 
            'EQUITY': '3000',
            'REVENUE': '4000',
            'EXPENSE': '5000'
        }
        
        category = account_type.category
        base_code = base_codes.get(category, '1000')
        
        # Find all existing codes in this category for this company
        existing_codes = ChartOfAccount.objects.filter(
            company=company,
            account_code__startswith=base_code
        ).values_list('account_code', flat=True).order_by('account_code')
        
        if not existing_codes:
            return base_code
        
        # Find the highest code and increment
        max_code = max(existing_codes)
        try:
            # Try to increment by 100, but if that fails, try smaller increments
            next_number = int(max_code) + 100
            next_code = str(next_number)
            
            # Verify this code doesn't already exist (race condition protection)
            if ChartOfAccount.objects.filter(company=company, account_code=next_code).exists():
                # If it exists, try incrementing by 1 until we find a free code
                counter = 1
                while True:
                    next_code = str(int(max_code) + counter)
                    if not ChartOfAccount.objects.filter(company=company, account_code=next_code).exists():
                        break
                    counter += 1
                    if counter > 1000:  # Safety limit
                        raise ValueError("Unable to generate unique account code")
            
            return next_code
        except ValueError:
            # If parsing fails, try to find the next available code
            try:
                # Find the highest numeric code and increment
                numeric_codes = [int(code) for code in existing_codes if code.isdigit()]
                if numeric_codes:
                    max_numeric = max(numeric_codes)
                    next_code = str(max_numeric + 100)
                    
                    # Verify this code doesn't already exist
                    if not ChartOfAccount.objects.filter(company=company, account_code=next_code).exists():
                        return next_code
                
                # Fallback: use base code + 100
                fallback_code = str(int(base_code) + 100)
                if not ChartOfAccount.objects.filter(company=company, account_code=fallback_code).exists():
                    return fallback_code
                
                # Last resort: find any available code
                counter = 1
                while counter <= 1000:
                    test_code = str(int(base_code) + counter)
                    if not ChartOfAccount.objects.filter(company=company, account_code=test_code).exists():
                        return test_code
                    counter += 1
                
                raise ValueError("Unable to generate unique account code")
            except (ValueError, TypeError):
                raise ValueError("Unable to generate unique account code")


class AccountBalanceForm(forms.ModelForm):
    """Form for Account Balance management"""
    class Meta:
        model = AccountBalance
        fields = ['fiscal_year', 'period', 'opening_balance', 'debit_total', 'credit_total', 'closing_balance']
        widgets = {
            'fiscal_year': forms.Select(attrs={'class': 'form-select'}),
            'period': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'YYYY-MM',
                'pattern': '[0-9]{4}-[0-9]{2}'
            }),
            'opening_balance': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'debit_total': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'credit_total': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'closing_balance': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
        }


class AccountGroupForm(forms.ModelForm):
    """Form for Account Group management"""
    class Meta:
        model = AccountGroup
        fields = ['name', 'description', 'account_type', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter group name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'account_type': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AccountTemplateForm(forms.ModelForm):
    """Form for Account Template management"""
    class Meta:
        model = AccountTemplate
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter template name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AccountTemplateItemForm(forms.ModelForm):
    """Form for Account Template Item management"""
    class Meta:
        model = AccountTemplateItem
        fields = ['account_code', 'name', 'description', 'account_type', 'account_nature', 'parent_code', 'is_group']
        widgets = {
            'account_code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'account_type': forms.Select(attrs={'class': 'form-select'}),
            'account_nature': forms.Select(attrs={'class': 'form-select'}),
            'parent_code': forms.TextInput(attrs={'class': 'form-control'}),
            'is_group': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make account_nature optional for template items too
        self.fields['account_nature'].required = False
        self.fields['account_nature'].choices = [('', 'Auto-determine from account type')] + list(self.fields['account_nature'].choices)


class ChartOfAccountSearchForm(forms.Form):
    """Form for searching Chart of Accounts"""
    SEARCH_CHOICES = [
        ('code', 'Account Code'),
        ('name', 'Account Name'),
        ('type', 'Account Type'),
        ('category', 'Category'),
    ]
    
    search_term = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search accounts...'
        })
    )
    
    search_by = forms.ChoiceField(
        choices=SEARCH_CHOICES,
        initial='name',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    account_type = forms.ModelChoiceField(
        queryset=AccountType.objects.filter(is_active=True),
        required=False,
        empty_label="All Account Types",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    category = forms.ChoiceField(
        choices=[('', 'All Categories')] + AccountType.ACCOUNT_CATEGORIES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    is_active = forms.ChoiceField(
        choices=[
            ('', 'All Status'),
            ('True', 'Active'),
            ('False', 'Inactive')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    is_group = forms.ChoiceField(
        choices=[
            ('', 'All Accounts'),
            ('True', 'Group Accounts Only'),
            ('False', 'Detail Accounts Only')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class BulkAccountImportForm(forms.Form):
    """Form for bulk importing accounts from CSV/Excel"""
    file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls'
        }),
        help_text="Upload CSV or Excel file with account data"
    )
    
    template = forms.ModelChoiceField(
        queryset=AccountTemplate.objects.filter(is_active=True),
        required=False,
        empty_label="No Template",
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Optional: Use a template for validation"
    )
    
    update_existing = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Update existing accounts if they exist"
    )
    
    def clean_file(self):
        file = self.cleaned_data['file']
        if file:
            # Check file size (max 5MB)
            if file.size > 5 * 1024 * 1024:
                raise ValidationError(_('File size must be less than 5MB.'))
            
            # Check file extension
            allowed_extensions = ['.csv', '.xlsx', '.xls']
            file_extension = file.name.lower()
            if not any(file_extension.endswith(ext) for ext in allowed_extensions):
                raise ValidationError(_('Please upload a CSV or Excel file.'))
        
        return file


class AccountOpeningBalanceForm(forms.Form):
    """Form for setting opening balances"""
    account = forms.ModelChoiceField(
        queryset=ChartOfAccount.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    opening_balance = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01'
        })
    )
    
    balance_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    notes = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Optional notes about this opening balance'
        })
    )