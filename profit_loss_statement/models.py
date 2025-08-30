from django.db import models
from django.contrib.auth.models import User
from company.company_model import Company


class ProfitLossReport(models.Model):
    """Model to store generated Profit & Loss reports"""
    
    REPORT_PERIOD_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
        ('custom', 'Custom Period'),
    ]
    
    COMPARISON_CHOICES = [
        ('none', 'No Comparison'),
        ('previous_period', 'Previous Period'),
        ('previous_year', 'Previous Year'),
        ('budget', 'Budget Comparison'),
    ]
    
    title = models.CharField(max_length=200)
    from_date = models.DateField()
    to_date = models.DateField()
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    report_period = models.CharField(max_length=20, choices=REPORT_PERIOD_CHOICES, default='custom')
    comparison_type = models.CharField(max_length=20, choices=COMPARISON_CHOICES, default='none')
    
    # Report data (JSON field to store the actual report data)
    report_data = models.JSONField(default=dict)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Export settings
    include_headers = models.BooleanField(default=True)
    include_totals = models.BooleanField(default=True)
    include_comparison = models.BooleanField(default=False)
    currency_format = models.CharField(max_length=10, default='AED')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Profit & Loss Report'
        verbose_name_plural = 'Profit & Loss Reports'
    
    def __str__(self):
        return f"{self.title} - {self.from_date} to {self.to_date}"
    
    @property
    def total_revenue(self):
        """Calculate total revenue from report data"""
        return self.report_data.get('total_revenue', 0)
    
    @property
    def total_cogs(self):
        """Calculate total cost of goods sold"""
        return self.report_data.get('total_cogs', 0)
    
    @property
    def gross_profit(self):
        """Calculate gross profit"""
        return self.total_revenue - self.total_cogs
    
    @property
    def total_expenses(self):
        """Calculate total operating expenses"""
        return self.report_data.get('total_expenses', 0)
    
    @property
    def operating_profit(self):
        """Calculate operating profit"""
        return self.gross_profit - self.total_expenses
    
    @property
    def net_profit(self):
        """Calculate net profit"""
        other_income = self.report_data.get('total_other_income', 0)
        other_expenses = self.report_data.get('total_other_expenses', 0)
        return self.operating_profit + other_income - other_expenses


class ReportTemplate(models.Model):
    """Model to store customizable report templates"""
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Template configuration
    show_revenue_section = models.BooleanField(default=True)
    show_cogs_section = models.BooleanField(default=True)
    show_expenses_section = models.BooleanField(default=True)
    show_other_income_expenses = models.BooleanField(default=True)
    
    # Styling options
    primary_color = models.CharField(max_length=7, default='#1e3a8a')
    secondary_color = models.CharField(max_length=7, default='#6b7280')
    font_family = models.CharField(max_length=50, default='Inter')
    
    # Grouping options
    group_by_department = models.BooleanField(default=False)
    group_by_cost_center = models.BooleanField(default=False)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_default = models.BooleanField(default=False)
    
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