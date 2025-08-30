from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
from company.company_model import Company
from fiscal_year.models import FiscalYear
from chart_of_accounts.models import ChartOfAccount
from django.utils import timezone


class JournalEntry(models.Model):
    """Model for General Journal Entries"""
    
    ENTRY_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancelled', 'Cancelled'),
    ]
    
    journal_number = models.CharField(max_length=20, unique=True, blank=True)
    date = models.DateField()
    reference = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    total_debit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_credit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=20, choices=ENTRY_STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True)
    
    # Foreign Keys
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='journal_entries')
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.CASCADE, related_name='journal_entries')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_journal_entries')
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='posted_journal_entries')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    posted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Journal Entry'
        verbose_name_plural = 'Journal Entries'
    
    def __str__(self):
        return f"JE-{self.journal_number} - {self.date}"
    
    def save(self, *args, **kwargs):
        if not self.journal_number:
            self.journal_number = self.generate_journal_number()
        super().save(*args, **kwargs)
    
    def generate_journal_number(self):
        """Generate unique journal entry number"""
        year = self.fiscal_year.start_date.year
        last_entry = JournalEntry.objects.filter(
            fiscal_year=self.fiscal_year,
            journal_number__startswith=f'JE-{year}-'
        ).order_by('-journal_number').first()
        
        if last_entry:
            try:
                last_number = int(last_entry.journal_number.split('-')[-1])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1
        
        return f'JE-{year}-{new_number:06d}'
    
    def calculate_totals(self):
        """Calculate total debit and credit amounts"""
        self.total_debit = sum(line.debit_amount for line in self.lines.all())
        self.total_credit = sum(line.credit_amount for line in self.lines.all())
        self.save(update_fields=['total_debit', 'total_credit'])
    
    def is_balanced(self):
        """Check if the journal entry is balanced (debits = credits)"""
        return self.total_debit == self.total_credit
    
    def can_post(self):
        """Check if the journal entry can be posted"""
        return (self.status == 'draft' and 
                self.is_balanced() and 
                self.lines.count() >= 2)
    
    def post(self, user):
        """Post the journal entry"""
        if self.can_post():
            self.status = 'posted'
            self.posted_by = user
            self.posted_at = timezone.now()
            self.save()
            return True
        return False
    
    def cancel(self):
        """Cancel the journal entry"""
        if self.status == 'draft':
            self.status = 'cancelled'
            self.save()
            return True
        return False


class JournalEntryLine(models.Model):
    """Model for individual lines in a Journal Entry"""
    
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey(ChartOfAccount, on_delete=models.CASCADE, related_name='journal_lines')
    description = models.CharField(max_length=255, blank=True)
    debit_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))])
    credit_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))])
    reference = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Journal Entry Line'
        verbose_name_plural = 'Journal Entry Lines'
    
    def __str__(self):
        return f"{self.journal_entry.journal_number} - {self.account.account_name}"
    
    def clean(self):
        """Validate that either debit or credit amount is provided, but not both"""
        from django.core.exceptions import ValidationError
        
        if self.debit_amount > 0 and self.credit_amount > 0:
            raise ValidationError("A line cannot have both debit and credit amounts.")
        
        if self.debit_amount == 0 and self.credit_amount == 0:
            raise ValidationError("Either debit or credit amount must be provided.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        # Recalculate totals for the journal entry
        self.journal_entry.calculate_totals()
    
    @property
    def amount(self):
        """Return the amount (debit or credit)"""
        return self.debit_amount if self.debit_amount > 0 else self.credit_amount
    
    @property
    def is_debit(self):
        """Check if this is a debit line"""
        return self.debit_amount > 0
    
    @property
    def is_credit(self):
        """Check if this is a credit line"""
        return self.credit_amount > 0
