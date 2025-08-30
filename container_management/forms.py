from django import forms
from django.core.validators import MinValueValidator
from django.utils import timezone
from .models import (
    Container, ContainerBooking, ContainerTracking, 
    ContainerInventory, ContainerMovement, ContainerNotification
)

class ContainerForm(forms.ModelForm):
    """Form for creating and editing containers"""
    
    class Meta:
        model = Container
        fields = [
            'container_number', 'container_type', 'size', 'tare_weight', 
            'max_payload', 'status', 'current_location', 'yard_location',
            'line_operator', 'purchase_date', 'last_maintenance', 
            'next_maintenance', 'notes'
        ]
        widgets = {
            'container_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., ABCD1234567'}),
            'container_type': forms.Select(attrs={'class': 'form-select'}),
            'size': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 20ft, 40ft'}),
            'tare_weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_payload': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'current_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Port/Terminal/Yard'}),
            'yard_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Specific yard location'}),
            'line_operator': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Shipping line operator'}),
            'purchase_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'last_maintenance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'next_maintenance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def clean_container_number(self):
        container_number = self.cleaned_data['container_number']
        if len(container_number) != 11:
            raise forms.ValidationError("Container number must be exactly 11 characters (ISO 6346 standard)")
        return container_number.upper()
    
    def clean(self):
        cleaned_data = super().clean()
        tare_weight = cleaned_data.get('tare_weight')
        max_payload = cleaned_data.get('max_payload')
        
        if tare_weight and max_payload and tare_weight <= 0:
            raise forms.ValidationError("Tare weight must be greater than 0")
        
        if max_payload and max_payload <= 0:
            raise forms.ValidationError("Maximum payload must be greater than 0")
        
        return cleaned_data

class ContainerBookingForm(forms.ModelForm):
    """Form for creating and editing container bookings"""
    
    class Meta:
        model = ContainerBooking
        fields = [
            'container', 'customer', 'freight_quotation', 'freight_booking',
            'container_type', 'container_size', 'soc_coc', 'pickup_date',
            'pickup_location', 'drop_off_port', 'drop_off_date',
            'cargo_description', 'weight', 'volume', 'rate',
            'special_instructions', 'booking_confirmation_file', 'soc_coc_details'
        ]
        widgets = {
            'container': forms.Select(attrs={'class': 'form-select'}),
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'freight_quotation': forms.Select(attrs={'class': 'form-select'}),
            'freight_booking': forms.Select(attrs={'class': 'form-select'}),
            'container_type': forms.Select(attrs={'class': 'form-select'}),
            'container_size': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 20ft, 40ft'}),
            'soc_coc': forms.Select(attrs={'class': 'form-select'}),
            'pickup_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'pickup_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pickup location'}),
            'drop_off_port': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Drop-off port'}),
            'drop_off_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'cargo_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe the cargo'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Weight in kg'}),
            'volume': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Volume in CBM'}),
            'rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Daily rate in AED'}),
            'special_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Special instructions'}),
            'booking_confirmation_file': forms.FileInput(attrs={'class': 'form-control'}),
            'soc_coc_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'SOC/COC details'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter containers to show only available ones
        self.fields['container'].queryset = Container.objects.filter(status='available')
    
    def clean(self):
        cleaned_data = super().clean()
        pickup_date = cleaned_data.get('pickup_date')
        drop_off_date = cleaned_data.get('drop_off_date')
        
        if pickup_date and drop_off_date:
            if pickup_date >= drop_off_date:
                raise forms.ValidationError("Drop-off date must be after pickup date")
            
            if pickup_date < timezone.now().date():
                raise forms.ValidationError("Pickup date cannot be in the past")
        
        weight = cleaned_data.get('weight')
        volume = cleaned_data.get('volume')
        
        if weight and weight <= 0:
            raise forms.ValidationError("Weight must be greater than 0")
        
        if volume and volume <= 0:
            raise forms.ValidationError("Volume must be greater than 0")
        
        return cleaned_data

class ContainerTrackingForm(forms.ModelForm):
    """Form for creating and editing container tracking events"""
    
    class Meta:
        model = ContainerTracking
        fields = [
            'container_booking', 'container', 'milestone', 'location',
            'vessel_name', 'voyage_number', 'event_date', 'eta',
            'actual_date', 'is_completed', 'is_delayed', 'delay_reason',
            'notes', 'documents'
        ]
        widgets = {
            'container_booking': forms.Select(attrs={'class': 'form-select'}),
            'container': forms.Select(attrs={'class': 'form-select'}),
            'milestone': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Location'}),
            'vessel_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Vessel name'}),
            'voyage_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Voyage number'}),
            'event_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'eta': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'actual_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'is_completed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_delayed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'delay_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Reason for delay'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional notes'}),
            'documents': forms.FileInput(attrs={'class': 'form-control'}),
        }

