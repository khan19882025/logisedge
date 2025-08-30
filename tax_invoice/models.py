import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class TaxInvoice(models.Model):
    """Model for Tax Invoice documents"""
    INVOICE_STATUS = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    CURRENCY_CHOICES = [
        ('AED', 'UAE Dirham'),
        ('SAR', 'Saudi Riyal'),
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_number = models.CharField(max_length=50, unique=True)
    invoice_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='AED')
    status = models.CharField(max_length=20, choices=INVOICE_STATUS, default='draft')
    
    # Company details
    company_name = models.CharField(max_length=200)
    company_address = models.TextField()
    company_trn = models.CharField(max_length=50, blank=True)  # Tax Registration Number
    company_phone = models.CharField(max_length=20, blank=True)
    company_email = models.EmailField(blank=True)
    company_website = models.URLField(blank=True)
    
    # Customer details
    customer_name = models.CharField(max_length=200)
    customer_address = models.TextField()
    customer_trn = models.CharField(max_length=50, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    customer_email = models.EmailField(blank=True)
    
    # Invoice totals
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_vat = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Additional information
    notes = models.TextField(blank=True)
    terms_conditions = models.TextField(blank=True)
    payment_instructions = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_tax_invoices')
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_tax_invoices')
    
    class Meta:
        ordering = ['-invoice_date', '-created_at']
        verbose_name = 'Tax Invoice'
        verbose_name_plural = 'Tax Invoices'
    
    def __str__(self):
        return f"Tax Invoice {self.invoice_number} - {self.customer_name}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # Generate invoice number
            last_invoice = TaxInvoice.objects.order_by('-created_at').first()
            if last_invoice:
                try:
                    last_number = int(last_invoice.invoice_number.split('-')[-1])
                    self.invoice_number = f"TI-{timezone.now().strftime('%Y%m')}-{last_number + 1:04d}"
                except (ValueError, IndexError):
                    self.invoice_number = f"TI-{timezone.now().strftime('%Y%m')}-0001"
            else:
                self.invoice_number = f"TI-{timezone.now().strftime('%Y%m')}-0001"
        
        # Calculate totals
        self.calculate_totals()
        super().save(*args, **kwargs)
    
    def calculate_totals(self):
        """Calculate invoice totals from line items"""
        subtotal = Decimal('0.00')
        total_vat = Decimal('0.00')
        
        for item in self.items.all():
            subtotal += item.total_amount
            total_vat += item.vat_amount
        
        self.subtotal = subtotal
        self.total_vat = total_vat
        self.grand_total = subtotal + total_vat


class TaxInvoiceItem(models.Model):
    """Model for Tax Invoice line items"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(TaxInvoice, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=500)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    taxable_amount = models.DecimalField(max_digits=15, decimal_places=2)
    vat_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    vat_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Optional product reference
    product_code = models.CharField(max_length=50, blank=True)
    product_category = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['id']
        verbose_name = 'Tax Invoice Item'
        verbose_name_plural = 'Tax Invoice Items'
    
    def __str__(self):
        return f"{self.description} - {self.quantity} x {self.unit_price}"
    
    def save(self, *args, **kwargs):
        # Calculate amounts
        self.taxable_amount = self.quantity * self.unit_price
        self.vat_amount = self.taxable_amount * (self.vat_percentage / Decimal('100'))
        self.total_amount = self.taxable_amount + self.vat_amount
        super().save(*args, **kwargs)


class TaxInvoiceTemplate(models.Model):
    """Model for Tax Invoice templates"""
    TEMPLATE_TYPE = [
        ('standard', 'Standard'),
        ('detailed', 'Detailed'),
        ('minimal', 'Minimal'),
        ('custom', 'Custom'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPE, default='standard')
    description = models.TextField(blank=True)
    
    # Template settings
    include_logo = models.BooleanField(default=True)
    include_qr_code = models.BooleanField(default=False)
    include_bank_details = models.BooleanField(default=True)
    include_terms = models.BooleanField(default=True)
    
    # Styling options
    primary_color = models.CharField(max_length=7, default='#007bff')
    secondary_color = models.CharField(max_length=7, default='#6c757d')
    font_family = models.CharField(max_length=50, default='Arial, sans-serif')
    
    # Content
    header_text = models.TextField(blank=True)
    footer_text = models.TextField(blank=True)
    terms_conditions = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Tax Invoice Template'
        verbose_name_plural = 'Tax Invoice Templates'
    
    def __str__(self):
        return self.name


class TaxInvoiceSettings(models.Model):
    """Model for Tax Invoice module settings"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Company defaults
    default_company_name = models.CharField(max_length=200, blank=True)
    default_company_address = models.TextField(blank=True)
    default_company_trn = models.CharField(max_length=50, blank=True)
    default_company_phone = models.CharField(max_length=20, blank=True)
    default_company_email = models.EmailField(blank=True)
    default_company_website = models.URLField(blank=True)
    
    # Invoice defaults
    default_currency = models.CharField(max_length=3, choices=TaxInvoice.CURRENCY_CHOICES, default='AED')
    default_payment_terms = models.IntegerField(default=30)  # days
    default_vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    
    # Template defaults
    default_template = models.ForeignKey(TaxInvoiceTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Export settings
    pdf_orientation = models.CharField(max_length=10, choices=[('portrait', 'Portrait'), ('landscape', 'Landscape')], default='portrait')
    pdf_page_size = models.CharField(max_length=10, choices=[('A4', 'A4'), ('A3', 'A3'), ('Letter', 'Letter')], default='A4')
    
    # Email settings
    email_subject_template = models.CharField(max_length=200, default='Tax Invoice {invoice_number} from {company_name}')
    email_body_template = models.TextField(blank=True)
    
    # Validation settings
    require_customer_trn = models.BooleanField(default=False)
    require_vat_number = models.BooleanField(default=True)
    validate_vat_rates = models.BooleanField(default=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = 'Tax Invoice Settings'
        verbose_name_plural = 'Tax Invoice Settings'
    
    def __str__(self):
        return "Tax Invoice Settings"
    
    @classmethod
    def get_settings(cls):
        """Get or create settings instance"""
        settings, created = cls.objects.get_or_create()
        return settings


class TaxInvoiceExport(models.Model):
    """Model for tracking Tax Invoice exports"""
    EXPORT_FORMAT = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('email', 'Email'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(TaxInvoice, on_delete=models.CASCADE, related_name='exports')
    export_format = models.CharField(max_length=10, choices=EXPORT_FORMAT)
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.IntegerField(default=0)
    exported_at = models.DateTimeField(auto_now_add=True)
    exported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-exported_at']
        verbose_name = 'Tax Invoice Export'
        verbose_name_plural = 'Tax Invoice Exports'
    
    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.export_format} - {self.exported_at.strftime('%Y-%m-%d %H:%M')}"
