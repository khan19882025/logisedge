from django import forms
from django.forms import inlineformset_factory
from .models import StockTransfer, StockTransferItem, StockLedger
from facility.models import Facility
from items.models import Item


class StockTransferForm(forms.ModelForm):
    """Form for creating and editing stock transfers"""
    
    class Meta:
        model = StockTransfer
        fields = [
            'transfer_date', 'transfer_type', 'source_facility', 'destination_facility',
            'reference_number', 'notes', 'special_instructions'
        ]
        widgets = {
            'transfer_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'required': True
            }),
            'transfer_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'source_facility': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'destination_facility': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'reference_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'External reference number (optional)'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes or remarks'
            }),
            'special_instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Special handling instructions'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter facilities to only show active warehouses
        self.fields['source_facility'].queryset = Facility.objects.filter(
            facility_type='warehouse',
            status='active'
        ).order_by('facility_name')
        self.fields['destination_facility'].queryset = Facility.objects.filter(
            facility_type='warehouse',
            status='active'
        ).order_by('facility_name')
    
    def clean(self):
        cleaned_data = super().clean()
        source_facility = cleaned_data.get('source_facility')
        destination_facility = cleaned_data.get('destination_facility')
        
        if source_facility and destination_facility:
            if source_facility == destination_facility:
                raise forms.ValidationError(
                    "Source and destination facilities cannot be the same."
                )
        
        return cleaned_data


class StockTransferItemForm(forms.ModelForm):
    """Form for adding items to stock transfers"""
    
    item_search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search items by name or code...',
            'autocomplete': 'off'
        }),
        help_text="Search for items to add to the transfer"
    )
    
    class Meta:
        model = StockTransferItem
        fields = [
            'item', 'quantity', 'available_quantity', 'unit_of_measure',
            'batch_number', 'serial_number', 'source_location', 'destination_location',
            'unit_cost', 'unit_weight', 'unit_volume', 'notes', 'expiry_date'
        ]
        widgets = {
            'item': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'required': True
            }),
            'available_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'readonly': True
            }),
            'unit_of_measure': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': True
            }),
            'batch_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Batch number (optional)'
            }),
            'serial_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Serial number (optional)'
            }),
            'source_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Source location within facility'
            }),
            'destination_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Destination location within facility'
            }),
            'unit_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'unit_weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0'
            }),
            'unit_volume': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Item-specific notes'
            }),
            'expiry_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        source_facility = kwargs.pop('source_facility', None)
        super().__init__(*args, **kwargs)
        
        # Filter items to only show active items
        self.fields['item'].queryset = Item.objects.filter(status='active').order_by('item_name')
        
        if source_facility:
            self.fields['item'].queryset = self.fields['item'].queryset.filter(
                # You might want to add logic here to filter by available stock
                # This would require a stock/inventory model
            )
    
    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get('quantity')
        available_quantity = cleaned_data.get('available_quantity')
        
        if quantity and available_quantity:
            if quantity > available_quantity:
                raise forms.ValidationError(
                    f"Transfer quantity ({quantity}) cannot exceed available quantity ({available_quantity})"
                )
        
        return cleaned_data


class StockTransferSearchForm(forms.Form):
    """Form for searching and filtering stock transfers"""
    
    transfer_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Transfer number'
        })
    )
    
    transfer_date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    transfer_date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    transfer_type = forms.ChoiceField(
        choices=[('', 'All Types')] + StockTransfer.TRANSFER_TYPES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + StockTransfer.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    source_facility = forms.ModelChoiceField(
        queryset=Facility.objects.filter(facility_type='warehouse').order_by('facility_name'),
        required=False,
        empty_label="All Source Facilities",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    destination_facility = forms.ModelChoiceField(
        queryset=Facility.objects.filter(facility_type='warehouse').order_by('facility_name'),
        required=False,
        empty_label="All Destination Facilities",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    created_by = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Created by'
        })
    )


class StockLedgerSearchForm(forms.Form):
    """Form for searching stock ledger entries"""
    
    item = forms.ModelChoiceField(
        queryset=Item.objects.filter(status='active').order_by('item_name'),
        required=False,
        empty_label="All Items",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    facility = forms.ModelChoiceField(
        queryset=Facility.objects.filter(facility_type='warehouse').order_by('facility_name'),
        required=False,
        empty_label="All Facilities",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    movement_type = forms.ChoiceField(
        choices=[('', 'All Types')] + StockLedger.MOVEMENT_TYPES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    movement_date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    movement_date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    reference_number = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Reference number'
        })
    )


class StockTransferApprovalForm(forms.ModelForm):
    """Form for approving stock transfers"""
    
    approval_notes = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Approval notes (optional)'
        })
    )
    
    class Meta:
        model = StockTransfer
        fields = []  # No fields needed for approval


class StockTransferProcessingForm(forms.ModelForm):
    """Form for processing stock transfers"""
    
    processing_notes = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Processing notes (optional)'
        })
    )
    
    class Meta:
        model = StockTransfer
        fields = []  # No fields needed for processing


# Inline formset for transfer items
StockTransferItemFormSet = inlineformset_factory(
    StockTransfer,
    StockTransferItem,
    form=StockTransferItemForm,
    extra=1,
    can_delete=True,
    fields=[
        'item', 'quantity', 'available_quantity', 'unit_of_measure',
        'batch_number', 'serial_number', 'source_location', 'destination_location',
        'unit_cost', 'unit_weight', 'unit_volume', 'notes', 'expiry_date'
    ]
) 