class ContainerInventoryForm(forms.ModelForm):
    """Form for creating and editing container inventory records"""
    
    class Meta:
        model = ContainerInventory
        fields = [
            'container', 'port', 'terminal', 'yard', 'bay', 'row', 'tier',
            'status', 'arrival_date', 'expected_departure', 'actual_departure',
            'is_overstayed', 'overstay_reason', 'container_booking', 'notes'
        ]
        widgets = {
            'container': forms.Select(attrs={'class': 'form-select'}),
            'port': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Port name'}),
            'terminal': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Terminal name'}),
            'yard': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Yard location'}),
            'bay': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bay number'}),
            'row': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Row number'}),
            'tier': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tier number'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'arrival_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'expected_departure': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'actual_departure': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'is_overstayed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'overstay_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Reason for overstay'}),
            'container_booking': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional notes'}),
        }

class ContainerMovementForm(forms.ModelForm):
    """Form for creating and editing container movements"""
    
    class Meta:
        model = ContainerMovement
        fields = [
            'container', 'movement_type', 'from_location', 'to_location',
            'movement_date', 'vessel_name', 'voyage_number',
            'container_booking', 'container_tracking', 'notes'
        ]
        widgets = {
            'container': forms.Select(attrs={'class': 'form-select'}),
            'movement_type': forms.Select(attrs={'class': 'form-select'}),
            'from_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'From location'}),
            'to_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'To location'}),
            'movement_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'vessel_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Vessel name'}),
            'voyage_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Voyage number'}),
            'container_booking': forms.Select(attrs={'class': 'form-select'}),
            'container_tracking': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Movement notes'}),
        }

class ContainerSearchForm(forms.Form):
    """Form for searching containers"""
    
    SEARCH_BY_CHOICES = [
        ('container_number', 'Container Number'),
        ('booking_number', 'Booking Number'),
        ('customer', 'Customer'),
        ('location', 'Location'),
        ('status', 'Status'),
    ]
    
    search_by = forms.ChoiceField(
        choices=SEARCH_BY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    search_term = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter search term'})
    )
    container_type = forms.ChoiceField(
        choices=[('', 'All Types')] + Container.CONTAINER_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + Container.CONTAINER_STATUS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    port = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Port'})
    )

class ContainerBookingSearchForm(forms.Form):
    """Form for searching container bookings"""
    
    search_by = forms.ChoiceField(
        choices=[
            ('booking_number', 'Booking Number'),
            ('container_number', 'Container Number'),
            ('customer', 'Customer'),
            ('status', 'Status'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    search_term = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter search term'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + ContainerBooking.BOOKING_STATUS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

class ContainerInventorySearchForm(forms.Form):
    """Form for searching container inventory"""
    
    port = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Port'})
    )
    terminal = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Terminal'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + ContainerInventory.INVENTORY_STATUS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    container_type = forms.ChoiceField(
        choices=[('', 'All Types')] + Container.CONTAINER_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    overstayed_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

class ContainerBulkUploadForm(forms.Form):
    """Form for bulk uploading containers via Excel/CSV"""
    
    file = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx,.xls,.csv'})
    )
    file_type = forms.ChoiceField(
        choices=[
            ('excel', 'Excel (.xlsx, .xls)'),
            ('csv', 'CSV (.csv)'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    update_existing = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

class ContainerNotificationForm(forms.ModelForm):
    """Form for creating container notifications"""
    
    class Meta:
        model = ContainerNotification
        fields = [
            'notification_type', 'priority', 'container', 'container_booking',
            'container_tracking', 'title', 'message', 'recipient_email',
            'recipient_name'
        ]
        widgets = {
            'notification_type': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'container': forms.Select(attrs={'class': 'form-select'}),
            'container_booking': forms.Select(attrs={'class': 'form-select'}),
            'container_tracking': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Notification title'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Notification message'}),
            'recipient_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Recipient email'}),
            'recipient_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Recipient name'}),
        }

class ContainerStatusUpdateForm(forms.Form):
    """Form for updating container status"""
    
    status = forms.ChoiceField(
        choices=Container.CONTAINER_STATUS,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    location = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'New location'})
    )
    notes = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Status update notes'})
    )

class ContainerMaintenanceForm(forms.Form):
    """Form for scheduling container maintenance"""
    
    maintenance_type = forms.ChoiceField(
        choices=[
            ('routine', 'Routine Maintenance'),
            ('repair', 'Repair'),
            ('inspection', 'Inspection'),
            ('cleaning', 'Cleaning'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    scheduled_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    estimated_duration = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Duration in days'})
    )
    description = forms.CharField(
        max_length=500,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Maintenance description'})
    )
    cost_estimate = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Estimated cost in AED'})
    )
