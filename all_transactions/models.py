from django.db import models
from django.contrib.auth.models import User
from chart_of_accounts.models import ChartOfAccount as Account
from django.utils import timezone


class TransactionView(models.Model):
    """
    A view model that aggregates transactions from different modules
    This is used for displaying all transactions in a unified view
    """
    
    TRANSACTION_TYPES = [
        ('sales_invoice', 'Sales Invoice'),
        ('purchase_invoice', 'Purchase Invoice'),
        ('payment_voucher', 'Payment Voucher'),
        ('receipt_voucher', 'Receipt Voucher'),
        ('journal_entry', 'Journal Entry'),
        ('contra_entry', 'Contra Entry'),
        ('adjustment_entry', 'Adjustment Entry'),
        ('opening_balance', 'Opening Balance'),
    ]
    
    STATUS_CHOICES = [
        ('posted', 'Posted'),
        ('draft', 'Draft'),
        ('reversed', 'Reversed'),
    ]
    
    # Transaction details
    transaction_date = models.DateField()
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    document_number = models.CharField(max_length=50)
    reference_number = models.CharField(max_length=50, blank=True, null=True)
    
    # Account details
    debit_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='debit_transactions', null=True, blank=True)
    credit_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='credit_transactions', null=True, blank=True)
    
    # Amount and details
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    narration = models.TextField(blank=True, null=True)
    
    # User and status
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posted_transactions')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='posted')
    
    # Source document reference
    source_model = models.CharField(max_length=50)  # e.g., 'invoice.Invoice', 'payment_voucher.PaymentVoucher'
    source_id = models.IntegerField()  # ID of the source document
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'all_transactions_view'
        ordering = ['-transaction_date', '-created_at']
        indexes = [
            models.Index(fields=['transaction_date']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['status']),
            models.Index(fields=['posted_by']),
            models.Index(fields=['debit_account']),
            models.Index(fields=['credit_account']),
            models.Index(fields=['source_model', 'source_id']),
        ]
    
    def __str__(self):
        return f"{self.transaction_type} - {self.document_number} - {self.amount}"
    
    @property
    def transaction_type_display(self):
        return dict(self.TRANSACTION_TYPES)[self.transaction_type]
    
    @property
    def status_display(self):
        return dict(self.STATUS_CHOICES)[self.status]
    
    @property
    def source_url(self):
        """Generate URL to the source document"""
        if self.source_model == 'invoice.Invoice':
            return f'/accounting/invoice/{self.source_id}/'
        elif self.source_model == 'payment_voucher.PaymentVoucher':
            return f'/accounting/payment-voucher/{self.source_id}/'
        elif self.source_model == 'receipt_voucher.ReceiptVoucher':
            return f'/accounting/receipt-voucher/{self.source_id}/'
        elif self.source_model == 'general_journal.GeneralJournal':
            return f'/accounting/general-journal/{self.source_id}/'
        elif self.source_model == 'contra_entry.ContraEntry':
            return f'/accounting/contra-entry/{self.source_id}/'
        elif self.source_model == 'adjustment_entry.AdjustmentEntry':
            return f'/accounting/adjustment-entry/{self.source_id}/'
        elif self.source_model == 'opening_balance.OpeningBalanceEntry':
            return f'/accounting/opening-balance/{self.source_id}/'
        return '#' 