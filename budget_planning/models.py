from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid


class BudgetPlan(models.Model):
    """Model for budget plans"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('archived', 'Archived'),
    ]
    
    BUDGET_PERIODS = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    budget_code = models.CharField(max_length=50, unique=True, help_text="Unique budget code")
    budget_name = models.CharField(max_length=200)
    fiscal_year = models.CharField(max_length=4, help_text="Fiscal year (e.g., 2024)")
    budget_period = models.CharField(max_length=20, choices=BUDGET_PERIODS, default='yearly')
    start_date = models.DateField()
    end_date = models.DateField()
    total_budget_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default='AED')
    notes = models.TextField(blank=True, help_text="Budget justification and notes")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_budget_plans')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_budget_plans')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_budget_plans')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Budget Plan'
        verbose_name_plural = 'Budget Plans'
        unique_together = ['budget_code']
    
    def __str__(self):
        return f"{self.budget_code} - {self.budget_name}"
    
    @property
    def total_allocated_amount(self):
        """Calculate total allocated amount across all budget items"""
        return self.budget_items.aggregate(
            total=models.Sum('budget_amount')
        )['total'] or Decimal('0.00')
    
    @property
    def total_actual_amount(self):
        """Calculate total actual amount spent"""
        return self.budget_items.aggregate(
            total=models.Sum('actual_amount')
        )['total'] or Decimal('0.00')
    
    @property
    def total_variance(self):
        """Calculate total variance"""
        return self.total_allocated_amount - self.total_actual_amount
    
    @property
    def variance_percentage(self):
        """Calculate variance percentage"""
        if self.total_allocated_amount > 0:
            return (self.total_variance / self.total_allocated_amount) * 100
        return 0
    
    @property
    def is_over_budget(self):
        """Check if budget is over allocated"""
        return self.total_actual_amount > self.total_allocated_amount


class BudgetItem(models.Model):
    """Model for individual budget items"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    budget_plan = models.ForeignKey(BudgetPlan, on_delete=models.CASCADE, related_name='budget_items')
    cost_center = models.ForeignKey('cost_center_management.CostCenter', on_delete=models.CASCADE, related_name='budget_items')
    department = models.ForeignKey('cost_center_management.Department', on_delete=models.CASCADE, related_name='budget_items')
    account = models.ForeignKey('chart_of_accounts.ChartOfAccount', on_delete=models.CASCADE, related_name='budget_items')
    budget_amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    actual_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_budget_items')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_budget_items')
    
    class Meta:
        ordering = ['cost_center__code', 'account__account_code']
        verbose_name = 'Budget Item'
        verbose_name_plural = 'Budget Items'
        unique_together = ['budget_plan', 'cost_center', 'account']
    
    def __str__(self):
        return f"{self.budget_plan.budget_code} - {self.cost_center.code} - {self.account.name}"
    
    @property
    def variance(self):
        """Calculate variance (budget - actual)"""
        return self.budget_amount - self.actual_amount
    
    @property
    def variance_percentage(self):
        """Calculate variance percentage"""
        if self.budget_amount > 0:
            return (self.variance / self.budget_amount) * 100
        return 0
    
    @property
    def is_over_budget(self):
        """Check if item is over budget"""
        return self.actual_amount > self.budget_amount


class BudgetApproval(models.Model):
    """Model for budget approval workflow"""
    APPROVAL_TYPES = [
        ('submit', 'Submit for Approval'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('return', 'Return for Revision'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    budget_plan = models.ForeignKey(BudgetPlan, on_delete=models.CASCADE, related_name='approvals')
    approval_type = models.CharField(max_length=20, choices=APPROVAL_TYPES)
    comments = models.TextField(blank=True)
    approved_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='budget_approvals')
    
    class Meta:
        ordering = ['-approved_at']
        verbose_name = 'Budget Approval'
        verbose_name_plural = 'Budget Approvals'
    
    def __str__(self):
        return f"{self.budget_plan.budget_code} - {self.approval_type} by {self.approved_by}"


class BudgetTemplate(models.Model):
    """Model for budget templates"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    fiscal_year = models.CharField(max_length=4)
    budget_period = models.CharField(max_length=20, choices=BudgetPlan.BUDGET_PERIODS, default='yearly')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_budget_templates')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Budget Template'
        verbose_name_plural = 'Budget Templates'
    
    def __str__(self):
        return f"{self.template_name} - {self.fiscal_year}"


class BudgetTemplateItem(models.Model):
    """Model for budget template items"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(BudgetTemplate, on_delete=models.CASCADE, related_name='template_items')
    cost_center = models.ForeignKey('cost_center_management.CostCenter', on_delete=models.CASCADE, related_name='template_items')
    account = models.ForeignKey('chart_of_accounts.ChartOfAccount', on_delete=models.CASCADE, related_name='template_items')
    default_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['cost_center__code', 'account__account_code']
        verbose_name = 'Budget Template Item'
        verbose_name_plural = 'Budget Template Items'
        unique_together = ['template', 'cost_center', 'account']
    
    def __str__(self):
        return f"{self.template.template_name} - {self.cost_center.code} - {self.account.name}"


class BudgetImport(models.Model):
    """Model for tracking budget imports"""
    IMPORT_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    import_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=IMPORT_STATUS, default='pending')
    total_records = models.IntegerField(default=0)
    processed_records = models.IntegerField(default=0)
    error_records = models.IntegerField(default=0)
    error_log = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='budget_imports')
    
    class Meta:
        ordering = ['-import_date']
        verbose_name = 'Budget Import'
        verbose_name_plural = 'Budget Imports'
    
    def __str__(self):
        return f"{self.file_name} - {self.status}"


