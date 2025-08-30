import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class TaxSummaryReport(models.Model):
    """Model for Tax Summary Reports"""
    REPORT_TYPES = [
        ('input_output', 'Input/Output Tax Summary'),
        ('vat_summary', 'VAT Summary'),
        ('detailed', 'Detailed Tax Report'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('generated', 'Generated'),
        ('exported', 'Exported'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES, default='input_output')
    start_date = models.DateField()
    end_date = models.DateField()
    currency = models.CharField(max_length=3, default='AED')
    
    # Summary totals
    total_input_tax = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_output_tax = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    net_vat_payable = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Transaction counts
    input_transactions_count = models.IntegerField(default=0)
    output_transactions_count = models.IntegerField(default=0)
    
    # Filters applied
    filters_applied = models.JSONField(default=dict, blank=True)
    
    # Status and metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='generated_tax_summaries')
    
    class Meta:
        ordering = ['-generated_at']
        verbose_name = 'Tax Summary Report'
        verbose_name_plural = 'Tax Summary Reports'
    
    def __str__(self):
        return f"{self.report_name} ({self.start_date} to {self.end_date})"
    
    @property
    def net_vat_calculated(self):
        """Calculate net VAT payable/refundable"""
        return self.total_output_tax - self.total_input_tax


class TaxSummaryTransaction(models.Model):
    """Model for individual transactions in tax summary reports"""
    TRANSACTION_TYPES = [
        ('input', 'Input Tax'),
        ('output', 'Output Tax'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(TaxSummaryReport, on_delete=models.CASCADE, related_name='transactions')
    transaction_date = models.DateField()
    invoice_number = models.CharField(max_length=100)
    party_name = models.CharField(max_length=255)
    vat_number = models.CharField(max_length=50, blank=True)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    taxable_amount = models.DecimalField(max_digits=15, decimal_places=2)
    vat_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    vat_amount = models.DecimalField(max_digits=15, decimal_places=2)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='AED')
    
    # Reference to original transaction
    original_transaction_id = models.CharField(max_length=100, blank=True)
    original_transaction_type = models.CharField(max_length=50, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['transaction_date', 'invoice_number']
        verbose_name = 'Tax Summary Transaction'
        verbose_name_plural = 'Tax Summary Transactions'
    
    def __str__(self):
        return f"{self.invoice_number} - {self.party_name} ({self.get_transaction_type_display()})"


class TaxSummaryFilter(models.Model):
    """Model for storing filter configurations for tax summary reports"""
    FILTER_TYPES = [
        ('date_range', 'Date Range'),
        ('party_name', 'Party Name'),
        ('vat_number', 'VAT Number'),
        ('transaction_type', 'Transaction Type'),
        ('tax_rate', 'Tax Rate'),
        ('currency', 'Currency'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(TaxSummaryReport, on_delete=models.CASCADE, related_name='filters')
    filter_type = models.CharField(max_length=20, choices=FILTER_TYPES)
    filter_value = models.CharField(max_length=255)
    filter_label = models.CharField(max_length=100)
    
    class Meta:
        verbose_name = 'Tax Summary Filter'
        verbose_name_plural = 'Tax Summary Filters'
    
    def __str__(self):
        return f"{self.filter_type}: {self.filter_label}"


class TaxSummaryExport(models.Model):
    """Model for tracking exported tax summary reports"""
    EXPORT_FORMATS = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(TaxSummaryReport, on_delete=models.CASCADE, related_name='exports')
    export_format = models.CharField(max_length=10, choices=EXPORT_FORMATS)
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.IntegerField(default=0)
    exported_at = models.DateTimeField(auto_now_add=True)
    exported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='exported_tax_summaries')
    
    class Meta:
        ordering = ['-exported_at']
        verbose_name = 'Tax Summary Export'
        verbose_name_plural = 'Tax Summary Exports'
    
    def __str__(self):
        return f"{self.report.report_name} - {self.get_export_format_display()} ({self.exported_at.date()})"
