from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from chart_of_accounts.models import ChartOfAccount
from company.company_model import Company
from multi_currency.models import Currency
from fiscal_year.models import FiscalYear
from manual_journal_entry.models import JournalEntry
import uuid
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class RecurringEntry(models.Model):
    """Recurring Journal Entry template model"""
    JOURNAL_TYPES = [
        ('GENERAL', 'General'),
        ('ADJUSTMENT', 'Adjustment'),
        ('OPENING', 'Opening'),
    ]
    
    FREQUENCY_CHOICES = [
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('ANNUALLY', 'Annually'),
    ]
    
    POSTING_DAY_CHOICES = [
        ('1ST', '1st of Month'),
        ('15TH', '15th of Month'),
        ('LAST', 'Last Day of Month'),
        ('CUSTOM', 'Custom Day'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('PAUSED', 'Paused'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    # Basic Information
    template_name = models.CharField(max_length=200, help_text="Name for this recurring entry template")
    journal_type = models.CharField(max_length=20, choices=JOURNAL_TYPES, default='GENERAL')
    narration = models.TextField(help_text="Description of the recurring entry")
    
    # Scheduling
    start_date = models.DateField(help_text="Date when recurring entries should start")
    end_date = models.DateField(null=True, blank=True, help_text="Optional end date for recurring entries")
    number_of_occurrences = models.PositiveIntegerField(null=True, blank=True, help_text="Optional number of occurrences")
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='MONTHLY')
    posting_day = models.CharField(max_length=10, choices=POSTING_DAY_CHOICES, default='1ST')
    custom_day = models.PositiveIntegerField(null=True, blank=True, help_text="Custom day of month (1-31)")
    
    # Financial Information
    total_debit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_credit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, default=1)  # Default to AED
    
    # Settings
    auto_post = models.BooleanField(default=False, help_text="Automatically post entries when due")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    
    # Company and Audit
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='recurring_entries')
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.CASCADE, related_name='recurring_entries')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_recurring_entries')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_recurring_entries')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Recurring Entry')
        verbose_name_plural = _('Recurring Entries')
    
    def __str__(self):
        return f"{self.template_name} - {self.get_frequency_display()}"
    
    def save(self, *args, **kwargs):
        # Calculate totals from line items
        self.calculate_totals()
        super().save(*args, **kwargs)
    
    def calculate_totals(self):
        """Calculate total debit and credit from line items"""
        if self.pk:
            self.total_debit = sum(line.debit for line in self.lines.all())
            self.total_credit = sum(line.credit for line in self.lines.all())
    
    @property
    def is_balanced(self):
        """Check if entry is balanced (debit = credit)"""
        return self.total_debit == self.total_credit
    
    @property
    def balance_difference(self):
        """Calculate the difference between debit and credit"""
        return self.total_debit - self.total_credit
    
    def get_next_posting_date(self, from_date=None):
        """Calculate the next posting date based on frequency and posting day"""
        if from_date is None:
            from_date = datetime.now().date()
        
        if from_date < self.start_date:
            from_date = self.start_date
        
        if self.end_date and from_date > self.end_date:
            return None
        
        # Calculate based on frequency
        if self.frequency == 'DAILY':
            next_date = from_date + timedelta(days=1)
        elif self.frequency == 'WEEKLY':
            next_date = from_date + timedelta(weeks=1)
        elif self.frequency == 'MONTHLY':
            next_date = self._get_monthly_date(from_date)
        elif self.frequency == 'QUARTERLY':
            next_date = self._get_quarterly_date(from_date)
        elif self.frequency == 'ANNUALLY':
            next_date = self._get_yearly_date(from_date)
        else:
            return None
        
        # Check if we've exceeded the end date or number of occurrences
        if self.end_date and next_date > self.end_date:
            return None
        
        if self.number_of_occurrences:
            generated_count = self.generated_entries.count()
            if generated_count >= self.number_of_occurrences:
                return None
        
        return next_date
    
    def _get_monthly_date(self, from_date):
        """Get next monthly posting date"""
        if self.posting_day == '1ST':
            return (from_date.replace(day=1) + relativedelta(months=1))
        elif self.posting_day == '15TH':
            next_date = from_date.replace(day=15)
            if next_date <= from_date:
                next_date = (from_date.replace(day=1) + relativedelta(months=1)).replace(day=15)
            return next_date
        elif self.posting_day == 'LAST':
            next_date = from_date.replace(day=1) + relativedelta(months=1) - timedelta(days=1)
            return next_date
        elif self.posting_day == 'CUSTOM' and self.custom_day:
            try:
                next_date = from_date.replace(day=self.custom_day)
                if next_date <= from_date:
                    next_date = (from_date.replace(day=1) + relativedelta(months=1)).replace(day=self.custom_day)
                return next_date
            except ValueError:
                # Handle invalid day (e.g., 31st in February)
                next_date = from_date.replace(day=1) + relativedelta(months=1)
                return next_date.replace(day=1) - timedelta(days=1)
        return None
    
    def _get_quarterly_date(self, from_date):
        """Get next quarterly posting date"""
        if self.posting_day == '1ST':
            return (from_date.replace(day=1) + relativedelta(months=3))
        elif self.posting_day == '15TH':
            next_date = from_date.replace(day=15)
            if next_date <= from_date:
                next_date = (from_date.replace(day=1) + relativedelta(months=3)).replace(day=15)
            return next_date
        elif self.posting_day == 'LAST':
            next_date = from_date.replace(day=1) + relativedelta(months=3) - timedelta(days=1)
            return next_date
        elif self.posting_day == 'CUSTOM' and self.custom_day:
            try:
                next_date = from_date.replace(day=self.custom_day)
                if next_date <= from_date:
                    next_date = (from_date.replace(day=1) + relativedelta(months=3)).replace(day=self.custom_day)
                return next_date
            except ValueError:
                next_date = from_date.replace(day=1) + relativedelta(months=3)
                return next_date.replace(day=1) - timedelta(days=1)
        return None
    
    def _get_yearly_date(self, from_date):
        """Get next yearly posting date"""
        if self.posting_day == '1ST':
            return (from_date.replace(day=1) + relativedelta(years=1))
        elif self.posting_day == '15TH':
            next_date = from_date.replace(day=15)
            if next_date <= from_date:
                next_date = (from_date.replace(day=1) + relativedelta(years=1)).replace(day=15)
            return next_date
        elif self.posting_day == 'LAST':
            next_date = from_date.replace(day=1) + relativedelta(years=1) - timedelta(days=1)
            return next_date
        elif self.posting_day == 'CUSTOM' and self.custom_day:
            try:
                next_date = from_date.replace(day=self.custom_day)
                if next_date <= from_date:
                    next_date = (from_date.replace(day=1) + relativedelta(years=1)).replace(day=self.custom_day)
                return next_date
            except ValueError:
                next_date = from_date.replace(day=1) + relativedelta(years=1)
                return next_date.replace(day=1) - timedelta(days=1)
        return None
    
    def generate_journal_entry(self, posting_date, user):
        """Generate a journal entry for the given posting date"""
        if not self.is_balanced:
            raise ValueError("Recurring entry must be balanced before generating journal entries")
        
        # Create the journal entry
        journal_entry = JournalEntry.objects.create(
            voucher_number=f"RE{posting_date.strftime('%Y%m%d')}{self.id:04d}",
            date=posting_date,
            reference_number=f"Recurring: {self.template_name}",
            narration=self.narration,
            currency=self.currency,
            fiscal_year=self.fiscal_year,
            company=self.company,
            created_by=user,
            status='POSTED' if self.auto_post else 'DRAFT'
        )
        
        # Create line items
        for line in self.lines.all():
            journal_entry.entries.create(
                account=line.account,
                description=line.description,
                debit=line.debit,
                credit=line.credit,
                order=line.order
            )
        
        # Create generated entry record
        GeneratedEntry.objects.create(
            recurring_entry=self,
            journal_entry=journal_entry,
            posting_date=posting_date,
            generated_by=user
        )
        
        return journal_entry
    
    def pause(self):
        """Pause the recurring entry"""
        self.status = 'PAUSED'
        self.save()
    
    def resume(self):
        """Resume the recurring entry"""
        self.status = 'ACTIVE'
        self.save()
    
    def cancel(self):
        """Cancel the recurring entry"""
        self.status = 'CANCELLED'
        self.save()


