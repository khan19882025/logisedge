from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
from bank_accounts.models import BankAccount
from chart_of_accounts.models import ChartOfAccount
from company.company_model import Company


class BankReconciliationSession(models.Model):
    """Model for managing bank reconciliation sessions"""
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('locked', 'Locked'),
    ]
    
    # Basic Information
    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='reconciliation_sessions')
    session_name = models.CharField(max_length=200, help_text="Name for this reconciliation session")
    reconciliation_date = models.DateField(help_text="Date of reconciliation")
    
    # Status and Settings
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    tolerance_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.01'),
        help_text="Tolerance amount for partial matches"
    )
    
    # Balances
    opening_balance_erp = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    opening_balance_bank = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    closing_balance_erp = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    closing_balance_bank = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Summary Statistics
    total_erp_credits = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_erp_debits = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_bank_credits = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_bank_debits = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Audit Fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_reconciliation_sessions')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_reconciliation_sessions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-reconciliation_date', '-created_at']
        verbose_name = 'Bank Reconciliation Session'
        verbose_name_plural = 'Bank Reconciliation Sessions'
    
    def __str__(self):
        return f"{self.bank_account.bank_name} - {self.session_name} ({self.reconciliation_date})"
    
    def save(self, *args, **kwargs):
        # Set company if not provided
        if not hasattr(self, 'company'):
            self.company = self.bank_account.company
        
        # Update completion timestamp
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    @property
    def difference_amount(self):
        """Calculate the difference between ERP and Bank closing balances"""
        return self.closing_balance_erp - self.closing_balance_bank
    
    @property
    def is_balanced(self):
        """Check if reconciliation is balanced"""
        return abs(self.difference_amount) <= self.tolerance_amount
    
    @property
    def matched_entries_count(self):
        """Get count of matched entries"""
        return self.matched_entries.count()
    
    @property
    def unmatched_erp_count(self):
        """Get count of unmatched ERP entries"""
        return self.erp_entries.filter(is_matched=False).count()
    
    @property
    def unmatched_bank_count(self):
        """Get count of unmatched bank entries"""
        return self.bank_entries.filter(is_matched=False).count()


class ERPTransaction(models.Model):
    """Model for ERP transactions to be reconciled"""
    
    # Session and Account
    reconciliation_session = models.ForeignKey(
        BankReconciliationSession, 
        on_delete=models.CASCADE, 
        related_name='erp_entries'
    )
    chart_account = models.ForeignKey(
        ChartOfAccount, 
        on_delete=models.CASCADE, 
        related_name='reconciliation_entries'
    )
    
    # Transaction Details
    transaction_date = models.DateField()
    description = models.CharField(max_length=500)
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    debit_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    credit_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Matching Status
    is_matched = models.BooleanField(default=False)
    matched_bank_entry = models.ForeignKey(
        'BankStatementEntry', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='matched_erp_entries'
    )
    match_notes = models.TextField(blank=True, null=True)
    
    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['transaction_date', 'created_at']
        verbose_name = 'ERP Transaction'
        verbose_name_plural = 'ERP Transactions'
    
    def __str__(self):
        return f"{self.description} - {self.transaction_date} ({self.reference_number or 'No Ref'})"
    
    @property
    def amount(self):
        """Get the transaction amount (positive for credit, negative for debit)"""
        if self.credit_amount > 0:
            return self.credit_amount
        return -self.debit_amount
    
    @property
    def transaction_type(self):
        """Get transaction type"""
        if self.credit_amount > 0:
            return 'credit'
        return 'debit'
    
    def match_with_bank_entry(self, bank_entry, notes=""):
        """Match this ERP entry with a bank entry"""
        self.is_matched = True
        self.matched_bank_entry = bank_entry
        self.match_notes = notes
        self.save()
        
        # Mark bank entry as matched
        bank_entry.is_matched = True
        bank_entry.matched_erp_entry = self
        bank_entry.save()
    
    def unmatch(self):
        """Unmatch this ERP entry"""
        if self.matched_bank_entry:
            # Unmatch bank entry
            self.matched_bank_entry.is_matched = False
            self.matched_bank_entry.matched_erp_entry = None
            self.matched_bank_entry.save()
        
        self.is_matched = False
        self.matched_bank_entry = None
        self.match_notes = ""
        self.save()


