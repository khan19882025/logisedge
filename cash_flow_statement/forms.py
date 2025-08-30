from django import forms
from django.contrib.auth.models import User
from .models import CashFlowStatement, CashFlowTemplate, CashFlowCategory, CashFlowItem
from company.company_model import Company
from fiscal_year.models import FiscalYear
from multi_currency.models import Currency
from chart_of_accounts.models import ChartOfAccount
from django.utils import timezone
from datetime import datetime, timedelta


class CashFlowStatementForm(forms.ModelForm):
    """Form for creating and editing cash flow statements"""
    
    class Meta:
        model = CashFlowStatement
        fields = [
            'name', 'description', 'from_date', 'to_date', 'currency',
            'report_type', 'export_format', 'include_comparative',
            'include_notes', 'include_charts'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter report name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter report description'
            }),
            'from_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'to_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'currency': forms.Select(attrs={
                'class': 'form-control'
            }),
            'report_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'export_format': forms.Select(attrs={
                'class': 'form-control'
            }),
            'include_comparative': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'include_notes': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'include_charts': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        # Set default dates
        if not self.instance.pk:
            today = timezone.now().date()
            self.fields['from_date'].initial = today.replace(day=1)
            self.fields['to_date'].initial = today
        
        # Filter currencies by company
        if company:
            self.fields['currency'].queryset = Currency.objects.filter(is_active=True)
        
        # Set default currency to AED
        if not self.instance.pk:
            try:
                aed_currency = Currency.objects.filter(code='AED').first()
                if aed_currency:
                    self.fields['currency'].initial = aed_currency
            except:
                pass
    
    def clean(self):
        cleaned_data = super().clean()
        from_date = cleaned_data.get('from_date')
        to_date = cleaned_data.get('to_date')
        
        if from_date and to_date:
            if from_date > to_date:
                raise forms.ValidationError("End date must be after start date")
            
            # Check if period is reasonable (not more than 5 years)
            if (to_date - from_date).days > 1825:  # 5 years
                raise forms.ValidationError("Report period cannot exceed 5 years")
        
        return cleaned_data


class QuickCashFlowForm(forms.Form):
    """Quick form for generating cash flow statements"""
    
    from_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='From Date'
    )
    
    to_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='To Date'
    )
    
    currency = forms.ModelChoiceField(
        queryset=Currency.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Currency'
    )
    
    report_type = forms.ChoiceField(
        choices=CashFlowStatement.REPORT_TYPES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        initial='DETAILED',
        label='Report Type'
    )
    
    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        # Set default dates
        today = timezone.now().date()
        self.fields['from_date'].initial = today.replace(day=1)
        self.fields['to_date'].initial = today
        
        # Set default currency to AED
        try:
            aed_currency = Currency.objects.filter(code='AED').first()
            if aed_currency:
                self.fields['currency'].initial = aed_currency
        except:
            pass
    
    def clean(self):
        cleaned_data = super().clean()
        from_date = cleaned_data.get('from_date')
        to_date = cleaned_data.get('to_date')
        
        if from_date and to_date:
            if from_date > to_date:
                raise forms.ValidationError("End date must be after start date")
        
        return cleaned_data


class CashFlowTemplateForm(forms.ModelForm):
    """Form for creating and editing cash flow templates"""
    
    class Meta:
        model = CashFlowTemplate
        fields = [
            'name', 'description', 'template_type',
            'include_operating_activities', 'include_investing_activities', 'include_financing_activities',
            'custom_operating_items', 'custom_investing_items', 'custom_financing_items',
            'is_active', 'is_public'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter template name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter template description'
            }),
            'template_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'include_operating_activities': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'include_investing_activities': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'include_financing_activities': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make JSON fields more user-friendly
        self.fields['custom_operating_items'].widget = forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter custom operating items (JSON format)'
        })
        self.fields['custom_investing_items'].widget = forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter custom investing items (JSON format)'
        })
        self.fields['custom_financing_items'].widget = forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter custom financing items (JSON format)'
        })


class CashFlowCategoryForm(forms.ModelForm):
    """Form for creating and editing cash flow categories"""
    
    class Meta:
        model = CashFlowCategory
        fields = ['name', 'category_type', 'description', 'display_order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter category name'
            }),
            'category_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter category description'
            }),
            'display_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class CashFlowItemForm(forms.ModelForm):
    """Form for creating and editing cash flow items"""
    
    class Meta:
        model = CashFlowItem
        fields = [
            'name', 'category', 'item_type', 'calculation_method',
            'account_codes', 'display_order', 'is_active', 'is_subtotal'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter item name'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'item_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'calculation_method': forms.Select(attrs={
                'class': 'form-control'
            }),
            'display_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_subtotal': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make account_codes field more user-friendly
        self.fields['account_codes'].widget = forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter account codes (comma-separated)'
        })
        
        # Filter categories by active status
        self.fields['category'].queryset = CashFlowCategory.objects.filter(is_active=True)
    
    def clean_account_codes(self):
        """Convert comma-separated account codes to list"""
        account_codes = self.cleaned_data.get('account_codes')
        if isinstance(account_codes, str):
            # Convert comma-separated string to list
            codes = [code.strip() for code in account_codes.split(',') if code.strip()]
            return codes
        return account_codes 