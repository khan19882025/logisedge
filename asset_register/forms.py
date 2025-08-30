from django import forms
from django.contrib.auth.models import User
from .models import (
    Asset, AssetCategory, AssetLocation, AssetStatus, AssetDepreciation,
    AssetMovement, AssetMaintenance
)
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date


class AssetCategoryForm(forms.ModelForm):
    """Form for creating and editing asset categories"""
    
    class Meta:
        model = AssetCategory
        fields = ['name', 'description', 'parent_category']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter category name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter category description'
            }),
            'parent_category': forms.Select(attrs={
                'class': 'form-control'
            })
        }

    def clean_name(self):
        name = self.cleaned_data['name']
        if AssetCategory.objects.filter(name__iexact=name).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise ValidationError('A category with this name already exists.')
        return name


class AssetLocationForm(forms.ModelForm):
    """Form for creating and editing asset locations"""
    
    class Meta:
        model = AssetLocation
        fields = ['name', 'building', 'floor', 'room', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter location name'
            }),
            'building': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter building name'
            }),
            'floor': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter floor number'
            }),
            'room': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter room number'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter location description'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def clean_name(self):
        name = self.cleaned_data['name']
        if AssetLocation.objects.filter(name__iexact=name).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise ValidationError('A location with this name already exists.')
        return name


class AssetStatusForm(forms.ModelForm):
    """Form for creating and editing asset statuses"""
    
    class Meta:
        model = AssetStatus
        fields = ['name', 'description', 'color', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter status name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter status description'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'placeholder': '#007bff'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def clean_name(self):
        name = self.cleaned_data['name']
        if AssetStatus.objects.filter(name__iexact=name).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise ValidationError('A status with this name already exists.')
        return name


class AssetDepreciationForm(forms.ModelForm):
    """Form for creating and editing asset depreciation methods"""
    
    class Meta:
        model = AssetDepreciation
        fields = ['name', 'method', 'rate_percentage', 'useful_life_years', 'salvage_value_percentage', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter depreciation method name'
            }),
            'method': forms.Select(attrs={
                'class': 'form-control'
            }),
            'rate_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': '0.00'
            }),
            'useful_life_years': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0'
            }),
            'salvage_value_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': '0.00'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter depreciation method description'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }


class AssetForm(forms.ModelForm):
    """Form for creating and editing assets"""
    
    class Meta:
        model = Asset
        fields = [
            'asset_name', 'description', 'category', 'location', 'status',
            'purchase_date', 'purchase_value', 'current_value', 'salvage_value',
            'depreciation_method', 'useful_life_years', 'assigned_to',
            'serial_number', 'model_number', 'manufacturer',
            'warranty_expiry', 'insurance_policy', 'insurance_expiry',
            'last_maintenance_date', 'next_maintenance_date', 'maintenance_notes'
        ]
        widgets = {
            'asset_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter asset name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter asset description'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'location': forms.Select(attrs={
                'class': 'form-control'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'purchase_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'purchase_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'current_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'salvage_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'depreciation_method': forms.Select(attrs={
                'class': 'form-control'
            }),
            'useful_life_years': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'form-control'
            }),
            'serial_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter serial number'
            }),
            'model_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter model number'
            }),
            'manufacturer': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter manufacturer name'
            }),
            'warranty_expiry': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'insurance_policy': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter insurance policy number'
            }),
            'insurance_expiry': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'last_maintenance_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'next_maintenance_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'maintenance_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter maintenance notes'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter active categories, locations, statuses, and depreciation methods
        self.fields['category'].queryset = AssetCategory.objects.all()
        self.fields['location'].queryset = AssetLocation.objects.filter(is_active=True)
        self.fields['status'].queryset = AssetStatus.objects.filter(is_active=True)
        self.fields['depreciation_method'].queryset = AssetDepreciation.objects.filter(is_active=True)
        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True)

    def clean_purchase_date(self):
        purchase_date = self.cleaned_data['purchase_date']
        if purchase_date > date.today():
            raise ValidationError('Purchase date cannot be in the future.')
        return purchase_date

    def clean_current_value(self):
        current_value = self.cleaned_data['current_value']
        purchase_value = self.cleaned_data.get('purchase_value', 0)
        if current_value > purchase_value:
            raise ValidationError('Current value cannot be greater than purchase value.')
        return current_value

    def clean_salvage_value(self):
        salvage_value = self.cleaned_data['salvage_value']
        purchase_value = self.cleaned_data.get('purchase_value', 0)
        if salvage_value > purchase_value:
            raise ValidationError('Salvage value cannot be greater than purchase value.')
        return salvage_value


