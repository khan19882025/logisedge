from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
from customer.models import Customer
from facility.models import FacilityLocation
from items.models import Item

class StorageCharges(models.Model):
    """Master table for storage charges per customer"""
    CHARGE_TYPES = [
        ('per_pallet_day', 'Per Pallet/Day'),
        ('per_cbm_day', 'Per CBM/Day'),
        ('per_item_day', 'Per Item/Day'),
        ('per_weight_day', 'Per Weight/Day'),
        ('fixed_monthly', 'Fixed Monthly'),
    ]
    
    customer = models.ForeignKey(
        Customer, 
        on_delete=models.CASCADE,
        related_name='storage_charges',
        verbose_name="Customer"
    )
    charge_type = models.CharField(
        max_length=20,
        choices=CHARGE_TYPES,
        verbose_name="Charge Type"
    )
    rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Rate"
    )
    effective_date = models.DateField(verbose_name="Effective Date")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    description = models.TextField(blank=True, verbose_name="Description")
    
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='storage_charges_created',
        verbose_name="Created By"
    )
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='storage_charges_updated',
        verbose_name="Updated By"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    class Meta:
        verbose_name = "Storage Charge"
        verbose_name_plural = "Storage Charges"
        ordering = ['-effective_date', 'customer__customer_name']
        unique_together = ['customer', 'charge_type', 'effective_date']
        indexes = [
            models.Index(fields=['customer', 'charge_type']),
            models.Index(fields=['effective_date']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.customer.customer_name} - {self.get_charge_type_display()} - {self.rate}"

class StorageLog(models.Model):
    """Log of storage activities for invoice calculation"""
    customer = models.ForeignKey(
        Customer, 
        on_delete=models.CASCADE,
        related_name='storage_logs',
        verbose_name="Customer"
    )
    location = models.ForeignKey(
        FacilityLocation, 
        on_delete=models.CASCADE,
        related_name='storage_logs',
        verbose_name="Location"
    )
    item = models.ForeignKey(
        Item, 
        on_delete=models.CASCADE,
        related_name='storage_logs',
        verbose_name="Item"
    )
    pallet_id = models.CharField(max_length=50, blank=True, verbose_name="Pallet ID")
    quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Quantity"
    )
    weight = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Weight (kg)"
    )
    volume = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Volume (m³)"
    )
    activity_type = models.CharField(
        max_length=20,
        choices=[
            ('in', 'Storage In'),
            ('out', 'Storage Out'),
            ('transfer', 'Transfer'),
        ],
        verbose_name="Activity Type"
    )
    activity_date = models.DateTimeField(verbose_name="Activity Date")
    reference_number = models.CharField(
        max_length=50, 
        blank=True, 
        verbose_name="Reference Number"
    )
    notes = models.TextField(blank=True, verbose_name="Notes")
    
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='storage_logs_created',
        verbose_name="Created By"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    
    class Meta:
        verbose_name = "Storage Log"
        verbose_name_plural = "Storage Logs"
        ordering = ['-activity_date']
        indexes = [
            models.Index(fields=['customer', 'activity_date']),
            models.Index(fields=['activity_type']),
            models.Index(fields=['pallet_id']),
        ]
    
    def __str__(self):
        return f"{self.customer.customer_name} - {self.activity_type} - {self.activity_date}"

