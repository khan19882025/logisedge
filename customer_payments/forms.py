from django import forms
from django.core.exceptions import ValidationError
from .models import CustomerPayment
from customer.models import Customer
from invoice.models import Invoice
from bank_accounts.models import BankAccount
from chart_of_accounts.models import ChartOfAccount
from company.company_model import Company
from datetime import date

class CustomerPaymentForm(forms.ModelForm):
    class Meta:
        model = CustomerPayment
        fields = ['customer', 'payment_date', 'amount', 'payment_method', 'bank_account', 'ledger_account', 'partial_payment_option', 'notes']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'payment_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'value': date.today().strftime('%Y-%m-%d')
            }),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'bank_account': forms.Select(attrs={'class': 'form-select'}),
            'ledger_account': forms.Select(attrs={'class': 'form-select'}),
            'partial_payment_option': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': '3'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Import CustomerType to filter by customer type
        from customer.models import CustomerType
        
        # Get customers who have unpaid or partially paid invoices
        # This allows customers to create multiple payments for different invoices
        # When a payment is deleted, the customer becomes available again
        # We need to show customers who have ANY unpaid invoices, even if they also have paid ones
        
        # First, get the 'Customer' type (CUS) to filter only actual customers, not suppliers/vendors
        try:
            customer_type = CustomerType.objects.get(code='CUS')
        except CustomerType.DoesNotExist:
            # Fallback: if CUS doesn't exist, try to get by name
            try:
                customer_type = CustomerType.objects.get(name='Customer')
            except CustomerType.DoesNotExist:
                # If no customer type found, show no customers to prevent showing suppliers
                self.fields['customer'].queryset = Customer.objects.none()
                return
        
        # Get only customers with 'Customer' type who have invoices
        customers_with_invoices = Customer.objects.filter(
            customer_types=customer_type,
            is_active=True,
            invoice__isnull=False
        ).distinct()
        
        # Then filter to show only those who have at least one unpaid invoice
        # Use a QuerySet instead of a list for better performance and Django compatibility
        available_customers = customers_with_invoices.filter(
            invoice__status__in=['draft', 'sent', 'overdue', 'partial']
        ).distinct().order_by('customer_name')
        
        # Debug logging
        print(f"🔍 Customer Payment Form - Available Customers (Customer Type Only):")
        for customer in available_customers:
            unpaid_count = customer.invoice_set.filter(
                status__in=['draft', 'sent', 'overdue', 'partial']
            ).count()
            total_count = customer.invoice_set.count()
            customer_types = ", ".join([ct.name for ct in customer.customer_types.all()])
            print(f"  ✅ {customer.customer_name} ({customer_types}): {unpaid_count}/{total_count} invoices unpaid")
        
        self.fields['customer'].queryset = available_customers
        
        # Make partial payment option not required
        self.fields['partial_payment_option'].required = False
        
        # Make bank account not required
        self.fields['bank_account'].required = False
        
        # Set up ledger account queryset - initially show all active accounts
        self.fields['ledger_account'].queryset = ChartOfAccount.objects.filter(
            is_active=True,
            is_group=False  # Only show leaf accounts, not group accounts
        ).order_by('account_code')
        
        # Set default payment date to today if not already set
        if not self.instance.pk and not self.data:
            self.fields['payment_date'].initial = date.today()

    def clean(self):
        cleaned_data = super().clean()
        
        # Professional ERP validation for ledger account selection
        ledger_account = cleaned_data.get('ledger_account')
        payment_method = cleaned_data.get('payment_method')
        amount = cleaned_data.get('amount')
        
        if ledger_account and amount:
            # Validate that selected ledger account is appropriate for customer payments
            self._validate_ledger_account_for_payment(ledger_account, payment_method, amount)
        
        return cleaned_data
    
    def _validate_ledger_account_for_payment(self, ledger_account, payment_method, amount):
        """
        Professional ERP validation for ledger account selection.
        Ensures the selected account follows proper accounting principles.
        """
        # Rule 1: Only allow ASSET accounts for customer payments (cash, bank, etc.)
        if ledger_account.account_type.category != 'ASSET':
            raise ValidationError({
                'ledger_account': f'Invalid account type. Customer payments must be posted to ASSET accounts only. '
                                f'Selected account "{ledger_account.name}" is a {ledger_account.account_type.get_category_display()} account.'
            })
        
        # Rule 2: Validate account nature is DEBIT or BOTH (assets increase with debits, BOTH can handle both sides)
        if ledger_account.account_nature not in ['DEBIT', 'BOTH']:
            raise ValidationError({
                'ledger_account': f'Invalid account nature. Customer payments require DEBIT nature accounts. '
                                f'Selected account "{ledger_account.name}" has {ledger_account.account_nature} nature.'
            })
        
        # Rule 3: Ensure account is active and not a group account
        if not ledger_account.is_active:
            raise ValidationError({
                'ledger_account': f'Selected account "{ledger_account.name}" is inactive. Please select an active account.'
            })
        
        if ledger_account.is_group:
            raise ValidationError({
                'ledger_account': f'Cannot post to group account "{ledger_account.name}". Please select a detail account.'
            })
        
        # Rule 4: Payment method specific validations
        if payment_method == 'bank' and 'bank' not in ledger_account.name.lower():
            # Warning for bank payments not going to bank accounts
            pass  # Could add warning here if needed
        
        if payment_method == 'cash' and 'cash' not in ledger_account.name.lower():
            # Warning for cash payments not going to cash accounts
            pass  # Could add warning here if needed
        
        # Rule 5: Validate amount is positive
        if amount <= 0:
            raise ValidationError({
                'amount': 'Payment amount must be greater than zero.'
            })
        
        # Rule 6: Professional ERP message about debit posting
        # This will be shown as a success message in the view
        self._debit_posting_info = {
            'account': ledger_account,
            'amount': amount,
            'message': f'✅ Professional ERP Standard: Payment will DEBIT "{ledger_account.account_code} - {ledger_account.name}" '
                      f'for {amount:.2f}, increasing your {ledger_account.name.lower()} balance.'
        }