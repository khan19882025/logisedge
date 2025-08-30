from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from company.company_model import Company
from multi_currency.models import Currency


class AccountType(models.Model):
    """Account Type model for categorizing accounts"""
    ACCOUNT_CATEGORIES = [
        ('ASSET', 'Assets'),
        ('LIABILITY', 'Liabilities'),
        ('EQUITY', 'Equity'),
        ('REVENUE', 'Revenue'),
        ('EXPENSE', 'Expenses'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=20, choices=ACCOUNT_CATEGORIES)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'name']
        verbose_name = _('Account Type')
        verbose_name_plural = _('Account Types')
    
    def __str__(self):
        return f"{self.get_category_display()} - {self.name}"


class ChartOfAccount(models.Model):
    """Chart of Accounts model with hierarchical structure"""
    ACCOUNT_NATURES = [
        ('DEBIT', 'Debit'),
        ('CREDIT', 'Credit'),
        ('BOTH', 'Both (Debit & Credit)'),
    ]
    
    # Basic Information
    account_code = models.CharField(max_length=20, help_text="Unique account code (e.g., 1000, 1100)")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Account Classification
    account_type = models.ForeignKey(AccountType, on_delete=models.CASCADE, related_name='accounts')
    account_nature = models.CharField(
        max_length=10, 
        choices=ACCOUNT_NATURES, 
        blank=True, 
        null=True,
        help_text="Normal balance side (optional - can be determined by account type)"
    )
    
    # Hierarchical Structure
    parent_account = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_accounts')
    is_group = models.BooleanField(default=False, help_text="Check if this is a group account (parent)")
    level = models.PositiveIntegerField(default=0, help_text="Hierarchy level (0 for root)")
    
    # Financial Settings
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, default=1)  # Default to AED
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    # Status and Company
    is_active = models.BooleanField(default=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='chart_accounts')
    
    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_accounts')
    updated_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_accounts')
    
    class Meta:
        ordering = ['account_code']
        verbose_name = _('Chart of Account')
        verbose_name_plural = _('Chart of Accounts')
        unique_together = ['account_code', 'company']
    
    def __str__(self):
        return f"{self.account_code} - {self.name}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate level based on parent
        if self.parent_account:
            self.level = self.parent_account.level + 1
        else:
            self.level = 0
        
        # Auto-set is_group if has sub_accounts (only if instance has been saved)
        if self.pk and self.sub_accounts.exists():
            self.is_group = True
        
        # Auto-set account nature based on account type if not specified
        if not self.account_nature and self.account_type:
            self.account_nature = self.get_default_nature()
        
        super().save(*args, **kwargs)
    
    def get_default_nature(self):
        """Get default account nature based on account type category"""
        category = self.account_type.category
        if category in ['ASSET', 'EXPENSE']:
            return 'DEBIT'
        elif category in ['LIABILITY', 'EQUITY', 'REVENUE']:
            return 'CREDIT'
        else:
            return 'BOTH'
    
    @property
    def full_name(self):
        """Return full hierarchical name with indentation"""
        indent = "  " * self.level
        return f"{indent}{self.account_code} - {self.name}"
    
    @property
    def total_balance(self):
        """Calculate total balance including sub-accounts"""
        if self.is_group and self.pk:
            return sum(sub.total_balance for sub in self.sub_accounts.filter(is_active=True))
        return self.current_balance
    
    @property
    def is_debit_balance(self):
        """Check if account normally has debit balance"""
        if self.account_nature:
            return self.account_nature == 'DEBIT'
        return self.account_type.category in ['ASSET', 'EXPENSE']
    
    @property
    def is_credit_balance(self):
        """Check if account normally has credit balance"""
        if self.account_nature:
            return self.account_nature == 'CREDIT'
        return self.account_type.category in ['LIABILITY', 'EQUITY', 'REVENUE']
    
    @property
    def is_both_nature(self):
        """Check if account can have both debit and credit balances"""
        return self.account_nature == 'BOTH'
    
    def get_children_recursive(self, visited=None):
        """Get all child accounts recursively with circular reference protection"""
        if visited is None:
            visited = set()
        
        # Prevent circular references
        if self.pk in visited:
            return []
        
        visited.add(self.pk)
        children = []
        
        if self.pk:
            for child in self.sub_accounts.filter(is_active=True):
                children.append(child)
                children.extend(child.get_children_recursive(visited.copy()))
        
        return children
    
    def get_parents_recursive(self, visited=None):
        """Get all parent accounts recursively with circular reference protection"""
        if visited is None:
            visited = set()
        
        # Prevent circular references
        if self.pk in visited:
            return []
        
        visited.add(self.pk)
        parents = []
        
        if self.parent_account:
            parents.append(self.parent_account)
            parents.extend(self.parent_account.get_parents_recursive(visited.copy()))
        
        return parents


class AccountBalance(models.Model):
    """Account balance tracking for different periods"""
    account = models.ForeignKey(ChartOfAccount, on_delete=models.CASCADE, related_name='balances')
    fiscal_year = models.ForeignKey('fiscal_year.FiscalYear', on_delete=models.CASCADE, related_name='account_balances')
    period = models.CharField(max_length=7, help_text="YYYY-MM format")
    
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    debit_total = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    credit_total = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    closing_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['account', 'fiscal_year', 'period']
        ordering = ['account__account_code', 'period']
    
    def __str__(self):
        return f"{self.account.account_code} - {self.period} - {self.closing_balance}"
    
    @property
    def net_movement(self):
        """Calculate net movement for the period"""
        return self.debit_total - self.credit_total


class AccountGroup(models.Model):
    """Predefined account groups for standard accounting"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    account_type = models.ForeignKey(AccountType, on_delete=models.CASCADE, related_name='groups')
    is_system = models.BooleanField(default=False, help_text="System-defined groups cannot be modified")
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class AccountTemplate(models.Model):
    """Template for creating standard chart of accounts"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class AccountTemplateItem(models.Model):
    """Individual account items in templates"""
    template = models.ForeignKey(AccountTemplate, on_delete=models.CASCADE, related_name='items')
    account_code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    account_type = models.ForeignKey(AccountType, on_delete=models.CASCADE)
    account_nature = models.CharField(
        max_length=10, 
        choices=ChartOfAccount.ACCOUNT_NATURES,
        blank=True,
        null=True
    )
    parent_code = models.CharField(max_length=20, blank=True, null=True)
    is_group = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['account_code']
    
    def __str__(self):
        return f"{self.account_code} - {self.name}"
