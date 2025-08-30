from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid

class BankTransfer(models.Model):
    """Bank Transfer model for recording transfers between internal bank accounts"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
    ]
    
    TRANSFER_TYPES = [
        ('internal', 'Internal Transfer'),
        ('external', 'External Transfer'),
        ('interbank', 'Interbank Transfer'),
    ]
    
    # Basic Information
    transfer_number = models.CharField(max_length=50, unique=True, blank=True)
    transfer_date = models.DateField()
    transfer_type = models.CharField(max_length=20, choices=TRANSFER_TYPES, default='internal')
    
    # Account Information
    from_account = models.ForeignKey('chart_of_accounts.ChartOfAccount', on_delete=models.PROTECT, 
                                    related_name='transfers_from', 
                                    limit_choices_to={'account_type__category': 'ASSET'})
    to_account = models.ForeignKey('chart_of_accounts.ChartOfAccount', on_delete=models.PROTECT, 
                                  related_name='transfers_to', 
                                  limit_choices_to={'account_type__category': 'ASSET'})
    
    # Financial Information
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.ForeignKey('multi_currency.Currency', on_delete=models.PROTECT, default=3)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=6, default=1.000000, 
                                       help_text="Exchange rate if different currencies")
    converted_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00,
                                          help_text="Amount in target currency")
    
    # Additional Information
    reference_number = models.CharField(max_length=100, unique=True, blank=True, null=True)
    narration = models.TextField(blank=True, null=True)
    
    # Status and Workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    completed_at = models.DateTimeField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    
    # Audit Fields
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='bank_transfers_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='bank_transfers_updated', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='bank_transfers_completed', blank=True, null=True)
    cancelled_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='bank_transfers_cancelled', blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Bank Transfer'
        verbose_name_plural = 'Bank Transfers'
    
    def __str__(self):
        return f"BT-{self.transfer_number} - {self.from_account.name} to {self.to_account.name}"
    
    def save(self, *args, **kwargs):
        if not self.transfer_number:
            # Generate transfer number
            year = timezone.now().year
            last_transfer = BankTransfer.objects.filter(
                transfer_number__startswith=f'BT-{year}'
            ).order_by('-transfer_number').first()
            
            if last_transfer:
                try:
                    last_number = int(last_transfer.transfer_number.split('-')[-1])
                    new_number = last_number + 1
                except (ValueError, IndexError):
                    new_number = 1
            else:
                new_number = 1
            
            self.transfer_number = f'BT-{year}-{new_number:04d}'
        
        # Calculate converted amount if exchange rate is provided
        if self.exchange_rate and self.exchange_rate != 1:
            self.converted_amount = self.amount * self.exchange_rate
        else:
            self.converted_amount = self.amount
        
        super().save(*args, **kwargs)
    
    @property
    def fx_gain_loss(self):
        """Calculate foreign exchange gain/loss"""
        if self.exchange_rate and self.exchange_rate != 1:
            return self.converted_amount - self.amount
        return Decimal('0.00')
    
    @property
    def is_multi_currency(self):
        """Check if this is a multi-currency transfer"""
        return self.exchange_rate and self.exchange_rate != 1
    
    @property
    def can_edit(self):
        return self.status == 'draft'
    
    @property
    def can_complete(self):
        return self.status in ['draft', 'pending']
    
    @property
    def can_cancel(self):
        return self.status in ['draft', 'pending']
    
    def get_from_account_balance(self):
        """Get from account balance before transfer"""
        return self.from_account.current_balance
    
    def get_to_account_balance(self):
        """Get to account balance before transfer"""
        return self.to_account.current_balance
    
    def get_updated_from_balance(self):
        """Get from account balance after transfer"""
        return self.get_from_account_balance() - self.amount
    
    def get_updated_to_balance(self):
        """Get to account balance after transfer"""
        return self.get_to_account_balance() + self.converted_amount


class BankTransferAudit(models.Model):
    """Audit trail for bank transfers"""
    
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
    ]
    
    transfer = models.ForeignKey(BankTransfer, on_delete=models.CASCADE, related_name='audit_trail')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField()
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Bank Transfer Audit'
        verbose_name_plural = 'Bank Transfer Audits'
    
    def __str__(self):
        return f"{self.transfer.transfer_number} - {self.action} by {self.user.get_full_name()}"


class BankTransferTemplate(models.Model):
    """Templates for frequently used bank transfers"""
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    # Template data
    from_account = models.ForeignKey('chart_of_accounts.ChartOfAccount', on_delete=models.CASCADE, 
                                    related_name='transfer_templates_from')
    to_account = models.ForeignKey('chart_of_accounts.ChartOfAccount', on_delete=models.CASCADE, 
                                  related_name='transfer_templates_to')
    default_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    default_currency = models.ForeignKey('multi_currency.Currency', on_delete=models.CASCADE, default=3)
    default_narration = models.TextField(blank=True, null=True)
    
    # Template settings
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Bank Transfer Template'
        verbose_name_plural = 'Bank Transfer Templates'
    
    def __str__(self):
        return self.name
