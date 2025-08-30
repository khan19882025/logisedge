from django.db import models
from django.contrib.auth.models import User
from chart_of_accounts.models import ChartOfAccount
from company.company_model import Company
from fiscal_year.models import FiscalYear
from django.utils import timezone


class GeneralLedgerReport(models.Model):
    """Model to store General Ledger Report configurations and filters"""
    
    REPORT_TYPES = [
        ('DETAILED', 'Detailed Report'),
        ('SUMMARY', 'Summary Report'),
        ('COMPARATIVE', 'Comparative Report'),
    ]
    
    EXPORT_FORMATS = [
        ('PDF', 'PDF'),
        ('EXCEL', 'Excel'),
        ('CSV', 'CSV'),
    ]
    
    # Report Configuration
    name = models.CharField(max_length=200, help_text="Report name")
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES, default='DETAILED')
    
    # Date Range
    from_date = models.DateField(help_text="Start date for the report")
    to_date = models.DateField(help_text="End date for the report")
    
    # Account Filters
    account = models.ForeignKey(
        ChartOfAccount, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        help_text="Specific account to filter (optional)"
    )
    include_sub_accounts = models.BooleanField(
        default=True, 
        help_text="Include sub-accounts in the report"
    )
    
    # Company and Fiscal Year
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='general_ledger_reports')
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.CASCADE, related_name='general_ledger_reports')
    
    # Additional Filters
    min_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Minimum transaction amount to include"
    )
    max_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Maximum transaction amount to include"
    )
    include_reconciled_only = models.BooleanField(
        default=False,
        help_text="Include only reconciled entries"
    )
    include_unreconciled_only = models.BooleanField(
        default=False,
        help_text="Include only unreconciled entries"
    )
    
    # Export Settings
    export_format = models.CharField(
        max_length=10, 
        choices=EXPORT_FORMATS, 
        default='PDF',
        help_text="Default export format"
    )
    include_opening_balance = models.BooleanField(
        default=True,
        help_text="Include opening balance in the report"
    )
    include_closing_balance = models.BooleanField(
        default=True,
        help_text="Include closing balance in the report"
    )
    
    # Audit Fields
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='general_ledger_reports_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='general_ledger_reports_updated'
    )
    updated_at = models.DateTimeField(auto_now=True)
    
    # Report Status
    is_saved = models.BooleanField(default=False, help_text="Whether this is a saved report")
    last_generated = models.DateTimeField(null=True, blank=True, help_text="When the report was last generated")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "General Ledger Report"
        verbose_name_plural = "General Ledger Reports"
    
    def __str__(self):
        account_name = f" - {self.account.name}" if self.account else ""
        return f"{self.name} ({self.from_date} to {self.to_date}){account_name}"
    
    def save(self, *args, **kwargs):
        # Auto-generate name if not provided
        if not self.name:
            account_name = f" - {self.account.name}" if self.account else " - All Accounts"
            self.name = f"General Ledger Report{account_name} ({self.from_date} to {self.to_date})"
        
        super().save(*args, **kwargs)
    
    @property
    def date_range_display(self):
        """Return formatted date range"""
        return f"{self.from_date.strftime('%d/%m/%Y')} - {self.to_date.strftime('%d/%m/%Y')}"
    
    @property
    def filter_summary(self):
        """Return a summary of applied filters"""
        filters = []
        
        if self.account:
            filters.append(f"Account: {self.account.name}")
        
        if self.min_amount:
            filters.append(f"Min Amount: {self.min_amount:,.2f}")
        
        if self.max_amount:
            filters.append(f"Max Amount: {self.max_amount:,.2f}")
        
        if self.include_reconciled_only:
            filters.append("Reconciled Only")
        elif self.include_unreconciled_only:
            filters.append("Unreconciled Only")
        
        return ", ".join(filters) if filters else "All transactions"


class ReportTemplate(models.Model):
    """Model to store reusable report templates"""
    
    TEMPLATE_TYPES = [
        ('CUSTOM', 'Custom Template'),
        ('SYSTEM', 'System Template'),
    ]
    
    name = models.CharField(max_length=200, help_text="Template name")
    description = models.TextField(blank=True, help_text="Template description")
    template_type = models.CharField(max_length=10, choices=TEMPLATE_TYPES, default='CUSTOM')
    
    # Template Configuration (stored as JSON-like fields)
    default_from_date = models.DateField(null=True, blank=True, help_text="Default start date")
    default_to_date = models.DateField(null=True, blank=True, help_text="Default end date")
    default_account_codes = models.TextField(blank=True, help_text="Comma-separated account codes")
    
    # Settings
    include_sub_accounts = models.BooleanField(default=True)
    include_opening_balance = models.BooleanField(default=True)
    include_closing_balance = models.BooleanField(default=True)
    default_export_format = models.CharField(max_length=10, choices=GeneralLedgerReport.EXPORT_FORMATS, default='PDF')
    
    # Company and User
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='report_templates')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='report_templates_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=False, help_text="Available to all users in the company")
    
    class Meta:
        ordering = ['name']
        verbose_name = "Report Template"
        verbose_name_plural = "Report Templates"
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"
    
    @property
    def account_codes_list(self):
        """Return list of account codes"""
        if self.default_account_codes:
            return [code.strip() for code in self.default_account_codes.split(',') if code.strip()]
        return []
