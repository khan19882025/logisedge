from django import forms
from django.utils import timezone
from .models import Documentation
from port.models import Port
from job.models import Job


class DocumentationForm(forms.ModelForm):
    """Form for creating and editing documentation"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set current date as default for new documents
        if not self.instance.pk:  # Only for new documents
            self.fields['date'].initial = timezone.now().date()
        
        # Customize port fields to show only active ports and display port codes
        active_ports = Port.objects.filter(status='active').order_by('port_code')
        
        # Set queryset for port fields
        self.fields['port_of_loading'].queryset = active_ports
        self.fields['discharge_port'].queryset = active_ports
        self.fields['exit_point'].queryset = active_ports
        
        # Customize labels to show port codes
        self.fields['port_of_loading'].label_from_instance = lambda obj: obj.port_code
        self.fields['discharge_port'].label_from_instance = lambda obj: obj.port_code
        self.fields['exit_point'].label_from_instance = lambda obj: obj.port_code
        
        # Filter customer field to show only customers with documentation jobs
        documentation_customers = Job.objects.filter(
            job_type="Documentations"
        ).values_list('customer_name', flat=True).distinct()
        
        from customer.models import Customer, CustomerType
        self.fields['customer'].queryset = Customer.objects.filter(
            id__in=documentation_customers
        ).order_by('customer_name')
        
        # Set queryset for deliver_to field to show only customers with specified types
        from customer.models import Customer, CustomerType
        deliver_to_customers = Customer.objects.filter(
            customer_types__name__in=['Shipper', 'Consignee', 'Agent'],
            is_active=True
        ).distinct().order_by('customer_name')
        self.fields['deliver_to'].queryset = deliver_to_customers
    
    class Meta:
        model = Documentation
        fields = [
            # Left column fields
            'document_no', 'customer', 'document_type', 'bill_to', 
            'bill_to_address', 'deliver_to', 'deliver_to_address', 'port_of_loading', 'discharge_port',
            # Right column fields
            'date', 'payment_mode', 'container', 'bl_number', 'boe', 'exit_point', 
            'destination', 'ship_mode', 'ship_date', 'vessel', 'voyage', 'delivery_terms'
        ]
        widgets = {
            # Left column widgets
            'document_no': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly',
                'placeholder': 'Auto-generated'
            }),
            'customer': forms.Select(attrs={
                'class': 'form-control select2',
                'placeholder': 'Select customer'
            }),
            'document_type': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Select document type'
            }),
            'bill_to': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter bill to party'
            }),
            'bill_to_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter bill to address'
            }),
            'deliver_to': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Select delivery customer'
            }),
            'deliver_to_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter delivery address'
            }),
            'port_of_loading': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Select port of loading'
            }),
            'discharge_port': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Select discharge port'
            }),
            
            # Right column widgets
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'payment_mode': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Select payment mode'
            }),
            'container': forms.TextInput(attrs={
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
                'class': 'form-control',
                'placeholder': 'Select exit point'
            }),
            'destination': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Select destination country'
            }),
            'ship_mode': forms.Select(attrs={
                'class': 'form-control',
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
            })
        } 