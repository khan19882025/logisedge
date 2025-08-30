from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.forms import inlineformset_factory, BaseInlineFormSet
from decimal import Decimal

from .models import (
    DisposalRequest, DisposalItem, DisposalDocument, DisposalApproval,
    DisposalType, ApprovalLevel
)
from asset_register.models import Asset
from chart_of_accounts.models import ChartOfAccount


class DisposalRequestForm(forms.ModelForm):
    """Form for creating and editing disposal requests"""
    
    class Meta:
        model = DisposalRequest
        fields = [
            'title', 'description', 'is_batch', 'disposal_type', 'disposal_date',
            'disposal_value', 'reason', 'remarks', 'asset_account', 'disposal_account',
            'bank_account'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter disposal request title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe the disposal request'
            }),
            'disposal_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'disposal_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Explain the reason for disposal'
            }),
            'remarks': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Additional remarks (optional)'
            }),
            'disposal_type': forms.Select(attrs={'class': 'form-control'}),
            'asset_account': forms.Select(attrs={'class': 'form-control'}),
            'disposal_account': forms.Select(attrs={'class': 'form-control'}),
            'bank_account': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set default disposal date to today
        if not self.instance.pk and not self.data:
            self.fields['disposal_date'].initial = timezone.now().date()
        
        # Filter active disposal types
        self.fields['disposal_type'].queryset = DisposalType.objects.filter(is_active=True)
        
        # Filter asset accounts (Asset accounts)
        self.fields['asset_account'].queryset = ChartOfAccount.objects.filter(
            account_type__name__icontains='asset'
        ).order_by('name')
        
        # Filter disposal accounts (Expense/Loss accounts)
        self.fields['disposal_account'].queryset = ChartOfAccount.objects.filter(
            account_type__name__icontains='expense'
        ).order_by('name')
        
        # Filter bank accounts
        self.fields['bank_account'].queryset = ChartOfAccount.objects.filter(
            account_type__name__icontains='bank'
        ).order_by('name')

    def clean_disposal_date(self):
        """Validate disposal date"""
        disposal_date = self.cleaned_data.get('disposal_date')
        if disposal_date and disposal_date > timezone.now().date():
            raise ValidationError("Disposal date cannot be in the future.")
        return disposal_date

    def clean_disposal_value(self):
        """Validate disposal value"""
        disposal_value = self.cleaned_data.get('disposal_value')
        if disposal_value and disposal_value < 0:
            raise ValidationError("Disposal value cannot be negative.")
        return disposal_value


class DisposalItemForm(forms.ModelForm):
    """Form for individual disposal items"""
    
    class Meta:
        model = DisposalItem
        fields = ['asset', 'disposal_value', 'reason', 'remarks']
        widgets = {
            'asset': forms.Select(attrs={
                'class': 'form-control asset-select',
                'data-live-search': 'true'
            }),
            'disposal_value': forms.NumberInput(attrs={
                'class': 'form-control disposal-value',
                'step': '0.01',
                'min': '0'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Reason for this asset disposal'
            }),
            'remarks': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Additional remarks'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter available assets (not already disposed)
        self.fields['asset'].queryset = Asset.objects.filter(
            is_deleted=False,
            status__name__in=['Active', 'Available']
        ).select_related('category', 'location', 'status').order_by('asset_name')

    def clean_disposal_value(self):
        """Validate disposal value"""
        disposal_value = self.cleaned_data.get('disposal_value')
        if disposal_value and disposal_value < 0:
            raise ValidationError("Disposal value cannot be negative.")
        return disposal_value


class DisposalItemFormSet(BaseInlineFormSet):
    """Formset for disposal items with validation"""
    
    def clean(self):
        """Validate the formset"""
        super().clean()
        
        if not self.forms:
            raise ValidationError("At least one asset must be selected for disposal.")
        
        # Check for duplicate assets
        assets = []
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE'):
                asset = form.cleaned_data.get('asset')
                if asset:
                    if asset in assets:
                        raise ValidationError(f"Asset '{asset.asset_name}' is selected multiple times.")
                    assets.append(asset)


# Create formset for disposal items
DisposalItemFormSet = inlineformset_factory(
    DisposalRequest,
    DisposalItem,
    form=DisposalItemForm,
    formset=DisposalItemFormSet,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)


class AssetSelectionForm(forms.Form):
    """Form for selecting assets from asset register"""
    
    # Search and filter fields
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search assets by name, code, or serial number...'
        })
    )
    
    category = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    location = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="All Locations",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    status = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="All Statuses",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    assigned_to = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="All Users",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Asset selection
    selected_assets = forms.ModelMultipleChoiceField(
        queryset=Asset.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'asset-checkbox'
        }),
        required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set up querysets for filter fields
        from asset_register.models import AssetCategory, AssetLocation, AssetStatus
        
        self.fields['category'].queryset = AssetCategory.objects.all()
        self.fields['location'].queryset = AssetLocation.objects.filter(is_active=True)
        self.fields['status'].queryset = AssetStatus.objects.filter(is_active=True)
        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True)
        
        # Set up asset queryset
        self.fields['selected_assets'].queryset = Asset.objects.filter(
            is_deleted=False,
            status__name__in=['Active', 'Available']
        ).select_related('category', 'location', 'status', 'assigned_to')


class DisposalDocumentForm(forms.ModelForm):
    """Form for uploading disposal documents"""
    
    class Meta:
        model = DisposalDocument
        fields = ['title', 'file']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Document title'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png,.xls,.xlsx'
            })
        }

    def clean_file(self):
        """Validate uploaded file"""
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (max 10MB)
            if file.size > 10 * 1024 * 1024:
                raise ValidationError("File size must be less than 10MB.")
            
            # Check file type
            allowed_types = [
                'application/pdf',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'image/jpeg',
                'image/png',
                'application/vnd.ms-excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            ]
            
            if hasattr(file, 'content_type') and file.content_type not in allowed_types:
                raise ValidationError("Invalid file type. Please upload PDF, Word, Excel, or image files.")
        
        return file


class DisposalApprovalForm(forms.ModelForm):
    """Form for approval actions"""
    
    class Meta:
        model = DisposalApproval
        fields = ['action', 'comments']
        widgets = {
            'action': forms.Select(attrs={
                'class': 'form-control',
                'id': 'approval-action'
            }),
            'comments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter your comments...'
            })
        }

    def __init__(self, *args, **kwargs):
        self.disposal_request = kwargs.pop('disposal_request', None)
        super().__init__(*args, **kwargs)
        
        # Customize action choices based on current status
        if self.disposal_request:
            if self.disposal_request.status == 'pending_approval':
                self.fields['action'].choices = [
                    ('approve', 'Approve'),
                    ('reject', 'Reject'),
                    ('return', 'Return for Revision')
                ]
            else:
                self.fields['action'].choices = [
                    ('approve', 'Approve'),
                    ('reject', 'Reject')
                ]


class DisposalReversalForm(forms.Form):
    """Form for reversing a disposal"""
    
    reversal_reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Explain the reason for reversing this disposal...'
        }),
        help_text="Please provide a detailed explanation for the reversal."
    )
    
    confirm_reversal = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text="I confirm that I want to reverse this disposal and understand the financial implications."
    )


class DisposalSearchForm(forms.Form):
    """Form for searching and filtering disposal requests"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by request ID, title, or asset name...'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + DisposalRequest.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    disposal_type = forms.ModelChoiceField(
        queryset=DisposalType.objects.filter(is_active=True),
        required=False,
        empty_label="All Types",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    created_by = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        empty_label="All Users",
        widget=forms.Select(attrs={'class': 'form-control'})
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
    
    is_batch = forms.ChoiceField(
        choices=[
            ('', 'All'),
            ('True', 'Batch Only'),
            ('False', 'Individual Only')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class BulkDisposalForm(forms.Form):
    """Form for bulk disposal operations"""
    
    disposal_type = forms.ModelChoiceField(
        queryset=DisposalType.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    disposal_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    disposal_value = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': 'Total disposal value (optional)'
        })
    )
    
    asset_account = forms.ModelChoiceField(
        queryset=ChartOfAccount.objects.filter(
            account_type__category='ASSET',
            is_active=True
        ).order_by('name'),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    disposal_account = forms.ModelChoiceField(
        queryset=ChartOfAccount.objects.filter(
            account_type__category='EXPENSE',
            is_active=True
        ).order_by('name'),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Reason for bulk disposal'
        })
    )
    
    remarks = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Additional remarks'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['disposal_date'].initial = timezone.now().date()


class ApprovalLevelForm(forms.ModelForm):
    """Form for managing approval levels"""
    
    class Meta:
        model = ApprovalLevel
        fields = ['name', 'level', 'description', 'required_role', 'min_amount', 'max_amount', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Approval level name'
            }),
            'level': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description of this approval level'
            }),
            'required_role': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Required role or group name'
            }),
            'min_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'max_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def clean(self):
        """Validate approval level"""
        cleaned_data = super().clean()
        min_amount = cleaned_data.get('min_amount')
        max_amount = cleaned_data.get('max_amount')
        
        if min_amount and max_amount and min_amount >= max_amount:
            raise ValidationError("Minimum amount must be less than maximum amount.")
        
        return cleaned_data 