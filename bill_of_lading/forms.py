from django import forms
from django.forms import ModelForm, inlineformset_factory
from .models import HBL, HBLItem, HBLCharge


class HBLForm(ModelForm):
    """Form for creating and editing House Bill of Lading documents"""
    
    class Meta:
        model = HBL
        fields = [
            'mbl_number', 'status', 'shipped_on_board', 'issue_date',
            'shipper', 'consignee', 'notify_party',
            'pre_carriage_by', 'place_of_receipt', 'ocean_vessel',
            'port_of_loading', 'port_of_discharge', 'place_of_delivery', 'terms',
            'description_of_goods', 'number_of_packages', 'package_type',
            'gross_weight', 'measurement',
            'freight_prepaid', 'freight_collect', 'freight_amount', 'currency',
            'remarks', 'special_instructions'
        ]
        widgets = {
            'mbl_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter MBL number'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'shipped_on_board': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'issue_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'shipper': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'consignee': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'notify_party': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'pre_carriage_by': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., BY SEA'
            }),
            'place_of_receipt': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter place of receipt'
            }),
            'ocean_vessel': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter ocean vessel'
            }),
            'port_of_loading': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter port of loading'
            }),
            'port_of_discharge': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter port of discharge'
            }),
            'place_of_delivery': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter place of delivery'
            }),
            'terms': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description_of_goods': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter description of goods'
            }),
            'number_of_packages': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'package_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter package type'
            }),
            'gross_weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'measurement': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'freight_prepaid': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'freight_collect': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'freight_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'currency': forms.Select(attrs={
                'class': 'form-select'
            }),
            'remarks': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter remarks'
            }),
            'special_instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter special instructions'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default currency
        if not self.instance.pk:
            self.fields['currency'].initial = 'USD'
            self.fields['pre_carriage_by'].initial = 'BY SEA'
    
    def clean(self):
        cleaned_data = super().clean()
        freight_prepaid = cleaned_data.get('freight_prepaid')
        freight_collect = cleaned_data.get('freight_collect')
        
        if freight_prepaid and freight_collect:
            raise forms.ValidationError("Freight cannot be both prepaid and collect.")
        
        return cleaned_data


class HBLItemForm(ModelForm):
    """Form for HBL cargo items"""
    
    class Meta:
        model = HBLItem
        fields = [
            'container_no', 'container_size', 'seal_no',
            'number_of_packages', 'package_type', 'custom_package_type',
            'description', 'gross_weight', 'net_weight', 'measurement'
        ]
        widgets = {
            'container_no': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter container number'
            }),
            'container_size': forms.Select(attrs={
                'class': 'form-select'
            }),
            'seal_no': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter seal number'
            }),
            'number_of_packages': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'package_type': forms.Select(attrs={
                'class': 'form-select package-type-select'
            }),
            'custom_package_type': forms.TextInput(attrs={
                'class': 'form-control custom-package-type',
                'placeholder': 'Specify package type'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Enter description'
            }),
            'gross_weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'net_weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'measurement': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
        }


class HBLChargeForm(ModelForm):
    """Form for HBL charges"""
    
    class Meta:
        model = HBLCharge
        fields = ['charge_type', 'amount', 'currency', 'description']
        widgets = {
            'charge_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'currency': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Enter description'
            }),
        }


# Inline formset for HBL items
HBLItemFormSet = inlineformset_factory(
    HBL,
    HBLItem,
    form=HBLItemForm,
    extra=1,
    can_delete=True,
    fields=[
        'container_no', 'container_size', 'seal_no',
        'number_of_packages', 'package_type', 'custom_package_type',
        'description', 'gross_weight', 'net_weight', 'measurement'
    ]
)


# Inline formset for HBL charges
HBLChargeFormSet = inlineformset_factory(
    HBL,
    HBLCharge,
    form=HBLChargeForm,
    extra=1,
    can_delete=True,
    fields=['charge_type', 'amount', 'currency', 'description']
)


class HBLSearchForm(forms.Form):
    """Form for searching HBL documents"""
    
    SEARCH_CHOICES = [
        ('hbl_number', 'HBL Number'),
        ('mbl_number', 'MBL Number'),
        ('shipper', 'Shipper'),
        ('consignee', 'Consignee'),
        ('notify_party', 'Notify Party'),
        ('ocean_vessel', 'Ocean Vessel'),
        ('container_no', 'Container Number'),
    ]
    
    search_term = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter search term...'
        })
    )
    
    search_field = forms.ChoiceField(
        choices=SEARCH_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + HBL.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
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
    
    terms = forms.ChoiceField(
        choices=[('', 'All Terms')] + HBL.TERMS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )


class HBLReportForm(forms.Form):
    """Form for generating HBL reports"""
    
    REPORT_TYPE_CHOICES = [
        ('summary', 'Summary Report'),
        ('detailed', 'Detailed Report'),
        ('custom', 'Custom Report'),
    ]
    
    report_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter report name'
        })
    )
    
    report_type = forms.ChoiceField(
        choices=REPORT_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
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
    
    mbl_number = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'MBL Number'
        })
    )
    
    hbl_number = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'HBL Number'
        })
    )
    
    container_no = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Container Number'
        })
    )
    
    customer = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Customer'
        })
    )
    
    shipper = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Shipper'
        })
    )
    
    consignee = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Consignee'
        })
    )
    
    description = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Description'
        })
    )
    
    port_loading = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Port of Loading'
        })
    )
    
    port_discharge = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Port of Discharge'
        })
    )
