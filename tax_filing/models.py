import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class TaxFilingReport(models.Model):
    """Model for Tax Filing Reports"""
    FILING_PERIODS = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('generated', 'Generated'),
        ('reviewed', 'Reviewed'),
        ('submitted', 'Submitted'),
        ('filed', 'Filed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_name = models.CharField(max_length=200)
    filing_period = models.CharField(max_length=20, choices=FILING_PERIODS, default='monthly')
    start_date = models.DateField()
    end_date = models.DateField()
    currency = models.CharField(max_length=3, default='AED')
    
    # Tax totals
    total_output_tax = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_input_tax = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_adjustments = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    net_tax_payable = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Transaction counts
    output_transactions_count = models.IntegerField(default=0)
    input_transactions_count = models.IntegerField(default=0)
    adjustment_transactions_count = models.IntegerField(default=0)
    
    # Validation flags
    has_missing_vat_numbers = models.BooleanField(default=False)
    has_mismatched_rates = models.BooleanField(default=False)
    validation_errors = models.JSONField(default=dict, blank=True)
    
    # Filing metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    filing_reference = models.CharField(max_length=100, blank=True)
    filing_date = models.DateTimeField(null=True, blank=True)
    filed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='filed_tax_reports')
    
    # Report metadata
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='generated_tax_filings')
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-generated_at']
        verbose_name = 'Tax Filing Report'
        verbose_name_plural = 'Tax Filing Reports'
    
    def __str__(self):
        return f"{self.report_name} ({self.start_date} to {self.end_date})"
    
    @property
    def net_tax_calculated(self):
        """Calculate net tax payable/refundable"""
        return self.total_output_tax - self.total_input_tax + self.total_adjustments


class TaxFilingTransaction(models.Model):
    """Model for individual transactions in tax filing reports"""
    TRANSACTION_TYPES = [
        ('output', 'Output Tax (Sales)'),
        ('input', 'Input Tax (Purchases)'),
        ('adjustment', 'Adjustment'),
    ]
    
    ADJUSTMENT_TYPES = [
        ('credit_note', 'Credit Note'),
        ('debit_note', 'Debit Note'),
        ('refund', 'Refund'),
        ('write_off', 'Write-off'),
        ('correction', 'Correction'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(TaxFilingReport, on_delete=models.CASCADE, related_name='transactions')
    transaction_date = models.DateField()
    invoice_number = models.CharField(max_length=100)
    party_name = models.CharField(max_length=255)
    vat_number = models.CharField(max_length=50, blank=True)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    adjustment_type = models.CharField(max_length=20, choices=ADJUSTMENT_TYPES, blank=True)
    taxable_amount = models.DecimalField(max_digits=15, decimal_places=2)
    vat_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    vat_amount = models.DecimalField(max_digits=15, decimal_places=2)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='AED')
    
    # Validation flags
    has_vat_number = models.BooleanField(default=True)
    vat_rate_matches = models.BooleanField(default=True)
    validation_notes = models.TextField(blank=True)
    
    # Reference to original transaction
    original_transaction_id = models.CharField(max_length=100, blank=True)
    original_transaction_type = models.CharField(max_length=50, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['transaction_date', 'invoice_number']
        verbose_name = 'Tax Filing Transaction'
        verbose_name_plural = 'Tax Filing Transactions'
    
    def __str__(self):
        return f"{self.invoice_number} - {self.party_name} ({self.get_transaction_type_display()})"


class TaxFilingValidation(models.Model):
    """Model for tracking validation issues in tax filing reports"""
    VALIDATION_TYPES = [
        ('missing_vat_number', 'Missing VAT Number'),
        ('mismatched_rate', 'Mismatched VAT Rate'),
        ('invalid_amount', 'Invalid Amount'),
        ('duplicate_invoice', 'Duplicate Invoice'),
        ('date_out_of_range', 'Date Out of Range'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(TaxFilingReport, on_delete=models.CASCADE, related_name='validations')
    transaction = models.ForeignKey(TaxFilingTransaction, on_delete=models.CASCADE, related_name='validations', null=True, blank=True)
    validation_type = models.CharField(max_length=50, choices=VALIDATION_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    description = models.TextField()
    field_name = models.CharField(max_length=100, blank=True)
    expected_value = models.CharField(max_length=255, blank=True)
    actual_value = models.CharField(max_length=255, blank=True)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_validations')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-severity', '-created_at']
        verbose_name = 'Tax Filing Validation'
        verbose_name_plural = 'Tax Filing Validations'
    
    def __str__(self):
        return f"{self.get_validation_type_display()} - {self.description[:50]}"


class TaxFilingExport(models.Model):
    """Model for tracking exported tax filing reports"""
    EXPORT_FORMATS = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
        ('xml', 'XML'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(TaxFilingReport, on_delete=models.CASCADE, related_name='exports')
    export_format = models.CharField(max_length=10, choices=EXPORT_FORMATS)
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.IntegerField(default=0)
    exported_at = models.DateTimeField(auto_now_add=True)
    exported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='exported_tax_filings')
    
    class Meta:
        ordering = ['-exported_at']
        verbose_name = 'Tax Filing Export'
        verbose_name_plural = 'Tax Filing Exports'
    
    def __str__(self):
        return f"{self.report.report_name} - {self.get_export_format_display()}"


class TaxFilingSettings(models.Model):
    """Model for tax filing configuration settings"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tax_authority_name = models.CharField(max_length=200, default='Local Tax Authority')
    tax_authority_code = models.CharField(max_length=50, blank=True)
    filing_deadline_days = models.IntegerField(default=28)
    auto_validation = models.BooleanField(default=True)
    require_vat_numbers = models.BooleanField(default=True)
    default_currency = models.CharField(max_length=3, default='AED')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_tax_filing_settings')
    
    class Meta:
        verbose_name = 'Tax Filing Setting'
        verbose_name_plural = 'Tax Filing Settings'
    
    def __str__(self):
        return f"Tax Filing Settings - {self.tax_authority_name}"
