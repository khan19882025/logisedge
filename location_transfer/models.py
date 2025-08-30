from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils import timezone
from decimal import Decimal
from facility.models import FacilityLocation
from items.models import Item
from grn.models import GRNPallet

class Pallet(models.Model):
    """Model for managing pallets in the warehouse"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('damaged', 'Damaged'),
        ('lost', 'Lost'),
        ('disposed', 'Disposed'),
    ]
    
    # Basic Information
    pallet_id = models.CharField(
        max_length=100, 
        unique=True,
        validators=[RegexValidator(r'^[A-Z0-9-]+$', 'Pallet ID must contain only uppercase letters, numbers, and hyphens.')],
        verbose_name="Pallet ID"
    )
    description = models.CharField(max_length=200, blank=True, verbose_name="Description")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="Status")
    
    # Current Location
    current_location = models.ForeignKey(
        FacilityLocation, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='pallets',
        verbose_name="Current Location"
    )
    
    # Physical Specifications
    weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Weight (KGS)")
    volume = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Volume (CBM)")
    dimensions = models.CharField(max_length=100, blank=True, verbose_name="Dimensions (LxWxH)")
    
    # Source Information
    grn_pallet = models.ForeignKey(
        GRNPallet, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Source GRN Pallet"
    )
    
    # Notes
    notes = models.TextField(blank=True, verbose_name="Notes")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='pallets_created',
        verbose_name="Created By"
    )
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='pallets_updated',
        verbose_name="Updated By"
    )
    
    class Meta:
        verbose_name = "Pallet"
        verbose_name_plural = "Pallets"
        ordering = ['pallet_id']
        db_table = 'location_transfer_pallet'
    
    def __str__(self):
        return f"Pallet {self.pallet_id}"
    
    @property
    def display_name(self):
        """Return display name with location"""
        if self.current_location:
            return f"{self.pallet_id} - {self.current_location.display_name}"
        return self.pallet_id
    
    @property
    def is_available_for_transfer(self):
        """Check if pallet is available for transfer"""
        return self.status == 'active' and self.current_location is not None
    
    def get_items(self):
        """Get items on this pallet"""
        return self.pallet_items.all()

class PalletItem(models.Model):
    """Model for items stored on pallets"""
    
    pallet = models.ForeignKey(Pallet, on_delete=models.CASCADE, related_name='pallet_items', verbose_name="Pallet")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name="Item")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Quantity")
    unit_of_measure = models.CharField(max_length=20, blank=True, verbose_name="Unit of Measure")
    batch_number = models.CharField(max_length=100, blank=True, verbose_name="Batch Number")
    serial_number = models.CharField(max_length=100, blank=True, verbose_name="Serial Number")
    expiry_date = models.DateField(null=True, blank=True, verbose_name="Expiry Date")
    
    # Cost and Value
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Unit Cost")
    total_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Total Value")
    
    # Notes
    notes = models.TextField(blank=True, verbose_name="Notes")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    class Meta:
        verbose_name = "Pallet Item"
        verbose_name_plural = "Pallet Items"
        ordering = ['pallet', 'item']
        db_table = 'location_transfer_pallet_item'
        unique_together = ['pallet', 'item', 'batch_number', 'serial_number']
    
    def __str__(self):
        return f"{self.pallet.pallet_id} - {self.item.item_name} ({self.quantity})"
    
    def save(self, *args, **kwargs):
        # Calculate total value if unit cost is provided
        if self.unit_cost and self.quantity:
            self.total_value = self.unit_cost * self.quantity
        super().save(*args, **kwargs)

class LocationTransfer(models.Model):
    """Model for tracking location transfers of pallets"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
    ]
    
    TRANSFER_TYPES = [
        ('internal', 'Internal Transfer'),
        ('cross_facility', 'Cross Facility Transfer'),
        ('temporary', 'Temporary Transfer'),
        ('permanent', 'Permanent Transfer'),
    ]
    
    # Basic Information
    transfer_number = models.CharField(max_length=50, unique=True, verbose_name="Transfer Number")
    transfer_type = models.CharField(max_length=20, choices=TRANSFER_TYPES, default='internal', verbose_name="Transfer Type")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Status")
    
    # Pallet Information
    pallet = models.ForeignKey(Pallet, on_delete=models.CASCADE, verbose_name="Pallet")
    
    # Location Information
    source_location = models.ForeignKey(
        FacilityLocation, 
        on_delete=models.CASCADE, 
        related_name='source_transfers',
        verbose_name="Source Location"
    )
    destination_location = models.ForeignKey(
        FacilityLocation, 
        on_delete=models.CASCADE, 
        related_name='destination_transfers',
        verbose_name="Destination Location"
    )
    
    # Transfer Details
    transfer_date = models.DateTimeField(default=timezone.now, verbose_name="Transfer Date")
    scheduled_date = models.DateTimeField(null=True, blank=True, verbose_name="Scheduled Date")
    completed_date = models.DateTimeField(null=True, blank=True, verbose_name="Completed Date")
    
    # Priority and Urgency
    priority = models.CharField(
        max_length=20, 
        choices=[
            ('low', 'Low'),
            ('normal', 'Normal'),
            ('high', 'High'),
            ('urgent', 'Urgent'),
        ],
        default='normal',
        verbose_name="Priority"
    )
    
    # Notes and Instructions
    notes = models.TextField(blank=True, verbose_name="Notes")
    special_instructions = models.TextField(blank=True, verbose_name="Special Instructions")
    
    # Approval and Processing
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='location_transfers_approved',
        verbose_name="Approved By"
    )
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name="Approved At")
    processed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='location_transfers_processed',
        verbose_name="Processed By"
    )
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name="Processed At")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='location_transfers_created',
        verbose_name="Created By"
    )
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='location_transfers_updated',
        verbose_name="Updated By"
    )
    
    class Meta:
        verbose_name = "Location Transfer"
        verbose_name_plural = "Location Transfers"
        ordering = ['-created_at']
        db_table = 'location_transfer_transfer'
    
    def __str__(self):
        return f"Transfer {self.transfer_number} - {self.pallet.pallet_id}"
    
    def save(self, *args, **kwargs):
        if not self.transfer_number:
            # Generate transfer number
            last_transfer = LocationTransfer.objects.order_by('-id').first()
            if last_transfer:
                last_number = int(last_transfer.transfer_number.split('-')[1])
                self.transfer_number = f"LT-{last_number + 1:06d}"
            else:
                self.transfer_number = "LT-000001"
        super().save(*args, **kwargs)
    
    @property
    def is_approved(self):
        """Check if transfer is approved"""
        return self.approved_by is not None
    
    @property
    def is_completed(self):
        """Check if transfer is completed"""
        return self.status == 'completed'
    
    @property
    def can_be_processed(self):
        """Check if transfer can be processed"""
        return self.status in ['pending', 'in_progress'] and self.is_approved
    
    def approve(self, user):
        """Approve the transfer"""
        self.approved_by = user
        self.approved_at = timezone.now()
        self.status = 'pending'
        self.save()
    
    def process(self, user):
        """Process the transfer"""
        if not self.can_be_processed:
            raise ValueError("Transfer cannot be processed")
        
        # Update pallet location
        self.pallet.current_location = self.destination_location
        self.pallet.updated_by = user
        self.pallet.save()
        
        # Update transfer status
        self.status = 'completed'
        self.processed_by = user
        self.processed_at = timezone.now()
        self.completed_date = timezone.now()
        self.save()
        
        # Create history entry
        LocationTransferHistory.objects.create(
            transfer=self,
            action='completed',
            description=f'Transfer completed by {user.get_full_name() or user.username}',
            performed_by=user
        )

class LocationTransferHistory(models.Model):
    """Model for tracking transfer history and audit trail"""
    
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('approved', 'Approved'),
        ('started', 'Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
        ('location_updated', 'Location Updated'),
        ('notes_updated', 'Notes Updated'),
    ]
    
    transfer = models.ForeignKey(LocationTransfer, on_delete=models.CASCADE, related_name='history', verbose_name="Transfer")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name="Action")
    description = models.TextField(verbose_name="Description")
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Performed By")
    performed_at = models.DateTimeField(auto_now_add=True, verbose_name="Performed At")
    
    # Additional data (JSON field for flexibility)
    additional_data = models.JSONField(null=True, blank=True, verbose_name="Additional Data")
    
    class Meta:
        verbose_name = "Location Transfer History"
        verbose_name_plural = "Location Transfer History"
        ordering = ['-performed_at']
        db_table = 'location_transfer_history'
    
    def __str__(self):
        return f"{self.transfer.transfer_number} - {self.action} ({self.performed_at.strftime('%Y-%m-%d %H:%M')})"
