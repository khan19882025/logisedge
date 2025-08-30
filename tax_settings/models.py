from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid


class TaxJurisdiction(models.Model):
    """Model for tax jurisdictions (countries, states, etc.)"""
    JURISDICTION_TYPES = [
        ('country', 'Country'),
        ('state', 'State/Province'),
        ('city', 'City'),
        ('special_zone', 'Special Economic Zone'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    jurisdiction_type = models.CharField(max_length=20, choices=JURISDICTION_TYPES, default='country')
    parent_jurisdiction = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_jurisdictions')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_jurisdictions')
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Tax Jurisdiction'
        verbose_name_plural = 'Tax Jurisdictions'
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class TaxType(models.Model):
    """Model for different types of taxes"""
    TAX_TYPES = [
        ('standard_vat', 'Standard VAT'),
        ('zero_rated', 'Zero-Rated'),
        ('exempt', 'Exempt'),
        ('reverse_charge', 'Reverse Charge'),
        ('reduced_rate', 'Reduced Rate'),
        ('super_reduced_rate', 'Super Reduced Rate'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    tax_type = models.CharField(max_length=20, choices=TAX_TYPES, default='standard_vat')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_tax_types')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_tax_types')
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Tax Type'
        verbose_name_plural = 'Tax Types'
    
    def __str__(self):
        return f"{self.name} ({self.get_tax_type_display()})"


class TaxRate(models.Model):
    """Model for tax rates with effective dates"""
    ROUNDING_METHODS = [
        ('nearest_001', 'Nearest 0.01'),
        ('nearest_005', 'Nearest 0.05'),
        ('nearest_010', 'Nearest 0.10'),
        ('no_rounding', 'No Rounding'),
        ('round_up', 'Round Up'),
        ('round_down', 'Round Down'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    rate_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))]
    )
    tax_type = models.ForeignKey(TaxType, on_delete=models.CASCADE, related_name='tax_rates')
    jurisdiction = models.ForeignKey(TaxJurisdiction, on_delete=models.CASCADE, related_name='tax_rates')
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    rounding_method = models.CharField(max_length=20, choices=ROUNDING_METHODS, default='nearest_001')
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_tax_rates')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_tax_rates')
    
    class Meta:
        ordering = ['-effective_from', 'name']
        verbose_name = 'Tax Rate'
        verbose_name_plural = 'Tax Rates'
        unique_together = ['tax_type', 'jurisdiction', 'effective_from']
    
    def __str__(self):
        return f"{self.name} - {self.rate_percentage}% ({self.jurisdiction.name})"
    
    @property
    def is_current(self):
        """Check if this tax rate is currently effective"""
        from django.utils import timezone
        today = timezone.now().date()
        return (self.effective_from <= today and 
                (self.effective_to is None or self.effective_to >= today))


class ProductTaxCategory(models.Model):
    """Model for product tax categories"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    default_tax_rate = models.ForeignKey(TaxRate, on_delete=models.SET_NULL, null=True, blank=True, related_name='product_categories')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_product_tax_categories')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_product_tax_categories')
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Product Tax Category'
        verbose_name_plural = 'Product Tax Categories'
    
    def __str__(self):
        return self.name


class CustomerTaxProfile(models.Model):
    """Model for customer tax profiles"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.OneToOneField('customer.Customer', on_delete=models.CASCADE, related_name='tax_profile')
    tax_registration_number = models.CharField(max_length=50, blank=True)
    tax_exemption_number = models.CharField(max_length=50, blank=True)
    default_tax_rate = models.ForeignKey(TaxRate, on_delete=models.SET_NULL, null=True, blank=True, related_name='customer_profiles')
    is_tax_exempt = models.BooleanField(default=False)
    tax_exemption_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_customer_tax_profiles')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_customer_tax_profiles')
    
    class Meta:
        verbose_name = 'Customer Tax Profile'
        verbose_name_plural = 'Customer Tax Profiles'
    
    def __str__(self):
        return f"Tax Profile - {self.customer.name}"


class SupplierTaxProfile(models.Model):
    """Model for supplier tax profiles"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier_name = models.CharField(max_length=255)
    supplier_code = models.CharField(max_length=50, blank=True)
    tax_registration_number = models.CharField(max_length=50, blank=True)
    tax_exemption_number = models.CharField(max_length=50, blank=True)
    default_tax_rate = models.ForeignKey(TaxRate, on_delete=models.SET_NULL, null=True, blank=True, related_name='supplier_profiles')
    is_tax_exempt = models.BooleanField(default=False)
    tax_exemption_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_supplier_tax_profiles')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_supplier_tax_profiles')
    
    class Meta:
        verbose_name = 'Supplier Tax Profile'
        verbose_name_plural = 'Supplier Tax Profiles'
    
    def __str__(self):
        return f"Tax Profile - {self.supplier_name}"


class TaxTransaction(models.Model):
    """Model for tracking tax transactions"""
    TRANSACTION_TYPES = [
        ('sale', 'Sale'),
        ('purchase', 'Purchase'),
        ('refund', 'Refund'),
        ('adjustment', 'Adjustment'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    document_type = models.CharField(max_length=50)  # Invoice, Credit Note, etc.
    document_number = models.CharField(max_length=50)
    document_date = models.DateField()
    customer = models.ForeignKey('customer.Customer', on_delete=models.CASCADE, null=True, blank=True, related_name='tax_transactions')
    supplier_name = models.CharField(max_length=255, blank=True)
    tax_rate = models.ForeignKey(TaxRate, on_delete=models.CASCADE, related_name='transactions')
    taxable_amount = models.DecimalField(max_digits=15, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='AED')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_tax_transactions')
    
    class Meta:
        ordering = ['-document_date', '-created_at']
        verbose_name = 'Tax Transaction'
        verbose_name_plural = 'Tax Transactions'
    
    def __str__(self):
        return f"{self.document_type} {self.document_number} - {self.tax_amount}"


class TaxSettingsAuditLog(models.Model):
    """Model for auditing changes to tax settings"""
    ACTION_TYPES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('activate', 'Activate'),
        ('deactivate', 'Deactivate'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    field_name = models.CharField(max_length=100, blank=True)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='tax_audit_logs')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Tax Settings Audit Log'
        verbose_name_plural = 'Tax Settings Audit Logs'
    
    def __str__(self):
        return f"{self.action} on {self.model_name} by {self.user} at {self.timestamp}"


class VATReport(models.Model):
    """Model for VAT reports"""
    REPORT_PERIODS = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_name = models.CharField(max_length=100)
    report_period = models.CharField(max_length=20, choices=REPORT_PERIODS)
    start_date = models.DateField()
    end_date = models.DateField()
    total_sales = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_purchases = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_sales_tax = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_purchase_tax = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    net_vat_payable = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='AED')
    is_filed = models.BooleanField(default=False)
    filed_date = models.DateTimeField(null=True, blank=True)
    filed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='filed_vat_reports')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_vat_reports')
    
    class Meta:
        ordering = ['-start_date']
        verbose_name = 'VAT Report'
        verbose_name_plural = 'VAT Reports'
    
    def __str__(self):
        return f"{self.report_name} ({self.start_date} to {self.end_date})"
    
    @property
    def net_vat_payable_calculated(self):
        """Calculate net VAT payable"""
        return self.total_sales_tax - self.total_purchase_tax
