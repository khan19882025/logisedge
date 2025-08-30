from django import forms
from django.forms import inlineformset_factory
from .models import Quotation, QuotationItem


class QuotationForm(forms.ModelForm):
    class Meta:
        model = Quotation
        fields = [
            'customer', 'facility', 'salesman', 'subject', 'description',
            'valid_until', 'additional_tax_amount', 'discount_amount', 'currency',
            'terms_conditions', 'notes'
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'facility': forms.Select(attrs={'class': 'form-select'}),
            'salesman': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'valid_until': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'additional_tax_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'discount_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'currency': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('AED', 'AED - UAE Dirham'),
                ('USD', 'USD - US Dollar'),
                ('EUR', 'EUR - Euro'),
                ('GBP', 'GBP - British Pound'),
            ]),
            'terms_conditions': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 6,
                'placeholder': '1. IF ANY CUSTOM HOLD OR ANY CUSTOM INSPECTION RELATED WORK, CHARGES WILL BE AS PER ACTUAL.\n2. IF CROSS STUFF OR LOAD/OFFLOAD TAKE MORE TIME THAN ACTUAL TIME (SPECIAL CARGO), CHARGES WILL BE APPLICABLE.\n3. IF ANY LINE DETENTION OR PORT DEMURAGE, CHARGES AS PER ACTUAL.\n4. IF IMPORT CONTAINER MECREC, CHARGES WILL BE AS PER ACTUAL.'
            }),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'customer': 'Customer',
            'facility': 'Facility',
            'salesman': 'Salesman',
            'subject': 'Subject',
            'description': 'Description',
            'valid_until': 'Valid Until',
            'additional_tax_amount': 'Additional Tax Amount',
            'discount_amount': 'Discount Amount',
            'currency': 'Currency',
            'terms_conditions': 'Terms & Conditions',
            'notes': 'Notes',
        }
        help_texts = {
            'customer': 'Select the customer for this quotation',
            'facility': 'Select the facility where services will be provided',
            'salesman': 'Select the responsible salesman',
            'subject': 'Brief subject or title for the quotation',
            'description': 'Detailed description of the services or products',
            'valid_until': 'Date until which this quotation is valid',
            'additional_tax_amount': 'Additional tax amount (VAT is calculated automatically)',
            'discount_amount': 'Discount amount to be applied',
            'currency': 'Currency for the quotation',
            'terms_conditions': 'Terms and conditions for this quotation (you can edit or add more)',
            'notes': 'Additional notes or comments',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter customers to only show those with 'Customer' type
        from customer.models import Customer, CustomerType
        
        try:
            customer_type = CustomerType.objects.get(code='CUS')
        except CustomerType.DoesNotExist:
            # Fallback: if CUS doesn't exist, try to get by name
            try:
                customer_type = CustomerType.objects.get(name='Customer')
            except CustomerType.DoesNotExist:
                # If no customer type found, show no customers to prevent showing suppliers
                self.fields['customer'].queryset = Customer.objects.none()
                return
        
        # Filter customers to only show those with 'Customer' type and are active
        self.fields['customer'].queryset = Customer.objects.filter(
            customer_types=customer_type,
            is_active=True
        ).distinct().order_by('customer_name')
        
        # Set default terms and conditions for new quotations
        if not self.instance.pk:  # Only for new quotations
            default_terms = """1. IF ANY CUSTOM HOLD OR ANY CUSTOM INSPECTION RELATED WORK, CHARGES WILL BE AS PER ACTUAL.
2. IF CROSS STUFF OR LOAD/OFFLOAD TAKE MORE TIME THAN ACTUAL TIME (SPECIAL CARGO), CHARGES WILL BE APPLICABLE.
3. IF ANY LINE DETENTION OR PORT DEMURAGE, CHARGES AS PER ACTUAL.
4. IF IMPORT CONTAINER MECREC, CHARGES WILL BE AS PER ACTUAL."""
            
            if not self.initial.get('terms_conditions'):
                self.initial['terms_conditions'] = default_terms


class QuotationItemForm(forms.ModelForm):
    class Meta:
        model = QuotationItem
        fields = ['service', 'description', 'quantity', 'unit_price', 'notes']
        widgets = {
            'service': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        labels = {
            'service': 'Service',
            'description': 'Description',
            'quantity': 'Quantity',
            'unit_price': 'Unit Price',
            'notes': 'Notes',
        }
        help_texts = {
            'service': 'Select the service to include in the quotation',
            'description': 'Custom description for this service',
            'quantity': 'Quantity of the service',
            'unit_price': 'Price per unit',
            'notes': 'Additional notes for this service',
        }


# Create formset for quotation items
QuotationItemFormSet = inlineformset_factory(
    Quotation,
    QuotationItem,
    form=QuotationItemForm,
    extra=1,
    can_delete=True,
    fields=['service', 'description', 'quantity', 'unit_price', 'notes']
)