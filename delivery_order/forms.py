from django import forms
from .models import DeliveryOrder, DeliveryOrderItem
from customer.models import Customer
from facility.models import Facility, FacilityLocation
from items.models import Item
from salesman.models import Salesman
from grn.models import GRN

class DeliveryOrderForm(forms.ModelForm):
    class Meta:
        model = DeliveryOrder
        fields = [
            'do_number', 'document_type', 'customer', 'customer_ref', 'facility', 'grn',
            'bill_to', 'bill_to_address', 'deliver_to_address',
            'port_of_loading', 'discharge_port',
            'delivery_contact', 'delivery_phone', 'delivery_email',
            'date',
            'payment_mode', 'container', 'bl_number', 'boe',
            'exit_point', 'destination', 'ship_mode', 'ship_date',
            'vessel', 'voyage', 'delivery_terms',
            'shipping_method', 'tracking_number', 'carrier',
            'notes', 'special_instructions', 'assigned_to'
        ]
        widgets = {
            'do_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Auto-generated',
                'readonly': 'readonly'
            }),
            'document_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Document Type'
            }),
            'customer': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Select Customer'
            }),
            'customer_ref': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Customer Reference'
            }),
            'facility': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Select Facility'
            }),
            'grn': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Select Related GRN (Optional)'
            }),
            'bill_to': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Bill To'
            }),
            'bill_to_address': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Bill to Address',
                'rows': 3
            }),
            'deliver_to_address': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Deliver to Address',
                'rows': 3
            }),
            'port_of_loading': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Port of Loading'
            }),
            'discharge_port': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Discharge Port'
            }),
            'delivery_contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Delivery Contact Person'
            }),
            'delivery_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Delivery Phone Number'
            }),
            'delivery_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Delivery Email Address'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'payment_mode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Payment Mode'
            }),
            'container': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Container'
            }),
            'bl_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'BL Number'
            }),
            'boe': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'BOE'
            }),
            'exit_point': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Exit Point'
            }),
            'destination': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Destination'
            }),
            'ship_mode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ship Mode'
            }),
            'ship_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'vessel': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Vessel'
            }),
            'voyage': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Voyage'
            }),
            'delivery_terms': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Delivery Terms'
            }),
            'shipping_method': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Shipping Method'
            }),
            'tracking_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tracking Number'
            }),
            'carrier': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Carrier Name'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Notes',
                'rows': 3
            }),
            'special_instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Special Instructions',
                'rows': 3
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Select Salesman'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter customers to show only those with available GRNs (draft or received status)
        customers_with_grns = Customer.objects.filter(
            grn__status__in=['draft', 'received']
        ).distinct().order_by('customer_name')
        
        # Filter querysets
        self.fields['customer'].queryset = customers_with_grns
        self.fields['facility'].queryset = Facility.objects.all().order_by('facility_name')
        self.fields['grn'].queryset = GRN.objects.filter(status__in=['draft', 'received']).order_by('-grn_date')
        self.fields['assigned_to'].queryset = Salesman.objects.all().order_by('first_name', 'last_name')
        
        # Make some fields required
        self.fields['customer'].required = True
        self.fields['deliver_to_address'].required = True
        self.fields['date'].required = True


class DeliveryOrderItemForm(forms.ModelForm):
    class Meta:
        model = DeliveryOrderItem
        fields = ['item', 'requested_qty', 'source_location', 'unit_price', 'production_date', 'expiry_date', 'notes']
        widgets = {
            'item': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Select Item'
            }),
            'requested_qty': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Requested Quantity',
                'step': '0.01',
                'min': '0'
            }),
            'source_location': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Select Source Location'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Unit Price',
                'step': '0.01',
                'min': '0'
            }),
            'production_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'placeholder': 'Production Date'
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'placeholder': 'Expiry Date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Item Notes',
                'rows': 2
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter querysets
        self.fields['item'].queryset = Item.objects.all().order_by('item_name')
        self.fields['source_location'].queryset = FacilityLocation.objects.all().order_by('location_name')
        
        # Make required fields
        self.fields['item'].required = True
        self.fields['requested_qty'].required = True


# Inline formset for delivery order items
DeliveryOrderItemFormSet = forms.inlineformset_factory(
    DeliveryOrder,
    DeliveryOrderItem,
    form=DeliveryOrderItemForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
) 