class RecurringEntryLine(models.Model):
    """Individual line items in a recurring entry"""
    recurring_entry = models.ForeignKey(RecurringEntry, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey(ChartOfAccount, on_delete=models.CASCADE, related_name='recurring_entry_lines')
    description = models.CharField(max_length=255, blank=True)
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    
    # Order field for maintaining line order
    order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'id']
        verbose_name = _('Recurring Entry Line')
        verbose_name_plural = _('Recurring Entry Lines')
    
    def __str__(self):
        return f"{self.recurring_entry.template_name} - {self.account.account_code} - {self.description}"
    
    def save(self, *args, **kwargs):
        # Ensure only one of debit or credit has a value
        if self.debit > 0 and self.credit > 0:
            raise ValueError("A line item cannot have both debit and credit amounts")
        
        # Set order if not provided
        if not self.order and self.recurring_entry:
            max_order = RecurringEntryLine.objects.filter(recurring_entry=self.recurring_entry).aggregate(
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


class GeneratedEntry(models.Model):
    """Track generated journal entries from recurring entries"""
    recurring_entry = models.ForeignKey(RecurringEntry, on_delete=models.CASCADE, related_name='generated_entries')
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='recurring_source')
    posting_date = models.DateField()
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-posting_date']
        verbose_name = _('Generated Entry')
        verbose_name_plural = _('Generated Entries')
        unique_together = ['recurring_entry', 'posting_date']
    
    def __str__(self):
        return f"{self.recurring_entry.template_name} - {self.posting_date}"
