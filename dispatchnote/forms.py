from django import forms
from django.core.exceptions import ValidationError
from .models import DispatchNote, DispatchItem
from customer.models import Customer
from job.models import Job
from items.models import Item
from delivery_order.models import DeliveryOrder
from facility.models import Facility
import datetime

class DispatchNoteForm(forms.ModelForm):
    """Form for creating and editing dispatch notes"""
    
    # Define facility and mode as ChoiceField at class level
    facility = forms.ChoiceField(
        choices=[('', 'Select Facility')],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'placeholder': 'Select Facility'
        })
    )
    
    mode = forms.ChoiceField(
        choices=[
            ('', 'Select Mode'),
            ('road', 'Road'),
            ('air', 'Air'),
            ('sea', 'Sea'),
            ('rail', 'Rail'),
        ],
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'placeholder': 'Select Mode'
        })
    )
    
    class Meta:
        model = DispatchNote
        fields = [
            'dispatch_date', 'customer', 'delivery_order', 'job', 'deliver_to', 'deliver_address', 'facility',
            'mode', 'vehicle_no', 'name', 'contact_number', 'status', 'notes'
        ]
        widgets = {
            'dispatch_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'customer': forms.Select(attrs={
                'class': 'form-control select2',
                'data-placeholder': 'Select Customer'
            }),
            'delivery_order': forms.Select(attrs={
                'class': 'form-control select2',
                'data-placeholder': 'Select Delivery Order'
            }),
            'job': forms.Select(attrs={
                'class': 'form-control select2',
                'data-placeholder': 'Select Job (Optional)'
            }),
            'deliver_to': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Deliver To'
            }),
            'deliver_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Deliver Address'
            }),
            'vehicle_no': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Vehicle Number'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Name'
            }),
            'contact_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contact Number'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Additional notes...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter customers to only those who have delivery orders
        customers_with_do = Customer.objects.filter(
            is_active=True,
            deliveryorder__status__in=['draft', 'pending', 'in_progress', 'shipped']
        ).distinct()
        self.fields['customer'].queryset = customers_with_do
        
        # Filter delivery orders based on selected customer
        if self.instance.pk and self.instance.customer:
            # For existing instances
            self.fields['delivery_order'].queryset = DeliveryOrder.objects.filter(
                customer=self.instance.customer,
                status__in=['draft', 'pending', 'in_progress', 'shipped']
            )
        elif self.is_bound and self.data.get('customer'):
            # For form validation with POST data
            try:
                customer_id = self.data.get('customer')
                customer = Customer.objects.get(id=customer_id)
                self.fields['delivery_order'].queryset = DeliveryOrder.objects.filter(
                    customer=customer,
                    status__in=['draft', 'pending', 'in_progress', 'shipped']
                )
            except (Customer.DoesNotExist, ValueError):
                self.fields['delivery_order'].queryset = DeliveryOrder.objects.none()
        else:
            # For new forms
            self.fields['delivery_order'].queryset = DeliveryOrder.objects.none()
        
        # Filter jobs to only active ones
        self.fields['job'].queryset = Job.objects.filter(status__name__in=['Active', 'In Progress'])
        
        # Make job field optional
        self.fields['job'].required = False
        
        # Set facility choices
        facilities = Facility.objects.all()
        facility_choices = [('', 'Select Facility')]
        for facility in facilities:
            facility_choices.append((facility.id, facility.facility_name))
        self.fields['facility'].choices = facility_choices
        
        # Set initial value for dispatch_date to today if not set
        if not self.is_bound and not self.initial.get('dispatch_date') and not getattr(self.instance, 'dispatch_date', None):
            self.initial['dispatch_date'] = datetime.date.today()
    
    def clean_facility(self):
        """Convert facility ID to facility name for saving"""
        facility_id = self.cleaned_data.get('facility')
        if facility_id:
            try:
                facility = Facility.objects.get(id=facility_id)
                return facility.facility_name
            except Facility.DoesNotExist:
                raise ValidationError('Selected facility does not exist.')
        return ''
    
    def clean(self):
        cleaned_data = super().clean()
        customer = cleaned_data.get('customer')
        delivery_order = cleaned_data.get('delivery_order')
        job = cleaned_data.get('job')
        
        # If delivery order is selected, validate it belongs to the customer
        if delivery_order and customer:
            if delivery_order.customer != customer:
                raise ValidationError({
                    'delivery_order': 'The selected delivery order does not belong to the selected customer.'
                })
        
        # If job is selected, validate it belongs to the customer
        if job and customer:
            if job.customer_name != customer:
                raise ValidationError({
                    'job': 'The selected job does not belong to the selected customer.'
                })
        
        return cleaned_data


class DispatchItemForm(forms.ModelForm):
    """Form for creating and editing dispatch items"""
    
    class Meta:
        model = DispatchItem
        fields = [
            'grn_no', 'item_code', 'item', 'item_name', 'hs_code', 'unit', 'quantity',
            'coo', 'n_weight', 'g_weight', 'cbm', 'p_date', 'e_date', 'color', 'size',
            'barcode', 'rate', 'amount', 'ed_cntr', 'ed', 'ctnr'
        ]
        widgets = {
            'grn_no': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'GRN No'
            }),
            'item_code': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Item Code'
            }),
            'item': forms.Select(attrs={
                'class': 'form-control form-control-sm select2',
                'data-placeholder': 'Select Item'
            }),
            'item_name': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Item Name'
            }),
            'hs_code': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'HS Code'
            }),
            'unit': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Unit'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'min': '0.01',
                'step': '0.01',
                'placeholder': 'QTY'
            }),
            'coo': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'COO'
            }),
            'n_weight': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'min': '0.00',
                'step': '0.01',
                'placeholder': 'N-weight'
            }),
            'g_weight': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'min': '0.00',
                'step': '0.01',
                'placeholder': 'G-weight'
            }),
            'cbm': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'min': '0.00',
                'step': '0.01',
                'placeholder': 'CBM'
            }),
            'p_date': forms.DateInput(attrs={
                'class': 'form-control form-control-sm',
                'type': 'date'
            }),
            'e_date': forms.DateInput(attrs={
                'class': 'form-control form-control-sm',
                'type': 'date'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Color'
            }),
            'size': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Size'
            }),
            'barcode': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Barcode'
            }),
            'rate': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'min': '0.00',
                'step': '0.01',
                'placeholder': 'Rate'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'min': '0.00',
                'step': '0.01',
                'placeholder': 'Amount',
                'readonly': 'readonly'
            }),
            'ed_cntr': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'ED CNTR'
            }),
            'ed': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'ED'
            }),
            'ctnr': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'CTNR'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter items to only active ones
        self.fields['item'].queryset = Item.objects.filter(is_active=True)
        # Make item field optional since we have item_name
        self.fields['item'].required = False
    
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity and quantity <= 0:
            raise ValidationError('Quantity must be greater than zero.')
        return quantity
    
    def clean_rate(self):
        rate = self.cleaned_data.get('rate')
        if rate and rate < 0:
            raise ValidationError('Rate cannot be negative.')
        return rate


class DispatchNoteSearchForm(forms.Form):
    """Form for searching dispatch notes"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by GDN number, customer, or job...'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + DispatchNote.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.filter(is_active=True),
        required=False,
        empty_label="All Customers",
        widget=forms.Select(attrs={
            'class': 'form-control select2',
            'data-placeholder': 'Select Customer'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'From Date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'To Date'
        })
    ) 