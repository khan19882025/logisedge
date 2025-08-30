from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid

class CashTransaction(models.Model):
    """Cash Transaction model for recording cash inflows and outflows"""
    
    TRANSACTION_TYPES = [
        ('cash_in', 'Cash In'),
        ('cash_out', 'Cash Out'),
    ]
    
    CATEGORIES = [
        ('petty_expense', 'Petty Expense'),
        ('cash_sale', 'Cash Sale'),
        ('staff_advance', 'Staff Advance'),
        ('reimbursement', 'Reimbursement'),
        ('cash_purchase', 'Cash Purchase'),
        ('cash_receipt', 'Cash Receipt'),
        ('cash_payment', 'Cash Payment'),
        ('other', 'Other'),
    ]
    
    # Basic Information
    transaction_number = models.CharField(max_length=50, unique=True, blank=True)
    transaction_date = models.DateField()
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    category = models.CharField(max_length=30, choices=CATEGORIES)
    
    # Account Information
    from_account = models.ForeignKey('chart_of_accounts.ChartOfAccount', on_delete=models.PROTECT, 
                                    related_name='cash_transactions_from', blank=True, null=True)
    to_account = models.ForeignKey('chart_of_accounts.ChartOfAccount', on_delete=models.PROTECT, 
                                  related_name='cash_transactions_to', blank=True, null=True)
    
    # Financial Information
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.ForeignKey('multi_currency.Currency', on_delete=models.PROTECT, default=3)
    
    # Location and Reference
    location = models.CharField(max_length=100, blank=True, null=True, help_text="Branch or location")
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    narration = models.TextField(blank=True, null=True)
    
    # File Attachment
    attachment = models.FileField(upload_to='cash_transactions/', blank=True, null=True)
    
    # Status and Workflow
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancelled', 'Cancelled'),
    ], default='draft')
    
    # Audit Fields
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='cash_transactions_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='cash_transactions_updated', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    posted_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='cash_transactions_posted', blank=True, null=True)
    posted_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Cash Transaction'
        verbose_name_plural = 'Cash Transactions'
    
    def __str__(self):
        return f"CT-{self.transaction_number} - {self.get_transaction_type_display()} - {self.amount}"
    
    def save(self, *args, **kwargs):
        if not self.transaction_number:
            # Generate transaction number
            year = timezone.now().year
            last_transaction = CashTransaction.objects.filter(
                transaction_number__startswith=f'CT-{year}'
            ).order_by('-transaction_number').first()
            
            if last_transaction:
                try:
                    last_number = int(last_transaction.transaction_number.split('-')[-1])
                    new_number = last_number + 1
                except (ValueError, IndexError):
                    new_number = 1
            else:
                new_number = 1
            
            self.transaction_number = f'CT-{year}-{new_number:04d}'
        
        super().save(*args, **kwargs)
    
    @property
    def is_cash_in(self):
        return self.transaction_type == 'cash_in'
    
    @property
    def is_cash_out(self):
        return self.transaction_type == 'cash_out'
    
    @property
    def can_edit(self):
        return self.status == 'draft'
    
    @property
    def can_post(self):
        return self.status == 'draft'
    
    @property
    def can_cancel(self):
        return self.status in ['draft', 'posted']
    
    def get_display_amount(self):
        """Get amount with proper sign based on transaction type"""
        if self.is_cash_out:
            return -self.amount
        return self.amount


class CashTransactionAudit(models.Model):
    """Audit trail for cash transactions"""
    
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('posted', 'Posted'),
        ('cancelled', 'Cancelled'),
    ]
    
    transaction = models.ForeignKey(CashTransaction, on_delete=models.CASCADE, related_name='audit_trail')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField()
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Cash Transaction Audit'
        verbose_name_plural = 'Cash Transaction Audits'
    
    def __str__(self):
        return f"{self.transaction.transaction_number} - {self.action} by {self.user.get_full_name()}"


class CashBalance(models.Model):
    """Track cash balance at different locations"""
    
    location = models.CharField(max_length=100)
    currency = models.ForeignKey('multi_currency.Currency', on_delete=models.PROTECT, default=3)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['location', 'currency']
        verbose_name = 'Cash Balance'
        verbose_name_plural = 'Cash Balances'
    
    def __str__(self):
        return f"{self.location} - {self.balance} {self.currency.code}"
    
    def update_balance(self, amount, transaction_type):
        """Update balance based on transaction"""
        if transaction_type == 'cash_in':
            self.balance += amount
        else:  # cash_out
            self.balance -= amount
        self.save()
