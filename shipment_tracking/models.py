from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.utils import timezone
import uuid

class Shipment(models.Model):
    """Main shipment model for tracking containers and shipments"""
    
    STATUS_CHOICES = [
        ('at_origin_port', 'At Origin Port'),
        ('sailing', 'Sailing'),
        ('arrived_destination', 'Arrived at Destination Port'),
        ('customs_cleared', 'Customs Cleared'),
        ('delivered', 'Delivered'),
        ('on_hold', 'On Hold'),
        ('damaged', 'Damaged'),
        ('returned', 'Returned'),
    ]
    
    # Basic Information
    shipment_id = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    container_number = models.CharField(max_length=20, blank=True, null=True)
    booking_id = models.CharField(max_length=50, blank=True, null=True)
    hbl_number = models.CharField(max_length=50, blank=True, null=True)
    customer_reference = models.CharField(max_length=100, blank=True, null=True)
    
    # Customer Information
    customer = models.ForeignKey('customer.Customer', on_delete=models.CASCADE, related_name='shipments')
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField(blank=True, null=True)
    customer_phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Origin and Destination
    origin_port = models.CharField(max_length=100)
    destination_port = models.CharField(max_length=100)
    origin_country = models.CharField(max_length=100)
    destination_country = models.CharField(max_length=100)
    
    # Dates
    booking_date = models.DateField()
    expected_departure = models.DateField(blank=True, null=True)
    expected_arrival = models.DateField(blank=True, null=True)
    actual_departure = models.DateField(blank=True, null=True)
    actual_arrival = models.DateField(blank=True, null=True)
    
    # Current Status
    current_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='at_origin_port')
    current_location = models.CharField(max_length=200, blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    # Additional Information
    vessel_name = models.CharField(max_length=100, blank=True, null=True)
    voyage_number = models.CharField(max_length=50, blank=True, null=True)
    shipping_line = models.CharField(max_length=100, blank=True, null=True)
    cargo_description = models.TextField(blank=True, null=True)
    cargo_weight = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    cargo_volume = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Tracking
    is_tracking_enabled = models.BooleanField(default=True)
    gps_coordinates = models.CharField(max_length=100, blank=True, null=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_shipments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Notes
    internal_notes = models.TextField(blank=True, null=True)
    customer_notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Shipment'
        verbose_name_plural = 'Shipments'
    
    def __str__(self):
        return f"{self.shipment_id} - {self.container_number or self.booking_id}"
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('shipment_tracking:shipment_detail', kwargs={'pk': self.pk})
    
    @property
    def is_delivered(self):
        return self.current_status == 'delivered'
    
    @property
    def is_delayed(self):
        if self.expected_arrival and self.actual_arrival:
            return self.actual_arrival > self.expected_arrival
        return False

class StatusUpdate(models.Model):
    """Model for tracking status updates and movement history"""
    
    STATUS_CHOICES = [
        ('at_origin_port', 'At Origin Port'),
        ('sailing', 'Sailing'),
        ('arrived_destination', 'Arrived at Destination Port'),
        ('customs_cleared', 'Customs Cleared'),
        ('delivered', 'Delivered'),
        ('on_hold', 'On Hold'),
        ('damaged', 'Damaged'),
        ('returned', 'Returned'),
    ]
    
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='status_updates')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    location = models.CharField(max_length=200)
    timestamp = models.DateTimeField(default=timezone.now)
    
    # Additional Details
    description = models.TextField(blank=True, null=True)
    estimated_completion = models.DateTimeField(blank=True, null=True)
    
    # Updated By
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='status_updates')
    
    # Coordinates
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    
    # Notification
    notification_sent = models.BooleanField(default=False)
    notification_sent_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Status Update'
        verbose_name_plural = 'Status Updates'
    
    def __str__(self):
        return f"{self.shipment.shipment_id} - {self.get_status_display()} at {self.location}"
    
    def save(self, *args, **kwargs):
        # Update the shipment's current status
        if not self.pk:  # Only on creation
            self.shipment.current_status = self.status
            self.shipment.current_location = self.location
            self.shipment.last_updated = self.timestamp
            self.shipment.save()
        super().save(*args, **kwargs)