class BudgetAuditLog(models.Model):
    """Model for auditing budget changes"""
    ACTION_TYPES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('import', 'Import'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    budget_plan = models.ForeignKey(BudgetPlan, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    field_name = models.CharField(max_length=100, blank=True)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='budget_audit_logs')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Budget Audit Log'
        verbose_name_plural = 'Budget Audit Logs'
    
    def __str__(self):
        return f"{self.budget_plan.budget_code} - {self.action} by {self.user}"


class BudgetVarianceAlert(models.Model):
    """Model for budget variance alerts and notifications"""
    ALERT_TYPES = [
        ('variance_threshold', 'Variance Threshold'),
        ('over_budget', 'Over Budget'),
        ('approaching_limit', 'Approaching Limit'),
        ('custom', 'Custom Alert'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alert_name = models.CharField(max_length=200)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='medium')
    threshold_percentage = models.DecimalField(max_digits=5, decimal_places=2, help_text="Variance threshold percentage")
    threshold_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, help_text="Variance threshold amount")
    cost_center = models.ForeignKey('cost_center_management.CostCenter', on_delete=models.CASCADE, null=True, blank=True, related_name='variance_alerts')
    department = models.ForeignKey('cost_center_management.Department', on_delete=models.CASCADE, null=True, blank=True, related_name='variance_alerts')
    is_active = models.BooleanField(default=True)
    notify_finance_managers = models.BooleanField(default=True)
    notify_department_heads = models.BooleanField(default=True)
    notify_users = models.ManyToManyField(User, blank=True, related_name='variance_alerts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_variance_alerts')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Budget Variance Alert'
        verbose_name_plural = 'Budget Variance Alerts'
    
    def __str__(self):
        return f"{self.alert_name} - {self.alert_type}"


class BudgetVarianceNotification(models.Model):
    """Model for tracking variance notifications sent"""
    NOTIFICATION_TYPES = [
        ('email', 'Email'),
        ('in_app', 'In-App'),
        ('sms', 'SMS'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('read', 'Read'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alert = models.ForeignKey(BudgetVarianceAlert, on_delete=models.CASCADE, related_name='notifications')
    budget_item = models.ForeignKey(BudgetItem, on_delete=models.CASCADE, related_name='variance_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='variance_notifications')
    subject = models.CharField(max_length=255)
    message = models.TextField()
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Budget Variance Notification'
        verbose_name_plural = 'Budget Variance Notifications'
    
    def __str__(self):
        return f"{self.alert.alert_name} - {self.recipient.username} - {self.status}"


class BudgetVsActualReport(models.Model):
    """Model for storing generated Budget vs Actual reports"""
    REPORT_TYPES = [
        ('summary', 'Summary Report'),
        ('detailed', 'Detailed Report'),
        ('department', 'Department Report'),
        ('cost_center', 'Cost Center Report'),
        ('variance', 'Variance Report'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    fiscal_year = models.CharField(max_length=4)
    start_date = models.DateField()
    end_date = models.DateField()
    cost_center = models.ForeignKey('cost_center_management.CostCenter', on_delete=models.CASCADE, null=True, blank=True, related_name='budget_vs_actual_reports')
    department = models.ForeignKey('cost_center_management.Department', on_delete=models.CASCADE, null=True, blank=True, related_name='budget_vs_actual_reports')
    report_data = models.JSONField(default=dict, help_text="Stored report data")
    total_budget = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_actual = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_variance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    variance_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='generated_budget_vs_actual_reports')
    is_exported = models.BooleanField(default=False)
    export_format = models.CharField(max_length=10, blank=True, choices=[('pdf', 'PDF'), ('excel', 'Excel'), ('csv', 'CSV')])
    
    class Meta:
        ordering = ['-generated_at']
        verbose_name = 'Budget vs Actual Report'
        verbose_name_plural = 'Budget vs Actual Reports'
    
    def __str__(self):
        return f"{self.report_name} - {self.report_type} - {self.generated_at.strftime('%Y-%m-%d')}"
    
    @property
    def is_over_budget(self):
        """Check if report shows over budget"""
        return self.total_actual > self.total_budget
