from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import RFUser, ScanSession, ScanRecord, Location, Item


class RFLoginForm(AuthenticationForm):
    """RF Scanner Login Form"""
    employee_id = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Employee ID',
            'autocomplete': 'off'
        })
    )
    
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Full Name',
            'autocomplete': 'off'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove username field since we're using name instead
        if 'username' in self.fields:
            del self.fields['username']
        
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })


class ScanForm(forms.ModelForm):
    """Scan Record Form"""
    barcode = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Scan barcode...',
            'autofocus': True,
            'autocomplete': 'off'
        })
    )
    quantity = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0.01',
            'step': '0.01'
        })
    )
    location = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Location (optional)'
        })
    )

    class Meta:
        model = ScanRecord
        fields = ['barcode', 'quantity', 'location', 'notes']


class SessionForm(forms.ModelForm):
    """Scan Session Form"""
    class Meta:
        model = ScanSession
        fields = ['session_type', 'notes']
        widgets = {
            'session_type': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        }


class LocationForm(forms.ModelForm):
    """Location Form"""
    class Meta:
        model = Location
        fields = ['location_code', 'location_name', 'location_type']
        widgets = {
            'location_code': forms.TextInput(attrs={'class': 'form-control'}),
            'location_name': forms.TextInput(attrs={'class': 'form-control'}),
            'location_type': forms.TextInput(attrs={'class': 'form-control'})
        }


class ItemForm(forms.ModelForm):
    """Item Form"""
    class Meta:
        model = Item
        fields = ['item_code', 'item_name', 'barcode', 'description', 'unit']
        widgets = {
            'item_code': forms.TextInput(attrs={'class': 'form-control'}),
            'item_name': forms.TextInput(attrs={'class': 'form-control'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'unit': forms.TextInput(attrs={'class': 'form-control'})
        } 