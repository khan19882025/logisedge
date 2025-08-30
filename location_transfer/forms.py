from django import forms
from django.forms import inlineformset_factory
from .models import Pallet, PalletItem, LocationTransfer, LocationTransferHistory
from facility.models import FacilityLocation
from items.models import Item

class PalletSearchForm(forms.Form):
    """Form for searching pallets"""
    
    pallet_id = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Pallet ID...',
            'autocomplete': 'off'
        }),
        label="Pallet ID"
    )
    
    location = forms.ModelChoiceField(
        queryset=FacilityLocation.objects.filter(status='active'),
        required=False,
        empty_label="All Locations",
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label="Location"
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + Pallet.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label="Status"
    )
    
    facility = forms.ModelChoiceField(
        queryset=FacilityLocation.objects.values_list('facility', flat=True).distinct(),
        required=False,
        empty_label="All Facilities",
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label="Facility"
    )

class LocationTransferForm(forms.ModelForm):
    """Form for creating and editing location transfers"""
    
    class Meta:
        model = LocationTransfer
        fields = [
            'pallet', 'transfer_type', 'source_location', 'destination_location',
            'scheduled_date', 'priority', 'notes', 'special_instructions'
        ]
        widgets = {
            'pallet': forms.Select(attrs={
                'class': 'form-select',
                'id': 'pallet-select'
            }),
            'transfer_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'source_location': forms.Select(attrs={
                'class': 'form-select',
                'id': 'source-location-select',
                'readonly': True
            }),
            'destination_location': forms.Select(attrs={
                'class': 'form-select',
                'id': 'destination-location-select'
            }),
            'scheduled_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter transfer notes...'
            }),
            'special_instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter special instructions...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter pallets to only active ones with locations
        self.fields['pallet'].queryset = Pallet.objects.filter(
            status='active',
            current_location__isnull=False
        ).select_related('current_location')
        
        # Filter locations to only active ones
        self.fields['source_location'].queryset = FacilityLocation.objects.filter(status='active')
        self.fields['destination_location'].queryset = FacilityLocation.objects.filter(status='active')
        
        # Set initial source location if pallet is selected
        if self.instance.pk and self.instance.pallet:
            self.fields['source_location'].initial = self.instance.pallet.current_location
            self.fields['source_location'].widget.attrs['readonly'] = True
    
    def clean(self):
        cleaned_data = super().clean()
        source_location = cleaned_data.get('source_location')
        destination_location = cleaned_data.get('destination_location')
        pallet = cleaned_data.get('pallet')
        
        # Validate that source and destination are different
        if source_location and destination_location and source_location == destination_location:
            raise forms.ValidationError("Source and destination locations must be different.")
        
        # Validate that pallet is at source location
        if pallet and source_location and pallet.current_location != source_location:
            raise forms.ValidationError(f"Pallet {pallet.pallet_id} is not at the selected source location.")
        
        return cleaned_data

class LocationTransferApprovalForm(forms.ModelForm):
    """Form for approving location transfers"""
    
    class Meta:
        model = LocationTransfer
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter approval notes...'
            })
        }

class LocationTransferProcessingForm(forms.ModelForm):
    """Form for processing location transfers"""
    
    class Meta:
        model = LocationTransfer
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter processing notes...'
            })
        }

class LocationTransferSearchForm(forms.Form):
    """Form for searching location transfers"""
    
    transfer_number = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Transfer Number...'
        }),
        label="Transfer Number"
    )
    
    pallet_id = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Pallet ID...'
        }),
        label="Pallet ID"
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + LocationTransfer.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label="Status"
    )
    
    transfer_type = forms.ChoiceField(
        choices=[('', 'All Types')] + LocationTransfer.TRANSFER_TYPES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label="Transfer Type"
    )
    
    priority = forms.ChoiceField(
        choices=[('', 'All Priorities')] + [
            ('low', 'Low'),
            ('normal', 'Normal'),
            ('high', 'High'),
            ('urgent', 'Urgent'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label="Priority"
    )
    
    source_location = forms.ModelChoiceField(
        queryset=FacilityLocation.objects.filter(status='active'),
        required=False,
        empty_label="All Source Locations",
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label="Source Location"
    )
    
    destination_location = forms.ModelChoiceField(
        queryset=FacilityLocation.objects.filter(status='active'),
        required=False,
        empty_label="All Destination Locations",
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label="Destination Location"
    )
    
    created_by = forms.ModelChoiceField(
        queryset=LocationTransfer.objects.values_list('created_by', flat=True).distinct(),
        required=False,
        empty_label="All Users",
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label="Created By"
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label="From Date"
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label="To Date"
    )

class PalletItemForm(forms.ModelForm):
    """Form for pallet items"""
    
    class Meta:
        model = PalletItem
        fields = [
            'item', 'quantity', 'unit_of_measure', 'batch_number', 
            'serial_number', 'expiry_date', 'unit_cost', 'notes'
        ]
        widgets = {
            'item': forms.Select(attrs={
                'class': 'form-select item-select'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'unit_of_measure': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'batch_number': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'serial_number': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'unit_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            })
        }

# Inline formset for pallet items
PalletItemFormSet = inlineformset_factory(
    Pallet,
    PalletItem,
    form=PalletItemForm,
    extra=1,
    can_delete=True,
    fields=[
        'item', 'quantity', 'unit_of_measure', 'batch_number', 
        'serial_number', 'expiry_date', 'unit_cost', 'notes'
    ]
)

class QuickTransferForm(forms.Form):
    """Form for quick pallet transfer"""
    
    pallet_id = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Pallet ID...',
            'id': 'quick-pallet-id'
        }),
        label="Pallet ID"
    )
    
    destination_location = forms.ModelChoiceField(
        queryset=FacilityLocation.objects.filter(status='active'),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'quick-destination-location'
        }),
        label="Destination Location"
    )
    
    notes = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter transfer notes...'
        }),
        label="Notes"
    )
    
    def clean_pallet_id(self):
        pallet_id = self.cleaned_data['pallet_id']
        try:
            pallet = Pallet.objects.get(pallet_id=pallet_id, status='active')
            if not pallet.current_location:
                raise forms.ValidationError("This pallet is not currently located anywhere.")
        except Pallet.DoesNotExist:
            raise forms.ValidationError("Pallet not found or not active.")
        return pallet_id 