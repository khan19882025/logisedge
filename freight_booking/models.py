from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
import uuid


class Carrier(models.Model):
    """Carrier/Vendor model for freight bookings"""
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    country = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class BookingCoordinator(models.Model):
    """Internal booking coordinator/agent model"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100, blank=True)
    phone_extension = models.CharField(max_length=10, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['user__first_name', 'user__last_name']

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"


class FreightBooking(models.Model):
    """Main freight booking model"""
    
    SHIPMENT_TYPE_CHOICES = [
        ('fcl', 'FCL (Full Container Load)'),
        ('lcl', 'LCL (Less than Container Load)'),
        ('air', 'Air Freight'),
        ('land', 'Land Transport'),
        ('express', 'Express'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('booked', 'Booked'),
        ('confirmed', 'Confirmed'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    CONTAINER_TYPE_CHOICES = [
        ('20ft', '20ft Standard'),
        ('40ft', '40ft Standard'),
        ('40hc', '40ft High Cube'),
        ('45ft', '45ft High Cube'),
        ('reefer', 'Reefer Container'),
        ('open_top', 'Open Top'),
        ('flat_rack', 'Flat Rack'),
        ('tank', 'Tank Container'),
    ]

    # Basic Information
    booking_reference = models.CharField(max_length=50, unique=True, editable=False)
    quotation = models.ForeignKey('freight_quotation.FreightQuotation', on_delete=models.SET_NULL, null=True, blank=True)
    customer = models.ForeignKey('freight_quotation.Customer', on_delete=models.CASCADE)
    shipment_type = models.CharField(max_length=20, choices=SHIPMENT_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Origin & Destination
    origin_country = models.CharField(max_length=100)
    origin_port = models.CharField(max_length=100, blank=True)
    origin_city = models.CharField(max_length=100)
    destination_country = models.CharField(max_length=100)
    destination_port = models.CharField(max_length=100, blank=True)
    destination_city = models.CharField(max_length=100)
    
    # Carrier & Coordinator
    carrier = models.ForeignKey(Carrier, on_delete=models.CASCADE)
    booking_coordinator = models.ForeignKey(BookingCoordinator, on_delete=models.SET_NULL, null=True)
    
    # Cargo Details
    cargo_description = models.TextField()
    commodity = models.CharField(max_length=200)
    weight = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    volume = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    packages = models.PositiveIntegerField(default=1)
    container_type = models.CharField(max_length=20, choices=CONTAINER_TYPE_CHOICES, blank=True)
    container_count = models.PositiveIntegerField(default=0)
    
    # Dates
    pickup_date = models.DateField()
    delivery_date = models.DateField()
    booking_date = models.DateTimeField(auto_now_add=True)
    confirmed_date = models.DateTimeField(null=True, blank=True)
    transit_start_date = models.DateTimeField(null=True, blank=True)
    delivered_date = models.DateTimeField(null=True, blank=True)
    
    # Financial Information
    freight_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    additional_costs = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='AED')
    
    # Additional Information
    special_instructions = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_bookings')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_bookings')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.booking_reference} - {self.customer.name}"

    def save(self, *args, **kwargs):
        if not self.booking_reference:
            # Generate unique booking reference
            prefix = "BK"
            year = timezone.now().year
            month = timezone.now().month
            # Get count of bookings for this month
            count = FreightBooking.objects.filter(
                created_at__year=year,
                created_at__month=month
            ).count() + 1
            self.booking_reference = f"{prefix}{year}{month:02d}{count:04d}"
        
        # Calculate total cost
        self.total_cost = self.freight_cost + self.additional_costs
        
        super().save(*args, **kwargs)


class BookingDocument(models.Model):
    """Documents attached to freight bookings"""
    
    DOCUMENT_TYPE_CHOICES = [
        ('commercial_invoice', 'Commercial Invoice'),
        ('packing_list', 'Packing List'),
        ('msds', 'MSDS (Material Safety Data Sheet)'),
        ('certificate_of_origin', 'Certificate of Origin'),
        ('bill_of_lading', 'Bill of Lading'),
        ('airway_bill', 'Airway Bill'),
        ('customs_declaration', 'Customs Declaration'),
        ('insurance_certificate', 'Insurance Certificate'),
        ('other', 'Other'),
    ]
    
    booking = models.ForeignKey(FreightBooking, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPE_CHOICES)
    filename = models.CharField(max_length=255)
    file = models.FileField(upload_to='booking_documents/')
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.booking.booking_reference} - {self.get_document_type_display()}"


class BookingHistory(models.Model):
    """History tracking for booking status changes"""
    
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('status_changed', 'Status Changed'),
        ('document_added', 'Document Added'),
        ('document_removed', 'Document Removed'),
        ('cancelled', 'Cancelled'),
    ]
    
    booking = models.ForeignKey(FreightBooking, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Booking history'

    def __str__(self):
        return f"{self.booking.booking_reference} - {self.action} by {self.user.username}"


class BookingCharge(models.Model):
    """Additional charges for freight bookings"""
    
    CHARGE_TYPE_CHOICES = [
        ('freight', 'Freight Cost'),
        ('handling', 'Handling Charges'),
        ('customs', 'Customs Charges'),
        ('insurance', 'Insurance'),
        ('storage', 'Storage Charges'),
        ('detention', 'Detention Charges'),
        ('demurrage', 'Demurrage Charges'),
        ('other', 'Other'),
    ]
    
    booking = models.ForeignKey(FreightBooking, on_delete=models.CASCADE, related_name='charges')
    charge_type = models.CharField(max_length=20, choices=CHARGE_TYPE_CHOICES)
    description = models.TextField()
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, default='AED')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.booking.booking_reference} - {self.get_charge_type_display()}: {self.amount} {self.currency}"