class AssetMovementForm(forms.ModelForm):
    """Form for recording asset movements"""
    
    class Meta:
        model = AssetMovement
        fields = ['movement_type', 'from_location', 'to_location', 'from_user', 'to_user', 'movement_date', 'reason', 'notes']
        widgets = {
            'movement_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'from_location': forms.Select(attrs={
                'class': 'form-control'
            }),
            'to_location': forms.Select(attrs={
                'class': 'form-control'
            }),
            'from_user': forms.Select(attrs={
                'class': 'form-control'
            }),
            'to_user': forms.Select(attrs={
                'class': 'form-control'
            }),
            'movement_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter reason for movement'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter additional notes'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['from_location'].queryset = AssetLocation.objects.filter(is_active=True)
        self.fields['to_location'].queryset = AssetLocation.objects.filter(is_active=True)
        self.fields['from_user'].queryset = User.objects.filter(is_active=True)
        self.fields['to_user'].queryset = User.objects.filter(is_active=True)

    def clean(self):
        cleaned_data = super().clean()
        movement_type = cleaned_data.get('movement_type')
        from_location = cleaned_data.get('from_location')
        to_location = cleaned_data.get('to_location')
        from_user = cleaned_data.get('from_user')
        to_user = cleaned_data.get('to_user')

        if movement_type == 'transfer':
            if not from_location or not to_location:
                raise ValidationError('Both from and to locations are required for transfers.')
            if from_location == to_location:
                raise ValidationError('From and to locations cannot be the same.')

        if movement_type == 'assignment':
            if not to_user:
                raise ValidationError('To user is required for assignments.')

        if movement_type == 'return':
            if not from_user:
                raise ValidationError('From user is required for returns.')

        return cleaned_data


class AssetMaintenanceForm(forms.ModelForm):
    """Form for recording asset maintenance"""
    
    class Meta:
        model = AssetMaintenance
        fields = ['maintenance_type', 'maintenance_date', 'description', 'cost', 'performed_by', 'next_maintenance_date', 'notes']
        widgets = {
            'maintenance_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'maintenance_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter maintenance description'
            }),
            'cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'performed_by': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter who performed the maintenance'
            }),
            'next_maintenance_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter additional notes'
            })
        }

    def clean_maintenance_date(self):
        maintenance_date = self.cleaned_data['maintenance_date']
        if maintenance_date > date.today():
            raise ValidationError('Maintenance date cannot be in the future.')
        return maintenance_date

    def clean_cost(self):
        cost = self.cleaned_data['cost']
        if cost < 0:
            raise ValidationError('Cost cannot be negative.')
        return cost


class AssetSearchForm(forms.Form):
    """Form for searching and filtering assets"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search assets...'
        })
    )
    category = forms.ModelChoiceField(
        queryset=AssetCategory.objects.all(),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    location = forms.ModelChoiceField(
        queryset=AssetLocation.objects.filter(is_active=True),
        required=False,
        empty_label="All Locations",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    status = forms.ModelChoiceField(
        queryset=AssetStatus.objects.filter(is_active=True),
        required=False,
        empty_label="All Statuses",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        empty_label="All Users",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    purchase_date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    purchase_date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    value_min = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': 'Min value'
        })
    )
    value_max = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': 'Max value'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        purchase_date_from = cleaned_data.get('purchase_date_from')
        purchase_date_to = cleaned_data.get('purchase_date_to')
        value_min = cleaned_data.get('value_min')
        value_max = cleaned_data.get('value_max')

        if purchase_date_from and purchase_date_to and purchase_date_from > purchase_date_to:
            raise ValidationError('From date cannot be after to date.')

        if value_min and value_max and value_min > value_max:
            raise ValidationError('Minimum value cannot be greater than maximum value.')

        return cleaned_data


class AssetDisposalForm(forms.Form):
    """Form for disposing assets"""
    disposal_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    disposal_reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter disposal reason'
        })
    )
    disposal_value = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': '0.00'
        })
    )

    def clean_disposal_date(self):
        disposal_date = self.cleaned_data['disposal_date']
        if disposal_date > date.today():
            raise ValidationError('Disposal date cannot be in the future.')
        return disposal_date 