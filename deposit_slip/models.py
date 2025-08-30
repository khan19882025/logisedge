from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid

class DepositSlip(models.Model):
    """Deposit Slip model for recording bank deposits"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic Information
    slip_number = models.CharField(max_length=50, unique=True, blank=True)
    deposit_date = models.DateField()
    deposit_to = models.ForeignKey('chart_of_accounts.ChartOfAccount', on_delete=models.PROTECT, 
                                 related_name='deposit_slips', 
                                 limit_choices_to={'account_type__category': 'ASSET'})
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    narration = models.TextField(blank=True, null=True)
    
    # Financial Information
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    currency = models.ForeignKey('multi_currency.Currency', on_delete=models.PROTECT, default=1)
    
    # Status and Workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    submitted_at = models.DateTimeField(blank=True, null=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)
    
    # Audit Fields
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='deposit_slips_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='deposit_slips_updated', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='deposit_slips_submitted', blank=True, null=True)
    confirmed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='deposit_slips_confirmed', blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Deposit Slip'
        verbose_name_plural = 'Deposit Slips'
    
    def __str__(self):
        return f"DS-{self.slip_number} - {self.deposit_date}"
    
    def save(self, *args, **kwargs):
        if not self.slip_number:
            # Generate slip number
            year = timezone.now().year
            last_slip = DepositSlip.objects.filter(
                slip_number__startswith=f'DS-{year}'
            ).order_by('-slip_number').first()
            
            if last_slip:
                try:
                    last_number = int(last_slip.slip_number.split('-')[-1])
                    new_number = last_number + 1
                except (ValueError, IndexError):
                    new_number = 1
            else:
                new_number = 1
            
            self.slip_number = f'DS-{year}-{new_number:04d}'
        
        # Calculate total amount from items
        if self.pk:
            self.total_amount = sum(item.amount for item in self.items.all())
        
        super().save(*args, **kwargs)
    
    @property
    def total_items(self):
        return self.items.count()
    
    @property
    def cash_amount(self):
        return sum(item.amount for item in self.items.filter(receipt_voucher__receipt_mode='cash'))
    
    @property
    def cheque_amount(self):
        return sum(item.amount for item in self.items.filter(receipt_voucher__receipt_mode='cheque'))
    
    @property
    def other_amount(self):
        return sum(item.amount for item in self.items.exclude(
            receipt_voucher__receipt_mode__in=['cash', 'cheque']
        ))
    
    @property
    def can_edit(self):
        return self.status == 'draft'
    
    @property
    def can_submit(self):
        return self.status == 'draft' and self.items.exists()
    
    @property
    def can_confirm(self):
        return self.status == 'submitted'


class DepositSlipItem(models.Model):
    """Individual receipt vouchers included in a deposit slip"""
    
    deposit_slip = models.ForeignKey(DepositSlip, on_delete=models.CASCADE, related_name='items')
    receipt_voucher = models.ForeignKey('receipt_voucher.ReceiptVoucher', on_delete=models.PROTECT, 
                                       related_name='deposit_slip_items')
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    
    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        unique_together = ['deposit_slip', 'receipt_voucher']
        ordering = ['created_at']
        verbose_name = 'Deposit Slip Item'
        verbose_name_plural = 'Deposit Slip Items'
    
    def __str__(self):
        return f"{self.deposit_slip.slip_number} - {self.receipt_voucher.voucher_number}"
    
    def save(self, *args, **kwargs):
        # Set amount from receipt voucher if not specified
        if not self.amount:
            self.amount = self.receipt_voucher.amount
        
        super().save(*args, **kwargs)
        
        # Update deposit slip total
        self.deposit_slip.save()


class DepositSlipAudit(models.Model):
    """Audit trail for deposit slips"""
    
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('submitted', 'Submitted'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('item_added', 'Item Added'),
        ('item_removed', 'Item Removed'),
    ]
    
    deposit_slip = models.ForeignKey(DepositSlip, on_delete=models.CASCADE, related_name='audit_trail')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField()
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Deposit Slip Audit'
        verbose_name_plural = 'Deposit Slip Audits'
    
    def __str__(self):
        return f"{self.deposit_slip.slip_number} - {self.action} by {self.user.get_full_name()}"
