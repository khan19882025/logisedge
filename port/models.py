from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone

class Port(models.Model):
    """Port model for managing shipping ports"""
    
    PORT_TYPES = [
        ('seaport', 'Sea Port'),
        ('airport', 'Air Port'),
        ('dryport', 'Dry Port'),
        ('inland', 'Inland Port'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Under Maintenance'),
    ]
    
    # Basic Information
    port_code = models.CharField(
        max_length=10, 
        unique=True,
        validators=[RegexValidator(r'^[A-Z0-9]+$', 'Port code must contain only uppercase letters and numbers.')],
        help_text="Unique port code (e.g., JED, DXB)"
    )
    port_name = models.CharField(max_length=100, help_text="Full name of the port")
    port_type = models.CharField(max_length=20, choices=PORT_TYPES, default='seaport')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Location Information
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state_province = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Contact Information
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    
    # Operational Information
    timezone = models.CharField(max_length=50, default='UTC')
    customs_office = models.CharField(max_length=100, blank=True)
    customs_phone = models.CharField(max_length=20, blank=True)
    
    # Capacity and Facilities
    max_vessel_size = models.CharField(max_length=50, blank=True, help_text="Maximum vessel size in TEU or DWT")
    berth_count = models.PositiveIntegerField(default=0)
    container_capacity = models.PositiveIntegerField(default=0, help_text="Container capacity in TEU")
    
    # Financial Information
    currency = models.CharField(max_length=3, default='USD')
    handling_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    storage_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Additional Information
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='ports_created'
    )
    updated_by = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='ports_updated'
    )
    
    class Meta:
        ordering = ['port_name']
        verbose_name = 'Port'
        verbose_name_plural = 'Ports'
        db_table = 'port'
    
    def __str__(self):
        return f"{self.port_code} - {self.port_name}"
    
    def get_full_location(self):
        """Return full location string"""
        location_parts = [self.city]
        if self.state_province:
            location_parts.append(self.state_province)
        location_parts.append(self.country)
        return ', '.join(location_parts)
    
    def get_coordinates(self):
        """Return coordinates as tuple"""
        if self.latitude and self.longitude:
            return (float(self.latitude), float(self.longitude))
        return None
    
    @property
    def is_active(self):
        """Check if port is active"""
        return self.status == 'active'
    
    @property
    def display_name(self):
        """Return display name with code"""
        return f"{self.port_code} - {self.port_name}"
