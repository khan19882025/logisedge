from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import TransactionTagging, DefaultCostCenterMapping, TransactionTaggingRule, TransactionTaggingReport
from cost_center_management.models import CostCenter


class TransactionTaggingForm(forms.ModelForm):
    """Form for creating and updating transaction taggings"""
    
    class Meta:
        model = TransactionTagging
        fields = [
            'reference_number', 'transaction_type', 'cost_center', 'amount',
            'currency', 'transaction_date', 'description', 'status'
        ]
        widgets = {
            'reference_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter reference number (e.g., INV-001, PO-123)'
            }),
            'transaction_type': forms.Select(attrs={
                'class': 'form-control',
                'id': 'transaction_type'
            }),
            'cost_center': forms.Select(attrs={
                'class': 'form-control',
                'id': 'cost_center'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'currency': forms.Select(attrs={
                'class': 'form-control'
            }, choices=[('AED', 'AED'), ('USD', 'USD'), ('EUR', 'EUR')]),
            'transaction_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter transaction description'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter only active cost centers
        self.fields['cost_center'].queryset = CostCenter.objects.filter(is_active=True)
        
        # Set default date to today
        if not self.instance.pk:
            self.fields['transaction_date'].initial = timezone.now().date()
    
    def clean(self):
        cleaned_data = super().clean()
        cost_center = cleaned_data.get('cost_center')
        transaction_date = cleaned_data.get('transaction_date')
        status = cleaned_data.get('status')
        
        # Validate cost center is active
        if cost_center and not cost_center.is_active:
            raise ValidationError("Cannot tag transaction to inactive cost center")
        
        # Validate cost center is not expired
        if cost_center and cost_center.end_date and transaction_date:
            if transaction_date > cost_center.end_date:
                raise ValidationError("Cannot tag transaction to expired cost center")
        
        # Validate amount is positive
        amount = cleaned_data.get('amount')
        if amount and amount <= 0:
            raise ValidationError("Amount must be greater than zero")
        
        return cleaned_data


class DefaultCostCenterMappingForm(forms.ModelForm):
    """Form for creating and updating default cost center mappings"""
    
    class Meta:
        model = DefaultCostCenterMapping
        fields = ['mapping_type', 'entity_id', 'entity_name', 'cost_center', 'is_active']
        widgets = {
            'mapping_type': forms.Select(attrs={
                'class': 'form-control',
                'id': 'mapping_type'
            }),
            'entity_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter entity ID'
            }),
            'entity_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter entity name'
            }),
            'cost_center': forms.Select(attrs={
                'class': 'form-control'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter only active cost centers
        self.fields['cost_center'].queryset = CostCenter.objects.filter(is_active=True)
    
    def clean(self):
        cleaned_data = super().clean()
        mapping_type = cleaned_data.get('mapping_type')
        entity_id = cleaned_data.get('entity_id')
        cost_center = cleaned_data.get('cost_center')
        
        # Validate cost center is active
        if cost_center and not cost_center.is_active:
            raise ValidationError("Cannot map to inactive cost center")
        
        # Check for duplicate mapping
        if mapping_type and entity_id:
            existing = DefaultCostCenterMapping.objects.filter(
                mapping_type=mapping_type,
                entity_id=entity_id
            ).exclude(pk=self.instance.pk if self.instance.pk else None)
            
            if existing.exists():
                raise ValidationError(f"A mapping already exists for {mapping_type} with ID {entity_id}")
        
        return cleaned_data


class TransactionTaggingRuleForm(forms.ModelForm):
    """Form for creating and updating transaction tagging rules"""
    
    class Meta:
        model = TransactionTaggingRule
        fields = ['rule_name', 'rule_type', 'transaction_type', 'account_type', 'cost_center', 'priority', 'is_active']
        widgets = {
            'rule_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter rule name'
            }),
            'rule_type': forms.Select(attrs={
                'class': 'form-control',
                'id': 'rule_type'
            }),
            'transaction_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'account_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter account type (optional)'
            }),
            'cost_center': forms.Select(attrs={
                'class': 'form-control'
            }),
            'priority': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '100'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter only active cost centers
        self.fields['cost_center'].queryset = CostCenter.objects.filter(is_active=True)
    
    def clean(self):
        cleaned_data = super().clean()
        cost_center = cleaned_data.get('cost_center')
        
        # Validate cost center is active
        if cost_center and not cost_center.is_active:
            raise ValidationError("Cannot create rule for inactive cost center")
        
        return cleaned_data


class TransactionTaggingReportForm(forms.ModelForm):
    """Form for creating transaction tagging reports"""
    
    class Meta:
        model = TransactionTaggingReport
        fields = ['report_name', 'report_type', 'cost_center', 'start_date', 'end_date']
        widgets = {
            'report_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter report name'
            }),
            'report_type': forms.Select(attrs={
                'class': 'form-control',
                'id': 'report_type'
            }),
            'cost_center': forms.Select(attrs={
                'class': 'form-control'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter only active cost centers
        self.fields['cost_center'].queryset = CostCenter.objects.filter(is_active=True)
        
        # Set default dates
        if not self.instance.pk:
            today = timezone.now().date()
            self.fields['start_date'].initial = today.replace(day=1)  # First day of current month
            self.fields['end_date'].initial = today
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        # Validate date range
        if start_date and end_date and start_date > end_date:
            raise ValidationError("Start date cannot be after end date")
        
        return cleaned_data


class TransactionTaggingSearchForm(forms.Form):
    """Form for searching transaction taggings"""
    transaction_id = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Transaction ID'
        })
    )
    reference_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Reference Number'
        })
    )
    transaction_type = forms.ChoiceField(
        choices=[('', 'All Types')] + TransactionTagging.TRANSACTION_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    cost_center = forms.ModelChoiceField(
        queryset=CostCenter.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + TransactionTagging.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    min_amount = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0'
        })
    )
    max_amount = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0'
        })
    )


class BulkTransactionTaggingForm(forms.Form):
    """Form for bulk transaction tagging"""
    transaction_ids = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Enter transaction IDs, one per line'
        }),
        help_text="Enter transaction IDs separated by new lines"
    )
    cost_center = forms.ModelChoiceField(
        queryset=CostCenter.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select the cost center to assign to all transactions"
    )
    
    def clean_transaction_ids(self):
        transaction_ids = self.cleaned_data['transaction_ids']
        if not transaction_ids.strip():
            raise ValidationError("Please enter at least one transaction ID")
        
        # Split and clean transaction IDs
        ids = [tid.strip() for tid in transaction_ids.split('\n') if tid.strip()]
        if not ids:
            raise ValidationError("Please enter at least one valid transaction ID")
        
        return ids
