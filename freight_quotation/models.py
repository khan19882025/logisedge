from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator
import uuid


class Customer(models.Model):
    """Customer model for freight quotations"""
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    country = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class CargoType(models.Model):
    """Cargo type model"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Incoterm(models.Model):
    """Incoterms model"""
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        ordering = ['code']


class ChargeType(models.Model):
    """Charge type model for breakdown"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class FreightQuotation(models.Model):
    """Main freight quotation model"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    MODE_CHOICES = [
        ('air', 'Air'),
        ('sea', 'Sea'),
        ('road', 'Road'),
    ]

    # Basic Information
    quotation_number = models.CharField(max_length=50, unique=True, blank=True)
    quotation_date = models.DateField(default=timezone.now)
    validity_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Customer Information
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='quotations')
    
    # Transport Details
    mode_of_transport = models.CharField(max_length=10, choices=MODE_CHOICES)
    origin = models.CharField(max_length=200)
    destination = models.CharField(max_length=200)
    transit_time_estimate = models.CharField(max_length=100, blank=True)
    
    # Cargo Details
    cargo_type = models.ForeignKey(CargoType, on_delete=models.CASCADE)
    cargo_details = models.TextField()
    weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    volume = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    packages = models.PositiveIntegerField(null=True, blank=True)
    
    # Terms and Conditions
    incoterm = models.ForeignKey(Incoterm, on_delete=models.SET_NULL, null=True, blank=True)
    remarks = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)
    
    # Financial Information
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='AED')
    vat_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_freight_quotations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Quote {self.quotation_number} - {self.customer.name}"

    def save(self, *args, **kwargs):
        if not self.quotation_number:
            # Generate unique quotation number
            year = timezone.now().year
            last_quote = FreightQuotation.objects.filter(
                quotation_number__startswith=f'FQ{year}'
            ).order_by('-quotation_number').first()
            
            if last_quote:
                try:
                    last_number = int(last_quote.quotation_number[-4:])
                    new_number = last_number + 1
                except ValueError:
                    new_number = 1
            else:
                new_number = 1
            
            self.quotation_number = f'FQ{year}{new_number:04d}'
        
        # Calculate totals
        self.calculate_totals()
        
        super().save(*args, **kwargs)

    def calculate_totals(self):
        """Calculate total amounts from charges"""
        if self.pk:  # Only calculate if the object has been saved
            total = sum(charge.total_amount for charge in self.charges.all())
            self.total_amount = total
            
            # Calculate VAT
            self.vat_amount = (self.total_amount * self.vat_percentage) / 100
            self.grand_total = self.total_amount + self.vat_amount
        else:
            # For new objects, set defaults
            self.total_amount = 0
            self.vat_amount = 0
            self.grand_total = 0

    class Meta:
        ordering = ['-created_at']


class QuotationCharge(models.Model):
    """Individual charges for freight quotation"""
    UNIT_CHOICES = [
        ('cbm', 'Per CBM'),
        ('ton', 'Per Ton'),
        ('container', 'Per Container'),
        ('package', 'Per Package'),
        ('flat', 'Flat Rate'),
    ]

    quotation = models.ForeignKey(FreightQuotation, on_delete=models.CASCADE, related_name='charges')
    charge_type = models.ForeignKey(ChargeType, on_delete=models.CASCADE)
    description = models.TextField()
    currency = models.CharField(max_length=3, default='AED')
    rate = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1, validators=[MinValueValidator(0)])
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.charge_type.name} - {self.quotation.quotation_number}"

    def save(self, *args, **kwargs):
        # Auto-calculate total amount
        self.total_amount = self.rate * self.quantity
        super().save(*args, **kwargs)
        
        # Update quotation totals if quotation exists
        if hasattr(self, 'quotation') and self.quotation.pk:
            self.quotation.calculate_totals()
            self.quotation.save()

    class Meta:
        ordering = ['charge_type__name']


class QuotationAttachment(models.Model):
    """Attachments for freight quotations"""
    quotation = models.ForeignKey(FreightQuotation, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='freight_quotations/attachments/')
    filename = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.filename} - {self.quotation.quotation_number}"

    class Meta:
        ordering = ['-uploaded_at']


class QuotationHistory(models.Model):
    """Audit trail for quotation changes"""
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('sent', 'Sent'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    quotation = models.ForeignKey(FreightQuotation, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.action} - {self.quotation.quotation_number}"

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Quotation histories'
