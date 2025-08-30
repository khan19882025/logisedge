from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
from company.company_model import Company
from fiscal_year.models import FiscalYear
from chart_of_accounts.models import ChartOfAccount


class BalanceSheetReport(models.Model):
    """Model for Balance Sheet Reports"""
    
    title = models.CharField(max_length=200)
    as_of_date = models.DateField()
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    branch = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    
    # Report data stored as JSON
    report_data = models.JSONField(default=dict)
    
    # Export options
    include_headers = models.BooleanField(default=True)
    include_totals = models.BooleanField(default=True)
    include_comparison = models.BooleanField(default=False)
    include_percentages = models.BooleanField(default=False)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_balance_sheets')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Balance Sheet Report'
        verbose_name_plural = 'Balance Sheet Reports'
    
    def __str__(self):
        return f"Balance Sheet - {self.as_of_date}"


class ReportTemplate(models.Model):
    """Model for Balance Sheet Report Templates"""
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    
    # Template configuration
    template_config = models.JSONField(default=dict)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_balance_templates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Report Template'
        verbose_name_plural = 'Report Templates'
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Ensure only one default template
        if self.is_default:
            ReportTemplate.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class AccountGroup(models.Model):
    """Model for grouping accounts in balance sheet"""
    
    ASSET_TYPES = [
        ('current_assets', 'Current Assets'),
        ('non_current_assets', 'Non-Current Assets'),
        ('current_liabilities', 'Current Liabilities'),
        ('non_current_liabilities', 'Non-Current Liabilities'),
        ('equity', 'Equity'),
    ]
    
    name = models.CharField(max_length=100)
    asset_type = models.CharField(max_length=30, choices=ASSET_TYPES)
    parent_group = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subgroups')
    accounts = models.ManyToManyField(ChartOfAccount, blank=True, related_name='balance_groups')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['asset_type', 'order', 'name']
        verbose_name = 'Account Group'
        verbose_name_plural = 'Account Groups'
    
    def __str__(self):
        return f"{self.get_asset_type_display()} - {self.name}"
    
    @property
    def total_balance(self):
        """Calculate total balance for this group"""
        return sum(account.balance for account in self.accounts.all())
    
    @property
    def subgroups_total(self):
        """Calculate total from subgroups"""
        return sum(subgroup.total_balance for subgroup in self.subgroups.all())
    
    @property
    def grand_total(self):
        """Calculate grand total including subgroups"""
        return self.total_balance + self.subgroups_total
