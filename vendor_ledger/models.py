from django.db import models
from django.contrib.auth.models import User
from customer.models import Customer
from company.company_model import Company
from fiscal_year.models import FiscalYear


class VendorLedgerReport(models.Model):
    """Model to store vendor ledger report configurations"""
    
    PAYMENT_STATUS_CHOICES = [
        ('all', 'All'),
        ('pending', 'Pending'),
        ('fully_paid', 'Fully Paid'),
        ('partially_paid', 'Partially Paid'),
    ]
    
    # Report Configuration
    report_name = models.CharField(max_length=100, help_text="Name for this report configuration")
    vendor = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True, 
                              help_text="Specific vendor (leave blank for all vendors)")
    date_from = models.DateField(help_text="Start date for the report")
    date_to = models.DateField(help_text="End date for the report")
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, 
                                    default='all', help_text="Payment status filter")
    
    # Company and Fiscal Year
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.CASCADE)
    
    # Audit fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                 related_name='vendor_ledger_reports_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                 related_name='vendor_ledger_reports_updated')
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vendor_ledger_report'
        verbose_name = 'Vendor Ledger Report'
        verbose_name_plural = 'Vendor Ledger Reports'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.report_name} - {self.date_from} to {self.date_to}"
    
    @property
    def date_range_display(self):
        return f"{self.date_from.strftime('%d/%m/%Y')} - {self.date_to.strftime('%d/%m/%Y')}"
    
    @property
    def vendor_display(self):
        return self.vendor.customer_name if self.vendor else "All Vendors"