from django import forms
from django.forms import ModelForm
from .models import CrossStuffing
from job.models import Job
from customer.models import Customer
from facility.models import Facility
from port.models import Port
from django.contrib.auth.models import User


class CrossStuffingForm(ModelForm):
    """Form for creating and editing cross stuffing records"""
    
    class Meta:
        model = CrossStuffing
        fields = [
            # Left section fields
            'cs_number', 'document_type', 'customer', 'job', 'facility', 'bill_to', 'bill_to_customer', 'bill_to_address', 
            'deliver_to_customer', 'deliver_to_address', 'port_of_loading', 'discharge_port',
            # Right section fields
            'cs_date', 'payment_mode', 'container_number', 'bl_number', 'boe', 
            'exit_point', 'destination', 'ship_mode', 'ship_date', 'vessel', 
            'voyage', 'delivery_terms'
        ]
        widgets = {
            # Left section widgets
            'cs_number': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly',
                'placeholder': 'Auto-generated'
            }),
            'document_type': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Select document type'
            }),
            'customer': forms.Select(attrs={
                'class': 'form-select',
                'id': 'customer-select'
            }),
            'job': forms.Select(attrs={
                'class': 'form-select',
                'id': 'job-select',
                'placeholder': 'Select job'
            }),
            'facility': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Select facility'
            }),
            'bill_to': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter bill to party'
            }),
            'bill_to_customer': forms.Select(attrs={
                'class': 'form-select',
                'id': 'bill_to_customer'
            }),
            'bill_to_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter bill to address'
            }),
            'deliver_to_customer': forms.Select(attrs={
                'class': 'form-select',
                'id': 'deliver_to_customer'
            }),
            'deliver_to_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter delivery address'
            }),
            'port_of_loading': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Select port of loading'
            }),
            'discharge_port': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Select discharge port'
            }),
            
            # Right section widgets
            'cs_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'payment_mode': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Select payment mode'
            }),
            'container_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter container number'
            }),
            'bl_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter BL number'
            }),
            'boe': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter BOE number'
            }),
            'exit_point': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Select exit point'
            }),
            'destination': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Select destination country'
            }),
            'ship_mode': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Select ship mode'
            }),
            'ship_date': forms.DateInput(attrs={
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
            'delivery_terms': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter delivery terms'
            }),
        }
        labels = {
            # Left section labels
            'cs_number': 'CS No',
            'document_type': 'Document Type',
            'customer': 'Customer',
            'job': 'Job',
            'facility': 'Facility',
            'bill_to': 'Bill To',
            'bill_to_customer': 'Bill To Customer',
            'bill_to_address': 'Bill to Address',
            'deliver_to_customer': 'Deliver To Customer',
            'deliver_to_address': 'Deliver to Address',
            'port_of_loading': 'Port of Loading',
            'discharge_port': 'Discharge Port',
            
            # Right section labels
            'cs_date': 'Date',
            'payment_mode': 'Payment Mode',
            'container_number': 'Container',
            'bl_number': 'BL Number',
            'boe': 'BOE',
            'exit_point': 'Exit Point',
            'destination': 'Destination',
            'ship_mode': 'Ship Mode',
            'ship_date': 'Ship Date',
            'vessel': 'Vessel',
            'voyage': 'Voyage',
            'delivery_terms': 'Delivery Terms',
        }
        help_texts = {
            'cs_number': 'Auto-generated cross stuffing number',
            'document_type': 'Type of document for this operation',
            'customer': 'Select the customer for this operation',
            'job': 'Select the job for this cross stuffing operation',
            'facility': 'Select the facility where operation will be performed',
            'bill_to': 'Party to be billed for this operation',
            'bill_to_customer': 'Select customer for billing (Shipper, Consignee, or Agent)',
            'bill_to_address': 'Billing address for the operation',
            'deliver_to_customer': 'Select customer for delivery (Shipper, Consignee, or Agent)',
            'deliver_to_address': 'Delivery address for the goods',
            'port_of_loading': 'Port where goods will be loaded',
            'discharge_port': 'Port where goods will be discharged',
            'cs_date': 'Date of the cross stuffing operation',
            'payment_mode': 'Mode of payment for this operation',
            'container_number': 'Container number for the operation',
            'bl_number': 'Bill of Lading number',
            'boe': 'Bill of Entry number',
            'exit_point': 'Exit point for the goods',
            'destination': 'Final destination country',
            'ship_mode': 'Mode of shipping',
            'ship_date': 'Date of shipment',
            'vessel': 'Name of the vessel',
            'voyage': 'Voyage number',
            'delivery_terms': 'Terms of delivery',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter active customers
        cross_stuffing_customers = Customer.objects.filter(
            is_active=True,
            jobs_as_customer__job_type="Cross Stuffing"
        ).distinct().order_by('customer_name')
        self.fields['customer'].queryset = cross_stuffing_customers
        
        # Filter jobs by customer and type
        self.fields['job'].queryset = Job.objects.filter(
            job_type="Cross Stuffing"
        ).order_by('job_code')
        
        # Filter active facilities
        self.fields['facility'].queryset = Facility.objects.filter(
            status='active'
        ).order_by('facility_name')
        
        # Filter customer fields by customer types (shipper, consignee, agent)
        customer_type_filter = Customer.objects.filter(
            customer_types__name__in=['Shipper', 'Consignee', 'Agent']
        ).distinct().order_by('customer_name')
        self.fields['bill_to_customer'].queryset = customer_type_filter
        self.fields['deliver_to_customer'].queryset = customer_type_filter
        
        # Filter active ports (using status field instead of is_active)
        self.fields['port_of_loading'].queryset = Port.objects.filter(status='active').order_by('port_name')
        self.fields['discharge_port'].queryset = Port.objects.filter(status='active').order_by('port_name')
        self.fields['exit_point'].queryset = Port.objects.filter(status='active').order_by('port_name')

    def clean(self):
        cleaned_data = super().clean()
        # Add any custom validation here if needed
        return cleaned_data 