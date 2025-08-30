from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Facility, FacilityLocation


class FacilityForm(forms.ModelForm):
    """Form for creating and editing facilities"""
    
    class Meta:
        model = Facility
        fields = [
            'facility_code', 'facility_name', 'facility_type', 'status',
            'description', 'short_description',
            'address', 'city', 'state', 'country', 'postal_code', 'latitude', 'longitude',
            'phone', 'email', 'contact_person', 'contact_phone', 'contact_email',
            'total_area', 'usable_area', 'height', 'capacity', 'max_weight_capacity',
            'operating_hours', 'timezone', 'is_24_7', 'has_security', 'has_cctv', 
            'has_fire_suppression', 'has_climate_control',
            'loading_docks', 'forklifts', 'pallet_racks', 'refrigeration_units', 'power_generators',
            'monthly_rent', 'utilities_cost', 'maintenance_cost', 'currency',
            'owner', 'lease_start_date', 'lease_end_date', 'is_owned',
            'notes', 'internal_notes'
        ]
        widgets = {
            'facility_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter facility code (e.g., FAC-001, WH-002)',
                'maxlength': '20'
            }),
            'facility_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter facility name',
                'maxlength': '200'
            }),
            'facility_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '4',
                'placeholder': 'Enter detailed description'
            }),
            'short_description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter brief description',
                'maxlength': '500'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': 'Enter complete address'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter city'
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter state/province'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter country'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter postal code'
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.000001',
                'placeholder': 'GPS latitude'
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.000001',
                'placeholder': 'GPS longitude'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Facility phone number'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Facility email address'
            }),
            'contact_person': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Primary contact person'
            }),
            'contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contact phone number'
            }),
            'contact_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contact email address'
            }),
            'total_area': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Total area in square meters'
            }),
            'usable_area': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Usable area in square meters'
            }),
            'height': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Ceiling height in meters'
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Storage capacity in cubic meters'
            }),
            'max_weight_capacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Maximum weight capacity in tons'
            }),
            'operating_hours': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Mon-Fri 8AM-6PM, Sat 9AM-3PM'
            }),
            'timezone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'UTC'
            }),
            'is_24_7': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'has_security': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'has_cctv': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'has_fire_suppression': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'has_climate_control': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'loading_docks': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Number of loading docks'
            }),
            'forklifts': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Number of forklifts'
            }),
            'pallet_racks': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Number of pallet racks'
            }),
            'refrigeration_units': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Number of refrigeration units'
            }),
            'power_generators': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Number of power generators'
            }),
            'monthly_rent': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Monthly rent amount'
            }),
            'utilities_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Monthly utilities cost'
            }),
            'maintenance_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Monthly maintenance cost'
            }),
            'currency': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': '3',
                'placeholder': 'USD'
            }),
            'owner': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Facility owner or landlord'
            }),
            'lease_start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'lease_end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'is_owned': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': 'General notes'
            }),
            'internal_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': 'Internal notes (not visible to all users)'
            }),
        }
    
    def clean_facility_code(self):
        """Validate facility code format"""
        facility_code = self.cleaned_data['facility_code']
        if not facility_code:
            raise ValidationError(_('Facility code is required.'))
        
        # Check if facility code already exists (excluding current instance for updates)
        instance = getattr(self, 'instance', None)
        if Facility.objects.filter(facility_code=facility_code).exclude(pk=instance.pk if instance else None).exists():
            raise ValidationError(_('Facility code already exists.'))
        
        return facility_code.upper()
    
    def clean(self):
        """Additional validation"""
        cleaned_data = super().clean()
        total_area = cleaned_data.get('total_area')
        usable_area = cleaned_data.get('usable_area')
        lease_start = cleaned_data.get('lease_start_date')
        lease_end = cleaned_data.get('lease_end_date')
        is_owned = cleaned_data.get('is_owned')
        
        # Validate area measurements
        if total_area and usable_area and usable_area > total_area:
            raise ValidationError(_('Usable area cannot be greater than total area.'))
        
        # Validate lease dates
        if lease_start and lease_end and lease_start > lease_end:
            raise ValidationError(_('Lease start date cannot be after lease end date.'))
        
        # Validate ownership vs lease
        if is_owned and (lease_start or lease_end):
            raise ValidationError(_('Owned facilities should not have lease dates.'))
        
        return cleaned_data


