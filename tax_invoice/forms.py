from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import TaxInvoice, TaxInvoiceItem, TaxInvoiceTemplate, TaxInvoiceSettings, TaxInvoiceExport


class TaxInvoiceForm(forms.ModelForm):
    """Form for creating and updating TaxInvoice objects"""
    
    class Meta:
        model = TaxInvoice
        fields = [
            'invoice_date', 'due_date', 'currency', 'status',
            'company_name', 'company_address', 'company_trn', 'company_phone', 'company_email', 'company_website',
            'customer_name', 'customer_address', 'customer_trn', 'customer_phone', 'customer_email',
            'notes', 'terms_conditions', 'payment_instructions'
        ]
        widgets = {
            'invoice_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'currency': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'company_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'company_trn': forms.TextInput(attrs={'class': 'form-control'}),
            'company_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'company_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'company_website': forms.URLInput(attrs={'class': 'form-control'}),
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'customer_trn': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'terms_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'payment_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default due date to 30 days from today
        if not self.instance.pk and not self.data:
            self.fields['due_date'].initial = timezone.now().date() + timedelta(days=30)
    
    def clean(self):
        cleaned_data = super().clean()
        invoice_date = cleaned_data.get('invoice_date')
        due_date = cleaned_data.get('due_date')
        
        if invoice_date and due_date:
            if due_date < invoice_date:
                raise ValidationError("Due date cannot be earlier than invoice date.")
        
        return cleaned_data


class TaxInvoiceItemForm(forms.ModelForm):
    """Form for creating and updating TaxInvoiceItem objects"""
    
    class Meta:
        model = TaxInvoiceItem
        fields = ['description', 'quantity', 'unit_price', 'vat_percentage', 'product_code', 'product_category']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'vat_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'product_code': forms.TextInput(attrs={'class': 'form-control'}),
            'product_category': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get('quantity')
        unit_price = cleaned_data.get('unit_price')
        vat_percentage = cleaned_data.get('vat_percentage')
        
        if quantity and quantity <= 0:
            raise ValidationError("Quantity must be greater than 0.")
        
        if unit_price and unit_price < 0:
            raise ValidationError("Unit price cannot be negative.")
        
        if vat_percentage and (vat_percentage < 0 or vat_percentage > 100):
            raise ValidationError("VAT percentage must be between 0 and 100.")
        
        return cleaned_data


# Create inline formset for TaxInvoiceItem objects
TaxInvoiceItemFormSet = forms.inlineformset_factory(
    TaxInvoice,
    TaxInvoiceItem,
    form=TaxInvoiceItemForm,
    extra=1,
    can_delete=True,
    fields=['description', 'quantity', 'unit_price', 'vat_percentage', 'product_code', 'product_category']
)


class TaxInvoiceTemplateForm(forms.ModelForm):
    """Form for creating and updating TaxInvoiceTemplate objects"""
    
    class Meta:
        model = TaxInvoiceTemplate
        fields = [
            'name', 'template_type', 'description',
            'include_logo', 'include_qr_code', 'include_bank_details', 'include_terms',
            'primary_color', 'secondary_color', 'font_family',
            'header_text', 'footer_text', 'terms_conditions',
            'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'template_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'include_logo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'include_qr_code': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'include_bank_details': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'include_terms': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'primary_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'secondary_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'font_family': forms.TextInput(attrs={'class': 'form-control'}),
            'header_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'footer_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'terms_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TaxInvoiceSettingsForm(forms.ModelForm):
    """Form for updating TaxInvoiceSettings"""
    
    class Meta:
        model = TaxInvoiceSettings
        fields = [
            'default_company_name', 'default_company_address', 'default_company_trn',
            'default_company_phone', 'default_company_email', 'default_company_website',
            'default_currency', 'default_payment_terms', 'default_vat_rate',
            'default_template', 'pdf_orientation', 'pdf_page_size',
            'email_subject_template', 'email_body_template',
            'require_customer_trn', 'require_vat_number', 'validate_vat_rates'
        ]
        widgets = {
            'default_company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'default_company_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'default_company_trn': forms.TextInput(attrs={'class': 'form-control'}),
            'default_company_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'default_company_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'default_company_website': forms.URLInput(attrs={'class': 'form-control'}),
            'default_currency': forms.Select(attrs={'class': 'form-control'}),
            'default_payment_terms': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'default_vat_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'default_template': forms.Select(attrs={'class': 'form-control'}),
            'pdf_orientation': forms.Select(attrs={'class': 'form-control'}),
            'pdf_page_size': forms.Select(attrs={'class': 'form-control'}),
            'email_subject_template': forms.TextInput(attrs={'class': 'form-control'}),
            'email_body_template': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'require_customer_trn': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'require_vat_number': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'validate_vat_rates': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TaxInvoiceSearchForm(forms.Form):
    """Form for searching TaxInvoice objects"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search invoices...'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + TaxInvoice.INVOICE_STATUS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    currency = forms.ChoiceField(
        choices=[('', 'All Currencies')] + TaxInvoice.CURRENCY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    customer_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Customer name...'})
    )


class TaxInvoiceExportForm(forms.Form):
    """Form for exporting TaxInvoice objects"""
    EXPORT_FORMATS = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('email', 'Email'),
    ]
    
    export_format = forms.ChoiceField(
        choices=EXPORT_FORMATS,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    include_items = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    include_company_details = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    include_customer_details = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    include_terms = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    email_to = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address...'})
    )
    email_subject = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email subject...'})
    )
    email_message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Email message...'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        export_format = cleaned_data.get('export_format')
        email_to = cleaned_data.get('email_to')
        
        if export_format == 'email' and not email_to:
            raise ValidationError("Email address is required for email export.")
        
        return cleaned_data


class TaxInvoiceCalculatorForm(forms.Form):
    """Form for tax calculation"""
    amount = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'})
    )
    vat_rate = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        initial=5.00,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'})
    )
    calculation_type = forms.ChoiceField(
        choices=[
            ('exclusive', 'VAT Exclusive (Add VAT)'),
            ('inclusive', 'VAT Inclusive (Extract VAT)'),
        ],
        initial='exclusive',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get('amount')
        vat_rate = cleaned_data.get('vat_rate')
        
        if amount and amount < 0:
            raise ValidationError("Amount cannot be negative.")
        
        if vat_rate and (vat_rate < 0 or vat_rate > 100):
            raise ValidationError("VAT rate must be between 0 and 100.")
        
        return cleaned_data
