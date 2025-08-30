from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from chart_of_accounts.models import ChartOfAccount
from fiscal_year.models import FiscalYear


class OpeningBalance(models.Model):
    financial_year = models.ForeignKey(
        FiscalYear,
        on_delete=models.CASCADE,
        related_name='opening_balances',
        verbose_name='Financial Year'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_opening_balances'
    )
    
    class Meta:
        verbose_name = 'Opening Balance'
        verbose_name_plural = 'Opening Balances'
        unique_together = ['financial_year']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Opening Balance - {self.financial_year.name}"
    
    @property
    def total_debit(self):
        return sum(entry.amount for entry in self.entries.filter(balance_type='debit', account__isnull=False))
    
    @property
    def total_credit(self):
        return sum(entry.amount for entry in self.entries.filter(balance_type='credit', account__isnull=False))
    
    @property
    def is_balanced(self):
        return self.total_debit == self.total_credit
    
    @property
    def balance_difference(self):
        return self.total_debit - self.total_credit


class OpeningBalanceEntry(models.Model):
    BALANCE_TYPE_CHOICES = [
        ('debit', 'Debit'),
        ('credit', 'Credit'),
    ]
    
    opening_balance = models.ForeignKey(
        OpeningBalance,
        on_delete=models.CASCADE,
        related_name='entries',
        verbose_name='Opening Balance'
    )
    account = models.ForeignKey(
        ChartOfAccount,
        on_delete=models.CASCADE,
        related_name='opening_balance_entries',
        verbose_name='Account',
        null=True,
        blank=True
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name='Amount',
        null=True,
        blank=True
    )
    balance_type = models.CharField(
        max_length=6,
        choices=BALANCE_TYPE_CHOICES,
        verbose_name='Balance Type'
    )
    remarks = models.TextField(
        blank=True,
        null=True,
        verbose_name='Remarks'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Opening Balance Entry'
        verbose_name_plural = 'Opening Balance Entries'
        unique_together = ['opening_balance', 'account']
        ordering = ['account__account_code']
    
    def __str__(self):
        if self.account:
            return f"{self.account.account_code} - {self.amount} ({self.balance_type})"
        return f"No Account - {self.amount} ({self.balance_type})"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Check if account is already used in this opening balance
        if self.pk is None and self.account:  # Only for new entries with accounts
            existing_entry = OpeningBalanceEntry.objects.filter(
                opening_balance=self.opening_balance,
                account=self.account
            ).first()
            if existing_entry:
                raise ValidationError({
                    'account': f'Account {self.account.account_code} is already used in this opening balance.'
                })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs) 