from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
from chart_of_accounts.models import ChartOfAccount
from customer.models import Customer
from company.company_model import Company


class ChequeRegister(models.Model):
    """Model for managing cheque register entries"""
    
    CHEQUE_TYPE_CHOICES = [
        ('issued', 'Issued'),
        ('received', 'Received'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('cleared', 'Cleared'),
        ('bounced', 'Bounced'),
        ('cancelled', 'Cancelled'),
        ('stopped', 'Stopped'),
    ]
    
    # Basic Information
    cheque_number = models.CharField(max_length=50, help_text="Cheque number")
    cheque_date = models.DateField(help_text="Date on the cheque")
    cheque_type = models.CharField(max_length=10, choices=CHEQUE_TYPE_CHOICES, help_text="Type of cheque")
    
    # Party Information
    party_type = models.CharField(max_length=10, choices=[('customer', 'Customer'), ('supplier', 'Supplier')], help_text="Type of party")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True, related_name='cheques')
    supplier = models.CharField(max_length=255, blank=True, null=True, help_text="Supplier name")
    
    # Financial Information
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], help_text="Cheque amount")
    bank_account = models.ForeignKey(ChartOfAccount, on_delete=models.CASCADE, related_name='cheques', help_text="Bank account")
    
    # Related Transaction
    related_transaction = models.CharField(max_length=200, blank=True, null=True, help_text="Related payment/receipt voucher")
    transaction_reference = models.CharField(max_length=100, blank=True, null=True, help_text="Transaction reference number")
    
    # Status and Dates
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', help_text="Current status of the cheque")
    clearing_date = models.DateField(null=True, blank=True, help_text="Date when cheque was cleared")
    stop_payment_date = models.DateField(null=True, blank=True, help_text="Date when stop payment was requested")
    
    # Additional Information
    remarks = models.TextField(blank=True, null=True, help_text="Additional remarks or notes")
    is_post_dated = models.BooleanField(default=False, help_text="Whether this is a post-dated cheque")
    
    # Company and Audit Fields
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='cheque_registers', null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_cheques')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_cheques')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-cheque_date', '-created_at']
        verbose_name = 'Cheque Register'
        verbose_name_plural = 'Cheque Registers'
        unique_together = ['cheque_number', 'bank_account', 'company']
    
    def __str__(self):
        party_name = self.get_party_name()
        return f"{self.cheque_number} - {party_name} - {self.amount}"
    
    def save(self, *args, **kwargs):
        # Set company if not provided
        if not self.company and self.bank_account:
            self.company = self.bank_account.company
        
        # Check if post-dated
        if self.cheque_date and self.cheque_date > timezone.now().date():
            self.is_post_dated = True
        
        # Update clearing date based on status
        if self.status == 'cleared' and not self.clearing_date:
            self.clearing_date = timezone.now().date()
        
        super().save(*args, **kwargs)
    
    def get_party_name(self):
        """Get the name of the party (customer or supplier)"""
        if self.customer:
            return self.customer.customer_name
        elif self.supplier:
            return self.supplier
        return "Unknown Party"
    
    def get_party_type_display(self):
        """Get the display name of the party type"""
        if self.customer:
            return "Customer"
        elif self.supplier:
            return "Supplier"
        return "Unknown"
    
    @property
    def is_overdue(self):
        """Check if the cheque is overdue (pending and past due date)"""
        if self.status == 'pending' and self.cheque_date and self.cheque_date < timezone.now().date():
            return True
        return False
    
    @property
    def days_overdue(self):
        """Get number of days overdue"""
        if self.is_overdue:
            return (timezone.now().date() - self.cheque_date).days
        return 0
    
    def mark_as_cleared(self, clearing_date=None):
        """Mark cheque as cleared"""
        self.status = 'cleared'
        self.clearing_date = clearing_date or timezone.now().date()
        self.save()
    
    def mark_as_bounced(self):
        """Mark cheque as bounced"""
        self.status = 'bounced'
        self.save()
    
    def stop_payment(self):
        """Stop payment on the cheque"""
        self.status = 'stopped'
        self.stop_payment_date = timezone.now().date()
        self.save()
    
    def cancel_cheque(self):
        """Cancel the cheque"""
        self.status = 'cancelled'
        self.save()


class ChequeStatusHistory(models.Model):
    """Model for tracking cheque status changes"""
    
    cheque = models.ForeignKey(ChequeRegister, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=10, choices=ChequeRegister.STATUS_CHOICES, null=True, blank=True)
    new_status = models.CharField(max_length=10, choices=ChequeRegister.STATUS_CHOICES)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-changed_at']
        verbose_name = 'Cheque Status History'
        verbose_name_plural = 'Cheque Status Histories'
    
    def __str__(self):
        return f"{self.cheque.cheque_number} - {self.old_status} to {self.new_status}"


class ChequeAlert(models.Model):
    """Model for managing cheque alerts and notifications"""
    
    ALERT_TYPE_CHOICES = [
        ('post_dated_due', 'Post-dated Cheque Due'),
        ('overdue', 'Overdue Cheque'),
        ('bounced', 'Cheque Bounced'),
        ('cleared', 'Cheque Cleared'),
    ]
    
    cheque = models.ForeignKey(ChequeRegister, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Cheque Alert'
        verbose_name_plural = 'Cheque Alerts'
    
    def __str__(self):
        return f"{self.cheque.cheque_number} - {self.alert_type}"
