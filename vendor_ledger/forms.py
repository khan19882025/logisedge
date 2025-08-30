from django import forms
from django.utils import timezone
from customer.models import Customer, CustomerType
from .models import VendorLedgerReport


class VendorLedgerFilterForm(forms.Form):
    """Form for filtering vendor ledger report"""
    
    PAYMENT_STATUS_CHOICES = [
        ('all', 'All'),
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('partially_paid', 'Partially Paid'),
    ]
    
    vendor = forms.ModelChoiceField(
        queryset=Customer.objects.none(),  # Will be set in __init__
        required=False,
        empty_label="All Vendors",
        widget=forms.Select(attrs={
            'class': 'form-control select2',
            'data-placeholder': 'Select Vendor'
        })
    )
    
    date_from = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'From Date'
        })
    )
    
    date_to = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'To Date'
        })
    )
    
    payment_status = forms.ChoiceField(
        choices=PAYMENT_STATUS_CHOICES,
        required=False,
        initial='all',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Show only customers with 'Vendor' or 'Supplier' types
        try:
            vendor_types = CustomerType.objects.filter(name__in=['Vendor', 'Supplier'])
            if vendor_types.exists():
                self.fields['vendor'].queryset = Customer.objects.filter(
                    customer_types__in=vendor_types,
                    is_active=True
                ).distinct().order_by('customer_name')
            else:
                # Fallback: try to find by code
                vendor_types = CustomerType.objects.filter(code__in=['VEN', 'SUP'])
                if vendor_types.exists():
                    self.fields['vendor'].queryset = Customer.objects.filter(
                        customer_types__in=vendor_types,
                        is_active=True
                    ).distinct().order_by('customer_name')
                else:
                    self.fields['vendor'].queryset = Customer.objects.none()
        except CustomerType.DoesNotExist:
            self.fields['vendor'].queryset = Customer.objects.none()
        
        # Set default date range (current month)
        today = timezone.now().date()
        first_day_of_month = today.replace(day=1)
        
        if not self.data:
            self.fields['date_from'].initial = first_day_of_month
            self.fields['date_to'].initial = today
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to:
            if date_from > date_to:
                raise forms.ValidationError("From date cannot be later than to date.")
            
            # Check if date range is not too far in the future
            today = timezone.now().date()
            if date_from > today:
                raise forms.ValidationError("From date cannot be in the future.")
        
        return cleaned_data


class QuickFilterForm(forms.Form):
    """Form for quick date range filters"""
    
    QUICK_FILTER_CHOICES = [
        ('today', 'Today'),
        ('yesterday', 'Yesterday'),
        ('this_week', 'This Week'),
        ('last_week', 'Last Week'),
        ('this_month', 'This Month'),
        ('last_month', 'Last Month'),
        ('this_quarter', 'This Quarter'),
        ('last_quarter', 'Last Quarter'),
        ('this_year', 'This Year'),
        ('last_year', 'Last Year'),
    ]
    
    quick_filter = forms.ChoiceField(
        choices=QUICK_FILTER_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'onchange': 'setQuickFilter(this.value)'
        })
    )


class VendorLedgerReportForm(forms.ModelForm):
    """Form for creating/editing vendor ledger report configurations"""
    
    class Meta:
        model = VendorLedgerReport
        fields = ['report_name', 'vendor', 'date_from', 'date_to', 'payment_status']
        widgets = {
            'report_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter report name'
            }),
            'vendor': forms.Select(attrs={
                'class': 'form-control select2',
                'data-placeholder': 'Select Vendor'
            }),
            'date_from': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'date_to': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'payment_status': forms.Select(attrs={
                'class': 'form-control'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Show only customers with 'Vendor' or 'Supplier' types
        try:
            vendor_types = CustomerType.objects.filter(name__in=['Vendor', 'Supplier'])
            if vendor_types.exists():
                self.fields['vendor'].queryset = Customer.objects.filter(
                    customer_types__in=vendor_types,
                    is_active=True
                ).distinct().order_by('customer_name')
            else:
                # Fallback: try to find by code
                vendor_types = CustomerType.objects.filter(code__in=['VEN', 'SUP'])
                if vendor_types.exists():
                    self.fields['vendor'].queryset = Customer.objects.filter(
                        customer_types__in=vendor_types,
                        is_active=True
                    ).distinct().order_by('customer_name')
                else:
                    self.fields['vendor'].queryset = Customer.objects.none()
        except CustomerType.DoesNotExist:
            self.fields['vendor'].queryset = Customer.objects.none()
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError("From date cannot be later than to date.")
        
        return cleaned_data