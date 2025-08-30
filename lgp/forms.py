from django import forms
from django.forms import inlineformset_factory
from .models import LGP, LGPItem, LGPDispatch, PackageType
from customer.models import Customer
from facility.models import Facility


class LGPForm(forms.ModelForm):
    """Form for creating and editing LGP"""
    
    class Meta:
        model = LGP
        fields = [
            'customer', 'dpw_ref_no', 'document_date', 'document_validity_date',
            'warehouse', 'free_zone_company_name', 'local_company_name',
            'goods_coming_from', 'purpose_of_entry', 'notes'
        ]
        widgets = {
            'customer': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'dpw_ref_no': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter DPW Reference Number'
            }),
            'document_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'document_validity_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'warehouse': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'free_zone_company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Free Zone Company Name'
            }),
            'local_company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Local Company Name'
            }),
            'goods_coming_from': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Goods Coming From'
            }),
            'purpose_of_entry': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes (optional)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set queryset for dropdowns
        self.fields['customer'].queryset = Customer.objects.filter(is_active=True).order_by('customer_name')
        self.fields['warehouse'].queryset = Facility.objects.filter(status='active').order_by('facility_name')
        
        # Make certain fields required
        self.fields['customer'].required = True
        self.fields['warehouse'].required = True
        self.fields['dpw_ref_no'].required = True
        self.fields['document_date'].required = True
        self.fields['document_validity_date'].required = True
        self.fields['free_zone_company_name'].required = True
        self.fields['local_company_name'].required = True
        self.fields['goods_coming_from'].required = True
        self.fields['purpose_of_entry'].required = True


class LGPItemForm(forms.ModelForm):
    """Form for LGP items"""
    
    class Meta:
        model = LGPItem
        fields = [
            'line_number', 'hs_code', 'good_description', 'marks_and_nos',
            'package_type_new', 'package_type', 'quantity', 'weight', 'volume', 'value',
            'customs_declaration', 'remarks'
        ]
        widgets = {
            'line_number': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'min': '1'
            }),
            'hs_code': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'HS Code'
            }),
            'good_description': forms.Textarea(attrs={
                'class': 'form-control form-control-sm',
                'rows': 2,
                'placeholder': 'Good Description'
            }),
            'marks_and_nos': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Marks & Nos'
            }),
            'package_type_new': forms.Select(attrs={
                'class': 'form-select form-select-sm'
            }),
            'package_type': forms.Select(attrs={
                'class': 'form-select form-select-sm'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'step': '0.01',
                'min': '0'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'step': '0.001',
                'min': '0',
                'placeholder': 'KG'
            }),
            'volume': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'step': '0.001',
                'min': '0',
                'placeholder': 'CBM'
            }),
            'value': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'step': '0.01',
                'min': '0'
            }),
            'customs_declaration': forms.Textarea(attrs={
                'class': 'form-control form-control-sm',
                'rows': 2,
                'placeholder': 'Customs Declaration'
            }),
            'remarks': forms.Textarea(attrs={
                'class': 'form-control form-control-sm',
                'rows': 2,
                'placeholder': 'Remarks'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set queryset for package types
        self.fields['package_type_new'].queryset = PackageType.objects.filter(is_active=True).order_by('name')
        self.fields['package_type_new'].empty_label = "Select Package Type"
        
        # Make package_type_new required and package_type optional for backward compatibility
        self.fields['package_type_new'].required = False  # Will be handled by JavaScript
        self.fields['package_type'].required = False
        
        # Make specified fields non-mandatory
        self.fields['marks_and_nos'].required = False
        self.fields['volume'].required = False
        self.fields['customs_declaration'].required = False
        self.fields['remarks'].required = False


# Create the inline formset for LGP items
LGPItemFormSet = inlineformset_factory(
    LGP,
    LGPItem,
    form=LGPItemForm,
    extra=0,
    min_num=1,
    validate_min=True,
    can_delete=True,
    fields=[
        'line_number', 'hs_code', 'good_description', 'marks_and_nos',
        'package_type_new', 'package_type', 'quantity', 'weight', 'volume', 'value',
        'customs_declaration', 'remarks'
    ]
)


class LGPDispatchForm(forms.ModelForm):
    """Form for dispatching LGP"""
    
    class Meta:
        model = LGP
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Add dispatch notes (optional)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['notes'].label = 'Dispatch Notes'
        self.fields['notes'].required = False


class LGPSearchForm(forms.Form):
    """Form for searching LGPs"""
    
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by LGP number, customer name, DPW ref, or good description...'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + LGP.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.filter(is_active=True).order_by('customer_name'),
        required=False,
        empty_label='All Customers',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    warehouse = forms.ModelChoiceField(
        queryset=Facility.objects.filter(status='active').order_by('facility_name'),
        required=False,
        empty_label='All Warehouses',
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