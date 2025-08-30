from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
from customer.models import Customer
from items.models import Item

class Charge(models.Model):
    """Model for managing charges"""
    CHARGE_TYPES = [
        ('per_cbm_days', 'Per CBM/Days'),
        ('per_sqmts_days', 'Per SQMTS/Days'),
        ('per_weight_days', 'Per Weight/Days'),
        ('fixed', 'Fixed'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('draft', 'Draft'),
    ]
    
    customer = models.ForeignKey(
        Customer, 
        on_delete=models.CASCADE,
        related_name='charges',
        verbose_name="Customer"
    )
    item = models.ForeignKey(
        Item, 
        on_delete=models.CASCADE,
        related_name='charges',
        verbose_name="Item"
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
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Amount"
    )
    effective_date = models.DateField(verbose_name="Effective Date")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name="Status"
    )
    remarks = models.TextField(blank=True, verbose_name="Remarks")
    
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='charges_created',
        verbose_name="Created By"
    )
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='charges_updated',
        verbose_name="Updated By"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    class Meta:
        verbose_name = "Charge"
        verbose_name_plural = "Charges"
        ordering = ['-effective_date', 'customer__customer_name', 'item__item_name']
        unique_together = ['customer', 'item', 'charge_type', 'effective_date']
        indexes = [
            models.Index(fields=['customer', 'item']),
            models.Index(fields=['charge_type']),
            models.Index(fields=['effective_date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.customer.customer_name} - {self.item.item_name} - {self.get_charge_type_display()}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate amount based on charge type and rate
        if self.charge_type in ['fixed', 'weekly', 'monthly']:
            self.amount = self.rate
        else:
            # For per-unit charges, amount is the same as rate initially
            # This can be calculated when applied to actual quantities
            self.amount = self.rate
        
        super().save(*args, **kwargs)
    
    def calculate_amount(self, quantity=1, days=1, weight=0, volume=0):
        """Calculate amount based on charge type and parameters"""
        if self.charge_type == 'per_cbm_days':
            return self.rate * volume * days
        elif self.charge_type == 'per_sqmts_days':
            return self.rate * quantity * days
        elif self.charge_type == 'per_weight_days':
            return self.rate * weight * days
        elif self.charge_type == 'fixed':
            return self.rate
        elif self.charge_type == 'weekly':
            return self.rate * (days / 7)
        elif self.charge_type == 'monthly':
            return self.rate * (days / 30)
        else:
            return self.rate