class BankStatementEntry(models.Model):
    """Model for bank statement entries"""
    
    # Session
    reconciliation_session = models.ForeignKey(
        BankReconciliationSession, 
        on_delete=models.CASCADE, 
        related_name='bank_entries'
    )
    
    # Transaction Details
    transaction_date = models.DateField()
    description = models.CharField(max_length=500)
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    debit_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    credit_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Import Information
    import_source = models.CharField(max_length=50, default='manual', help_text="Source of import (manual, csv, excel)")
    import_reference = models.CharField(max_length=200, blank=True, null=True, help_text="Reference from import file")
    
    # Matching Status
    is_matched = models.BooleanField(default=False)
    matched_erp_entry = models.ForeignKey(
        ERPTransaction, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='matched_bank_entries'
    )
    match_notes = models.TextField(blank=True, null=True)
    
    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['transaction_date', 'created_at']
        verbose_name = 'Bank Statement Entry'
        verbose_name_plural = 'Bank Statement Entries'
    
    def __str__(self):
        return f"{self.description} - {self.transaction_date} ({self.reference_number or 'No Ref'})"
    
    @property
    def amount(self):
        """Get the transaction amount (positive for credit, negative for debit)"""
        if self.credit_amount > 0:
            return self.credit_amount
        return -self.debit_amount
    
    @property
    def transaction_type(self):
        """Get transaction type"""
        if self.credit_amount > 0:
            return 'credit'
        return 'debit'


class MatchedEntry(models.Model):
    """Model for tracking matched entries between ERP and Bank"""
    
    reconciliation_session = models.ForeignKey(
        BankReconciliationSession, 
        on_delete=models.CASCADE, 
        related_name='matched_entries'
    )
    erp_entry = models.ForeignKey(ERPTransaction, on_delete=models.CASCADE)
    bank_entry = models.ForeignKey(BankStatementEntry, on_delete=models.CASCADE)
    
    # Matching Details
    match_type = models.CharField(
        max_length=20, 
        choices=[
            ('exact', 'Exact Match'),
            ('partial', 'Partial Match'),
            ('manual', 'Manual Match'),
        ],
        default='manual'
    )
    match_confidence = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=100.00,
        help_text="Confidence score of the match (0-100)"
    )
    difference_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        help_text="Difference between ERP and Bank amounts"
    )
    
    # Notes and Comments
    notes = models.TextField(blank=True, null=True)
    
    # Audit Fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Matched Entry'
        verbose_name_plural = 'Matched Entries'
        unique_together = ['erp_entry', 'bank_entry']
    
    def __str__(self):
        return f"ERP: {self.erp_entry.description} ↔ Bank: {self.bank_entry.description}"
    
    def save(self, *args, **kwargs):
        # Calculate difference amount
        self.difference_amount = abs(self.erp_entry.amount - self.bank_entry.amount)
        
        # Calculate match confidence
        if self.erp_entry.amount != 0:
            self.match_confidence = (1 - (self.difference_amount / abs(self.erp_entry.amount))) * 100
        else:
            self.match_confidence = 100 if self.difference_amount == 0 else 0
        
        super().save(*args, **kwargs)


class ReconciliationReport(models.Model):
    """Model for storing reconciliation reports"""
    
    reconciliation_session = models.ForeignKey(
        BankReconciliationSession, 
        on_delete=models.CASCADE, 
        related_name='reports'
    )
    
    # Report Details
    report_type = models.CharField(
        max_length=30,
        choices=[
            ('summary', 'Summary Report'),
            ('detailed', 'Detailed Report'),
            ('unmatched', 'Unmatched Entries Report'),
            ('reconciliation_statement', 'Reconciliation Statement'),
        ]
    )
    report_date = models.DateTimeField(auto_now_add=True)
    
    # Report Content
    report_data = models.JSONField(default=dict, help_text="Structured report data")
    report_file = models.FileField(
        upload_to='reconciliation_reports/',
        blank=True, 
        null=True,
        help_text="Generated report file (PDF/Excel)"
    )
    
    # Audit Fields
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-report_date']
        verbose_name = 'Reconciliation Report'
        verbose_name_plural = 'Reconciliation Reports'
    
    def __str__(self):
        return f"{self.reconciliation_session.session_name} - {self.get_report_type_display()} ({self.report_date.strftime('%Y-%m-%d')})"
