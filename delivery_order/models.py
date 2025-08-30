from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator
from customer.models import Customer
from facility.models import Facility, FacilityLocation
from items.models import Item
from salesman.models import Salesman
from grn.models import GRN

class DeliveryOrder(models.Model):
    """Model for managing Delivery Orders"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    # Basic Information
    do_number = models.CharField(max_length=20, unique=True, blank=True, verbose_name="DO Number")
    document_type = models.CharField(max_length=50, blank=True, verbose_name="Document Type")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    
    # Related Records
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="Customer")
    customer_ref = models.CharField(max_length=100, blank=True, verbose_name="Customer Reference")
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Facility")
    grn = models.ForeignKey(GRN, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Related GRN")
    
    # Billing and Delivery Addresses
    bill_to = models.CharField(max_length=200, blank=True, verbose_name="Bill To")
    bill_to_address = models.TextField(blank=True, verbose_name="Bill to Address")
    deliver_to_address = models.TextField(blank=True, verbose_name="Deliver to Address")
    
    # Port Information
    port_of_loading = models.CharField(max_length=100, blank=True, verbose_name="Port of Loading")
    discharge_port = models.CharField(max_length=100, blank=True, verbose_name="Discharge Port")
    
    # Delivery Information
    delivery_address = models.TextField(blank=True, verbose_name="Delivery Address")
    delivery_contact = models.CharField(max_length=100, blank=True, verbose_name="Delivery Contact")
    delivery_phone = models.CharField(max_length=50, blank=True, verbose_name="Delivery Phone")
    delivery_email = models.EmailField(blank=True, verbose_name="Delivery Email")
    
    # Dates
    date = models.DateField(default=timezone.now, verbose_name="Date")
    do_date = models.DateField(default=timezone.now, verbose_name="DO Date")
    requested_date = models.DateField(blank=True, null=True, verbose_name="Requested Delivery Date")
    actual_delivery_date = models.DateField(blank=True, null=True, verbose_name="Actual Delivery Date")
    
    # Payment and Shipping Details
    payment_mode = models.CharField(max_length=50, blank=True, verbose_name="Payment Mode")
    container = models.CharField(max_length=50, blank=True, verbose_name="Container")
    bl_number = models.CharField(max_length=50, blank=True, verbose_name="BL Number")
    boe = models.CharField(max_length=50, blank=True, verbose_name="BOE")
    exit_point = models.CharField(max_length=100, blank=True, verbose_name="Exit Point")
    destination = models.CharField(max_length=100, blank=True, verbose_name="Destination")
    ship_mode = models.CharField(max_length=50, blank=True, verbose_name="Ship Mode")
    ship_date = models.DateField(blank=True, null=True, verbose_name="Ship Date")
    vessel = models.CharField(max_length=100, blank=True, verbose_name="Vessel")
    voyage = models.CharField(max_length=50, blank=True, verbose_name="Voyage")
    delivery_terms = models.CharField(max_length=200, blank=True, verbose_name="Delivery Terms")
    
    # Status and Priority
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="Status")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', verbose_name="Priority")
    
    # Shipping Information
    shipping_method = models.CharField(max_length=50, blank=True, verbose_name="Shipping Method")
    tracking_number = models.CharField(max_length=100, blank=True, verbose_name="Tracking Number")
    carrier = models.CharField(max_length=100, blank=True, verbose_name="Carrier")
    
    # Totals
    total_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Total Quantity")
    total_weight = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Total Weight (KGS)")
    total_volume = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Total Volume (CBM)")
    
    # Notes and Additional Info
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")
    special_instructions = models.TextField(blank=True, null=True, verbose_name="Special Instructions")
    
    # Audit Fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_delivery_orders', verbose_name="Created By")
    assigned_to = models.ForeignKey(Salesman, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_delivery_orders', verbose_name="Assigned To")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    class Meta:
        verbose_name = "Delivery Order"
        verbose_name_plural = "Delivery Orders"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.do_number}"
    
    def save(self, *args, **kwargs):
        # Auto-generate DO number if not provided
        if not self.do_number:
            current_year = timezone.now().year
            # Get the last DO number for the current year
            last_do = DeliveryOrder.objects.filter(
                do_number__startswith=f"DO-{current_year}-"
            ).order_by('-do_number').first()
            
            if last_do:
                try:
                    # Extract the number part from the last DO number
                    last_number = int(last_do.do_number.split('-')[-1])
                    new_number = last_number + 1
                except (ValueError, IndexError):
                    new_number = 1
            else:
                new_number = 1
            
            self.do_number = f"DO-{current_year}-{new_number:04d}"
        
        super().save(*args, **kwargs)
    
    @property
    def is_overdue(self):
        """Check if the delivery order is overdue"""
        if self.status in ['delivered', 'cancelled']:
            return False
        if self.requested_date is None:
            return False
        return self.requested_date < timezone.now().date()
    
    @property
    def is_delivered(self):
        """Check if the delivery order is delivered"""
        return self.status == 'delivered'
    
    def deliver(self):
        """Mark the delivery order as delivered"""
        self.status = 'delivered'
        self.actual_delivery_date = timezone.now().date()
        self.save()


class DeliveryOrderItem(models.Model):
    """Model for delivery order items"""
    delivery_order = models.ForeignKey(DeliveryOrder, on_delete=models.CASCADE, related_name='items', verbose_name="Delivery Order")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name="Item")
    
    # Quantity Information
    requested_qty = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Requested Quantity")
    shipped_qty = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Shipped Quantity")
    delivered_qty = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Delivered Quantity")
    
    # Location Information
    source_location = models.ForeignKey(FacilityLocation, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Source Location")
    
    # Additional Information
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Unit Price")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Total Price")
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")
    
    # Audit Fields
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    # New fields
    production_date = models.DateField(blank=True, null=True, verbose_name="Production Date")
    expiry_date = models.DateField(blank=True, null=True, verbose_name="Expiry Date")
    
    class Meta:
        verbose_name = "Delivery Order Item"
        verbose_name_plural = "Delivery Order Items"
        unique_together = ['delivery_order', 'item']
    
    def __str__(self):
        return f"{self.delivery_order.do_number} - {self.item.item_name}"
    
    def save(self, *args, **kwargs):
        # Calculate total price if unit price is provided
        if self.unit_price and self.requested_qty:
            self.total_price = self.unit_price * self.requested_qty
        super().save(*args, **kwargs)
    
    @property
    def remaining_qty(self):
        """Calculate remaining quantity to be shipped"""
        return self.requested_qty - self.shipped_qty
    
    @property
    def is_fully_shipped(self):
        """Check if item is fully shipped"""
        return self.shipped_qty >= self.requested_qty
    
    @property
    def is_fully_delivered(self):
        """Check if item is fully delivered"""
        return self.delivered_qty >= self.requested_qty
