from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid


class TransactionTagging(models.Model):
    """Model for tagging transactions with cost centers"""
    TRANSACTION_TYPES = [
        ('journal_entry', 'Journal Entry'),
        ('purchase_invoice', 'Purchase Invoice'),
        ('sales_invoice', 'Sales Invoice'),
        ('expense_claim', 'Expense Claim'),
        ('payment', 'Payment'),
        ('receipt', 'Receipt'),
        ('adjustment', 'Adjustment'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_id = models.CharField(max_length=100, unique=True, help_text="Unique transaction identifier")
    reference_number = models.CharField(max_length=100, help_text="Reference number (invoice, PO, etc.)")
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    cost_center = models.ForeignKey('cost_center_management.CostCenter', on_delete=models.CASCADE, related_name='tagged_transactions')
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.CharField(max_length=3, default='AED')
    transaction_date = models.DateField()
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_transaction_taggings')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_transaction_taggings')
    
    class Meta:
        ordering = ['-transaction_date', '-created_at']
        verbose_name = 'Transaction Tagging'
        verbose_name_plural = 'Transaction Taggings'
        indexes = [
            models.Index(fields=['transaction_type', 'transaction_date']),
            models.Index(fields=['cost_center', 'transaction_date']),
            models.Index(fields=['status', 'transaction_date']),
        ]
    
    def __str__(self):
        return f"{self.transaction_id} - {self.cost_center.code} ({self.amount})"
    
    def save(self, *args, **kwargs):
        # Auto-generate transaction_id if not provided
        if not self.transaction_id:
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            random_suffix = str(uuid.uuid4())[:8]
            self.transaction_id = f"TXN-{timestamp}-{random_suffix}"
        
        # Validate cost center is active
        if self.cost_center and not self.cost_center.is_active:
            raise ValueError("Cannot tag transaction to inactive cost center")
        
        super().save(*args, **kwargs)


class DefaultCostCenterMapping(models.Model):
    """Model for default cost center mappings by supplier, customer, or department"""
    MAPPING_TYPES = [
        ('supplier', 'Supplier'),
        ('customer', 'Customer'),
        ('department', 'Department'),
        ('project', 'Project'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mapping_type = models.CharField(max_length=20, choices=MAPPING_TYPES)
    entity_id = models.CharField(max_length=100, help_text="ID of the supplier, customer, department, or project")
    entity_name = models.CharField(max_length=200, help_text="Name of the entity")
    cost_center = models.ForeignKey('cost_center_management.CostCenter', on_delete=models.CASCADE, related_name='default_mappings')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_default_mappings')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_default_mappings')
    
    class Meta:
        ordering = ['mapping_type', 'entity_name']
        verbose_name = 'Default Cost Center Mapping'
        verbose_name_plural = 'Default Cost Center Mappings'
        unique_together = ['mapping_type', 'entity_id']
    
    def __str__(self):
        return f"{self.mapping_type}: {self.entity_name} -> {self.cost_center.code}"


class TransactionTaggingRule(models.Model):
    """Model for transaction tagging rules"""
    RULE_TYPES = [
        ('mandatory', 'Mandatory'),
        ('default', 'Default'),
        ('conditional', 'Conditional'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rule_name = models.CharField(max_length=200)
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES)
    transaction_type = models.CharField(max_length=20, choices=TransactionTagging.TRANSACTION_TYPES)
    account_type = models.CharField(max_length=50, blank=True, help_text="Account type for conditional rules")
    cost_center = models.ForeignKey('cost_center_management.CostCenter', on_delete=models.CASCADE, related_name='tagging_rules')
    priority = models.IntegerField(default=1, help_text="Rule priority (lower number = higher priority)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_tagging_rules')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_tagging_rules')
    
    class Meta:
        ordering = ['priority', 'rule_name']
        verbose_name = 'Transaction Tagging Rule'
        verbose_name_plural = 'Transaction Tagging Rules'
    
    def __str__(self):
        return f"{self.rule_name} ({self.rule_type})"


class TransactionTaggingAuditLog(models.Model):
    """Model for auditing transaction tagging changes"""
    ACTION_TYPES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('post', 'Post'),
        ('cancel', 'Cancel'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_tagging = models.ForeignKey(TransactionTagging, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    field_name = models.CharField(max_length=100, blank=True)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='transaction_tagging_audit_logs')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Transaction Tagging Audit Log'
        verbose_name_plural = 'Transaction Tagging Audit Logs'
    
    def __str__(self):
        return f"{self.transaction_tagging.transaction_id} - {self.action} by {self.user} at {self.timestamp}"


class TransactionTaggingReport(models.Model):
    """Model for transaction tagging reports"""
    REPORT_TYPES = [
        ('cost_center_pl', 'Cost Center P&L'),
        ('expense_summary', 'Expense Summary'),
        ('budget_variance', 'Budget Variance'),
        ('transaction_list', 'Transaction List'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    cost_center = models.ForeignKey('cost_center_management.CostCenter', on_delete=models.CASCADE, null=True, blank=True, related_name='tagging_reports')
    start_date = models.DateField()
    end_date = models.DateField()
    report_data = models.JSONField(default=dict)
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='generated_tagging_reports')
    
    class Meta:
        ordering = ['-generated_at']
        verbose_name = 'Transaction Tagging Report'
        verbose_name_plural = 'Transaction Tagging Reports'
    
    def __str__(self):
        return f"{self.report_name} - {self.report_type}"
