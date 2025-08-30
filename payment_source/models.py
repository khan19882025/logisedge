from django.db import models
from django.contrib.auth.models import User
from chart_of_accounts.models import ChartOfAccount


class PaymentSource(models.Model):
    """Payment Source master model for tracking payment sources in invoices and ledger entries"""
    
    PAYMENT_TYPE_CHOICES = [
        ('prepaid', 'Prepaid'),
        ('postpaid', 'Postpaid'),
        ('cash_bank', 'Cash/Bank'),
    ]
    
    SOURCE_TYPE_CHOICES = [
        ('prepaid', 'Prepaid'),
        ('postpaid', 'Postpaid'),
    ]
    
    CATEGORY_CHOICES = [
        ('cash', 'Cash'),
        ('bank', 'Bank'),
        ('credit_card', 'Credit Card'),
        ('advance_account', 'Advance Account'),
        ('other_payable', 'Other Payable'),
    ]
    
    name = models.CharField(max_length=50, verbose_name="Payment Source Name")
    code = models.CharField(
        max_length=20, 
        unique=True, 
        blank=True, 
        null=True,
        verbose_name="Short Code",
        help_text="Unique short code for this payment source"
    )
    description = models.TextField(blank=True, verbose_name="Description")
    
    # New fields for payment type and linked account
    payment_type = models.CharField(
        max_length=20, 
        choices=PAYMENT_TYPE_CHOICES, 
        verbose_name="Payment Type",
        help_text="Type of payment arrangement",
        default='postpaid'  # Default for existing records
    )
    
    # New professional fields
    source_type = models.CharField(
        max_length=20,
        choices=SOURCE_TYPE_CHOICES,
        verbose_name="Source Type",
        help_text="Type of payment source",
        default='postpaid'
    )
    
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        verbose_name="Category",
        help_text="Category of payment source",
        default='other_payable'
    )
    
    currency = models.ForeignKey(
        'multi_currency.Currency',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Currency",
        help_text="Currency for this payment source (required if multi-currency is enabled)"
    )
    
    linked_ledger = models.ForeignKey(
        ChartOfAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='linked_ledger_payment_sources',
        verbose_name="Linked Ledger",
        help_text="Chart of Account linked to this payment source (required)"
    )
    
    default_expense_ledger = models.ForeignKey(
        ChartOfAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_expense_payment_sources',
        verbose_name="Default Expense Ledger",
        help_text="Default expense account for this payment source (optional)"
    )
    
    default_vendor = models.ForeignKey(
        'customer.Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Default Vendor",
        help_text="Default vendor for this payment source (optional)"
    )
    
    active = models.BooleanField(default=True, verbose_name="Active Status")
    remarks = models.TextField(blank=True, verbose_name="Remarks")
    
    # Keep existing linked_account for backward compatibility
    linked_account = models.ForeignKey(
        ChartOfAccount, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='linked_account_payment_sources',
        verbose_name="Linked Account (Legacy)",
        help_text="Chart of Account linked to this payment source (legacy field)"
    )
    
    is_active = models.BooleanField(default=True, verbose_name="Active Status (Legacy)")
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='payment_sources_created',
        verbose_name="Created By"
    )
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='payment_sources_updated',
        verbose_name="Updated By"
    )
    
    class Meta:
        ordering = ['name']
        verbose_name = "Payment Source"
        verbose_name_plural = "Payment Sources"
        db_table = 'payment_source'
        unique_together = ['name', 'code']  # Ensure unique constraint on name + code
    
    def __str__(self):
        if self.code:
            return f"{self.name} ({self.code}) - {self.get_source_type_display()}"
        return f"{self.name} - {self.get_source_type_display()}"
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('payment_source:payment_source_detail', kwargs={'pk': self.pk})
    
    @property
    def status_display(self):
        """Return human-readable status"""
        return "Active" if self.active else "Inactive"
    
    @property
    def payment_type_display(self):
        """Return human-readable payment type"""
        return self.get_payment_type_display()
    
    @property
    def source_type_display(self):
        """Return human-readable source type"""
        return self.get_source_type_display()
    
    @property
    def category_display(self):
        """Return human-readable category"""
        return self.get_category_display()
    
    @property
    def linked_account_display(self):
        """Return linked account display name (backward compatibility)"""
        if self.linked_ledger:
            return f"{self.linked_ledger.account_code} - {self.linked_ledger.name}"
        elif self.linked_account:  # Legacy field
            return f"{self.linked_account.account_code} - {self.linked_account.name}"
        return "Not linked"
    
    def save(self, *args, **kwargs):
        """Ensure backward compatibility and set defaults"""
        # Set active field from is_active if not set
        if not hasattr(self, 'active') or self.active is None:
            self.active = self.is_active
        
        # Set linked_ledger from linked_account if not set (backward compatibility)
        if not self.linked_ledger and self.linked_account:
            self.linked_ledger = self.linked_account
        
        # Set source_type from payment_type if not set (backward compatibility)
        if not self.source_type:
            if self.payment_type == 'prepaid':
                self.source_type = 'prepaid'
            elif self.payment_type == 'postpaid':
                self.source_type = 'postpaid'
            else:
                self.source_type = 'postpaid'  # Default
        
        super().save(*args, **kwargs)
    
    def soft_delete(self, user=None):
        """Soft delete by setting active to False"""
        self.active = False
        self.is_active = False  # Keep legacy field in sync
        if user:
            self.updated_by = user
        self.save(update_fields=['active', 'is_active', 'updated_by', 'updated_at'])
    
    def restore(self, user=None):
        """Restore by setting active to True"""
        self.active = True
        self.is_active = True  # Keep legacy field in sync
        if user:
            self.updated_by = user
        self.save(update_fields=['active', 'is_active', 'updated_by', 'updated_at'])
    
    def get_default_linked_account(self):
        """Get default linked account based on payment type (backward compatibility)"""
        if self.linked_ledger:
            return self.linked_ledger
        
        if not self.payment_type:
            return None
            
        # Get company from the first active company
        from company.company_model import Company
        company = Company.objects.filter(is_active=True).first()
        if not company:
            return None
            
        if self.payment_type == 'prepaid':
            # Look for asset accounts (prepaid deposits)
            return ChartOfAccount.objects.filter(
                company=company,
                account_type__category='ASSET',
                is_active=True,
                name__icontains='prepaid'
            ).first()
        elif self.payment_type == 'postpaid':
            # Look for liability accounts (payables)
            return ChartOfAccount.objects.filter(
                company=company,
                account_type__category='LIABILITY',
                is_active=True,
                name__icontains='payable'
            ).first()
        elif self.payment_type == 'cash_bank':
            # Look for asset accounts (bank/cash)
            return ChartOfAccount.objects.filter(
                company=company,
                account_type__category='ASSET',
                is_active=True
            ).filter(
                models.Q(name__icontains='bank') | 
                models.Q(name__icontains='cash') |
                models.Q(name__icontains='current')
            ).first()
        
        return None
