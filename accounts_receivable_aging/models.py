from django.db import models
from django.utils import timezone
from decimal import Decimal


class AccountsReceivableAgingReport(models.Model):
    """
    Model to store accounts receivable aging report data
    """
    report_date = models.DateField(default=timezone.now)
    customer_name = models.CharField(max_length=255)
    customer_code = models.CharField(max_length=50, blank=True)
    
    # Aging buckets
    current_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    days_1_30 = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    days_31_60 = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    days_61_90 = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    days_over_90 = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    total_outstanding = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'accounts_receivable_aging_report'
        ordering = ['-report_date', 'customer_name']
        
    def __str__(self):
        return f"{self.customer_name} - {self.report_date}"
    
    @property
    def total_calculated(self):
        """Calculate total from all aging buckets"""
        return (self.current_amount + self.days_1_30 + 
                self.days_31_60 + self.days_61_90 + self.days_over_90)


class CustomerInvoiceAging(models.Model):
    """
    Model to store individual invoice aging details
    """
    customer_name = models.CharField(max_length=255)
    invoice_number = models.CharField(max_length=100)
    invoice_date = models.DateField()
    due_date = models.DateField()
    invoice_amount = models.DecimalField(max_digits=15, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    outstanding_amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    days_outstanding = models.IntegerField(default=0)
    aging_bucket = models.CharField(max_length=20, choices=[
        ('current', 'Current'),
        ('1-30', '1-30 Days'),
        ('31-60', '31-60 Days'),
        ('61-90', '61-90 Days'),
        ('over_90', 'Over 90 Days'),
    ])
    
    report_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'customer_invoice_aging'
        ordering = ['-report_date', 'customer_name', '-invoice_date']
        
    def __str__(self):
        return f"{self.customer_name} - {self.invoice_number}"
    
    def calculate_days_outstanding(self, as_of_date=None):
        """Calculate days outstanding from due date"""
        if as_of_date is None:
            as_of_date = timezone.now().date()
        
        if self.due_date <= as_of_date:
            self.days_outstanding = (as_of_date - self.due_date).days
        else:
            self.days_outstanding = 0
            
        # Determine aging bucket
        if self.days_outstanding <= 0:
            self.aging_bucket = 'current'
        elif self.days_outstanding <= 30:
            self.aging_bucket = '1-30'
        elif self.days_outstanding <= 60:
            self.aging_bucket = '31-60'
        elif self.days_outstanding <= 90:
            self.aging_bucket = '61-90'
        else:
            self.aging_bucket = 'over_90'
            
        return self.days_outstanding
