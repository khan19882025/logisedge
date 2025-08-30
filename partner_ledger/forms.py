from django import forms
from django.utils import timezone
from django.db import models
from customer.models import Customer, CustomerType
from company.company_model import Company
from fiscal_year.models import FiscalYear
from .models import PartnerLedgerReport
from datetime import datetime, timedelta


class PartnerLedgerFilterForm(forms.Form):
    """Form for filtering partner ledger report"""
    
    PAYMENT_STATUS_CHOICES = [
        ('all', 'All'),
        ('pending', 'Pending'),
        ('fully_paid', 'Fully Paid'),
        ('partially_paid', 'Partially Paid'),
    ]
    
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.none(),  # Will be set in __init__
        required=False,
        empty_label="All Customers",
        widget=forms.Select(attrs={
            'class': 'form-control select2',
            'data-placeholder': 'Select Customer'
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
        
        # Show only customers with 'Customer' type (not suppliers, vendors, etc.)
        try:
            customer_type = CustomerType.objects.get(code='CUS')
            self.fields['customer'].queryset = Customer.objects.filter(
                customer_types=customer_type,
                is_active=True
            ).distinct().order_by('customer_name')
        except CustomerType.DoesNotExist:
            # Fallback: if CUS doesn't exist, try to get by name
            try:
                customer_type = CustomerType.objects.get(name='Customer')
                self.fields['customer'].queryset = Customer.objects.filter(
                    customer_types=customer_type,
                    is_active=True
                ).distinct().order_by('customer_name')
            except CustomerType.DoesNotExist:
                # If no customer type found, show no customers to prevent showing suppliers
                self.fields['customer'].queryset = Customer.objects.none()
        
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
                raise forms.ValidationError("From date cannot be greater than To date.")
            
            # Check if date range is not too large (optional validation)
            if (date_to - date_from).days > 365:
                raise forms.ValidationError("Date range cannot exceed 365 days.")
        
        return cleaned_data


class PartnerLedgerReportForm(forms.ModelForm):
    """Form for creating/editing partner ledger report configurations"""
    
    class Meta:
        model = PartnerLedgerReport
        fields = ['report_name', 'customer', 'date_from', 'date_to', 'payment_status']
        widgets = {
            'report_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter report name'
            }),
            'customer': forms.Select(attrs={
                'class': 'form-control select2',
                'data-placeholder': 'Select Customer'
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
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Show only customers with 'Customer' type (not suppliers, vendors, etc.)
        try:
            customer_type = CustomerType.objects.get(code='CUS')
            self.fields['customer'].queryset = Customer.objects.filter(
                customer_types=customer_type,
                is_active=True
            ).distinct().order_by('customer_name')
        except CustomerType.DoesNotExist:
            # Fallback: if CUS doesn't exist, try to get by name
            try:
                customer_type = CustomerType.objects.get(name='Customer')
                self.fields['customer'].queryset = Customer.objects.filter(
                    customer_types=customer_type,
                    is_active=True
                ).distinct().order_by('customer_name')
            except CustomerType.DoesNotExist:
                # If no customer type found, show no customers to prevent showing suppliers
                self.fields['customer'].queryset = Customer.objects.none()
        
        self.fields['customer'].empty_label = "All Customers"
        
        # Set default date range if creating new report
        if not self.instance.pk:
            today = timezone.now().date()
            first_day_of_month = today.replace(day=1)
            self.fields['date_from'].initial = first_day_of_month
            self.fields['date_to'].initial = today
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.user:
            if not instance.pk:
                instance.created_by = self.user
                # Set company and fiscal year
                instance.company = Company.objects.filter(is_active=True).first()
                instance.fiscal_year = FiscalYear.objects.filter(is_active=True).first()
            instance.updated_by = self.user
        
        if commit:
            instance.save()
        
        return instance


class QuickFilterForm(forms.Form):
    """Quick filter form for common date ranges"""
    
    QUICK_FILTERS = [
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
        ('custom', 'Custom Range'),
    ]
    
    quick_filter = forms.ChoiceField(
        choices=QUICK_FILTERS,
        required=False,
        initial='this_month',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'quick-filter-select'
        })
    )
    
    def get_date_range(self, filter_type):
        """Get date range based on filter type"""
        today = timezone.now().date()
        
        if filter_type == 'today':
            return today, today
        elif filter_type == 'yesterday':
            yesterday = today - timedelta(days=1)
            return yesterday, yesterday
        elif filter_type == 'this_week':
            start_week = today - timedelta(days=today.weekday())
            return start_week, today
        elif filter_type == 'last_week':
            start_last_week = today - timedelta(days=today.weekday() + 7)
            end_last_week = start_last_week + timedelta(days=6)
            return start_last_week, end_last_week
        elif filter_type == 'this_month':
            start_month = today.replace(day=1)
            return start_month, today
        elif filter_type == 'last_month':
            first_this_month = today.replace(day=1)
            last_month_end = first_this_month - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)
            return last_month_start, last_month_end
        elif filter_type == 'this_quarter':
            quarter = (today.month - 1) // 3 + 1
            start_quarter = today.replace(month=(quarter - 1) * 3 + 1, day=1)
            return start_quarter, today
        elif filter_type == 'last_quarter':
            quarter = (today.month - 1) // 3 + 1
            if quarter == 1:
                last_quarter_start = today.replace(year=today.year - 1, month=10, day=1)
                last_quarter_end = today.replace(year=today.year - 1, month=12, day=31)
            else:
                last_quarter_start = today.replace(month=(quarter - 2) * 3 + 1, day=1)
                last_quarter_end = today.replace(month=(quarter - 1) * 3, day=1) - timedelta(days=1)
            return last_quarter_start, last_quarter_end
        elif filter_type == 'this_year':
            start_year = today.replace(month=1, day=1)
            return start_year, today
        elif filter_type == 'last_year':
            start_last_year = today.replace(year=today.year - 1, month=1, day=1)
            end_last_year = today.replace(year=today.year - 1, month=12, day=31)
            return start_last_year, end_last_year
        else:
            # Default to this month
            start_month = today.replace(day=1)
            return start_month, today