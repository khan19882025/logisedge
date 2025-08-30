from django import forms
from django.utils import timezone
from customer.models import Customer
from salesman.models import Salesman


class AgingReportForm(forms.Form):
    """
    Form for filtering accounts receivable aging report
    """
    as_of_date = forms.DateField(
        label='As of Date',
        initial=timezone.now().date(),
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'placeholder': 'Select date'
        })
    )
    
    customer = forms.ModelChoiceField(
        label='Customer',
        queryset=Customer.objects.none(),  # Will be set in __init__
        required=False,
        empty_label='All Customers',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'placeholder': 'Select customer (optional)'
        })
    )
    
    salesman = forms.ModelChoiceField(
        label='Salesman',
        queryset=Salesman.objects.none(),  # Will be set in __init__
        required=False,
        empty_label='All Salesmen',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'placeholder': 'Select salesman (optional)'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set customer queryset to only show customers with unpaid invoices
        from invoice.models import Invoice
        unpaid_statuses = ['draft', 'sent', 'overdue', 'partial']
        
        customers_with_unpaid_invoices = Customer.objects.filter(
            is_active=True,
            invoice__status__in=unpaid_statuses
        ).distinct().order_by('customer_name')
        
        self.fields['customer'].queryset = customers_with_unpaid_invoices
        self.fields['salesman'].queryset = Salesman.objects.filter(status='active').order_by('first_name', 'last_name')
    
    customer_code = forms.CharField(
        label='Customer Code',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter customer code (optional)'
        })
    )
    
    min_amount = forms.DecimalField(
        label='Minimum Amount',
        required=False,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01'
        })
    )
    
    aging_bucket = forms.ChoiceField(
        label='Aging Bucket',
        required=False,
        choices=[
            ('', 'All Buckets'),
            ('current', 'Current'),
            ('1-30', '1-30 Days'),
            ('31-60', '31-60 Days'),
            ('61-90', '61-90 Days'),
            ('over_90', 'Over 90 Days'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    show_zero_balances = forms.BooleanField(
        label='Show Zero Balances',
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    report_type = forms.ChoiceField(
        label='Report Type',
        required=False,
        choices=[
            ('summary', 'Summary'),
            ('details', 'Details'),
            ('summary_with_advance', 'Summary with Advance Payment'),
        ],
        initial='summary',
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class AgingReportExportForm(forms.Form):
    """
    Form for exporting aging report
    """
    export_format = forms.ChoiceField(
        label='Export Format',
        choices=[
            ('pdf', 'PDF'),
            ('excel', 'Excel'),
            ('csv', 'CSV'),
        ],
        initial='pdf',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    include_details = forms.BooleanField(
        label='Include Invoice Details',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )