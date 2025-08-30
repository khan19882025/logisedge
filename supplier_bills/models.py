from django.db import models
from datetime import datetime, timedelta

class SupplierBill(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('overdue', 'Overdue'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]
    
    number = models.CharField(max_length=50, unique=True, blank=True)
    supplier = models.CharField(max_length=255)
    bill_date = models.DateField()
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.number

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self.generate_supplier_bill_number()
        if not self.due_date:
            # Default due date is 30 days from bill date
            self.due_date = self.bill_date + timedelta(days=30)
        super().save(*args, **kwargs)

    def generate_supplier_bill_number(self):
        """Generate supplier bill number based on year and sequence"""
        today = datetime.now()
        year = today.year
        
        # Find the last supplier bill for this year
        last_bill = SupplierBill.objects.filter(
            number__startswith=f"SB-{year}-"
        ).order_by('-number').first()
        
        if last_bill and last_bill.number:
            try:
                # Extract the sequence number and increment
                last_sequence = int(last_bill.number.split('-')[-1])
                new_sequence = last_sequence + 1
            except (ValueError, IndexError):
                new_sequence = 1
        else:
            new_sequence = 1
        
        # Format: SB-YYYY-0001
        return f"SB-{year}-{new_sequence:04d}"
    
    @property
    def is_overdue(self):
        """Check if the bill is overdue"""
        return self.due_date < datetime.now().date() and self.status not in ['paid', 'cancelled']
    
    @property
    def days_overdue(self):
        """Calculate days overdue"""
        if self.is_overdue:
            return (datetime.now().date() - self.due_date).days
        return 0
    
    @property
    def status_display(self):
        """Get status display with overdue indicator"""
        if self.is_overdue:
            return f"{self.get_status_display()} (Overdue)"
        return self.get_status_display() 