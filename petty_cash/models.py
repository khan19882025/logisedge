from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid

class PettyCashDay(models.Model):
    """Model to track petty cash entries for each day"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('locked', 'Locked'),
    ]
    
    # Basic Information
    entry_date = models.DateField(unique=True)
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    closing_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_expenses = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    # Status and Workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_locked = models.BooleanField(default=False)
    
    # Notes and Comments
    notes = models.TextField(blank=True, null=True)
    
    # Audit Fields
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='petty_cash_days_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='petty_cash_days_updated', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='petty_cash_days_approved', blank=True, null=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-entry_date']
        verbose_name = 'Petty Cash Day'
        verbose_name_plural = 'Petty Cash Days'
    
    def __str__(self):
        return f"Petty Cash - {self.entry_date.strftime('%Y-%m-%d')} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate closing balance
        # Ensure both values are Decimal to prevent type errors
        opening_balance = Decimal(str(self.opening_balance)) if self.opening_balance is not None else Decimal('0.00')
        total_expenses = Decimal(str(self.total_expenses)) if self.total_expenses is not None else Decimal('0.00')
        self.closing_balance = opening_balance - total_expenses
        super().save(*args, **kwargs)
    
    @property
    def can_edit(self):
        return self.status == 'draft' and not self.is_locked
    
    @property
    def can_approve(self):
        return self.status == 'submitted' and not self.is_locked
    
    @property
    def can_lock(self):
        return self.status == 'approved' and not self.is_locked
    
    def update_totals(self):
        """Update total expenses from entries"""
        total = self.entries.aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        # Ensure total is always a Decimal to prevent type errors
        self.total_expenses = Decimal(str(total)) if total is not None else Decimal('0.00')
        self.save()
    
    def get_previous_day_balance(self):
        """Get closing balance from previous day"""
        try:
            previous_day = PettyCashDay.objects.filter(
                entry_date__lt=self.entry_date
            ).order_by('-entry_date').first()
            return previous_day.closing_balance if previous_day else Decimal('0.00')
        except:
            return Decimal('0.00')


class PettyCashEntry(models.Model):
    """Individual petty cash expense entry"""
    
    # Basic Information
    petty_cash_day = models.ForeignKey(PettyCashDay, on_delete=models.CASCADE, related_name='entries')
    entry_time = models.TimeField(blank=True, null=True, help_text="Time of expense (optional)")
    job_no = models.CharField(max_length=50, blank=True, null=True, help_text="Job reference number")
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    
    # Additional Information
    paid_by = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    # File Attachment
    attachment = models.FileField(upload_to='petty_cash/attachments/', blank=True, null=True)
    
    # Audit Fields
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='petty_cash_entries_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='petty_cash_entries_updated', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['entry_time', 'created_at']
        verbose_name = 'Petty Cash Entry'
        verbose_name_plural = 'Petty Cash Entries'
    
    def __str__(self):
        return f"{self.petty_cash_day.entry_date} - {self.description} - {self.amount}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update day totals
        self.petty_cash_day.update_totals()


class PettyCashBalance(models.Model):
    """Track petty cash balance at different locations"""
    
    location = models.CharField(max_length=100, default='Main Office')
    currency = models.ForeignKey('multi_currency.Currency', on_delete=models.PROTECT, default=3)
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['location', 'currency']
        verbose_name = 'Petty Cash Balance'
        verbose_name_plural = 'Petty Cash Balances'
    
    def __str__(self):
        return f"{self.location} - {self.current_balance} {self.currency.code}"
    
    def update_balance(self, amount, is_expense=True):
        """Update balance based on transaction"""
        if is_expense:
            self.current_balance -= amount
        else:
            self.current_balance += amount
        self.save()


class PettyCashAudit(models.Model):
    """Audit trail for petty cash operations"""
    
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('locked', 'Locked'),
        ('entry_added', 'Entry Added'),
        ('entry_updated', 'Entry Updated'),
        ('entry_deleted', 'Entry Deleted'),
    ]
    
    petty_cash_day = models.ForeignKey(PettyCashDay, on_delete=models.CASCADE, related_name='audit_trail')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField()
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Optional reference to specific entry
    entry = models.ForeignKey(PettyCashEntry, on_delete=models.SET_NULL, blank=True, null=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Petty Cash Audit'
        verbose_name_plural = 'Petty Cash Audits'
    
    def __str__(self):
        return f"{self.petty_cash_day.entry_date} - {self.action} by {self.user.get_full_name()}"