class StorageInvoice(models.Model):
    """Main storage invoice model"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('finalized', 'Finalized'),
        ('cancelled', 'Cancelled'),
        ('paid', 'Paid'),
    ]
    
    invoice_number = models.CharField(
        max_length=20, 
        unique=True, 
        verbose_name="Invoice Number"
    )
    customer = models.ForeignKey(
        Customer, 
        on_delete=models.CASCADE,
        related_name='storage_invoices',
        verbose_name="Customer"
    )
    invoice_date = models.DateField(verbose_name="Invoice Date")
    storage_period_from = models.DateField(verbose_name="Storage Period From")
    storage_period_to = models.DateField(verbose_name="Storage Period To")
    
    subtotal = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Subtotal"
    )
    tax_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Tax Amount"
    )
    total_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Total Amount"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="Status"
    )
    
    notes = models.TextField(blank=True, verbose_name="Notes")
    terms_conditions = models.TextField(blank=True, verbose_name="Terms & Conditions")
    
    generated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='storage_invoices_generated',
        verbose_name="Generated By"
    )
    finalized_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='storage_invoices_finalized',
        verbose_name="Finalized By"
    )
    cancelled_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='storage_invoices_cancelled',
        verbose_name="Cancelled By"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    finalized_at = models.DateTimeField(null=True, blank=True, verbose_name="Finalized At")
    cancelled_at = models.DateTimeField(null=True, blank=True, verbose_name="Cancelled At")
    
    class Meta:
        verbose_name = "Storage Invoice"
        verbose_name_plural = "Storage Invoices"
        ordering = ['-invoice_date', '-created_at']
        indexes = [
            models.Index(fields=['customer', 'invoice_date']),
            models.Index(fields=['status']),
            models.Index(fields=['storage_period_from', 'storage_period_to']),
        ]
    
    def __str__(self):
        return f"{self.invoice_number} - {self.customer.customer_name}"
    
    def save(self, *args, **kwargs):
        # Auto-generate invoice number if not provided
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        super().save(*args, **kwargs)
    
    def generate_invoice_number(self):
        """Generate unique invoice number"""
        prefix = "STI"
        year = timezone.now().year
        month = timezone.now().month
        
        # Get the last invoice number for this year/month
        last_invoice = StorageInvoice.objects.filter(
            invoice_number__startswith=f"{prefix}{year}{month:02d}"
        ).order_by('-invoice_number').first()
        
        if last_invoice:
            # Extract the sequence number and increment
            try:
                last_sequence = int(last_invoice.invoice_number[-4:])
                new_sequence = last_sequence + 1
            except ValueError:
                new_sequence = 1
        else:
            new_sequence = 1
        
        return f"{prefix}{year}{month:02d}{new_sequence:04d}"
    
    def calculate_totals(self):
        """Calculate invoice totals from line items"""
        items = self.items.all()
        self.subtotal = sum(item.line_total for item in items)
        # You can add tax calculation logic here
        self.tax_amount = Decimal('0.00')  # Placeholder
        self.total_amount = self.subtotal + self.tax_amount
        self.save()
    
    def finalize(self, user):
        """Finalize the invoice"""
        if self.status == 'draft':
            self.status = 'finalized'
            self.finalized_by = user
            self.finalized_at = timezone.now()
            self.save()
    
    def cancel(self, user):
        """Cancel the invoice"""
        if self.status in ['draft', 'finalized']:
            self.status = 'cancelled'
            self.cancelled_by = user
            self.cancelled_at = timezone.now()
            self.save()
    
    @property
    def is_editable(self):
        """Check if invoice can be edited"""
        return self.status == 'draft'
    
    @property
    def can_be_finalized(self):
        """Check if invoice can be finalized"""
        return self.status == 'draft'
    
    @property
    def can_be_cancelled(self):
        """Check if invoice can be cancelled"""
        return self.status in ['draft', 'finalized']

class StorageInvoiceItem(models.Model):
    """Line items for storage invoice"""
    invoice = models.ForeignKey(
        StorageInvoice, 
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Invoice"
    )
    item = models.ForeignKey(
        Item, 
        on_delete=models.CASCADE,
        related_name='storage_invoice_items',
        verbose_name="Item"
    )
    pallet_id = models.CharField(max_length=50, blank=True, verbose_name="Pallet ID")
    location = models.ForeignKey(
        FacilityLocation, 
        on_delete=models.CASCADE,
        related_name='storage_invoice_items',
        verbose_name="Location"
    )
    
    quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Quantity"
    )
    weight = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Weight (kg)"
    )
    volume = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Volume (m³)"
    )
    
    storage_days = models.IntegerField(verbose_name="Storage Days")
    charge_type = models.CharField(
        max_length=20,
        choices=StorageCharges.CHARGE_TYPES,
        verbose_name="Charge Type"
    )
    rate = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Rate"
    )
    line_total = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        verbose_name="Line Total"
    )
    
    description = models.TextField(blank=True, verbose_name="Description")
    
    class Meta:
        verbose_name = "Storage Invoice Item"
        verbose_name_plural = "Storage Invoice Items"
        ordering = ['invoice', 'item']
        indexes = [
            models.Index(fields=['invoice', 'item']),
            models.Index(fields=['pallet_id']),
        ]
    
    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.item.item_name}"
    
    def calculate_line_total(self):
        """Calculate line total based on charge type and storage days"""
        if self.charge_type == 'per_pallet_day':
            self.line_total = self.rate * self.storage_days
        elif self.charge_type == 'per_cbm_day':
            self.line_total = self.rate * self.volume * self.storage_days
        elif self.charge_type == 'per_item_day':
            self.line_total = self.rate * self.quantity * self.storage_days
        elif self.charge_type == 'per_weight_day':
            self.line_total = self.rate * self.weight * self.storage_days
        elif self.charge_type == 'fixed_monthly':
            # Calculate months between dates
            months = (self.invoice.storage_period_to - self.invoice.storage_period_from).days / 30
            self.line_total = self.rate * Decimal(str(months))
        else:
            self.line_total = Decimal('0.00')
        
        self.save()
        return self.line_total
