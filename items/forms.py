from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Item


class ItemForm(forms.ModelForm):
    """Form for creating and editing items"""
    
    class Meta:
        model = Item
        fields = [
            'item_code', 'item_name', 'item_category', 'status',
            'description', 'short_description',
            'brand', 'model', 'size', 'weight', 'color', 'material',
            'unit_of_measure', 'min_stock_level', 'max_stock_level', 'reorder_point',
            'cost_price', 'selling_price', 'currency',
            'supplier', 'supplier_code', 'lead_time',
            'warehouse_location', 'shelf_number', 'bin_number',
            'barcode', 'serial_number', 'warranty_period',
            'notes', 'internal_notes'
        ]
        widgets = {
            'item_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter item code (e.g., ITM-001)',
                'maxlength': '20'
            }),
            'item_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter item name',
                'maxlength': '200'
            }),
            'item_category': forms.Select(attrs={
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
            'brand': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter brand name'
            }),
            'model': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter model number'
            }),
            'size': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter size (e.g., 10x20cm)'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0',
                'placeholder': 'Weight in kg'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter color'
            }),
            'material': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter material'
            }),
            'unit_of_measure': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'PCS, KG, L, etc.',
                'maxlength': '20'
            }),
            'min_stock_level': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Minimum stock level'
            }),
            'max_stock_level': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Maximum stock level'
            }),
            'reorder_point': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Reorder point'
            }),
            'cost_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Cost price per unit'
            }),
            'selling_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Selling price per unit'
            }),
            'currency': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': '3',
                'placeholder': 'USD'
            }),
            'supplier': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter supplier name'
            }),
            'supplier_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Supplier item code'
            }),
            'lead_time': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Lead time in days'
            }),
            'warehouse_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Warehouse location'
            }),
            'shelf_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Shelf number'
            }),
            'bin_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Bin number'
            }),
            'barcode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Barcode or SKU'
            }),
            'serial_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Serial number'
            }),
            'warranty_period': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Warranty period in months'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': 'General notes'
            }),
            'internal_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': 'Internal notes (not visible to customers)'
            }),
        }
    
    def clean_item_code(self):
        """Validate item code format"""
        item_code = self.cleaned_data['item_code']
        if not item_code:
            raise ValidationError(_('Item code is required.'))
        
        # Check if item code already exists (excluding current instance for updates)
        instance = getattr(self, 'instance', None)
        if Item.objects.filter(item_code=item_code).exclude(pk=instance.pk if instance else None).exists():
            raise ValidationError(_('Item code already exists.'))
        
        return item_code.upper()
    
    def clean_barcode(self):
        """Validate barcode uniqueness"""
        barcode = self.cleaned_data['barcode']
        if barcode:
            instance = getattr(self, 'instance', None)
            if Item.objects.filter(barcode=barcode).exclude(pk=instance.pk if instance else None).exists():
                raise ValidationError(_('Barcode already exists.'))
        return barcode
    
    def clean(self):
        """Additional validation"""
        cleaned_data = super().clean()
        cost_price = cleaned_data.get('cost_price')
        selling_price = cleaned_data.get('selling_price')
        min_stock = cleaned_data.get('min_stock_level')
        max_stock = cleaned_data.get('max_stock_level')
        reorder_point = cleaned_data.get('reorder_point')
        
        # Validate pricing
        if cost_price and selling_price and cost_price > selling_price:
            raise ValidationError(_('Cost price cannot be higher than selling price.'))
        
        # Validate stock levels
        if min_stock and max_stock and min_stock > max_stock:
            raise ValidationError(_('Minimum stock level cannot be higher than maximum stock level.'))
        
        if reorder_point and max_stock and reorder_point > max_stock:
            raise ValidationError(_('Reorder point cannot be higher than maximum stock level.'))
        
        return cleaned_data


class ItemSearchForm(forms.Form):
    """Form for searching items"""
    
    SEARCH_CHOICES = [
        ('all', 'All Fields'),
        ('item_code', 'Item Code'),
        ('item_name', 'Item Name'),
        ('brand', 'Brand'),
        ('supplier', 'Supplier'),
        ('barcode', 'Barcode'),
    ]
    
    search_term = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search items...'
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
    
    item_category = forms.ChoiceField(
        choices=[('', 'All Categories')] + Item.ITEM_CATEGORIES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + Item.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    min_price = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Min price',
            'step': '0.01'
        })
    )
    
    max_price = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Max price',
            'step': '0.01'
        })
    ) 