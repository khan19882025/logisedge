from django.db import models
from django.contrib.auth.models import User
from company.company_model import Company
from fiscal_year.models import FiscalYear
from multi_currency.models import Currency
from django.utils import timezone
from decimal import Decimal


class CashFlowStatement(models.Model):
    """Model for storing cash flow statement configurations and results"""
    
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
    
    # Basic Information
    name = models.CharField(max_length=200, help_text="Report name")
    description = models.TextField(blank=True, help_text="Report description")
    
    # Date Range
    from_date = models.DateField(help_text="Start date for the report")
    to_date = models.DateField(help_text="End date for the report")
    
    # Company and Currency
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='cash_flow_statements')
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, default=1)  # Default to AED
    
    # Fiscal Year
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.CASCADE, related_name='cash_flow_statements')
    
    # Report Configuration
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES, default='DETAILED')
    export_format = models.CharField(max_length=10, choices=EXPORT_FORMATS, default='PDF')
    
    # Include Options
    include_comparative = models.BooleanField(default=False, help_text="Include comparative period")
    include_notes = models.BooleanField(default=True, help_text="Include explanatory notes")
    include_charts = models.BooleanField(default=True, help_text="Include charts and graphs")
    
    # Status and Audit
    is_saved = models.BooleanField(default=False, help_text="Whether this report is saved")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='cash_flow_reports_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Cash Flow Statement'
        verbose_name_plural = 'Cash Flow Statements'
    
    def __str__(self):
        return f"{self.name} - {self.from_date} to {self.to_date}"
    
    @property
    def period_days(self):
        """Calculate the number of days in the report period"""
        return (self.to_date - self.from_date).days + 1
    
    @property
    def is_current_period(self):
        """Check if this is the current fiscal period"""
        today = timezone.now().date()
        return self.from_date <= today <= self.to_date


class CashFlowTemplate(models.Model):
    """Model for storing reusable cash flow statement templates"""
    
    TEMPLATE_TYPES = [
        ('STANDARD', 'Standard Template'),
        ('CUSTOM', 'Custom Template'),
        ('INDUSTRY', 'Industry Specific'),
    ]
    
    name = models.CharField(max_length=200, help_text="Template name")
    description = models.TextField(blank=True, help_text="Template description")
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES, default='STANDARD')
    
    # Template Configuration
    include_operating_activities = models.BooleanField(default=True)
    include_investing_activities = models.BooleanField(default=True)
    include_financing_activities = models.BooleanField(default=True)
    
    # Customization Options
    custom_operating_items = models.JSONField(default=list, blank=True)
    custom_investing_items = models.JSONField(default=list, blank=True)
    custom_financing_items = models.JSONField(default=list, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=False, help_text="Available to all users")
    
    # Audit
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='cash_flow_templates_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Cash Flow Template'
        verbose_name_plural = 'Cash Flow Templates'
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"


class CashFlowCategory(models.Model):
    """Model for categorizing cash flow items"""
    
    CATEGORY_TYPES = [
        ('OPERATING', 'Operating Activities'),
        ('INVESTING', 'Investing Activities'),
        ('FINANCING', 'Financing Activities'),
    ]
    
    name = models.CharField(max_length=200, help_text="Category name")
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPES)
    description = models.TextField(blank=True, help_text="Category description")
    
    # Display Options
    display_order = models.PositiveIntegerField(default=0, help_text="Display order in reports")
    is_active = models.BooleanField(default=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category_type', 'display_order', 'name']
        verbose_name = 'Cash Flow Category'
        verbose_name_plural = 'Cash Flow Categories'
    
    def __str__(self):
        return f"{self.get_category_type_display()} - {self.name}"


class CashFlowItem(models.Model):
    """Model for individual cash flow line items"""
    
    ITEM_TYPES = [
        ('INCOME', 'Income'),
        ('EXPENSE', 'Expense'),
        ('ASSET', 'Asset'),
        ('LIABILITY', 'Liability'),
        ('EQUITY', 'Equity'),
    ]
    
    name = models.CharField(max_length=200, help_text="Item name")
    category = models.ForeignKey(CashFlowCategory, on_delete=models.CASCADE, related_name='items')
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES)
    
    # Calculation Method
    calculation_method = models.CharField(
        max_length=50,
        default='DIRECT',
        help_text="How to calculate this item (DIRECT, INDIRECT, CUSTOM)"
    )
    
    # Account Mapping (for automatic calculations)
    account_codes = models.JSONField(default=list, blank=True, help_text="Chart of account codes to include")
    
    # Display Options
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_subtotal = models.BooleanField(default=False, help_text="Whether this is a subtotal line")
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category__display_order', 'display_order', 'name']
        verbose_name = 'Cash Flow Item'
        verbose_name_plural = 'Cash Flow Items'
    
    def __str__(self):
        return f"{self.category.name} - {self.name}" 