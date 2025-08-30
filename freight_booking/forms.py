from django import forms
from django.contrib.auth.models import User
from .models import (
    FreightBooking, Carrier, BookingCoordinator, BookingDocument, 
    BookingCharge, BookingHistory
)
from freight_quotation.models import Customer, FreightQuotation


class CarrierForm(forms.ModelForm):
    """Form for creating and editing carriers"""
    
    class Meta:
        model = Carrier
        fields = [
            'name', 'code', 'contact_person', 'email', 'phone', 
            'address', 'country', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class BookingCoordinatorForm(forms.ModelForm):
    """Form for creating and editing booking coordinators"""
    
    class Meta:
        model = BookingCoordinator
        fields = ['user', 'employee_id', 'department', 'phone_extension', 'is_active']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_extension': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class FreightBookingForm(forms.ModelForm):
    """Main form for freight bookings"""
    
    # Additional fields for better UX
    quotation_search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search quotation by number...',
            'id': 'quotation-search'
        })
    )
    
    class Meta:
        model = FreightBooking
        fields = [
            'quotation', 'customer', 'shipment_type', 'status',
            'origin_country', 'origin_port', 'origin_city',
            'destination_country', 'destination_port', 'destination_city',
            'carrier', 'booking_coordinator',
            'cargo_description', 'commodity', 'weight', 'volume', 'packages',
            'container_type', 'container_count',
            'pickup_date', 'delivery_date',
            'freight_cost', 'additional_costs', 'currency',
            'special_instructions', 'internal_notes'
        ]
        widgets = {
            'quotation': forms.Select(attrs={'class': 'form-control'}),
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'shipment_type': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'origin_country': forms.TextInput(attrs={'class': 'form-control'}),
            'origin_port': forms.TextInput(attrs={'class': 'form-control'}),
            'origin_city': forms.TextInput(attrs={'class': 'form-control'}),
            'destination_country': forms.TextInput(attrs={'class': 'form-control'}),
            'destination_port': forms.TextInput(attrs={'class': 'form-control'}),
            'destination_city': forms.TextInput(attrs={'class': 'form-control'}),
            'carrier': forms.Select(attrs={'class': 'form-control'}),
            'booking_coordinator': forms.Select(attrs={'class': 'form-control'}),
            'cargo_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'commodity': forms.TextInput(attrs={'class': 'form-control'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'volume': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'packages': forms.NumberInput(attrs={'class': 'form-control'}),
            'container_type': forms.Select(attrs={'class': 'form-control'}),
            'container_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'pickup_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'delivery_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'freight_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'additional_costs': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('AED', 'AED - UAE Dirham'),
                ('USD', 'USD - US Dollar'),
                ('EUR', 'EUR - Euro'),
                ('GBP', 'GBP - British Pound'),
            ]),
            'special_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'internal_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make quotation field optional
        self.fields['quotation'].required = False
        self.fields['quotation'].empty_label = "Select a quotation (optional)"
        
        # Filter active carriers and coordinators
        self.fields['carrier'].queryset = Carrier.objects.filter(is_active=True)
        self.fields['booking_coordinator'].queryset = BookingCoordinator.objects.filter(is_active=True)
        self.fields['booking_coordinator'].empty_label = "Select a coordinator (optional)"

    def clean(self):
        cleaned_data = super().clean()
        pickup_date = cleaned_data.get('pickup_date')
        delivery_date = cleaned_data.get('delivery_date')
        
        if pickup_date and delivery_date and pickup_date > delivery_date:
            raise forms.ValidationError("Pickup date cannot be after delivery date.")
        
        return cleaned_data


class BookingDocumentForm(forms.ModelForm):
    """Form for uploading booking documents"""
    
    class Meta:
        model = BookingDocument
        fields = ['document_type', 'file', 'description']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (max 10MB)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError("File size must be under 10MB.")
            
            # Check file extension
            allowed_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.xls', '.xlsx']
            import os
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in allowed_extensions:
                raise forms.ValidationError(f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}")
        
        return file


class BookingChargeForm(forms.ModelForm):
    """Form for adding booking charges"""
    
    class Meta:
        model = BookingCharge
        fields = ['charge_type', 'description', 'amount', 'currency']
        widgets = {
            'charge_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('AED', 'AED - UAE Dirham'),
                ('USD', 'USD - US Dollar'),
                ('EUR', 'EUR - Euro'),
                ('GBP', 'GBP - British Pound'),
            ]),
        }


class BookingStatusForm(forms.Form):
    """Form for changing booking status"""
    
    STATUS_CHOICES = [
        ('booked', 'Booked'),
        ('confirmed', 'Confirmed'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Add notes about this status change...'})
    )


class BookingSearchForm(forms.Form):
    """Form for searching bookings"""
    
    booking_reference = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by booking reference...'
        })
    )
    
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
        required=False,
        empty_label="All Customers",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + FreightBooking.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    shipment_type = forms.ChoiceField(
        choices=[('', 'All Types')] + FreightBooking.SHIPMENT_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    carrier = forms.ModelChoiceField(
        queryset=Carrier.objects.filter(is_active=True),
        required=False,
        empty_label="All Carriers",
        widget=forms.Select(attrs={'class': 'form-control'})
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


class BookingSummaryForm(forms.Form):
    """Form for booking summary confirmation"""
    
    confirm_booking = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="I confirm that all information is correct and I want to proceed with this booking"
    )
    
    send_notification = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Send notification email to customer"
    )
