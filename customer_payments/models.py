from django.db import models
from customer.models import Customer
from invoice.models import Invoice
from bank_accounts.models import BankAccount
from chart_of_accounts.models import ChartOfAccount
from datetime import datetime

class CustomerPayment(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('credit_card', 'Credit Card'),
        ('cheque', 'Cheque'),
        ('other', 'Other'),
    ]
    
    PARTIAL_PAYMENT_OPTIONS = [
        ('keep_open', 'Keep Invoice Open'),
        ('discount', 'Apply Discount'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
    bank_account = models.ForeignKey(BankAccount, on_delete=models.SET_NULL, null=True, blank=True, 
                                   help_text="Select bank account for bank transfers")
    ledger_account = models.ForeignKey(ChartOfAccount, on_delete=models.SET_NULL, null=True, blank=True,
                                     help_text="Select ledger account for this payment")
    partial_payment_option = models.CharField(max_length=20, choices=PARTIAL_PAYMENT_OPTIONS, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Payment #{self.id} - {self.customer}"

    @property
    def formatted_payment_id(self):
        year = self.payment_date.year if self.payment_date else datetime.now().year
        if self.id:
            return f"CPR-{year}-{self.id:04d}"
        else:
            return f"CPR-{year}-XXXX"

class CustomerPaymentInvoice(models.Model):
    payment = models.ForeignKey(CustomerPayment, on_delete=models.CASCADE, related_name='payment_invoices')
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    amount_received = models.DecimalField(max_digits=12, decimal_places=2)
    original_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.payment} -> {self.invoice}"