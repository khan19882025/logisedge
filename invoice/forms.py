from django import forms
from django.core.exceptions import ValidationError
from .models import Invoice
from customer.models import Customer, CustomerType
from datetime import date
from django.db import models
from job.models import Job

class CommaSeparatedJobsField(forms.CharField):
    """Custom field to handle comma-separated job IDs"""
    
    def to_python(self, value):
        if not value:
            return []
        
        if isinstance(value, list):
            return value
        
        # Handle comma-separated string
        if isinstance(value, str):
            job_ids = [jid.strip() for jid in value.split(',') if jid.strip()]
            return job_ids
        
        return []
    
    def clean(self, value):
        value = self.to_python(value)
        if not value and self.required:
            raise ValidationError("Please select at least one job.")
        return value

class InvoiceForm(forms.ModelForm):
    """Form for creating and editing invoices"""
    
    class Meta:
        model = Invoice
        fields = [
            'invoice_number', 'invoice_date', 'customer', 'jobs', 'delivery_order',
            'payment_source', 'bill_to', 'bill_to_address', 'shipper', 'consignee', 'origin', 'destination', 
            'bl_number', 'ed_number', 'container_number', 'items_count', 'total_qty',
            'invoice_items', 'notes', 'status'
        ]
        widgets = {
            'invoice_date': forms.DateInput(attrs={'type': 'date'}),
            'jobs': forms.HiddenInput(),  # Hidden field for comma-separated job IDs
            'delivery_order': forms.Select(attrs={'class': 'form-control'}),
            'payment_source': forms.Select(attrs={'class': 'form-control'}),
            'bill_to': forms.TextInput(attrs={'class': 'form-control'}),
            'bill_to_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'shipper': forms.TextInput(attrs={'class': 'form-control'}),
            'consignee': forms.TextInput(attrs={'class': 'form-control'}),
            'origin': forms.TextInput(attrs={'class': 'form-control'}),
            'destination': forms.TextInput(attrs={'class': 'form-control'}),
            'bl_number': forms.TextInput(attrs={'class': 'form-control'}),
            'ed_number': forms.TextInput(attrs={'class': 'form-control'}),
            'container_number': forms.TextInput(attrs={'class': 'form-control'}),
            'items_count': forms.TextInput(attrs={'class': 'form-control'}),
            'total_qty': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'invoice_items': forms.HiddenInput(),  # Hidden field for JSON data
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Override the jobs field with our custom field
        self.fields['jobs'] = CommaSeparatedJobsField(
            required=True,
            widget=forms.HiddenInput(),
            help_text="Comma-separated job IDs"
        )
        
        # Set current date as default for new invoices
        if not self.instance.pk:  # Only for new invoices
            self.fields['invoice_date'].initial = date.today()
        else:
            # For editing existing invoices, populate jobs field with current selections
            if self.instance.pk and hasattr(self.instance, 'jobs'):
                current_jobs = self.instance.jobs.all()
                if current_jobs:
                    job_ids = [str(job.id) for job in current_jobs]
                    self.fields['jobs'].initial = ','.join(job_ids)
        
        # Filter customer field to only show customers who have jobs without invoices
        try:
            # Import models here to avoid circular import issues
            from .models import Invoice
            from job.models import Job
            
            # Get all job IDs that already have invoices (correct relationship)
            jobs_with_invoices = Invoice.objects.values_list('jobs', flat=True).distinct()
            
            # Get customers who have jobs that don't have invoices yet
            customers_with_available_jobs = Customer.objects.filter(
                jobs_as_customer__isnull=False,  # Has jobs
                jobs_as_customer__id__in=Job.objects.exclude(id__in=jobs_with_invoices).values_list('id', flat=True)  # Jobs without invoices
            ).distinct().filter(is_active=True)
            
            # Filter by customer type (not vendors)
            try:
                # Try different possible customer type codes
                customer_type = None
                for code in ['CUS', 'CUST', 'CUSTOMER']:
                    try:
                        customer_type = CustomerType.objects.get(code=code)
                        break
                    except CustomerType.DoesNotExist:
                        continue
                
                if customer_type:
                    # Filter to show only customers with this type who have available jobs
                    self.fields['customer'].queryset = customers_with_available_jobs.filter(
                        customer_types=customer_type
                    ).order_by('customer_name')
                else:
                    # Fallback: exclude vendors and show all other active customers with available jobs
                    vendor_type = None
                    try:
                        vendor_type = CustomerType.objects.get(code='VEN')
                        self.fields['customer'].queryset = customers_with_available_jobs.exclude(
                            customer_types=vendor_type
                        ).order_by('customer_name')
                    except CustomerType.DoesNotExist:
                        # Final fallback: show all active customers with available jobs
                        self.fields['customer'].queryset = customers_with_available_jobs.order_by('customer_name')
                        
            except Exception as e:
                print(f"Error filtering customers by type: {e}")
                # Fallback: show all active customers with available jobs
                self.fields['customer'].queryset = customers_with_available_jobs.order_by('customer_name')
                
        except Exception as e:
            print(f"Error filtering customers: {e}")
            # Fallback: show all active customers if filtering fails
            self.fields['customer'].queryset = Customer.objects.filter(is_active=True).order_by('customer_name')
        
        # Initially, no jobs are shown until customer is selected
        # Jobs will be filtered dynamically via JavaScript when customer is selected
        # We need to allow any job ID since they're loaded dynamically
        self.fields['jobs'].queryset = Job.objects.all()
        
        # Make customer field always visible since it's needed for job filtering
        self.fields['customer'].widget.attrs.update({
            'class': 'form-control customer-field',
            'data-conditional': 'false'
        })
    
    def clean(self):
        """Custom validation for the form"""
        cleaned_data = super().clean()
        
        # Check if customer is selected
        customer = cleaned_data.get('customer')
        if not customer:
            raise forms.ValidationError("Please select a customer for this invoice.")
        
        # Check if jobs are selected
        jobs_data = cleaned_data.get('jobs')
        if not jobs_data:
            raise forms.ValidationError("Please select at least one job for this invoice.")
        
        # Validate that selected jobs exist and are valid
        try:
            from .models import Invoice
            
            # Get jobs that already have invoices
            jobs_with_invoices = Job.objects.filter(invoice__isnull=False).values_list('id', flat=True).distinct()
            
            # Check each selected job
            for job_id in jobs_data:
                # Check if job exists
                try:
                    job_obj = Job.objects.get(id=job_id)
                except Job.DoesNotExist:
                    raise forms.ValidationError(f"Job with ID {job_id} does not exist.")
                
                # Check if job belongs to the selected customer
                if job_obj.customer_name != customer:
                    raise forms.ValidationError(f"Job {job_obj.job_code} does not belong to the selected customer.")
                
                # Check if job already has an invoice
                if job_obj.id in jobs_with_invoices:
                    raise forms.ValidationError(f"Job {job_obj.job_code} already has an invoice and cannot be selected again.")
                
                # Check if job is active
                if hasattr(job_obj, 'status') and hasattr(job_obj.status, 'is_active') and not job_obj.status.is_active:
                    raise forms.ValidationError(f"Job {job_obj.job_code} is not active and cannot be selected.")
                    
        except Exception as e:
            raise forms.ValidationError(f"Error validating jobs: {str(e)}")
        
        return cleaned_data