from django import forms
from .models import PaymentSource
from chart_of_accounts.models import ChartOfAccount
from multi_currency.models import Currency
from customer.models import Customer


class PaymentSourceForm(forms.ModelForm):
    """Form for creating and editing payment sources"""
    
    class Meta:
        model = PaymentSource
        fields = [
            'name', 'code', 'description', 'payment_type', 'source_type', 'category',
            'currency', 'linked_ledger', 'default_expense_ledger', 'default_vendor',
            'active', 'remarks'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter payment source name',
                'maxlength': '50'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter short code (optional)',
                'maxlength': '20'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter optional description'
            }),
            'payment_type': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_payment_type'
            }),
            'source_type': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_source_type'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_category'
            }),
            'currency': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_currency'
            }),
            'linked_ledger': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_linked_ledger'
            }),
            'default_expense_ledger': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_default_expense_ledger'
            }),
            'default_vendor': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_default_vendor'
            }),
            'active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'remarks': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter optional remarks'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make name and payment_type required
        self.fields['name'].required = True
        self.fields['payment_type'].required = True
        self.fields['linked_ledger'].required = True
        
        # Set default for active
        if not self.instance.pk:  # Only for new payment sources
            self.fields['active'].initial = True
        
        # Filter linked_ledger choices to only active accounts
        self.fields['linked_ledger'].queryset = ChartOfAccount.objects.filter(
            is_active=True
        ).order_by('account_code', 'name')
        
        # Filter default_expense_ledger choices to only active expense accounts
        self.fields['default_expense_ledger'].queryset = ChartOfAccount.objects.filter(
            is_active=True,
            account_type__category='EXPENSE'
        ).order_by('account_code', 'name')
        
        # Filter default_vendor choices to only active vendor customers
        try:
            from customer.models import CustomerType
            vendor_type = CustomerType.objects.filter(code='VEN').first()
            if vendor_type:
                self.fields['default_vendor'].queryset = Customer.objects.filter(
                    customer_types=vendor_type,
                    is_active=True
                ).order_by('customer_name')
            else:
                self.fields['default_vendor'].queryset = Customer.objects.none()
        except:
            self.fields['default_vendor'].queryset = Customer.objects.none()
        
        # Filter currency choices to only active currencies
        self.fields['currency'].queryset = Currency.objects.filter(
            is_active=True
        ).order_by('code')
        
        # Add empty choice for optional fields
        self.fields['default_expense_ledger'].empty_label = "Select an expense account (optional)"
        self.fields['default_vendor'].empty_label = "Select a vendor (optional)"
        self.fields['currency'].empty_label = "Select a currency (optional)"
        
        # Add help text
        self.fields['code'].help_text = "Optional unique short code for this payment source"
        self.fields['source_type'].help_text = "Type of payment source (should match payment type)"
        self.fields['category'].help_text = "Category classification of the payment source"
        self.fields['linked_ledger'].help_text = "Required: Chart of Account linked to this payment source"
        self.fields['default_expense_ledger'].help_text = "Optional: Default expense account for this payment source"
        self.fields['default_vendor'].help_text = "Optional: Default vendor for this payment source"
        self.fields['currency'].help_text = "Optional: Currency for this payment source (required if multi-currency is enabled)"
        self.fields['remarks'].help_text = "Optional additional notes or remarks"
    
    def clean_name(self):
        """Validate that name is unique (case-insensitive)"""
        name = self.cleaned_data.get('name')
        if name:
            # Check for existing payment sources with the same name (case-insensitive)
            existing = PaymentSource.objects.filter(name__iexact=name)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise forms.ValidationError(
                    "A payment source with this name already exists."
                )
        return name
    
    def clean_code(self):
        """Validate that code is unique if provided (case-insensitive)"""
        code = self.cleaned_data.get('code')
        if code:
            # Check for existing payment sources with the same code (case-insensitive)
            existing = PaymentSource.objects.filter(code__iexact=code)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise forms.ValidationError(
                    "A payment source with this code already exists."
                )
        return code
    
    def clean(self):
        """Additional validation"""
        cleaned_data = super().clean()
        payment_type = cleaned_data.get('payment_type')
        source_type = cleaned_data.get('source_type')
        linked_ledger = cleaned_data.get('linked_ledger')
        
        # Validate source_type matches payment_type for consistency
        if payment_type and source_type:
            if payment_type == 'prepaid' and source_type != 'prepaid':
                self.add_error('source_type', 
                    'Source type should match payment type for consistency.')
            elif payment_type == 'postpaid' and source_type != 'postpaid':
                self.add_error('source_type', 
                    'Source type should match payment type for consistency.')
        
        # Validate that linked_ledger is provided
        if not linked_ledger:
            # Try to get default linked account
            instance = self.instance
            if instance.pk:  # Existing instance
                instance.payment_type = payment_type
                default_account = instance.get_default_linked_account()
                if default_account:
                    cleaned_data['linked_ledger'] = default_account
                else:
                    self.add_error('linked_ledger', 
                        'Please select a linked ledger or ensure appropriate accounts exist in Chart of Accounts.')
            else:
                # For new instances, create a temporary one to get default
                temp_instance = PaymentSource(payment_type=payment_type)
                default_account = temp_instance.get_default_linked_account()
                if default_account:
                    cleaned_data['linked_ledger'] = default_account
                else:
                    self.add_error('linked_ledger', 
                        'Please select a linked ledger or ensure appropriate accounts exist in Chart of Accounts.')
        
        return cleaned_data


class PaymentSourceSearchForm(forms.Form):
    """Form for searching payment sources"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, code, or description...'
        })
    )
    
    source_type = forms.ChoiceField(
        choices=[('', 'All Source Types')] + PaymentSource.SOURCE_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    category = forms.ChoiceField(
        choices=[('', 'All Categories')] + PaymentSource.CATEGORY_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    payment_type = forms.ChoiceField(
        choices=[('', 'All Payment Types')] + PaymentSource.PAYMENT_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    is_active = forms.ChoiceField(
        choices=[
            ('all', 'All'),
            ('active', 'Active Only'),
            ('inactive', 'Inactive Only')
        ],
        required=False,
        initial='all',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    def clean_search(self):
        """Clean and validate search field"""
        search = self.cleaned_data.get('search')
        if search:
            return search.strip()
        return search
