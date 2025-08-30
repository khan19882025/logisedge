from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator
from customer.models import Customer
from facility.models import Facility
from items.models import Item
from salesman.models import Salesman


class GRN(models.Model):
    """Model for managing Goods Received Notes"""
    
    GRN_STATUS = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('received', 'Received'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    DOCUMENT_TYPE_CHOICES = [
        ('purchase_order', 'Purchase Order'),
        ('delivery_note', 'Delivery Note'),
        ('invoice', 'Invoice'),
        ('other', 'Other'),
    ]
    
    # Basic Information
    grn_number = models.CharField(max_length=20, unique=True, blank=True, verbose_name="GRN Number")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    
    # Related Records
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="Customer")
    customer_ref = models.CharField(max_length=100, blank=True, verbose_name="Customer Reference")
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Facility")
    job_ref = models.ForeignKey('job.Job', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Job Reference")
    
    # Mode
    MODE_CHOICES = [
        ("Sea", "Sea"),
        ("Land", "Land"),
        ("Air", "Air"),
    ]
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default="Sea", verbose_name="Mode")
    
    # Document Information
    document_type = models.CharField(
        max_length=20, 
        choices=DOCUMENT_TYPE_CHOICES,
        blank=True, 
        verbose_name="Document Type"
    )
    reference_number = models.CharField(max_length=100, blank=True, verbose_name="Reference Number")
    supplier_name = models.CharField(max_length=200, blank=True, verbose_name="Supplier Name")
    supplier_address = models.TextField(blank=True, verbose_name="Supplier Address")
    supplier_phone = models.CharField(max_length=50, blank=True, verbose_name="Supplier Phone")
    supplier_email = models.EmailField(blank=True, verbose_name="Supplier Email")
    
    # Dates
    grn_date = models.DateField(default=timezone.now, verbose_name="GRN Date")
    expected_date = models.DateField(blank=True, null=True, verbose_name="Expected Date")
    received_date = models.DateField(blank=True, null=True, verbose_name="Received Date")
    
    # Shipping Information
    vessel = models.CharField(max_length=100, blank=True, verbose_name="Vessel")
    voyage = models.CharField(max_length=50, blank=True, verbose_name="Voyage")
    container_number = models.CharField(max_length=50, blank=True, verbose_name="Container Number")
    seal_number = models.CharField(max_length=50, blank=True, verbose_name="Seal Number")
    bl_number = models.CharField(max_length=100, blank=True, verbose_name="BL Number")
    
    # Driver and Vehicle Information
    driver_name = models.CharField(max_length=100, blank=True, verbose_name="Driver Name")
    contact_no = models.CharField(max_length=50, blank=True, verbose_name="Contact Number")
    vehicle_no = models.CharField(max_length=50, blank=True, verbose_name="Vehicle Number")
    
    # Status and Priority
    status = models.CharField(max_length=20, choices=GRN_STATUS, default='draft', verbose_name="Status")
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], default='medium', verbose_name="Priority")
    
    # Totals
    total_packages = models.IntegerField(validators=[MinValueValidator(1)], blank=True, null=True, verbose_name="Total Packages")
    total_weight = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Total Weight (KGS)")
    total_volume = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Total Volume (CBM)")
    
    # Total Quantity
    total_qty = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Total Quantity")
    
    # Notes and Additional Info
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")
    special_instructions = models.TextField(blank=True, null=True, verbose_name="Special Instructions")
    
    # Audit Fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_grns', verbose_name="Created By")
    assigned_to = models.ForeignKey(Salesman, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_grns', verbose_name="Assigned To")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    class Meta:
        verbose_name = "Goods Received Note"
        verbose_name_plural = "Goods Received Notes"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.grn_number}"
    
    def save(self, *args, **kwargs):
        # Auto-generate GRN number if not provided
        if not self.grn_number:
            current_year = timezone.now().year
            # Get the last GRN number for the current year
            last_grn = GRN.objects.filter(
                grn_number__startswith=f"GRN-{current_year}-"
            ).order_by('-grn_number').first()
            
            if last_grn:
                try:
                    # Extract the number part from the last GRN number
                    last_number = int(last_grn.grn_number.split('-')[-1])
                    new_number = last_number + 1
                except (ValueError, IndexError):
                    new_number = 1
            else:
                new_number = 1
            
            self.grn_number = f"GRN-{current_year}-{new_number:04d}"
        
        super().save(*args, **kwargs)
    
    @property
    def is_overdue(self):
        """Check if the GRN is overdue"""
        if self.status in ['completed', 'cancelled']:
            return False
        if self.expected_date is None:
            return False
        return self.expected_date < timezone.now().date()
    
    @property
    def is_completed(self):
        """Check if the GRN is completed"""
        return self.status == 'completed'
    
    def complete(self):
        """Mark the GRN as completed"""
        self.status = 'completed'
        self.received_date = timezone.now().date()
        self.save()


