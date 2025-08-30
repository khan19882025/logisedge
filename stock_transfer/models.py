from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils import timezone
from decimal import Decimal
from facility.models import Facility
from items.models import Item


class StockTransfer(models.Model):
    """Model for stock transfers between warehouses/locations"""
    
    TRANSFER_TYPES = [
        ('warehouse_to_warehouse', 'Warehouse to Warehouse'),
        ('department_to_department', 'Department to Department'),
        ('location_to_location', 'Location to Location'),
        ('bin_to_bin', 'Bin to Bin'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('in_transit', 'In Transit'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic Information
    transfer_number = models.CharField(
        max_length=20, 
        unique=True,
        validators=[RegexValidator(r'^[A-Z0-9-]+$', 'Transfer number must contain only uppercase letters, numbers, and hyphens.')],
        help_text="Unique transfer number (e.g., ST-001, TRF-002)"
    )
    transfer_date = models.DateField(default=timezone.now, help_text="Date of transfer")
    transfer_type = models.CharField(max_length=30, choices=TRANSFER_TYPES, default='warehouse_to_warehouse')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Source and Destination
    source_facility = models.ForeignKey(
        Facility, 
        on_delete=models.CASCADE, 
        related_name='source_transfers',
        help_text="Source warehouse/facility"
    )
    destination_facility = models.ForeignKey(
        Facility, 
        on_delete=models.CASCADE, 
        related_name='destination_transfers',
        help_text="Destination warehouse/facility"
    )
    
    # Additional Information
    reference_number = models.CharField(max_length=100, blank=True, help_text="External reference number")
    notes = models.TextField(blank=True, help_text="Additional notes or remarks")
    special_instructions = models.TextField(blank=True, help_text="Special handling instructions")
    
    # Quantities and Values
    total_items = models.PositiveIntegerField(default=0, help_text="Total number of different items")
    total_quantity = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Total quantity transferred")
    total_weight = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Total weight in kg")
    total_volume = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Total volume in cubic meters")
    total_value = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Total value of transferred items")
    
    # Approval and Processing
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='transfers_approved'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='transfers_processed'
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Audit Information
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='transfers_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='transfers_updated'
    )
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-transfer_date', '-created_at']
        verbose_name = "Stock Transfer"
        verbose_name_plural = "Stock Transfers"
        indexes = [
            models.Index(fields=['transfer_number']),
            models.Index(fields=['transfer_date']),
            models.Index(fields=['status']),
            models.Index(fields=['source_facility', 'destination_facility']),
        ]
    
    def __str__(self):
        return f"{self.transfer_number} - {self.source_facility.facility_name} to {self.destination_facility.facility_name}"
    
    def save(self, *args, **kwargs):
        # Auto-generate transfer number if not provided
        if not self.transfer_number:
            self.transfer_number = self.generate_transfer_number()
        
        # Calculate totals from items
        self.calculate_totals()
        
        super().save(*args, **kwargs)
    
    def generate_transfer_number(self):
        """Generate unique transfer number"""
        year = timezone.now().year
        prefix = f"ST-{year}-"
        last_transfer = StockTransfer.objects.filter(
            transfer_number__startswith=prefix
        ).order_by('-transfer_number').first()
        
        if last_transfer:
            try:
                last_number = int(last_transfer.transfer_number.split('-')[-1])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1
        
        return f"{prefix}{new_number:04d}"
    
    def calculate_totals(self):
        """Calculate totals from transfer items"""
        items = self.items.all()
        
        self.total_items = items.count()
        self.total_quantity = sum(item.quantity for item in items)
        self.total_weight = sum(item.total_weight for item in items if item.total_weight)
        self.total_volume = sum(item.total_volume for item in items if item.total_volume)
        self.total_value = sum(item.total_value for item in items if item.total_value)
    
    def approve(self, user):
        """Approve the transfer"""
        self.status = 'approved'
        self.approved_by = user
        self.approved_at = timezone.now()
        self.save()
    
    def process(self, user):
        """Process the transfer (mark as completed)"""
        self.status = 'completed'
        self.processed_by = user
        self.processed_at = timezone.now()
        self.save()
    
    @property
    def is_approved(self):
        return self.status in ['approved', 'in_transit', 'completed']
    
    @property
    def is_completed(self):
        return self.status == 'completed'
    
    @property
    def can_be_processed(self):
        return self.status == 'approved'


class StockTransferItem(models.Model):
    """Model for individual items in a stock transfer"""
    
    transfer = models.ForeignKey(
        StockTransfer, 
        on_delete=models.CASCADE, 
        related_name='items',
        verbose_name="Stock Transfer"
    )
    item = models.ForeignKey(
        Item, 
        on_delete=models.CASCADE,
        verbose_name="Item"
    )
    
    # Quantity Information
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Quantity to Transfer")
    available_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Available Quantity at Source")
    unit_of_measure = models.CharField(max_length=20, default='PCS', verbose_name="Unit of Measure")
    
    # Batch and Serial Information
    batch_number = models.CharField(max_length=100, blank=True, verbose_name="Batch Number")
    serial_number = models.CharField(max_length=100, blank=True, verbose_name="Serial Number")
    
    # Location Information
    source_location = models.CharField(max_length=100, blank=True, verbose_name="Source Location")
    destination_location = models.CharField(max_length=100, blank=True, verbose_name="Destination Location")
    
    # Pricing and Value
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Unit Cost")
    total_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name="Total Value")
    
    # Physical Properties
    unit_weight = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name="Unit Weight (kg)")
    total_weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Total Weight (kg)")
    unit_volume = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name="Unit Volume (CBM)")
    total_volume = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Total Volume (CBM)")
    
    # Additional Information
    notes = models.TextField(blank=True, verbose_name="Notes")
    expiry_date = models.DateField(null=True, blank=True, verbose_name="Expiry Date")
    
    # Audit Information
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Stock Transfer Item"
        verbose_name_plural = "Stock Transfer Items"
        unique_together = ['transfer', 'item', 'batch_number', 'serial_number']
    
    def __str__(self):
        return f"{self.transfer.transfer_number} - {self.item.item_name} ({self.quantity})"
    
    def save(self, *args, **kwargs):
        # Calculate totals
        if self.unit_cost and self.quantity:
            self.total_value = self.unit_cost * self.quantity
        
        if self.unit_weight and self.quantity:
            self.total_weight = self.unit_weight * self.quantity
        
        if self.unit_volume and self.quantity:
            self.total_volume = self.unit_volume * self.quantity
        
        super().save(*args, **kwargs)
    
    @property
    def is_available(self):
        """Check if sufficient quantity is available"""
        return self.quantity <= self.available_quantity
    
    @property
    def shortfall(self):
        """Calculate shortfall if any"""
        if self.quantity > self.available_quantity:
            return self.quantity - self.available_quantity
        return 0


