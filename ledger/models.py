from django.db import models
from django.contrib.auth.models import User
from chart_of_accounts.models import ChartOfAccount as Account
from company.company_model import Company
from fiscal_year.models import FiscalYear
from django.utils import timezone
from decimal import Decimal


class Ledger(models.Model):
    """Ledger model for accounting entries"""
    
    ENTRY_TYPES = [
        ('DR', 'Debit'),
        ('CR', 'Credit'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('POSTED', 'Posted'),
        ('VOID', 'Void'),
    ]
    
    # Basic Information
    ledger_number = models.CharField(max_length=50, unique=True, help_text="Unique ledger entry number")
    entry_date = models.DateField(default=timezone.now, help_text="Date of the ledger entry")
    reference = models.CharField(max_length=100, blank=True, help_text="Reference number or description")
    description = models.TextField(help_text="Detailed description of the transaction")
    
    # Account Information
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='ledger_entries', help_text="Account for this entry")
    entry_type = models.CharField(max_length=2, choices=ENTRY_TYPES, help_text="Debit or Credit entry")
    amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Transaction amount (optional)")
    
    # Balance Information
    running_balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), help_text="Running balance after this entry")
    
    # Status and Control
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DRAFT', help_text="Entry status")
    is_reconciled = models.BooleanField(default=False, help_text="Whether this entry has been reconciled")
    reconciliation_date = models.DateField(null=True, blank=True, help_text="Date when entry was reconciled")
    
    # Audit Information
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='ledger_entries_created', help_text="User who created this entry")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Entry creation timestamp")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='ledger_entries_updated', help_text="User who last updated this entry")
    updated_at = models.DateTimeField(auto_now=True, help_text="Last update timestamp")
    
    # Company and Fiscal Year
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='ledger_entries', help_text="Company this entry belongs to")
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.CASCADE, related_name='ledger_entries', help_text="Fiscal year for this entry")
    
    # Additional Fields
    voucher_number = models.CharField(max_length=50, blank=True, help_text="Voucher number if applicable")
    cheque_number = models.CharField(max_length=50, blank=True, help_text="Cheque number if applicable")
    bank_reference = models.CharField(max_length=100, blank=True, help_text="Bank reference number")
    
    # Payment Source (linked from invoice)
    payment_source = models.ForeignKey('payment_source.PaymentSource', on_delete=models.SET_NULL, null=True, blank=True, help_text="Payment source from invoice")
    
    class Meta:
        ordering = ['-entry_date', '-created_at']
        verbose_name = "Ledger Entry"
        verbose_name_plural = "Ledger Entries"
        indexes = [
            models.Index(fields=['account', 'entry_date']),
            models.Index(fields=['ledger_number']),
            models.Index(fields=['status']),
            models.Index(fields=['company', 'fiscal_year']),
        ]
    
    def __str__(self):
        amount_str = f"{self.amount:,.2f}" if self.amount is not None else "0.00"
        return f"{self.ledger_number} - {self.account.name} - {amount_str}"
    
    def save(self, *args, **kwargs):
        # Auto-generate ledger number if not provided
        if not self.ledger_number:
            self.ledger_number = self.generate_ledger_number()
        
        # Calculate running balance
        if self.pk:  # Update existing entry
            self.calculate_running_balance()
        else:  # New entry
            self.calculate_running_balance()
        
        super().save(*args, **kwargs)
    
    def generate_ledger_number(self):
        """Generate unique ledger number"""
        # Use fiscal year name or extract year from start date
        year = self.fiscal_year.start_date.year if self.fiscal_year.start_date else self.fiscal_year.name
        prefix = f"LED-{year}-"
        last_entry = Ledger.objects.filter(
            ledger_number__startswith=prefix,
            company=self.company
        ).order_by('-ledger_number').first()
        
        if last_entry:
            try:
                last_number = int(last_entry.ledger_number.split('-')[-1])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1
        
        return f"{prefix}{new_number:06d}"
    
    def calculate_running_balance(self):
        """Calculate running balance for this account"""
        # Get all previous entries for this account in the same fiscal year
        previous_entries = Ledger.objects.filter(
            account=self.account,
            company=self.company,
            fiscal_year=self.fiscal_year,
            entry_date__lte=self.entry_date,
            status='POSTED'
        ).exclude(pk=self.pk).order_by('entry_date', 'created_at')
        
        # Calculate balance from previous entries
        balance = Decimal('0.00')
        for entry in previous_entries:
            if entry.amount is not None:
                if entry.entry_type == 'DR':
                    balance += entry.amount
                else:  # CR
                    balance -= entry.amount
        
        # Add current entry
        if self.amount is not None:
            if self.entry_type == 'DR':
                balance += self.amount
            else:  # CR
                balance -= self.amount
        
        self.running_balance = balance
    
    @property
    def formatted_amount(self):
        """Return formatted amount with currency symbol"""
        if self.amount is None:
            return "0.00"
        return f"{self.amount:,.2f}"
    
    @property
    def formatted_balance(self):
        """Return formatted running balance with currency symbol"""
        return f"{self.running_balance:,.2f}"
    
    @property
    def entry_type_display(self):
        """Return display name for entry type"""
        return dict(self.ENTRY_TYPES)[self.entry_type]
    
    @property
    def status_display(self):
        """Return display name for status"""
        return dict(self.STATUS_CHOICES)[self.status]


