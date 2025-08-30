from django.db import models
from django.contrib.auth.models import User
from customer.models import Customer
from invoice.models import Invoice
from customer_payments.models import CustomerPayment
from company.company_model import Company
from fiscal_year.models import FiscalYear
from decimal import Decimal
from django.utils import timezone


class PartnerLedgerReport(models.Model):
    """Model to store partner ledger report configurations"""
    
    PAYMENT_STATUS_CHOICES = [
        ('all', 'All'),
        ('pending', 'Pending'),
        ('fully_paid', 'Fully Paid'),
        ('partially_paid', 'Partially Paid'),
    ]
    
    # Report Configuration
    report_name = models.CharField(max_length=100, help_text="Name for this report configuration")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True, 
                               help_text="Specific customer (leave blank for all customers)")
    date_from = models.DateField(help_text="Start date for the report")
    date_to = models.DateField(help_text="End date for the report")
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, 
                                    default='all', help_text="Payment status filter")
    
    # Company and Fiscal Year
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.CASCADE)
    
    # Audit fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                 related_name='partner_ledger_reports_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                 related_name='partner_ledger_reports_updated')
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Partner Ledger Report'
        verbose_name_plural = 'Partner Ledger Reports'
    
    def __str__(self):
        customer_name = self.customer.customer_name if self.customer else "All Customers"
        return f"{self.report_name} - {customer_name} ({self.date_from} to {self.date_to})"


class PartnerLedgerEntry(models.Model):
    """Model to represent individual entries in partner ledger"""
    
    ENTRY_TYPES = [
        ('invoice', 'Invoice'),
        ('payment', 'Payment'),
        ('credit_note', 'Credit Note'),
        ('debit_note', 'Debit Note'),
        ('adjustment', 'Adjustment'),
    ]
    
    # Basic Information
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPES)
    entry_date = models.DateField()
    reference_number = models.CharField(max_length=50, help_text="Invoice number, payment number, etc.")
    description = models.TextField()
    
    # Financial Information
    debit_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    credit_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    running_balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Related Objects
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, null=True, blank=True)
    payment = models.ForeignKey(CustomerPayment, on_delete=models.CASCADE, null=True, blank=True)
    
    # Company and Fiscal Year
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.CASCADE)
    
    # Audit fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['customer', 'entry_date', 'created_at']
        verbose_name = 'Partner Ledger Entry'
        verbose_name_plural = 'Partner Ledger Entries'
        indexes = [
            models.Index(fields=['customer', 'entry_date']),
            models.Index(fields=['entry_type']),
            models.Index(fields=['reference_number']),
            models.Index(fields=['company', 'fiscal_year']),
        ]
    
    def __str__(self):
        return f"{self.customer.customer_name} - {self.reference_number} ({self.entry_date})"
    
    @property
    def net_amount(self):
        """Calculate net amount (debit - credit)"""
        return self.debit_amount - self.credit_amount