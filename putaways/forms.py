from django import forms
from .models import Putaway
from grn.models import GRN, GRNPallet
from items.models import Item
from facility.models import FacilityLocation

class PutawayForm(forms.ModelForm):
    pallet_id = forms.CharField(
        widget=forms.Select(attrs={
            'class': 'form-select',
            'placeholder': 'Select Pallet ID',
            'id': 'id_pallet_id'
        }),
        required=True,
        label="Pallet ID"
    )
    
    class Meta:
        model = Putaway
        fields = ['grn', 'pallet_id', 'item', 'quantity', 'location', 'notes', 'remarks']
        widgets = {
            'grn': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Select GRN',
                'id': 'id_grn'
            }),
            'item': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Select Item',
                'id': 'id_item'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Quantity will be auto-filled',
                'step': '0.01',
                'min': '0',
                'id': 'id_quantity'
            }),
            'location': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Select Location',
                'id': 'id_location'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Notes',
                'rows': 3,
                'id': 'id_notes'
            }),
            'remarks': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Remarks',
                'rows': 3,
                'id': 'id_remarks'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter GRNs to only show those with pallets
        self.fields['grn'].queryset = GRN.objects.filter(
            pallets__isnull=False
        ).distinct().order_by('-grn_date')
        
        # Initialize item field with all items (will be filtered by JavaScript)
        self.fields['item'].queryset = Item.objects.all().order_by('item_name')
        self.fields['item'].required = True
        
        # Filter locations
        self.fields['location'].queryset = FacilityLocation.objects.all().order_by('location_name')
        
        # Set initial choices for pallet_id dropdown
        self.fields['pallet_id'].widget.choices = [('', 'Select Pallet ID')]
    
    def clean(self):
        cleaned_data = super().clean()
        grn = cleaned_data.get('grn')
        pallet_id = cleaned_data.get('pallet_id')
        item = cleaned_data.get('item')
        
        # Validate that the pallet belongs to the selected GRN
        if grn and pallet_id:
            try:
                pallet = GRNPallet.objects.get(grn=grn, pallet_no=pallet_id)
                # Ensure the pallet_id is set correctly
                cleaned_data['pallet_id'] = pallet.pallet_no
                
                # If item is not selected, try to get it from the pallet
                if not item and pallet.item:
                    cleaned_data['item'] = pallet.item
                    
            except GRNPallet.DoesNotExist:
                raise forms.ValidationError("Selected pallet does not belong to the selected GRN.")
        
        # Ensure item is selected
        if not cleaned_data.get('item'):
            raise forms.ValidationError("Please select an item.")
        
        return cleaned_data 