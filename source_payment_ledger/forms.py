from django import forms
from payment_source.models import PaymentSource
from django.utils import timezone
from datetime import datetime, timedelta


class SourcePaymentLedgerForm(forms.Form):
    """Form for filtering Source Payment Ledger report"""
    
    payment_sources = forms.ModelMultipleChoiceField(
        queryset=PaymentSource.objects.filter(active=True).order_by('name'),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        required=False,
        help_text="Select payment sources to include in the report. Leave empty to include all."
    )
    
    date_from = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        required=False,
        help_text="Start date for the report (optional)"
    )
    
    date_to = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        required=False,
        help_text="End date for the report (optional)"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set default date range to current fiscal year or last 12 months
        today = timezone.now().date()
        year_ago = today - timedelta(days=365)
        
        if not self.data:
            self.fields['date_from'].initial = year_ago
            self.fields['date_to'].initial = today
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to:
            if date_from > date_to:
                raise forms.ValidationError("Start date cannot be later than end date.")
        
        return cleaned_data


class SourcePaymentLedgerExportForm(forms.Form):
    """Form for exporting Source Payment Ledger report"""
    
    EXPORT_FORMATS = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    ]
    
    export_format = forms.ChoiceField(
        choices=EXPORT_FORMATS,
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='pdf'
    )
    
    include_details = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Include detailed transaction breakdown"
    )