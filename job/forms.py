from django import forms
from django.contrib.auth.models import User
from django.forms import inlineformset_factory
from .models import Job, JobStatus, JobPriority, JobCargo, JobContainer
from customer.models import Customer
from facility.models import Facility
from items.models import Item
from salesman.models import Salesman
import datetime
from django.db import models
from django.utils import timezone


class JobForm(forms.ModelForm):
    """Form for creating and editing jobs"""
    
    class Meta:
        model = Job
        fields = [
            'title', 'job_type', 'doc_type', 'shipment_type', 'mode', 'customer_name', 'customer_ref', 'shipper', 'broker',
            'facility', 'assigned_to', 'status', 'priority',
            'due_date', 'estimated_hours', 'notes',
            'internal_notes', 'related_items', 'related_facilities',
            'bl_number', 'bl_shipper', 'bl_consignee', 'bl_notify_party', 'vessel_name', 'voyage_number', 'port_loading', 'port_discharge',
            'boe_number', 'boe_date', 'boe_value', 'mrn_number', 'fz_company', 'com_invoice', 'com_invoice_date',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter job title'
            }),
            'job_type': forms.Select(attrs={
                'class': 'form-select',
                'required': 'required'
            }),
            'doc_type': forms.Select(attrs={
                'class': 'form-select',
                'required': 'required'
            }),
            'shipment_type': forms.Select(attrs={
                'class': 'form-select',
                'required': 'required'
            }),
            'mode': forms.Select(attrs={
                'class': 'form-select'
            }),
            'customer_name': forms.Select(attrs={
                'class': 'form-select'
            }),
            'customer_ref': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter customer reference',
                'required': 'required'
            }),
            'shipper': forms.Select(attrs={
                'class': 'form-select'
            }),
            'broker': forms.Select(attrs={
                'class': 'form-select'
            }),
            'facility': forms.Select(attrs={
                'class': 'form-select'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'estimated_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.5',
                'min': '0'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes about the job'
            }),
            'internal_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Internal notes (visible only to staff)'
            }),
            'related_items': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '5'
            }),
            'related_facilities': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '5'
            }),
            # BL (Bill of Lading) fields
            'bl_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter BL number'
            }),
            'bl_shipper': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter shipper name'
            }),
            'bl_consignee': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter consignee name'
            }),
            'bl_notify_party': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter notify party'
            }),
            'port_loading': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter port of loading'
            }),
            'port_discharge': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter port of discharge'
            }),
            # BOE (Bill of Entry) fields
            'boe_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter BOE number'
            }),
            'boe_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'boe_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Enter BOE value'
            }),
            # MRN (Movement Reference Number) field
            'mrn_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter MRN number'
            }),
            # FZ Company field
            'fz_company': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter FZ company name'
            }),
            # COM-INVOICE field
            'com_invoice': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter COM-INVOICE number'
            }),
            # COM-INVOICE Date field
            'com_invoice_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set initial date to today if creating a new job
        if not self.instance.pk:
            self.fields['due_date'].initial = datetime.date.today()
            
            # Set default values for required fields
            self.fields['job_type'].initial = 'Inbound'
            self.fields['doc_type'].initial = 'Import'
            self.fields['shipment_type'].initial = 'FCL-FCL'
            
            # Set initial facility to '001' if it exists
            try:
                default_facility = Facility.objects.get(facility_code='FAC-001')
                self.fields['facility'].initial = default_facility.pk
            except Facility.DoesNotExist:
                pass
            
            # Set default status to 'In Process' for new jobs
            try:
                in_process_status = JobStatus.objects.get(name__iexact='In Process', is_active=True)
                self.fields['status'].initial = in_process_status.pk
            except JobStatus.DoesNotExist:
                # If 'In Process' doesn't exist, try to get the first active status
                first_status = JobStatus.objects.filter(is_active=True).first()
                if first_status:
                    self.fields['status'].initial = first_status.pk
        
        # Filter customers by their respective types
        from customer.models import CustomerType
        
        # Filter customer_name to show only 'Customer' type
        try:
            customer_type = CustomerType.objects.get(name='Customer')
            customer_customers = Customer.objects.filter(
                customer_types=customer_type,
                is_active=True
            ).distinct().order_by('customer_name')
            self.fields['customer_name'].queryset = customer_customers
        except CustomerType.DoesNotExist:
            self.fields['customer_name'].queryset = Customer.objects.none()
        
        # Filter shipper to show only 'Shipper' type
        try:
            shipper_type = CustomerType.objects.get(name='Shipper')
            shipper_customers = Customer.objects.filter(
                customer_types=shipper_type,
                is_active=True
            ).distinct().order_by('customer_name')
            self.fields['shipper'].queryset = shipper_customers
        except CustomerType.DoesNotExist:
            self.fields['shipper'].queryset = Customer.objects.none()
        
        # Filter broker to show only 'Broker' type
        try:
            broker_type = CustomerType.objects.get(name='Broker')
            broker_customers = Customer.objects.filter(
                customer_types=broker_type,
                is_active=True
            ).distinct().order_by('customer_name')
            self.fields['broker'].queryset = broker_customers
        except CustomerType.DoesNotExist:
            self.fields['broker'].queryset = Customer.objects.none()
        
        # Filter active facilities
        active_facilities = Facility.objects.filter(status='active').order_by('facility_name')
        self.fields['facility'].queryset = active_facilities
        
        # Filter active salesmen for assignment
        active_salesmen = Salesman.objects.filter(status='active').order_by('first_name', 'last_name')
        self.fields['assigned_to'].queryset = active_salesmen
        
        # Set current user as created_by if this is a new job
        if not self.instance.pk and user:
            self.instance.created_by = user

    def clean(self):
        cleaned_data = super().clean()
        
        # Validate required fields (only those that are required in the model)
        required_fields = ['job_type', 'doc_type', 'shipment_type', 'customer_ref']
        
        for field in required_fields:
            if not cleaned_data.get(field):
                self.add_error(field, f'{field.replace("_", " ").title()} is required.')
        
        # Set default mode if not provided
        if not cleaned_data.get('mode'):
            cleaned_data['mode'] = 'Sea'
        
        return cleaned_data


