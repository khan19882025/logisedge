from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone
from .models import GRN, GRNItem
from customer.models import Customer
from facility.models import Facility
from items.models import Item
from job.models import Job
from salesman.models import Salesman


class GRNForm(forms.ModelForm):
    """Form for GRN model"""
    
    class Meta:
        model = GRN
        fields = [
            'description', 'customer', 'customer_ref', 'facility', 'job_ref', 'mode', 'total_qty',
            'document_type', 'reference_number',
            'supplier_name', 'supplier_address', 'supplier_phone', 'supplier_email',
            'grn_date', 'expected_date', 'received_date',
            'vessel', 'voyage', 'container_number', 'seal_number', 'bl_number',
            'driver_name', 'contact_no', 'vehicle_no',
            'status', 'priority',
            'total_packages', 'total_weight', 'total_volume',
            'notes', 'special_instructions', 'assigned_to'
        ]
        widgets = {
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter description'
            }),
            'customer': forms.Select(attrs={
                'class': 'form-select',
                'id': 'customer-select'
            }),
            'customer_ref': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter customer reference'
            }),
            'facility': forms.Select(attrs={
                'class': 'form-select'
            }),
            'job_ref': forms.Select(attrs={
                'class': 'form-select',
                'id': 'job_ref'
            }),
            'mode': forms.Select(attrs={
                'class': 'form-select'
            }),
            'total_qty': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter total quantity',
                'step': '0.01'
            }),
            'document_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'reference_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter reference number'
            }),
            'supplier_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter supplier name'
            }),
            'supplier_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter supplier address'
            }),
            'supplier_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter supplier phone'
            }),
            'supplier_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter supplier email'
            }),
            'grn_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'expected_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'received_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'vessel': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter vessel name'
            }),
            'voyage': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter voyage number'
            }),
            'container_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter container number'
            }),
            'seal_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter seal number'
            }),
            'bl_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter BL number'
            }),
            'driver_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter driver name'
            }),
            'contact_no': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter contact number'
            }),
            'vehicle_no': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter vehicle number'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'total_packages': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter total packages'
            }),
            'total_weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter total weight (KGS)',
                'step': '0.01'
            }),
            'total_volume': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter total volume (CBM)',
                'step': '0.01'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter notes'
            }),
            'special_instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter special instructions'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial values
        if not self.instance.pk:
            self.fields['grn_date'].initial = timezone.now().date()
            self.fields['status'].initial = 'draft'
            self.fields['priority'].initial = 'medium'
        
        # Make essential fields required
        self.fields['customer'].required = True
        self.fields['grn_date'].required = True
        
        # Add required field styling
        for field_name in ['customer', 'grn_date']:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs['class'] = self.fields[field_name].widget.attrs.get('class', '') + ' required-field'
        
        # Filter job_ref field to only show inbound and warehousing jobs
        if 'job_ref' in self.fields:
            self.fields['job_ref'].queryset = Job.objects.filter(
                job_type__in=['Inbound', 'Warehousing']
            ).select_related('customer_name', 'facility', 'assigned_to').order_by('-created_at')
        
        # Set assigned_to field to use Salesman model
        if 'assigned_to' in self.fields:
            self.fields['assigned_to'].queryset = Salesman.objects.all().order_by('first_name')
            self.fields['assigned_to'].empty_label = "Select Salesman"
            # Set custom choice label to show full name
            self.fields['assigned_to'].label_from_instance = lambda obj: f"{obj.get_full_name()}"
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate that at least one item is added
        item_codes = self.data.getlist('item_code[]')
        item_ids = self.data.getlist('item[]')
        
        has_items = False
        for i in range(len(item_codes)):
            if item_codes[i] or item_ids[i]:
                has_items = True
                break
        
        # Make item validation optional for now
        if not has_items:
            print("Warning: No items added to GRN")
        
        return cleaned_data


class GRNItemForm(forms.ModelForm):
    """Form for GRN items"""
    
    class Meta:
        model = GRNItem
        fields = [
            'item', 'item_code', 'item_name', 'hs_code', 'unit',
            'expected_qty', 'received_qty', 'damaged_qty', 'short_qty',
            'net_weight', 'gross_weight', 'volume',
            'coo', 'batch_number', 'expiry_date', 'remark'
        ]
        widgets = {
            'item': forms.Select(attrs={
                'class': 'form-select item-select'
            }),
            'item_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Item code'
            }),
            'item_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Item name'
            }),
            'hs_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'HS code'
            }),
            'unit': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Unit'
            }),
            'expected_qty': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Expected quantity',
                'step': '0.01'
            }),
            'received_qty': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Received quantity',
                'step': '0.01'
            }),
            'damaged_qty': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Damaged quantity',
                'step': '0.01'
            }),
            'short_qty': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Short quantity',
                'step': '0.01'
            }),
            'net_weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Net weight (KGS)',
                'step': '0.01'
            }),
            'gross_weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Gross weight (KGS)',
                'step': '0.01'
            }),
            'volume': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Volume (CBM)',
                'step': '0.01'
            }),
            'coo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Country of origin'
            }),
            'batch_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Batch number'
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'remark': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Remark'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default values for quantities
        if not self.instance.pk:
            self.fields['damaged_qty'].initial = 0
            self.fields['short_qty'].initial = 0


# Create inline formset for GRN items
GRNItemFormSet = inlineformset_factory(
    GRN, 
    GRNItem, 
    form=GRNItemForm,
    extra=1,
    can_delete=True,
    fields=[
        'item', 'item_code', 'item_name', 'hs_code', 'unit',
        'expected_qty', 'received_qty', 'damaged_qty', 'short_qty',
        'net_weight', 'gross_weight', 'volume',
        'coo', 'batch_number', 'expiry_date', 'remark'
    ]
) 