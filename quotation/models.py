from django.db import models
from django.contrib.auth.models import User
from customer.models import Customer
from service.models import Service
from facility.models import Facility
from salesman.models import Salesman
from decimal import Decimal


class Quotation(models.Model):
    QUOTATION_STATUS = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]
    
    quotation_number = models.CharField(max_length=20, unique=True, help_text="Unique quotation number")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='quotations')
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='quotations')
    salesman = models.ForeignKey(Salesman, on_delete=models.CASCADE, related_name='quotations')
    
    # Quotation details
    subject = models.CharField(max_length=200, help_text="Quotation subject/title")
    description = models.TextField(blank=True, help_text="Detailed description of services")
    
    # Dates
    quotation_date = models.DateField(auto_now_add=True)
    valid_until = models.DateField(help_text="Quotation validity period")
    
    # Financial
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="VAT amount (5%)")
    additional_tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="Additional tax amount")
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=3, default='AED', help_text="Currency code")
    
    # Legacy field for backward compatibility
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=QUOTATION_STATUS, default='draft')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_quotations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional fields
    terms_conditions = models.TextField(blank=True, help_text="Terms and conditions")
    notes = models.TextField(blank=True, help_text="Additional notes")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Quotation'
        verbose_name_plural = 'Quotations'
    
    def __str__(self):
        return f"{self.quotation_number} - {self.customer.name}"
    
    def save(self, *args, **kwargs):
        if not self.quotation_number:
            # Auto-generate quotation number
            last_quote = Quotation.objects.order_by('-id').first()
            if last_quote:
                last_number = int(last_quote.quotation_number.split('-')[-1])
                self.quotation_number = f"QT-{str(last_number + 1).zfill(6)}"
            else:
                self.quotation_number = "QT-000001"
        
        super().save(*args, **kwargs)
    
    def calculate_totals(self):
        """Calculate quotation totals from line items"""
        def to_decimal(val):
            if val is None:
                return Decimal('0.00')
            if isinstance(val, Decimal):
                return val
            try:
                return Decimal(str(val))
            except (ValueError, TypeError):
                return Decimal('0.00')
        
        # Check if the quotation has been saved (has a primary key)
        if self.pk is None:
            # Quotation hasn't been saved yet, set default values
            self.subtotal = Decimal('0.00')
            self.vat_amount = Decimal('0.00')
            self.additional_tax_amount = Decimal('0.00')
            self.total_amount = Decimal('0.00')
            return
        
        # Quotation has been saved, calculate from line items
        line_items = self.quotation_items.all()
        self.subtotal = sum(to_decimal(item.total_price) for item in line_items)
        
        # Calculate VAT from items that have VAT enabled
        vat_total = Decimal('0.00')
        for item in line_items:
            if item.vat_applied:
                vat_total += to_decimal(item.total_price) * Decimal('0.05')
        self.vat_amount = vat_total
        
        # Ensure all fields are Decimal
        self.subtotal = to_decimal(self.subtotal)
        self.vat_amount = to_decimal(self.vat_amount)
        self.additional_tax_amount = to_decimal(self.additional_tax_amount)
        self.discount_amount = to_decimal(self.discount_amount)
        
        # Calculate total (subtotal + VAT + additional tax - discount)
        self.total_amount = (
            self.subtotal
            + self.vat_amount
            + self.additional_tax_amount
            - self.discount_amount
        )
        
        # Update legacy tax_amount field for backward compatibility
        self.tax_amount = self.vat_amount + self.additional_tax_amount


class QuotationItem(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='quotation_items')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='quotation_items')
    
    # Item details
    description = models.CharField(max_length=500, help_text="Service description")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # VAT tracking
    vat_applied = models.BooleanField(default=False, help_text="Whether VAT was applied to this item")
    
    # Additional fields
    notes = models.TextField(blank=True, help_text="Additional notes for this service")
    
    class Meta:
        verbose_name = 'Quotation Service'
        verbose_name_plural = 'Quotation Services'
    
    def __str__(self):
        return f"{self.quotation.quotation_number} - {self.service.service_name}"
    
    def save(self, *args, **kwargs):
        # Calculate total price
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)
