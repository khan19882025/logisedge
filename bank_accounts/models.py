from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from chart_of_accounts.models import ChartOfAccount
from multi_currency.models import Currency
from company.company_model import Company


class BankAccount(models.Model):
    """Bank Account model for managing company bank accounts"""
    
    ACCOUNT_TYPES = [
        ('current', 'Current Account'),
        ('savings', 'Savings Account'),
        ('loan', 'Loan Account'),
        ('overdraft', 'Overdraft Account'),
        ('credit_card', 'Credit Card'),
        ('term_deposit', 'Term Deposit'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('closed', 'Closed'),
    ]
    
    # Basic Information
    bank_name = models.CharField(max_length=200, help_text="Name of the bank")
    account_number = models.CharField(max_length=50, unique=True, help_text="Bank account number")
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='current')
    branch_name = models.CharField(max_length=200, blank=True, null=True, help_text="Branch name")
    ifsc_code = models.CharField(max_length=20, blank=True, null=True, help_text="IFSC/SWIFT code")
    
    # Financial Settings
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='bank_accounts')
    opening_balance = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0)]
    )
    current_balance = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0.00
    )
    
    # Chart of Account Link
    chart_account = models.ForeignKey(
        ChartOfAccount, 
        on_delete=models.CASCADE, 
        related_name='bank_accounts',
        limit_choices_to={'account_type__category': 'ASSET'},
        help_text="Link to Chart of Account (Bank-type ledgers only)"
    )
    
    # Status and Settings
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_default_for_payments = models.BooleanField(default=False, help_text="Default account for payments")
    is_default_for_receipts = models.BooleanField(default=False, help_text="Default account for receipts")
    
    # Additional Information
    notes = models.TextField(blank=True, null=True, help_text="Additional notes about the account")
    
    # Company and Audit
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='bank_accounts')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_bank_accounts')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_bank_accounts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['bank_name', 'account_number']
        verbose_name = 'Bank Account'
        verbose_name_plural = 'Bank Accounts'
        unique_together = ['account_number', 'company']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_balance = self.current_balance
    
    def __str__(self):
        return f"{self.bank_name} - {self.masked_account_number}"
    
    def save(self, *args, **kwargs):
        # Set company if not provided
        if not self.company_id:
            self.company = Company.objects.filter(is_active=True).first()
        
        # Update current balance if opening balance changed
        if self.pk and self._original_balance != self.current_balance:
            # This would typically be updated through transactions
            pass
        
        super().save(*args, **kwargs)
        self._original_balance = self.current_balance
    
    @property
    def masked_account_number(self):
        """Return partially masked account number for display"""
        if len(self.account_number) <= 4:
            return self.account_number
        return f"{'*' * (len(self.account_number) - 4)}{self.account_number[-4:]}"
    
    @property
    def balance_formatted(self):
        """Return formatted balance with currency symbol"""
        return f"{self.currency.symbol} {self.current_balance:,.2f}"
    
    @property
    def is_active(self):
        """Check if account is active"""
        return self.status == 'active'
    
    def update_balance(self, amount, transaction_type='credit'):
        """Update account balance based on transaction"""
        if transaction_type == 'credit':
            self.current_balance += amount
        else:  # debit
            self.current_balance -= amount
        self.save()
    
    def get_recent_transactions(self, limit=5):
        """Get recent transactions for this account"""
        # This would be implemented when transaction models are available
        return []
    
    def can_be_deleted(self):
        """Check if account can be safely deleted"""
        return self.current_balance == 0 and not self.get_recent_transactions()


class BankAccountTransaction(models.Model):
    """Model to track bank account transactions"""
    
    TRANSACTION_TYPES = [
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    ]
    
    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='transactions')
    transaction_date = models.DateField()
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.CharField(max_length=500)
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    
    # Balance tracking
    balance_before = models.DecimalField(max_digits=15, decimal_places=2)
    balance_after = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Audit fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-transaction_date', '-created_at']
        verbose_name = 'Bank Account Transaction'
        verbose_name_plural = 'Bank Account Transactions'
    
    def __str__(self):
        return f"{self.bank_account.bank_name} - {self.transaction_type} - {self.amount}"
    
    def save(self, *args, **kwargs):
        if not self.pk:  # New transaction
            self.balance_before = self.bank_account.current_balance
            if self.transaction_type == 'credit':
                self.balance_after = self.balance_before + self.amount
            else:
                self.balance_after = self.balance_before - self.amount
            
            # Update bank account balance
            self.bank_account.current_balance = self.balance_after
            self.bank_account.save()
        
        super().save(*args, **kwargs)