class GRNItem(models.Model):
    """Model for GRN items"""
    grn = models.ForeignKey(GRN, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name="Item", null=True, blank=True)
    
    # Item Details
    item_code = models.CharField(max_length=100, blank=True, verbose_name="Item Code")
    item_name = models.CharField(max_length=200, blank=True, verbose_name="Item Name")
    hs_code = models.CharField(max_length=50, blank=True, verbose_name="HS Code")
    unit = models.CharField(max_length=20, blank=True, verbose_name="Unit")
    
    # Quantities
    expected_qty = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Expected Quantity")
    received_qty = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Received Quantity")
    damaged_qty = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Damaged Quantity")
    short_qty = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Short Quantity")
    
    # Weights and Dimensions
    net_weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Net Weight")
    gross_weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Gross Weight")
    volume = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Volume")
    
    # Additional Information
    coo = models.CharField(max_length=3, blank=True, verbose_name="Country of Origin")
    batch_number = models.CharField(max_length=100, blank=True, verbose_name="Batch Number")
    expiry_date = models.DateField(blank=True, null=True, verbose_name="Expiry Date")
    remark = models.TextField(blank=True, verbose_name="Remark")
    
    # Additional fields from form
    p_date = models.DateField(blank=True, null=True, verbose_name="P-Date")
    color = models.CharField(max_length=50, blank=True, verbose_name="Color")
    size = models.CharField(max_length=50, blank=True, verbose_name="Size")
    ed = models.CharField(max_length=50, blank=True, verbose_name="ED")
    ctnr = models.CharField(max_length=50, blank=True, verbose_name="CTNR")
    
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    class Meta:
        verbose_name = "GRN Item"
        verbose_name_plural = "GRN Items"
    
    def __str__(self):
        return f"{self.grn.grn_number} - {self.item_name}"
    
    @property
    def total_qty(self):
        """Calculate total quantity (received + damaged + short)"""
        received = self.received_qty or 0
        damaged = self.damaged_qty or 0
        short = self.short_qty or 0
        return received + damaged + short
    
    @property
    def variance_qty(self):
        """Calculate variance between expected and received quantity"""
        if self.expected_qty and self.received_qty:
            return self.received_qty - self.expected_qty
        return 0


class GRNPallet(models.Model):
    """Model for GRN pallet details"""
    grn = models.ForeignKey(GRN, on_delete=models.CASCADE, related_name='pallets', verbose_name="GRN")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name="Item", null=True, blank=True)
    
    # Pallet Information
    pallet_no = models.CharField(max_length=100, verbose_name="Pallet Number")
    description = models.CharField(max_length=200, blank=True, verbose_name="Description")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Quantity")
    weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Weight (KGS)")
    volume = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Volume (CBM)")
    location = models.CharField(max_length=200, blank=True, verbose_name="Location")
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('received', 'Received'),
        ('in_transit', 'In Transit'),
        ('stored', 'Stored'),
    ], default='pending', verbose_name="Status")
    remark = models.TextField(blank=True, verbose_name="Remark")
    
    # Audit Fields
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    class Meta:
        verbose_name = "GRN Pallet"
        verbose_name_plural = "GRN Pallets"
        ordering = ['pallet_no']
    
    def __str__(self):
        return f"{self.grn.grn_number} - {self.pallet_no}"
