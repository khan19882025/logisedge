from django import forms
from django.contrib.auth.models import User
from .models import Shipment, StatusUpdate, ShipmentAttachment, NotificationLog
from customer.models import Customer
import pandas as pd
from django.core.exceptions import ValidationError

class ShipmentForm(forms.ModelForm):
    """Form for creating and editing shipments"""
    
    class Meta:
        model = Shipment
        fields = [
            'container_number', 'booking_id', 'hbl_number', 'customer_reference',
            'customer', 'customer_name', 'customer_email', 'customer_phone',
            'origin_port', 'destination_port', 'origin_country', 'destination_country',
            'booking_date', 'expected_departure', 'expected_arrival',
            'vessel_name', 'voyage_number', 'shipping_line',
            'cargo_description', 'cargo_weight', 'cargo_volume',
            'is_tracking_enabled', 'internal_notes', 'customer_notes'
        ]
        widgets = {
            'booking_date': forms.DateInput(attrs={'type': 'date'}),
            'expected_departure': forms.DateInput(attrs={'type': 'date'}),
            'expected_arrival': forms.DateInput(attrs={'type': 'date'}),
            'cargo_description': forms.Textarea(attrs={'rows': 3}),
            'internal_notes': forms.Textarea(attrs={'rows': 3}),
            'customer_notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make customer field optional for initial creation
        self.fields['customer'].required = False
        self.fields['customer'].queryset = Customer.objects.filter(is_active=True)
        
        # Add Bootstrap classes
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class StatusUpdateForm(forms.ModelForm):
    """Form for updating shipment status"""
    
    class Meta:
        model = StatusUpdate
        fields = ['status', 'location', 'description', 'estimated_completion']
        widgets = {
            'timestamp': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'estimated_completion': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.shipment = kwargs.pop('shipment', None)
        super().__init__(*args, **kwargs)
        
        # Add Bootstrap classes
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
    
    def clean_status(self):
        status = self.cleaned_data['status']
        if self.shipment and self.shipment.current_status == status:
            raise ValidationError("Status is already set to this value.")
        return status

class ShipmentSearchForm(forms.Form):
    """Form for searching shipments"""
    
    SEARCH_CHOICES = [
        ('all', 'All Fields'),
        ('container', 'Container Number'),
        ('booking', 'Booking ID'),
        ('hbl', 'HBL Number'),
        ('customer_ref', 'Customer Reference'),
        ('customer_name', 'Customer Name'),
    ]
    
    search_type = forms.ChoiceField(
        choices=SEARCH_CHOICES,
        initial='all',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    search_query = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter search term...'
        })
    )
    status_filter = forms.ChoiceField(
        choices=[('', 'All Statuses')] + Shipment.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )

class ShipmentAttachmentForm(forms.ModelForm):
    """Form for uploading attachments"""
    
    class Meta:
        model = ShipmentAttachment
        fields = ['file', 'file_type', 'description']
        widgets = {
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief description of the file'
            }),
            'file_type': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].widget.attrs.update({'class': 'form-control'})

class BulkUpdateForm(forms.Form):
    """Form for bulk updating shipments via Excel"""
    
    excel_file = forms.FileField(
        label='Excel File',
        help_text='Upload an Excel file with shipment updates. File should contain columns: shipment_id, status, location, description',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls'
        })
    )
    
    def clean_excel_file(self):
        file = self.cleaned_data['excel_file']
        
        # Check file extension
        if not file.name.endswith(('.xlsx', '.xls')):
            raise ValidationError("Please upload a valid Excel file (.xlsx or .xls)")
        
        # Check file size (max 5MB)
        if file.size > 5 * 1024 * 1024:
            raise ValidationError("File size must be less than 5MB")
        
        try:
            # Try to read the Excel file
            df = pd.read_excel(file)
            required_columns = ['shipment_id', 'status', 'location']
            
            # Check if required columns exist
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValidationError(f"Missing required columns: {', '.join(missing_columns)}")
            
            # Validate status values
            valid_statuses = [choice[0] for choice in Shipment.STATUS_CHOICES]
            invalid_statuses = df[~df['status'].isin(valid_statuses)]['status'].unique()
            if len(invalid_statuses) > 0:
                raise ValidationError(f"Invalid status values: {', '.join(invalid_statuses)}")
            
        except Exception as e:
            raise ValidationError(f"Error reading Excel file: {str(e)}")
        
        return file

class NotificationForm(forms.ModelForm):
    """Form for sending notifications"""
    
    NOTIFICATION_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
    ]
    
    notification_type = forms.ChoiceField(
        choices=NOTIFICATION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    recipient = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email address or phone number'
        })
    )
    subject = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Subject (for email notifications)'
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Enter your message...'
        })
    )
    
    class Meta:
        model = NotificationLog
        fields = ['notification_type', 'recipient', 'subject', 'message']

class ShipmentFilterForm(forms.Form):
    """Form for filtering shipments in the list view"""
    
    STATUS_CHOICES = [('', 'All Statuses')] + Shipment.STATUS_CHOICES
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    origin_port = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Origin Port'
        })
    )
    destination_port = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Destination Port'
        })
    )
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    is_tracking_enabled = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

class QuickStatusUpdateForm(forms.Form):
    """Form for quick status updates"""
    
    status = forms.ChoiceField(
        choices=Shipment.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    location = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Current location'
        })
    )
    description = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Additional details (optional)'
        })
    )
    send_notification = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

class ShipmentImportForm(forms.Form):
    """Form for importing shipments from Excel"""
    
    excel_file = forms.FileField(
        label='Excel File',
        help_text='Upload an Excel file with shipment data. Required columns: container_number, customer_name, origin_port, destination_port, booking_date',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls'
        })
    )
    
    def clean_excel_file(self):
        file = self.cleaned_data['excel_file']
        
        if not file.name.endswith(('.xlsx', '.xls')):
            raise ValidationError("Please upload a valid Excel file (.xlsx or .xls)")
        
        if file.size > 10 * 1024 * 1024:  # 10MB limit for imports
            raise ValidationError("File size must be less than 10MB")
        
        try:
            df = pd.read_excel(file)
            required_columns = ['container_number', 'customer_name', 'origin_port', 'destination_port', 'booking_date']
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValidationError(f"Missing required columns: {', '.join(missing_columns)}")
            
        except Exception as e:
            raise ValidationError(f"Error reading Excel file: {str(e)}")
        
        return file
