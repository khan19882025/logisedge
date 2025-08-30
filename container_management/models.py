from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
import uuid
from datetime import datetime, timedelta

class Container(models.Model):
    """Container model for managing container inventory"""
    
    CONTAINER_TYPES = [
        ('20ft', '20ft Standard'),
        ('40ft', '40ft Standard'),
        ('40hc', '40ft High Cube'),
        ('45ft', '45ft High Cube'),
        ('reefer', 'Reefer Container'),
        ('open_top', 'Open Top'),
        ('flat_rack', 'Flat Rack'),
        ('tank', 'Tank Container'),
    ]
    
    CONTAINER_STATUS = [
        ('available', 'Available'),
        ('booked', 'Booked'),
        ('in_use', 'In Use'),
        ('maintenance', 'Under Maintenance'),
        ('retired', 'Retired'),
    ]
    
    container_number = models.CharField(max_length=11, unique=True, help_text="ISO 6346 standard container number")
    container_type = models.CharField(max_length=20, choices=CONTAINER_TYPES)
    size = models.CharField(max_length=10, help_text="Container size (20ft, 40ft, etc.)")
    tare_weight = models.DecimalField(max_digits=8, decimal_places=2, help_text="Empty container weight in kg")
    max_payload = models.DecimalField(max_digits=8, decimal_places=2, help_text="Maximum payload in kg")
    status = models.CharField(max_length=20, choices=CONTAINER_STATUS, default='available')
    current_location = models.CharField(max_length=100, help_text="Current location (Port/Terminal/Yard)")
    yard_location = models.CharField(max_length=50, blank=True, help_text="Specific yard location")
    line_operator = models.CharField(max_length=100, blank=True, help_text="Shipping line operator")
    purchase_date = models.DateField(null=True, blank=True)
    last_maintenance = models.DateField(null=True, blank=True)
    next_maintenance = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['container_number']
        verbose_name = 'Container'
        verbose_name_plural = 'Containers'
    
    def __str__(self):
        return f"{self.container_number} - {self.get_container_type_display()}"
    
    def get_total_weight_capacity(self):
        """Get total weight capacity (tare + max payload)"""
        return self.tare_weight + self.max_payload
    
    def is_available(self):
        """Check if container is available for booking"""
        return self.status == 'available'
    
    def is_overdue_maintenance(self):
        """Check if container is overdue for maintenance"""
        if self.next_maintenance:
            return self.next_maintenance < timezone.now().date()
        return False

