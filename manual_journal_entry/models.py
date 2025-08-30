from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from chart_of_accounts.models import ChartOfAccount
from company.company_model import Company
from multi_currency.models import Currency
from fiscal_year.models import FiscalYear
import uuid


class JournalEntry(models.Model):
    """Manual Journal Entry model"""
    ENTRY_STATUS = [
        ('DRAFT', 'Draft'),
        ('POSTED', 'Posted'),
        ('VOID', 'Void'),
    ]
    
    # Basic Information
    voucher_number = models.CharField(max_length=20, unique=True, blank=True)
    date = models.DateField()
    reference_number = models.CharField(max_length=100, blank=True)
    narration = models.TextField()
    
    # Financial Information
    total_debit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_credit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, default=1)  # Default to AED
    
    # Status and Company
    status = models.CharField(max_length=10, choices=ENTRY_STATUS, default='DRAFT')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='manual_journal_entries')
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.CASCADE, related_name='manual_journal_entries')
    
    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='manual_created_journal_entries')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='manual_updated_journal_entries')
    posted_at = models.DateTimeField(null=True, blank=True)
    posted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='manual_posted_journal_entries')
    
    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = _('Journal Entry')
        verbose_name_plural = _('Journal Entries')
    
    def __str__(self):
        return f"{self.voucher_number} - {self.date} - {self.narration[:50]}"
    
    def save(self, *args, **kwargs):
        # Generate voucher number if not provided
        if not self.voucher_number:
            self.voucher_number = self.generate_voucher_number()
        
        # Calculate totals from line items
        self.calculate_totals()
        
        super().save(*args, **kwargs)
    
    def generate_voucher_number(self):
        """Generate unique voucher number"""
        prefix = "JE"
        year = self.date.year
        # Get count of entries for this year
        count = JournalEntry.objects.filter(
            date__year=year,
            voucher_number__startswith=f"{prefix}{year}"
        ).count() + 1
        return f"{prefix}{year}{count:06d}"
    
    def calculate_totals(self):
        """Calculate total debit and credit from line items"""
        if self.pk:
            self.total_debit = sum(line.debit for line in self.entries.all())
            self.total_credit = sum(line.credit for line in self.entries.all())
    
    @property
    def is_balanced(self):
        """Check if entry is balanced (debit = credit)"""
        return self.total_debit == self.total_credit
    
    @property
    def balance_difference(self):
        """Calculate the difference between debit and credit"""
        return self.total_debit - self.total_credit
    
    def post_entry(self, user):
        """Post the journal entry"""
        if self.status == 'DRAFT' and self.is_balanced:
            self.status = 'POSTED'
            self.posted_by = user
            self.posted_at = models.timezone.now()
            self.save()
            return True
        return False
    
    def void_entry(self, user):
        """Void the journal entry"""
        if self.status == 'POSTED':
            self.status = 'VOID'
            self.updated_by = user
            self.save()
            return True
        return False


class JournalEntryLine(models.Model):
    """Individual line items in a journal entry"""
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='entries')
    account = models.ForeignKey(ChartOfAccount, on_delete=models.CASCADE, related_name='manual_journal_lines')
    description = models.CharField(max_length=255, blank=True)
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    
    # Order field for maintaining line order
    order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'id']
        verbose_name = _('Journal Entry Line')
        verbose_name_plural = _('Journal Entry Lines')
    
    def __str__(self):
        return f"{self.journal_entry.voucher_number} - {self.account.account_code} - {self.description}"
    
    def save(self, *args, **kwargs):
        # Ensure only one of debit or credit has a value
        if self.debit > 0 and self.credit > 0:
            raise ValueError("A line item cannot have both debit and credit amounts")
        
        # Set order if not provided
        if not self.order and self.journal_entry:
            max_order = JournalEntryLine.objects.filter(journal_entry=self.journal_entry).aggregate(
                models.Max('order')
            )['order__max'] or 0
            self.order = max_order + 1
        
        super().save(*args, **kwargs)
    
    @property
    def amount(self):
        """Return the amount (debit or credit)"""
        return self.debit if self.debit > 0 else self.credit
    
    @property
    def is_debit(self):
        """Check if this is a debit entry"""
        return self.debit > 0
    
    @property
    def is_credit(self):
        """Check if this is a credit entry"""
        return self.credit > 0 