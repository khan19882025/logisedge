from django.db import models
from django.contrib.auth.models import User
from customer.models import Customer
from job.models import Job
from items.models import Item
from delivery_order.models import DeliveryOrder

class DispatchNote(models.Model):
    """Dispatch Note Model"""
    
    # Basic Information
    gdn_number = models.CharField(max_length=20, unique=True, blank=True)
    dispatch_date = models.DateField()
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="Customer")
    delivery_order = models.ForeignKey(DeliveryOrder, on_delete=models.CASCADE, verbose_name="Delivery Order", null=True, blank=True)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, verbose_name="Job", null=True, blank=True)
    
    # Delivery Information
    deliver_to = models.CharField(max_length=200, blank=True)
    deliver_address = models.TextField(blank=True)
    facility = models.CharField(max_length=100, blank=True)
    
    # Transport Information
    mode = models.CharField(max_length=50, blank=True)
    vehicle_no = models.CharField(max_length=20, blank=True)
    name = models.CharField(max_length=100, blank=True)
    contact_number = models.CharField(max_length=20, blank=True)
    
    # Status and Notes
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('ready', 'Ready for Dispatch'),
        ('dispatched', 'Dispatched'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True)
    
    # System fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='dispatch_notes_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='dispatch_notes_updated')
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-dispatch_date', '-created_at']
        verbose_name = 'Dispatch Note'
        verbose_name_plural = 'Dispatch Notes'
    
    def __str__(self):
        return f"{self.gdn_number} - {self.customer.customer_name}"
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('dispatchnote:dispatch_detail', kwargs={'pk': self.pk})
    
    def save(self, *args, **kwargs):
        if not self.gdn_number:
            self.gdn_number = self.generate_gdn_number()
        super().save(*args, **kwargs)
    
    def generate_gdn_number(self):
        """Generate GDN number based on year and sequence"""
        from datetime import datetime
        
        today = datetime.now()
        year = today.year
        
        # Find the last dispatch note for this year
        last_dispatch = DispatchNote.objects.filter(
            gdn_number__startswith=f"GDN-{year}-"
        ).order_by('-gdn_number').first()
        
        if last_dispatch and last_dispatch.gdn_number:
            try:
                # Extract the sequence number and increment
                last_sequence = int(last_dispatch.gdn_number.split('-')[-1])
                new_sequence = last_sequence + 1
            except (ValueError, IndexError):
                new_sequence = 1
        else:
            new_sequence = 1
        
        # Format: GDN-YYYY-0001
        return f"GDN-{year}-{new_sequence:04d}"
    
    @property
    def total_items(self):
        """Get total number of items in this dispatch note"""
        return self.dispatch_items.count()
    
    @property
    def total_quantity(self):
        """Get total quantity of all items"""
        return sum(item.quantity for item in self.dispatch_items.all())


class DispatchItem(models.Model):
    """Dispatch Item Model"""
    
    dispatch_note = models.ForeignKey(DispatchNote, on_delete=models.CASCADE, related_name='dispatch_items')
    grn_no = models.CharField(max_length=50, blank=True)
    item_code = models.CharField(max_length=50, blank=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name="Item", null=True, blank=True)
    item_name = models.CharField(max_length=200, blank=True)
    hs_code = models.CharField(max_length=50, blank=True)
    unit = models.CharField(max_length=20, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    coo = models.CharField(max_length=100, blank=True)  # Country of Origin
    n_weight = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Net weight
    g_weight = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Gross weight
    cbm = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Cubic meters
    p_date = models.DateField(null=True, blank=True)  # Production date
    e_date = models.DateField(null=True, blank=True)  # Expiry date
    color = models.CharField(max_length=50, blank=True)
    size = models.CharField(max_length=50, blank=True)
    barcode = models.CharField(max_length=100, blank=True)
    rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    ed_cntr = models.CharField(max_length=50, blank=True)  # ED Container
    ed = models.CharField(max_length=50, blank=True)  # ED (Export Declaration)
    ctnr = models.CharField(max_length=50, blank=True)  # CTNR (Container)
    
    class Meta:
        ordering = ['item_name']
        verbose_name = 'Dispatch Item'
        verbose_name_plural = 'Dispatch Items'
    
    def __str__(self):
        return f"{self.item_name or self.item.item_name if self.item else 'Unknown'} - {self.quantity}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate amount if not set
        if not self.amount and self.quantity and self.rate:
            self.amount = self.quantity * self.rate
        super().save(*args, **kwargs)