class ContainerBooking(models.Model):
    """Container booking model"""
    
    BOOKING_STATUS = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    SOC_COC_CHOICES = [
        ('soc', 'Shipper Owned Container (SOC)'),
        ('coc', 'Carrier Owned Container (COC)'),
    ]
    
    booking_number = models.CharField(max_length=20, unique=True, blank=True)
    container = models.ForeignKey(Container, on_delete=models.CASCADE, related_name='bookings')
    customer = models.ForeignKey('freight_quotation.Customer', on_delete=models.CASCADE)
    freight_quotation = models.ForeignKey('freight_quotation.FreightQuotation', on_delete=models.SET_NULL, null=True, blank=True)
    freight_booking = models.ForeignKey('freight_booking.FreightBooking', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Container details
    container_type = models.CharField(max_length=20, choices=Container.CONTAINER_TYPES)
    container_size = models.CharField(max_length=10)
    soc_coc = models.CharField(max_length=10, choices=SOC_COC_CHOICES, default='coc')
    
    # Booking details
    pickup_date = models.DateField()
    pickup_location = models.CharField(max_length=100)
    drop_off_port = models.CharField(max_length=100)
    drop_off_date = models.DateField()
    
    # Cargo details
    cargo_description = models.TextField()
    weight = models.DecimalField(max_digits=8, decimal_places=2, help_text="Cargo weight in kg")
    volume = models.DecimalField(max_digits=8, decimal_places=2, help_text="Cargo volume in CBM")
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=BOOKING_STATUS, default='pending')
    booking_date = models.DateTimeField(auto_now_add=True)
    confirmed_date = models.DateTimeField(null=True, blank=True)
    
    # Financial
    rate = models.DecimalField(max_digits=10, decimal_places=2, help_text="Daily rate in AED")
    total_days = models.IntegerField(default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Additional info
    special_instructions = models.TextField(blank=True)
    booking_confirmation_file = models.FileField(upload_to='container_bookings/confirmations/', blank=True)
    soc_coc_details = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-booking_date']
        verbose_name = 'Container Booking'
        verbose_name_plural = 'Container Bookings'
    
    def __str__(self):
        return f"Booking {self.booking_number} - {self.container.container_number}"
    
    def save(self, *args, **kwargs):
        if not self.booking_number:
            # Generate unique booking number
            year = timezone.now().year
            month = timezone.now().month
            count = ContainerBooking.objects.filter(
                booking_date__year=year,
                booking_date__month=month
            ).count() + 1
            self.booking_number = f"CB{year}{month:02d}{count:04d}"
        
        # Calculate total days and amount
        if self.pickup_date and self.drop_off_date:
            delta = self.drop_off_date - self.pickup_date
            self.total_days = delta.days + 1
            self.total_amount = self.rate * self.total_days
        
        super().save(*args, **kwargs)
    
    def get_status_display_class(self):
        """Get CSS class for status display"""
        status_classes = {
            'pending': 'warning',
            'confirmed': 'info',
            'active': 'primary',
            'completed': 'success',
            'cancelled': 'danger',
        }
        return status_classes.get(self.status, 'secondary')

class ContainerTracking(models.Model):
    """Container tracking and milestone updates"""
    
    MILESTONE_CHOICES = [
        ('gate_in', 'Gate In'),
        ('gate_out', 'Gate Out'),
        ('stuffing', 'Stuffing'),
        ('loaded', 'Loaded on Vessel'),
        ('in_transit', 'In Transit'),
        ('at_destination', 'At Destination Port'),
        ('unloaded', 'Unloaded'),
        ('delivered', 'Delivered'),
        ('returned', 'Returned'),
    ]
    
    tracking_number = models.CharField(max_length=50, unique=True, blank=True)
    container_booking = models.ForeignKey(ContainerBooking, on_delete=models.CASCADE, related_name='tracking_events')
    container = models.ForeignKey(Container, on_delete=models.CASCADE, related_name='tracking_events')
    
    # Tracking details
    milestone = models.CharField(max_length=20, choices=MILESTONE_CHOICES)
    location = models.CharField(max_length=100)
    vessel_name = models.CharField(max_length=100, blank=True)
    voyage_number = models.CharField(max_length=50, blank=True)
    
    # Dates
    event_date = models.DateTimeField()
    eta = models.DateTimeField(null=True, blank=True)
    actual_date = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_completed = models.BooleanField(default=False)
    is_delayed = models.BooleanField(default=False)
    delay_reason = models.TextField(blank=True)
    
    # Additional info
    notes = models.TextField(blank=True)
    documents = models.FileField(upload_to='container_tracking/documents/', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-event_date']
        verbose_name = 'Container Tracking'
        verbose_name_plural = 'Container Tracking'
    
    def __str__(self):
        return f"{self.container.container_number} - {self.get_milestone_display()} at {self.location}"
    
    def save(self, *args, **kwargs):
        if not self.tracking_number:
            # Generate unique tracking number
            self.tracking_number = f"CT{uuid.uuid4().hex[:8].upper()}"
        
        # Check for delays
        if self.eta and self.actual_date and self.actual_date > self.eta:
            self.is_delayed = True
        
        super().save(*args, **kwargs)
    
    def get_milestone_display_class(self):
        """Get CSS class for milestone badge"""
        classes = {
            'gate_in': 'primary',
            'gate_out': 'info',
            'stuffing': 'warning',
            'loaded': 'success',
            'in_transit': 'secondary',
            'at_destination': 'info',
            'unloaded': 'warning',
            'delivered': 'success',
            'returned': 'dark',
        }
        return classes.get(self.milestone, 'secondary')
    
    @property
    def is_active(self):
        """Check if tracking is active (not completed)"""
        return not self.is_completed
    
    @property
    def status(self):
        """Get status based on completion and delay"""
        if self.is_completed:
            return 'completed'
        elif self.is_delayed:
            return 'delayed'
        else:
            return 'on_time'
    
    @property
    def last_updated(self):
        """Get last updated timestamp"""
        return self.updated_at or self.created_at

class ContainerInventory(models.Model):
    """Container inventory by port/location"""
    
    INVENTORY_STATUS = [
        ('empty', 'Empty'),
        ('stuffed', 'Stuffed'),
        ('loaded', 'Loaded on Vessel'),
        ('in_transit', 'In Transit'),
        ('at_port', 'At Port'),
        ('returned', 'Returned'),
        ('overstayed', 'Overstayed'),
    ]
    
    container = models.ForeignKey(Container, on_delete=models.CASCADE, related_name='inventory_records')
    port = models.CharField(max_length=100)
    terminal = models.CharField(max_length=100)
    yard = models.CharField(max_length=50)
    bay = models.CharField(max_length=20, blank=True)
    row = models.CharField(max_length=20, blank=True)
    tier = models.CharField(max_length=20, blank=True)
    
    status = models.CharField(max_length=20, choices=INVENTORY_STATUS)
    arrival_date = models.DateTimeField()
    expected_departure = models.DateTimeField(null=True, blank=True)
    actual_departure = models.DateTimeField(null=True, blank=True)
    
    # Overstay tracking
    is_overstayed = models.BooleanField(default=False)
    overstay_days = models.IntegerField(default=0)
    overstay_reason = models.TextField(blank=True)
    
    # Associated booking
    container_booking = models.ForeignKey(ContainerBooking, on_delete=models.SET_NULL, null=True, blank=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-arrival_date']
        verbose_name = 'Container Inventory'
        verbose_name_plural = 'Container Inventory'
        unique_together = ['container', 'port', 'terminal', 'yard']
    
    def __str__(self):
        return f"{self.container.container_number} at {self.port} - {self.terminal}"
    
    def save(self, *args, **kwargs):
        # Check for overstay
        if self.expected_departure and timezone.now() > self.expected_departure:
            self.is_overstayed = True
            delta = timezone.now() - self.expected_departure
            self.overstay_days = delta.days
        
        super().save(*args, **kwargs)

class ContainerMovement(models.Model):
    """Container movement history"""
    
    MOVEMENT_TYPE = [
        ('arrival', 'Arrival'),
        ('departure', 'Departure'),
        ('transfer', 'Transfer'),
        ('maintenance', 'Maintenance'),
    ]
    
    container = models.ForeignKey(Container, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPE)
    
    from_location = models.CharField(max_length=100)
    to_location = models.CharField(max_length=100)
    movement_date = models.DateTimeField()
    
    # Vessel details (if applicable)
    vessel_name = models.CharField(max_length=100, blank=True)
    voyage_number = models.CharField(max_length=50, blank=True)
    
    # Associated records
    container_booking = models.ForeignKey(ContainerBooking, on_delete=models.SET_NULL, null=True, blank=True)
    container_tracking = models.ForeignKey(ContainerTracking, on_delete=models.SET_NULL, null=True, blank=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-movement_date']
        verbose_name = 'Container Movement'
        verbose_name_plural = 'Container Movements'
    
    def __str__(self):
        return f"{self.container.container_number} - {self.get_movement_type_display()} from {self.from_location} to {self.to_location}"

class ContainerNotification(models.Model):
    """Container-related notifications"""
    
    NOTIFICATION_TYPE = [
        ('status_change', 'Status Change'),
        ('overstay', 'Overstay Alert'),
        ('maintenance', 'Maintenance Due'),
        ('booking_confirmation', 'Booking Confirmation'),
        ('tracking_update', 'Tracking Update'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPE)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    # Related objects
    container = models.ForeignKey(Container, on_delete=models.CASCADE, null=True, blank=True)
    container_booking = models.ForeignKey(ContainerBooking, on_delete=models.CASCADE, null=True, blank=True)
    container_tracking = models.ForeignKey(ContainerTracking, on_delete=models.CASCADE, null=True, blank=True)
    
    # Notification details
    title = models.CharField(max_length=200)
    message = models.TextField()
    recipient_email = models.EmailField(blank=True)
    recipient_name = models.CharField(max_length=100, blank=True)
    
    # Status
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Container Notification'
        verbose_name_plural = 'Container Notifications'
    
    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.title}"
    
    def get_notification_type_display_class(self):
        """Get CSS class for notification type badge"""
        classes = {
            'status_change': 'primary',
            'overstay': 'danger',
            'maintenance': 'warning',
            'booking_confirmation': 'success',
            'tracking_update': 'info',
        }
        return classes.get(self.notification_type, 'secondary')
    
    def get_priority_display_class(self):
        """Get CSS class for priority badge"""
        classes = {
            'low': 'secondary',
            'medium': 'info',
            'high': 'warning',
            'urgent': 'danger',
        }
        return classes.get(self.priority, 'secondary')