class ShipmentAttachment(models.Model):
    """Model for storing attachments related to shipments"""
    
    ATTACHMENT_TYPES = [
        ('pod', 'Proof of Delivery'),
        ('photo', 'Photo'),
        ('gate_pass', 'Gate Pass'),
        ('customs_doc', 'Customs Document'),
        ('invoice', 'Invoice'),
        ('packing_list', 'Packing List'),
        ('other', 'Other'),
    ]
    
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='attachments')
    status_update = models.ForeignKey(StatusUpdate, on_delete=models.CASCADE, related_name='attachments', blank=True, null=True)
    
    file = models.FileField(
        upload_to='shipment_attachments/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx', 'xls', 'xlsx'])]
    )
    file_type = models.CharField(max_length=20, choices=ATTACHMENT_TYPES)
    description = models.CharField(max_length=200, blank=True, null=True)
    
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_attachments')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Shipment Attachment'
        verbose_name_plural = 'Shipment Attachments'
    
    def __str__(self):
        return f"{self.shipment.shipment_id} - {self.get_file_type_display()}"

class NotificationLog(models.Model):
    """Model for tracking notification history"""
    
    NOTIFICATION_TYPES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
        ('system', 'System Notification'),
    ]
    
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='notifications')
    status_update = models.ForeignKey(StatusUpdate, on_delete=models.CASCADE, related_name='notifications', blank=True, null=True)
    
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    recipient = models.CharField(max_length=200)
    subject = models.CharField(max_length=200, blank=True, null=True)
    message = models.TextField()
    
    sent_at = models.DateTimeField(auto_now_add=True)
    sent_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sent_notifications')
    
    # Status
    is_sent = models.BooleanField(default=False)
    is_delivered = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-sent_at']
        verbose_name = 'Notification Log'
        verbose_name_plural = 'Notification Logs'
    
    def __str__(self):
        return f"{self.shipment.shipment_id} - {self.get_notification_type_display()} to {self.recipient}"

class BulkUpdateLog(models.Model):
    """Model for tracking bulk update operations"""
    
    UPDATE_TYPES = [
        ('excel_upload', 'Excel Upload'),
        ('api_update', 'API Update'),
        ('manual_bulk', 'Manual Bulk Update'),
    ]
    
    update_type = models.CharField(max_length=20, choices=UPDATE_TYPES)
    file_uploaded = models.FileField(upload_to='bulk_updates/%Y/%m/%d/', blank=True, null=True)
    
    total_records = models.IntegerField(default=0)
    successful_updates = models.IntegerField(default=0)
    failed_updates = models.IntegerField(default=0)
    
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='bulk_updates')
    processed_at = models.DateTimeField(auto_now_add=True)
    
    # Results
    success_details = models.JSONField(blank=True, null=True)
    error_details = models.JSONField(blank=True, null=True)
    
    class Meta:
        ordering = ['-processed_at']
        verbose_name = 'Bulk Update Log'
        verbose_name_plural = 'Bulk Update Logs'
    
    def __str__(self):
        return f"{self.get_update_type_display()} - {self.processed_at.strftime('%Y-%m-%d %H:%M')}"

class ShipmentSearch(models.Model):
    """Model for storing search history and preferences"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shipment_searches')
    search_query = models.CharField(max_length=200)
    search_type = models.CharField(max_length=20, choices=[
        ('container', 'Container Number'),
        ('booking', 'Booking ID'),
        ('hbl', 'HBL Number'),
        ('customer_ref', 'Customer Reference'),
        ('general', 'General Search'),
    ])
    search_results_count = models.IntegerField(default=0)
    searched_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-searched_at']
        verbose_name = 'Shipment Search'
        verbose_name_plural = 'Shipment Searches'
    
    def __str__(self):
        return f"{self.user.username} - {self.search_query} ({self.searched_at.strftime('%Y-%m-%d')})"
