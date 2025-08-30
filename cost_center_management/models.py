from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid


class Department(models.Model):
    """Model for departments/business units"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_departments')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_departments')
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class CostCenter(models.Model):
    """Model for cost centers"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('temporary', 'Temporary'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=20, unique=True, help_text="Unique cost center code")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='cost_centers')
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_cost_centers')
    parent_cost_center = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='child_cost_centers')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    budget_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default='AED')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_cost_centers')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_cost_centers')
    
    class Meta:
        ordering = ['code']
        verbose_name = 'Cost Center'
        verbose_name_plural = 'Cost Centers'
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    @property
    def is_temporary(self):
        """Check if cost center is temporary based on dates"""
        if self.start_date and self.end_date:
            today = timezone.now().date()
            return self.start_date <= today <= self.end_date
        return False
    
    @property
    def total_expenses(self):
        """Calculate total expenses for this cost center"""
        return self.cost_center_transactions.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
    
    @property
    def budget_variance(self):
        """Calculate budget variance"""
        return self.budget_amount - self.total_expenses
    
    @property
    def budget_utilization_percentage(self):
        """Calculate budget utilization percentage"""
        if self.budget_amount > 0:
            return (self.total_expenses / self.budget_amount) * 100
        return 0


class CostCenterBudget(models.Model):
    """Model for cost center budgets"""
    BUDGET_PERIODS = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.CASCADE, related_name='budgets')
    budget_period = models.CharField(max_length=20, choices=BUDGET_PERIODS, default='yearly')
    start_date = models.DateField()
    end_date = models.DateField()
    budget_amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='AED')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_cost_center_budgets')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_cost_center_budgets')
    
    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Cost Center Budget'
        verbose_name_plural = 'Cost Center Budgets'
        unique_together = ['cost_center', 'start_date', 'end_date']
    
    def __str__(self):
        return f"{self.cost_center.code} - {self.budget_period} ({self.start_date} to {self.end_date})"
    
    @property
    def total_expenses(self):
        """Calculate total expenses for this budget period"""
        return self.cost_center.cost_center_transactions.filter(
            transaction_date__gte=self.start_date,
            transaction_date__lte=self.end_date
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
    
    @property
    def budget_variance(self):
        """Calculate budget variance"""
        return self.budget_amount - self.total_expenses
    
    @property
    def budget_utilization_percentage(self):
        """Calculate budget utilization percentage"""
        if self.budget_amount > 0:
            return (self.total_expenses / self.budget_amount) * 100
        return 0


class CostCenterTransaction(models.Model):
    """Model for cost center transactions"""
    TRANSACTION_TYPES = [
        ('expense', 'Expense'),
        ('purchase', 'Purchase'),
        ('journal', 'Journal Entry'),
        ('adjustment', 'Adjustment'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.CASCADE, related_name='cost_center_transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    transaction_date = models.DateField()
    reference_number = models.CharField(max_length=50)
    reference_type = models.CharField(max_length=50)  # Invoice, Purchase Order, Journal Entry, etc.
    description = models.TextField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='AED')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_cost_center_transactions')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_cost_center_transactions')
    
    class Meta:
        ordering = ['-transaction_date', '-created_at']
        verbose_name = 'Cost Center Transaction'
        verbose_name_plural = 'Cost Center Transactions'
    
    def __str__(self):
        return f"{self.cost_center.code} - {self.reference_number} ({self.amount})"


class CostCenterReport(models.Model):
    """Model for cost center reports"""
    REPORT_TYPES = [
        ('expense_summary', 'Expense Summary'),
        ('budget_variance', 'Budget Variance'),
        ('profit_loss', 'Profit & Loss'),
        ('utilization', 'Budget Utilization'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.CASCADE, null=True, blank=True, related_name='reports')
    start_date = models.DateField()
    end_date = models.DateField()
    report_data = models.JSONField(default=dict)
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='generated_cost_center_reports')
    
    class Meta:
        ordering = ['-generated_at']
        verbose_name = 'Cost Center Report'
        verbose_name_plural = 'Cost Center Reports'
    
    def __str__(self):
        return f"{self.report_name} - {self.report_type}"


class CostCenterAuditLog(models.Model):
    """Model for auditing changes to cost centers"""
    ACTION_TYPES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('activate', 'Activate'),
        ('deactivate', 'Deactivate'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    field_name = models.CharField(max_length=100, blank=True)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='cost_center_audit_logs')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Cost Center Audit Log'
        verbose_name_plural = 'Cost Center Audit Logs'
    
    def __str__(self):
        return f"{self.cost_center.code} - {self.action} by {self.user} at {self.timestamp}"
