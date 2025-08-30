from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid

class ContraEntry(models.Model):
    """Contra Entry model for fund transfers between bank and cash accounts"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic Information
    voucher_number = models.CharField(max_length=50, unique=True, blank=True)
    date = models.DateField()
    narration = models.TextField()
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    
    # Status and Workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    posted_at = models.DateTimeField(blank=True, null=True)
    posted_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='contra_entries_posted', blank=True, null=True)
    
    # Audit Fields
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='contra_entries_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='contra_entries_updated', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contra Entry'
        verbose_name_plural = 'Contra Entries'
    
    def __str__(self):
        return f"CE-{self.voucher_number} - {self.narration[:50]}"
    
    def save(self, *args, **kwargs):
        if not self.voucher_number:
            # Generate voucher number
            year = timezone.now().year
            last_entry = ContraEntry.objects.filter(
                voucher_number__startswith=f'CE-{year}'
            ).order_by('-voucher_number').first()
            
            if last_entry:
                try:
                    last_number = int(last_entry.voucher_number.split('-')[-1])
                    new_number = last_number + 1
                except (ValueError, IndexError):
                    new_number = 1
            else:
                new_number = 1
            
            self.voucher_number = f'CE-{year}-{new_number:04d}'
        
        super().save(*args, **kwargs)
    
    @property
    def total_debit(self):
        """Calculate total debit amount"""
        return self.entries.filter(debit__isnull=False).aggregate(
            total=models.Sum('debit')
        )['total'] or Decimal('0.00')
    
    @property
    def total_credit(self):
        """Calculate total credit amount"""
        return self.entries.filter(credit__isnull=False).aggregate(
            total=models.Sum('credit')
        )['total'] or Decimal('0.00')
    
    @property
    def is_balanced(self):
        """Check if debit equals credit"""
        return self.total_debit == self.total_credit
    
    @property
    def can_post(self):
        """Check if entry can be posted"""
        return (self.status == 'draft' and 
                self.entries.count() >= 2 and 
                self.is_balanced)
    
    @property
    def can_edit(self):
        """Check if entry can be edited"""
        return self.status == 'draft'
    
    @property
    def can_cancel(self):
        """Check if entry can be cancelled"""
        return self.status in ['draft', 'posted']


class ContraEntryDetail(models.Model):
    """Individual debit/credit entries within a contra entry"""
    
    contra_entry = models.ForeignKey(ContraEntry, on_delete=models.CASCADE, related_name='entries')
    account = models.ForeignKey('chart_of_accounts.ChartOfAccount', on_delete=models.PROTECT)
    debit = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('0.01'))])
    credit = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('0.01'))])
    
    class Meta:
        ordering = ['id']
        verbose_name = 'Contra Entry Detail'
        verbose_name_plural = 'Contra Entry Details'
    
    def __str__(self):
        amount = self.debit if self.debit else self.credit
        return f"{self.contra_entry.voucher_number} - {self.account.name} - {amount}"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Ensure either debit or credit is provided, but not both
        if self.debit and self.credit:
            raise ValidationError('An entry cannot have both debit and credit amounts.')
        
        if not self.debit and not self.credit:
            raise ValidationError('Either debit or credit amount must be provided.')
        
        # Ensure amounts are positive
        if self.debit and self.debit <= 0:
            raise ValidationError('Debit amount must be greater than zero.')
        
        if self.credit and self.credit <= 0:
            raise ValidationError('Credit amount must be greater than zero.')
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    @property
    def amount(self):
        """Get the amount (debit or credit)"""
        return self.debit if self.debit else self.credit
    
    @property
    def entry_type(self):
        """Get the entry type (debit or credit)"""
        return 'debit' if self.debit else 'credit'


class ContraEntryAudit(models.Model):
    """Audit trail for contra entries"""
    
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('posted', 'Posted'),
        ('cancelled', 'Cancelled'),
        ('entry_added', 'Entry Added'),
        ('entry_updated', 'Entry Updated'),
        ('entry_removed', 'Entry Removed'),
    ]
    
    contra_entry = models.ForeignKey(ContraEntry, on_delete=models.CASCADE, related_name='audit_trail')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField()
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Contra Entry Audit'
        verbose_name_plural = 'Contra Entry Audits'
    
    def __str__(self):
        return f"{self.contra_entry.voucher_number} - {self.action} by {self.user.get_full_name()}"