class StockLedger(models.Model):
    """Model for tracking stock movements and balances"""
    
    MOVEMENT_TYPES = [
        ('in', 'Stock In'),
        ('out', 'Stock Out'),
        ('transfer_in', 'Transfer In'),
        ('transfer_out', 'Transfer Out'),
        ('adjustment', 'Adjustment'),
        ('damage', 'Damage/Loss'),
    ]
    
    # Basic Information
    movement_date = models.DateField(default=timezone.now, help_text="Date of stock movement")
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES, help_text="Type of stock movement")
    reference_number = models.CharField(max_length=100, blank=True, help_text="Reference number (GRN, DO, Transfer, etc.)")
    
    # Item and Location
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='stock_movements')
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='stock_movements')
    location = models.CharField(max_length=100, blank=True, help_text="Specific location within facility")
    
    # Quantity Information
    quantity_in = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Quantity received/in")
    quantity_out = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Quantity issued/out")
    running_balance = models.DecimalField(max_digits=10, decimal_places=2, help_text="Running balance after this movement")
    
    # Batch and Serial Information
    batch_number = models.CharField(max_length=100, blank=True, help_text="Batch number if applicable")
    serial_number = models.CharField(max_length=100, blank=True, help_text="Serial number if applicable")
    
    # Value Information
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Unit cost at time of movement")
    total_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Total value of movement")
    
    # Related Transfer (if applicable)
    stock_transfer = models.ForeignKey(
        StockTransfer, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='ledger_entries'
    )
    
    # Additional Information
    notes = models.TextField(blank=True, help_text="Additional notes")
    
    # Audit Information
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='stock_movements_created')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-movement_date', '-created_at']
        verbose_name = "Stock Ledger Entry"
        verbose_name_plural = "Stock Ledger Entries"
        indexes = [
            models.Index(fields=['item', 'facility', 'movement_date']),
            models.Index(fields=['movement_type']),
            models.Index(fields=['reference_number']),
        ]
    
    def __str__(self):
        movement_str = f"{self.get_movement_type_display()}: {self.quantity_in or self.quantity_out}"
        return f"{self.item.item_name} - {movement_str} - {self.facility.facility_name}"
    
    def save(self, *args, **kwargs):
        # Calculate running balance
        self.calculate_running_balance()
        
        # Calculate total value
        if self.unit_cost:
            if self.quantity_in > 0:
                self.total_value = self.unit_cost * self.quantity_in
            elif self.quantity_out > 0:
                self.total_value = self.unit_cost * self.quantity_out
        
        super().save(*args, **kwargs)
    
    def calculate_running_balance(self):
        """Calculate running balance based on previous movements"""
        # Get previous balance for this item and facility
        previous_entry = StockLedger.objects.filter(
            item=self.item,
            facility=self.facility,
            movement_date__lte=self.movement_date
        ).exclude(pk=self.pk).order_by('-movement_date', '-created_at').first()
        
        if previous_entry:
            previous_balance = previous_entry.running_balance
        else:
            previous_balance = 0
        
        # Calculate new balance
        net_movement = self.quantity_in - self.quantity_out
        self.running_balance = previous_balance + net_movement
    
    @property
    def net_quantity(self):
        """Calculate net quantity movement"""
        return self.quantity_in - self.quantity_out
    
    @property
    def is_in_movement(self):
        """Check if this is an incoming movement"""
        return self.movement_type in ['in', 'transfer_in', 'adjustment'] and self.quantity_in > 0
    
    @property
    def is_out_movement(self):
        """Check if this is an outgoing movement"""
        return self.movement_type in ['out', 'transfer_out', 'damage'] and self.quantity_out > 0
