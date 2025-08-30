from django import forms
from django.core.validators import MinValueValidator
from decimal import Decimal
from datetime import date
from .models import SupplierPayment
from customer.models import Customer, CustomerType
from chart_of_accounts.models import ChartOfAccount

class SupplierPaymentForm(forms.ModelForm):
    class Meta:
        model = SupplierPayment
        fields = ['supplier', 'payment_date', 'amount', 'payment_method', 'ledger_account', 'reference_number', 'notes']
        widgets = {
            'supplier': forms.Select(attrs={
                'class': 'form-control',
                'id': 'supplier-select'
            }),
            'payment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'id': 'payment-date'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'id': 'payment-amount'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-control',
                'id': 'payment-method'
            }),
            'ledger_account': forms.Select(attrs={
                'class': 'form-control',
                'id': 'ledger-account'
            }),
            'reference_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter reference number',
                'id': 'reference-number'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter any additional notes',
                'id': 'payment-notes'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set current date as default for payment_date
        if not self.instance.pk:  # Only for new payments
            self.fields['payment_date'].initial = date.today()
        
        # Make ledger_account required
        self.fields['ledger_account'].required = True
        self.fields['ledger_account'].empty_label = "Select a ledger account"
        
        # Show only customers with vendor or supplier types who have unpaid invoices or pending bills
        vendor_supplier_types = CustomerType.objects.filter(
            name__icontains='vendor'
        ) | CustomerType.objects.filter(
            name__icontains='supplier'
        )
        
        # Get suppliers with unpaid invoices
        from invoice.models import Invoice
        unpaid_statuses = ['draft', 'sent', 'overdue']
        
        # Method 1: Suppliers who are main customers of unpaid invoices
        suppliers_with_unpaid_invoices = Customer.objects.filter(
            is_active=True,
            customer_types__in=vendor_supplier_types,
            invoice__status__in=unpaid_statuses
        ).distinct()
        
        # Method 2: Vendors/suppliers mentioned in invoice items of unpaid invoices
        vendors_in_invoice_items = set()
        unpaid_invoices = Invoice.objects.filter(status__in=unpaid_statuses)
        
        for invoice in unpaid_invoices:
            if invoice.invoice_items:
                for item in invoice.invoice_items:
                    vendor_field = item.get('vendor', '')
                    if vendor_field:
                        # Extract vendor code from format "VEN0001 - Waseem Transport (Vendor)"
                        if ' - ' in vendor_field:
                            vendor_code = vendor_field.split(' - ')[0].strip()
                            try:
                                vendor = Customer.objects.get(
                                    customer_code=vendor_code,
                                    is_active=True,
                                    customer_types__in=vendor_supplier_types
                                )
                                vendors_in_invoice_items.add(vendor.id)
                            except Customer.DoesNotExist:
                                continue
        
        # Method 3: Suppliers with pending supplier bills
        from supplier_bills.models import SupplierBill
        suppliers_with_pending_bills = set()
        
        # Get all vendor/supplier customer names
        vendor_supplier_names = Customer.objects.filter(
            is_active=True,
            customer_types__in=vendor_supplier_types
        ).values_list('customer_name', flat=True)
        
        # Find supplier bills with pending status
        pending_bills = SupplierBill.objects.filter(
            status__in=['draft', 'sent', 'overdue', 'paid'],
            supplier__in=vendor_supplier_names
        )
        
        # Map supplier names back to Customer objects
        for bill in pending_bills:
            try:
                supplier_customer = Customer.objects.get(
                    customer_name=bill.supplier,
                    is_active=True,
                    customer_types__in=vendor_supplier_types
                )
                suppliers_with_pending_bills.add(supplier_customer.id)
            except Customer.DoesNotExist:
                continue
        
        # Combine all methods
        all_supplier_ids = set(suppliers_with_unpaid_invoices.values_list('id', flat=True))
        all_supplier_ids.update(vendors_in_invoice_items)
        all_supplier_ids.update(suppliers_with_pending_bills)
        
        # Get final queryset
        final_suppliers = Customer.objects.filter(
            id__in=all_supplier_ids,
            is_active=True
        ).order_by('customer_name')
        
        self.fields['supplier'].queryset = final_suppliers
        
        # Set up ledger account queryset - initially show all active accounts
        self.fields['ledger_account'].queryset = ChartOfAccount.objects.filter(
            is_active=True,
            is_group=False  # Only show leaf accounts, not group accounts
        ).order_by('account_code')
        
        # Add validation
        self.fields['amount'].validators.append(MinValueValidator(Decimal('0.01')))
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount
    
    def clean_ledger_account(self):
        ledger_account = self.cleaned_data.get('ledger_account')
        if not ledger_account:
            raise forms.ValidationError("Ledger account is required for proper accounting.")
        return ledger_account