class JobSearchForm(forms.Form):
    """Form for searching and filtering jobs"""
    
    search_term = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search jobs...'
        })
    )
    
    search_field = forms.ChoiceField(
        choices=[
            ('title', 'Title'),
            ('description', 'Description'),
            ('job_code', 'Job Code'),
            ('notes', 'Notes')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    job_type = forms.ChoiceField(
        choices=[('', 'All Types')] + Job.JOB_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    status = forms.ModelChoiceField(
        queryset=JobStatus.objects.filter(is_active=True),
        required=False,
        empty_label="All Statuses",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    priority = forms.ModelChoiceField(
        queryset=JobPriority.objects.filter(is_active=True),
        required=False,
        empty_label="All Priorities",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    mode = forms.ChoiceField(
        choices=[('', 'All Modes')] + Job.MODE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    assigned_to = forms.ModelChoiceField(
        queryset=Salesman.objects.filter(status='active'),
        required=False,
        empty_label="All Salesmen",
        widget=forms.Select(attrs={'class': 'form-select'})
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
    
    overdue_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    ) 


class JobCargoForm(forms.ModelForm):
    class Meta:
        model = JobCargo
        fields = ['id', 'item', 'item_code', 'hs_code', 'unit', 'quantity', 'coo', 'net_weight', 'gross_weight', 'rate', 'amount', 'remark']
        widgets = {
            'id': forms.HiddenInput(),  # Hidden field for existing records
            'item': forms.Select(attrs={'class': 'form-select form-select-sm item-select'}),
            'item_code': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'readonly': 'readonly'}),
            'hs_code': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'unit': forms.Select(attrs={'class': 'form-select form-select-sm'}, choices=[
                ('', 'Unit'),
                ('PCS', 'PCS'),
                ('KG', 'KG'),
                ('TON', 'TON'),
                ('M3', 'M3'),
                ('LTR', 'LTR'),
                ('BOX', 'BOX'),
                ('CARTON', 'CARTON'),
                ('PALLET', 'PALLET'),
            ]),
            'quantity': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0'}),
            'coo': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'net_weight': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0'}),
            'gross_weight': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0'}),
            'rate': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'step': '0.01',
                'min': '0',
                'readonly': 'readonly',
                'placeholder': '0.00'
            }),
            'remark': forms.TextInput(attrs={'class': 'form-control form-control-sm'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter active items
        active_items = Item.objects.filter(status='active').order_by('item_name')
        self.fields['item'].queryset = active_items
        
        # Set up item change event
        if self.instance.pk:
            self.fields['item'].initial = self.instance.item

    def clean(self):
        cleaned_data = super().clean()
        
        # Auto-calculate amount if rate and quantity are provided
        rate = cleaned_data.get('rate')
        quantity = cleaned_data.get('quantity')
        if rate and quantity:
            # Round to 2 decimal places to match the model field definition
            calculated_amount = rate * quantity
            cleaned_data['amount'] = round(calculated_amount, 2)
        
        return cleaned_data


class JobContainerForm(forms.ModelForm):
    class Meta:
        model = JobContainer
        fields = ['id', 'cargo_bond', 'ed_number', 'm1_number', 'container_number', 'container_size', 'seal_number']
        widgets = {
            'id': forms.HiddenInput(),  # Hidden field for existing records
            'cargo_bond': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Cargo Bond'}),
            'ed_number': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'ED Number'}),
            'm1_number': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'M1 Number'}),
            'container_number': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Container Number'}),
            'container_size': forms.Select(attrs={'class': 'form-select form-select-sm'}, choices=[
                ('', 'Select Size'),
                ('20\' Standard', '20\' Standard'),
                ('40\' Standard', '40\' Standard'),
                ('40\' High Cube', '40\' High Cube'),
                ('45\' High Cube', '45\' High Cube'),
            ]),
            'seal_number': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Seal Number'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields optional
        for field in self.fields.values():
            field.required = False


# Create inline formset for JobCargo
JobCargoFormSet = inlineformset_factory(
    Job, JobCargo,
    form=JobCargoForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False
)

# Create inline formset for JobContainer
JobContainerFormSet = inlineformset_factory(
    Job, JobContainer,
    form=JobContainerForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False
)


class CustomJobContainerFormSet(JobContainerFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # For new jobs (no instance or no pk), ensure we have at least one form
        if not self.instance or not self.instance.pk:
            # If no forms exist, add one empty form
            if len(self.forms) == 0:
                self.forms.append(self._construct_form(len(self.forms)))
    
    def clean(self):
        super().clean()
        # Count non-empty forms
        non_empty_forms = 0
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                # Check if any field has data
                has_data = any(form.cleaned_data.get(field) for field in ['ed_number', 'm1_number', 'container_number', 'container_size', 'seal_number'])
                if has_data:
                    non_empty_forms += 1
        
        # For new jobs, containers are optional
        # No validation errors needed


class CustomJobCargoFormSet(JobCargoFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # For new jobs (no instance or no pk), ensure we have at least one form
        if not self.instance or not self.instance.pk:
            # If no forms exist, add one empty form
            if len(self.forms) == 0:
                self.forms.append(self._construct_form(len(self.forms)))
        
        # Ensure all forms have the correct item queryset
        for i, form in enumerate(self.forms):
            if hasattr(form, 'fields') and 'item' in form.fields:
                form.fields['item'].queryset = Item.objects.all().order_by('item_name')
                form.fields['item'].empty_label = "Select Item"
                
                # Set initial value for existing instances
                if form.instance and form.instance.pk and form.instance.item:
                    form.fields['item'].initial = form.instance.item.pk
    
    def clean(self):
        # Call parent clean to set up cleaned_data
        cleaned_data = super().clean()
        
        # Only validate if we have POST data (form is being submitted)
        if not hasattr(self, 'data') or not self.data:
            return cleaned_data
        
        # Check if this is a new job (no instance or no pk)
        is_new_job = not self.instance or not self.instance.pk
        
        # Count non-empty forms
        non_empty_forms = 0
        for form in self.forms:
            if not form.cleaned_data.get('DELETE', False):
                item = form.cleaned_data.get('item')
                quantity = form.cleaned_data.get('quantity')
                if item and quantity:
                    non_empty_forms += 1
        
        # For new jobs, allow creation without cargo items (make it optional)
        # This allows users to create a job first and add cargo items later
        
        return cleaned_data