class LedgerBatch(models.Model):
    """Batch model for grouping related ledger entries"""
    
    BATCH_TYPES = [
        ('JOURNAL', 'Journal Entry'),
        ('PAYMENT', 'Payment'),
        ('RECEIPT', 'Receipt'),
        ('ADJUSTMENT', 'Adjustment'),
        ('OPENING', 'Opening Balance'),
    ]
    
    batch_number = models.CharField(max_length=50, unique=True, help_text="Unique batch number")
    batch_type = models.CharField(max_length=20, choices=BATCH_TYPES, help_text="Type of batch")
    description = models.TextField(help_text="Batch description")
    total_debit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), help_text="Total debit amount")
    total_credit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), help_text="Total credit amount")
    
    # Status
    is_balanced = models.BooleanField(default=False, help_text="Whether debits equal credits")
    is_posted = models.BooleanField(default=False, help_text="Whether batch has been posted")
    
    # Audit
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='ledger_batches_created')
    created_at = models.DateTimeField(auto_now_add=True)
    posted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='ledger_batches_posted')
    posted_at = models.DateTimeField(null=True, blank=True)
    
    # Company and Fiscal Year
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='ledger_batches')
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.CASCADE, related_name='ledger_batches')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Ledger Batch"
        verbose_name_plural = "Ledger Batches"
    
    def __str__(self):
        return f"{self.batch_number} - {self.batch_type}"
    
    def save(self, *args, **kwargs):
        # Auto-generate batch number if not provided
        if not self.batch_number:
            self.batch_number = self.generate_batch_number()
        
        # Check if batch is balanced
        self.is_balanced = (self.total_debit == self.total_credit)
        
        super().save(*args, **kwargs)
    
    def generate_batch_number(self):
        """Generate unique batch number"""
        # Use fiscal year name or extract year from start date
        year = self.fiscal_year.start_date.year if self.fiscal_year.start_date else self.fiscal_year.name
        prefix = f"BATCH-{year}-"
        last_batch = LedgerBatch.objects.filter(
            batch_number__startswith=prefix,
            company=self.company
        ).order_by('-batch_number').first()
        
        if last_batch:
            try:
                last_number = int(last_batch.batch_number.split('-')[-1])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1
        
        return f"{prefix}{new_number:06d}"
    
    @property
    def entry_count(self):
        """Return number of entries in this batch"""
        return self.ledger_entries.count()
    
    @property
    def difference(self):
        """Return difference between debits and credits"""
        return abs(self.total_debit - self.total_credit)