class FacilityLocationForm(forms.ModelForm):
    """Form for creating and editing facility locations"""
    
    class Meta:
        model = FacilityLocation
        fields = [
            'facility', 'location_code', 'location_name', 'location_type', 'status',
            'description', 'area', 'height', 'capacity', 'max_weight',
            'floor_level', 'section', 'zone',
            'rack_number', 'aisle_number', 'bay_number', 'level_number',
            'x_coordinate', 'y_coordinate',
            'access_restrictions', 'temperature_range', 'humidity_range',
            'has_lighting', 'has_climate_control', 'has_security', 'has_fire_suppression',
            'is_accessible_by_forklift', 'is_accessible_by_pallet_jack',
            'current_utilization', 'reserved_capacity',
            'notes', 'internal_notes'
        ]
        widgets = {
            'facility': forms.Select(attrs={
                'class': 'form-select'
            }),
            'location_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter location code (e.g., RACK-A1, AISLE-01)',
                'maxlength': '20'
            }),
            'location_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter location name',
                'maxlength': '200'
            }),
            'location_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': 'Enter detailed description'
            }),
            'area': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Area in square meters'
            }),
            'height': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Height in meters'
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Storage capacity in cubic meters'
            }),
            'max_weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Maximum weight capacity in tons'
            }),
            'floor_level': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., G, 1, 2, B1'
            }),
            'section': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Section within the facility'
            }),
            'zone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Zone designation'
            }),
            'rack_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Rack number if applicable'
            }),
            'aisle_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Aisle number if applicable'
            }),
            'bay_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Bay number if applicable'
            }),
            'level_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Level number if applicable'
            }),
            'x_coordinate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'X coordinate for mapping'
            }),
            'y_coordinate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Y coordinate for mapping'
            }),
            'access_restrictions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '2',
                'placeholder': 'Any access restrictions or special requirements'
            }),
            'temperature_range': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2-8°C, -18°C'
            }),
            'humidity_range': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 30-60%'
            }),
            'has_lighting': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'has_climate_control': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'has_security': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'has_fire_suppression': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_accessible_by_forklift': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_accessible_by_pallet_jack': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'current_utilization': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': 'Current utilization percentage'
            }),
            'reserved_capacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': 'Reserved capacity percentage'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': 'General notes'
            }),
            'internal_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': 'Internal notes (not visible to all users)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter facilities to only show active ones
        self.fields['facility'].queryset = Facility.objects.filter(status='active')
    
    def clean_location_code(self):
        """Validate location code format"""
        location_code = self.cleaned_data['location_code']
        if not location_code:
            raise ValidationError(_('Location code is required.'))
        
        facility = self.cleaned_data.get('facility')
        if facility:
            # Check if location code already exists within the same facility
            instance = getattr(self, 'instance', None)
            if FacilityLocation.objects.filter(
                facility=facility, 
                location_code=location_code
            ).exclude(pk=instance.pk if instance else None).exists():
                raise ValidationError(_('Location code already exists in this facility.'))
        
        return location_code.upper()
    
    def clean(self):
        """Additional validation"""
        cleaned_data = super().clean()
        current_utilization = cleaned_data.get('current_utilization', 0)
        reserved_capacity = cleaned_data.get('reserved_capacity', 0)
        
        # Validate utilization percentages
        if current_utilization + reserved_capacity > 100:
            raise ValidationError(_('Current utilization and reserved capacity cannot exceed 100%.'))
        
        return cleaned_data


class FacilitySearchForm(forms.Form):
    """Form for searching facilities"""
    
    SEARCH_CHOICES = [
        ('all', 'All Fields'),
        ('facility_code', 'Facility Code'),
        ('facility_name', 'Facility Name'),
        ('city', 'City'),
        ('contact_person', 'Contact Person'),
    ]
    
    search_term = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search facilities...'
        })
    )
    
    search_field = forms.ChoiceField(
        choices=SEARCH_CHOICES,
        initial='all',
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    facility_type = forms.ChoiceField(
        choices=[('', 'All Types')] + Facility.FACILITY_TYPES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + Facility.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    city = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filter by city'
        })
    )
    
    is_owned = forms.ChoiceField(
        choices=[
            ('', 'All'),
            ('True', 'Owned'),
            ('False', 'Leased')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )


class FacilityLocationSearchForm(forms.Form):
    """Form for searching facility locations"""
    
    SEARCH_CHOICES = [
        ('all', 'All Fields'),
        ('location_code', 'Location Code'),
        ('location_name', 'Location Name'),
        ('facility', 'Facility'),
    ]
    
    search_term = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search locations...'
        })
    )
    
    search_field = forms.ChoiceField(
        choices=SEARCH_CHOICES,
        initial='all',
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    facility = forms.ModelChoiceField(
        queryset=Facility.objects.filter(status='active'),
        required=False,
        empty_label="All Facilities",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    location_type = forms.ChoiceField(
        choices=[('', 'All Types')] + FacilityLocation.LOCATION_TYPES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + FacilityLocation.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    availability = forms.ChoiceField(
        choices=[
            ('', 'All'),
            ('available', 'Available'),
            ('full', 'Full'),
            ('reserved', 'Reserved')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    ) 