from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid


class CostCenterFinancialReport(models.Model):
    """Model for cost center financial reports"""
    REPORT_TYPES = [
        ('summary', 'Summary View'),
        ('detailed', 'Detailed View'),
        ('budget_variance', 'Budget Variance'),
        ('profit_loss', 'Profit & Loss'),
        ('expense_analysis', 'Expense Analysis'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('generated', 'Generated'),
        ('archived', 'Archived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    cost_center = models.ForeignKey('cost_center_management.CostCenter', on_delete=models.CASCADE, null=True, blank=True, related_name='financial_reports')
    department = models.ForeignKey('cost_center_management.Department', on_delete=models.CASCADE, null=True, blank=True, related_name='financial_reports')
    include_inactive = models.BooleanField(default=False, help_text="Include inactive cost centers in the report")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    report_data = models.JSONField(default=dict, help_text="Stored report data")
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='generated_cost_center_financial_reports')
    
    class Meta:
        ordering = ['-generated_at']
        verbose_name = 'Cost Center Financial Report'
        verbose_name_plural = 'Cost Center Financial Reports'
    
    def __str__(self):
        return f"{self.report_name} ({self.report_type}) - {self.start_date} to {self.end_date}"
    
    @property
    def total_budget(self):
        """Calculate total budget for the report period"""
        if self.cost_center:
            return self.cost_center.budget_amount
        return Decimal('0.00')
    
    @property
    def total_actual(self):
        """Calculate total actual spend for the report period"""
        from cost_center_transaction_tagging.models import TransactionTagging
        
        queryset = TransactionTagging.objects.filter(
            transaction_date__range=[self.start_date, self.end_date],
            is_active=True
        )
        
        if self.cost_center:
            queryset = queryset.filter(cost_center=self.cost_center)
        elif self.department:
            queryset = queryset.filter(cost_center__department=self.department)
        
        return queryset.aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
    
    @property
    def total_variance(self):
        """Calculate total variance"""
        return self.total_budget - self.total_actual
    
    @property
    def variance_percentage(self):
        """Calculate variance percentage"""
        if self.total_budget > 0:
            return (self.total_variance / self.total_budget) * 100
        return 0


class CostCenterReportFilter(models.Model):
    """Model for storing report filters"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(CostCenterFinancialReport, on_delete=models.CASCADE, related_name='filters')
    filter_name = models.CharField(max_length=100)
    filter_value = models.TextField()
    filter_type = models.CharField(max_length=50, help_text="Type of filter (date_range, cost_center, department, etc.)")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['filter_name']
        verbose_name = 'Cost Center Report Filter'
        verbose_name_plural = 'Cost Center Report Filters'
    
    def __str__(self):
        return f"{self.filter_name}: {self.filter_value}"


class CostCenterReportExport(models.Model):
    """Model for storing report exports"""
    EXPORT_TYPES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(CostCenterFinancialReport, on_delete=models.CASCADE, related_name='exports')
    export_type = models.CharField(max_length=10, choices=EXPORT_TYPES)
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.IntegerField(default=0, help_text="File size in bytes")
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='generated_cost_center_report_exports')
    
    class Meta:
        ordering = ['-generated_at']
        verbose_name = 'Cost Center Report Export'
        verbose_name_plural = 'Cost Center Report Exports'
    
    def __str__(self):
        return f"{self.report.report_name} - {self.export_type.upper()} ({self.generated_at.strftime('%Y-%m-%d %H:%M')})"


class CostCenterReportSchedule(models.Model):
    """Model for scheduling automated reports"""
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    schedule_name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=CostCenterFinancialReport.REPORT_TYPES)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    recipients = models.JSONField(default=list, help_text="List of email addresses to receive the report")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_cost_center_report_schedules')
    
    class Meta:
        ordering = ['schedule_name']
        verbose_name = 'Cost Center Report Schedule'
        verbose_name_plural = 'Cost Center Report Schedules'
    
    def __str__(self):
        return f"{self.schedule_name} ({self.frequency})"
