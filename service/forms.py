from django import forms
from django.core.exceptions import ValidationError
from .models import Service

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = '__all__'
        exclude = ['service_code', 'created_by', 'updated_by', 'created_at', 'updated_at']
        widgets = {
            'service_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter service name'
            }),
            'service_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4, 
                'placeholder': 'Enter detailed description'
            }),
            'short_description': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter short description'
            }),
            'base_price': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'placeholder': 'Enter base price'
            }),
            'sale_price': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'placeholder': 'Enter sale price'
            }),
            'cost_price': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'placeholder': 'Enter cost price'
            }),
            'currency': forms.Select(attrs={
                'class': 'form-select'
            }),
            'pricing_model': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter pricing model (Fixed, Variable, Per Unit, etc.)'
            }),
            'duration': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter estimated duration'
            }),
            'requirements': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Enter service requirements'
            }),
            'deliverables': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Enter service deliverables'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_available_online': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'has_vat': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make service_name required
        self.fields['service_name'].required = True
        self.fields['service_type'].required = True
        self.fields['service_type'].empty_label = "Select service type"
        self.fields['currency'].required = True
        self.fields['sale_price'].required = True
        self.fields['cost_price'].required = True
        # Show service_code as read-only if instance exists
        if self.instance and self.instance.pk:
            self.fields['service_code'] = forms.CharField(
                initial=self.instance.service_code,
                label='Service Code',
                required=False,
                widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
            )
    
    def clean_base_price(self):
        base_price = self.cleaned_data.get('base_price')
        if base_price and base_price < 0:
            raise ValidationError("Base price cannot be negative.")
        return base_price
    
    def clean_sale_price(self):
        sale_price = self.cleaned_data.get('sale_price')
        if sale_price is not None and sale_price < 0:
            raise ValidationError("Sale price cannot be negative.")
        return sale_price

    def clean_cost_price(self):
        cost_price = self.cleaned_data.get('cost_price')
        if cost_price is not None and cost_price < 0:
            raise ValidationError("Cost price cannot be negative.")
        return cost_price

    def clean_currency(self):
        currency = self.cleaned_data.get('currency')
        if currency:
            currency = currency.upper().strip()
            if len(currency) != 3:
                raise ValidationError("Currency code must be exactly 3 characters.")
        return currency

class ServiceSearchForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by service code, name, or description...'
        })
    )
    service_type = forms.ChoiceField(
        choices=[('', 'All Types')] + Service.SERVICE_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + Service.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    is_featured = forms.ChoiceField(
        choices=[('', 'All'), ('True', 'Featured'), ('False', 'Not Featured')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    ) 