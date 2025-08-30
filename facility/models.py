from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone


class Facility(models.Model):
    """Facility model for managing business facilities"""
    
    FACILITY_TYPES = [
        ('warehouse', 'Warehouse'),
        ('office', 'Office'),
        ('factory', 'Factory'),
        ('store', 'Store'),
        ('distribution_center', 'Distribution Center'),
        ('cold_storage', 'Cold Storage'),
        ('parking', 'Parking'),
        ('maintenance', 'Maintenance'),
        ('security', 'Security'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Under Maintenance'),
        ('closed', 'Closed'),
    ]
    
    # Basic Information
    facility_code = models.CharField(
        max_length=20, 
        unique=True,
        validators=[RegexValidator(r'^[A-Z0-9-]+$', 'Facility code must contain only uppercase letters, numbers, and hyphens.')],
        help_text="Unique facility code (e.g., FAC-001, WH-002)"
    )
    facility_name = models.CharField(max_length=200, help_text="Name of the facility")
    facility_type = models.CharField(max_length=30, choices=FACILITY_TYPES, default='warehouse')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Description and Details
    description = models.TextField(blank=True, help_text="Detailed description of the facility")
    short_description = models.CharField(max_length=500, blank=True, help_text="Brief description for display")
    
    # Location Information
    address = models.TextField(help_text="Complete address of the facility")
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='United States')
    postal_code = models.CharField(max_length=20)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="GPS latitude")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="GPS longitude")
    
    # Contact Information
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    contact_person = models.CharField(max_length=100, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
    
    # Facility Specifications
    total_area = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Total area in square meters")
    usable_area = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Usable area in square meters")
    height = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Ceiling height in meters")
    capacity = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Storage capacity in cubic meters")
    max_weight_capacity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Maximum weight capacity in tons")
    
    # Operational Information
    operating_hours = models.CharField(max_length=200, blank=True, help_text="e.g., Mon-Fri 8AM-6PM, Sat 9AM-3PM")
    timezone = models.CharField(max_length=50, default='UTC')
    is_24_7 = models.BooleanField(default=False, help_text="Facility operates 24/7")
    has_security = models.BooleanField(default=False)
    has_cctv = models.BooleanField(default=False)
    has_fire_suppression = models.BooleanField(default=False)
    has_climate_control = models.BooleanField(default=False)
    
    # Equipment and Features
    loading_docks = models.PositiveIntegerField(default=0)
    forklifts = models.PositiveIntegerField(default=0)
    pallet_racks = models.PositiveIntegerField(default=0)
    refrigeration_units = models.PositiveIntegerField(default=0)
    power_generators = models.PositiveIntegerField(default=0)
    
    # Financial Information
    monthly_rent = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Monthly rent amount")
    utilities_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Monthly utilities cost")
    maintenance_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Monthly maintenance cost")
    currency = models.CharField(max_length=3, default='USD')
    
    # Ownership and Management
    owner = models.CharField(max_length=200, blank=True, help_text="Facility owner or landlord")
    lease_start_date = models.DateField(null=True, blank=True)
    lease_end_date = models.DateField(null=True, blank=True)
    is_owned = models.BooleanField(default=False, help_text="Facility is owned by the company")
    
    # Additional Information
    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True, help_text="Internal notes not visible to all users")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='facilities_created'
    )
    updated_by = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='facilities_updated'
    )
    
    class Meta:
        ordering = ['facility_name']
        verbose_name = 'Facility'
        verbose_name_plural = 'Facilities'
        db_table = 'facility'
    
    def __str__(self):
        return f"{self.facility_code} - {self.facility_name}"
    
    @property
    def is_active(self):
        """Check if facility is active"""
        return self.status == 'active'
    
    @property
    def display_name(self):
        """Return display name with code"""
        return f"{self.facility_code} - {self.facility_name}"
    
    @property
    def full_address(self):
        """Return complete address"""
        address_parts = [self.address, self.city, self.state, self.postal_code, self.country]
        return ', '.join(filter(None, address_parts))
    
    @property
    def total_monthly_cost(self):
        """Calculate total monthly cost"""
        total = 0
        if self.monthly_rent:
            total += self.monthly_rent
        if self.utilities_cost:
            total += self.utilities_cost
        if self.maintenance_cost:
            total += self.maintenance_cost
        return total
    
    @property
    def utilization_rate(self):
        """Calculate facility utilization rate"""
        if self.total_area and self.usable_area and self.total_area > 0:
            return (self.usable_area / self.total_area) * 100
        return 0
    
    @property
    def lease_status(self):
        """Get lease status"""
        if self.is_owned:
            return 'Owned'
        if self.lease_end_date:
            if self.lease_end_date < timezone.now().date():
                return 'Expired'
            elif self.lease_end_date <= timezone.now().date() + timezone.timedelta(days=30):
                return 'Expiring Soon'
            else:
                return 'Active'
        return 'Unknown'
    
    def get_facility_features(self):
        """Return facility features as a dictionary"""
        features = {}
        if self.has_security:
            features['Security'] = 'Yes'
        if self.has_cctv:
            features['CCTV'] = 'Yes'
        if self.has_fire_suppression:
            features['Fire Suppression'] = 'Yes'
        if self.has_climate_control:
            features['Climate Control'] = 'Yes'
        if self.is_24_7:
            features['24/7 Operation'] = 'Yes'
        if self.loading_docks > 0:
            features['Loading Docks'] = self.loading_docks
        if self.forklifts > 0:
            features['Forklifts'] = self.forklifts
        if self.pallet_racks > 0:
            features['Pallet Racks'] = self.pallet_racks
        return features


class FacilityLocation(models.Model):
    """Model for managing storage locations within facilities"""
    
    LOCATION_TYPES = [
        ('rack', 'Rack'),
        ('aisle', 'Aisle'),
        ('general_area', 'General Area'),
        ('loading_dock', 'Loading Dock'),
        ('cold_storage', 'Cold Storage'),
        ('hazardous_area', 'Hazardous Area'),
        ('office_area', 'Office Area'),
        ('parking_area', 'Parking Area'),
        ('maintenance_area', 'Maintenance Area'),
        ('security_area', 'Security Area'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Under Maintenance'),
        ('reserved', 'Reserved'),
        ('full', 'Full'),
    ]
    
    # Basic Information
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='locations')
    location_code = models.CharField(
        max_length=20,
        validators=[RegexValidator(r'^[A-Z0-9-]+$', 'Location code must contain only uppercase letters, numbers, and hyphens.')],
        help_text="Unique location code within the facility (e.g., RACK-A1, AISLE-01)"
    )
    location_name = models.CharField(max_length=200, help_text="Name of the location")
    location_type = models.CharField(max_length=20, choices=LOCATION_TYPES, default='rack')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Description
    description = models.TextField(blank=True, help_text="Detailed description of the location")
    
    # Physical Specifications
    area = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Area in square meters")
    height = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Height in meters")
    capacity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Storage capacity in cubic meters")
    max_weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Maximum weight capacity in tons")
    
    # Location Details
    floor_level = models.CharField(max_length=10, blank=True, help_text="Floor level (e.g., G, 1, 2, B1)")
    section = models.CharField(max_length=50, blank=True, help_text="Section within the facility")
    zone = models.CharField(max_length=50, blank=True, help_text="Zone designation")
    
    # Rack/Aisle Specific
    rack_number = models.CharField(max_length=20, blank=True, help_text="Rack number if applicable")
    aisle_number = models.CharField(max_length=20, blank=True, help_text="Aisle number if applicable")
    bay_number = models.CharField(max_length=20, blank=True, help_text="Bay number if applicable")
    level_number = models.CharField(max_length=20, blank=True, help_text="Level number if applicable")
    
    # Coordinates (for future mapping)
    x_coordinate = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="X coordinate for mapping")
    y_coordinate = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Y coordinate for mapping")
    
    # Access and Restrictions
    access_restrictions = models.TextField(blank=True, help_text="Any access restrictions or special requirements")
    temperature_range = models.CharField(max_length=50, blank=True, help_text="Temperature range if applicable")
    humidity_range = models.CharField(max_length=50, blank=True, help_text="Humidity range if applicable")
    
    # Equipment and Features
    has_lighting = models.BooleanField(default=True)
    has_climate_control = models.BooleanField(default=False)
    has_security = models.BooleanField(default=False)
    has_fire_suppression = models.BooleanField(default=False)
    is_accessible_by_forklift = models.BooleanField(default=True)
    is_accessible_by_pallet_jack = models.BooleanField(default=True)
    
    # Utilization
    current_utilization = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Current utilization percentage")
    reserved_capacity = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Reserved capacity percentage")
    
    # Notes
    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True, help_text="Internal notes not visible to all users")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='facility_locations_created'
    )
    updated_by = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='facility_locations_updated'
    )
    
    class Meta:
        ordering = ['facility', 'location_type', 'location_code']
        verbose_name = 'Facility Location'
        verbose_name_plural = 'Facility Locations'
        unique_together = ['facility', 'location_code']
        db_table = 'facility_location'
    
    def __str__(self):
        return f"{self.facility.facility_code} - {self.location_code} ({self.location_name})"
    
    @property
    def full_location_code(self):
        """Return full location code with facility prefix"""
        return f"{self.facility.facility_code}-{self.location_code}"
    
    @property
    def display_name(self):
        """Return display name"""
        return f"{self.location_code} - {self.location_name}"
    
    @property
    def is_available(self):
        """Check if location is available for storage"""
        return self.status == 'active' and self.current_utilization < 100
    
    @property
    def available_capacity(self):
        """Calculate available capacity"""
        if self.capacity:
            return self.capacity * (100 - self.current_utilization - self.reserved_capacity) / 100
        return 0
    
    @property
    def location_path(self):
        """Return hierarchical location path"""
        path_parts = []
        if self.floor_level:
            path_parts.append(f"Floor {self.floor_level}")
        if self.section:
            path_parts.append(f"Section {self.section}")
        if self.zone:
            path_parts.append(f"Zone {self.zone}")
        if self.rack_number:
            path_parts.append(f"Rack {self.rack_number}")
        if self.aisle_number:
            path_parts.append(f"Aisle {self.aisle_number}")
        if self.bay_number:
            path_parts.append(f"Bay {self.bay_number}")
        if self.level_number:
            path_parts.append(f"Level {self.level_number}")
        
        return " > ".join(path_parts) if path_parts else "Main Area"
    
    def get_location_features(self):
        """Return location features as a dictionary"""
        features = {}
        if self.has_lighting:
            features['Lighting'] = 'Yes'
        if self.has_climate_control:
            features['Climate Control'] = 'Yes'
        if self.has_security:
            features['Security'] = 'Yes'
        if self.has_fire_suppression:
            features['Fire Suppression'] = 'Yes'
        if self.is_accessible_by_forklift:
            features['Forklift Access'] = 'Yes'
        if self.is_accessible_by_pallet_jack:
            features['Pallet Jack Access'] = 'Yes'
        if self.temperature_range:
            features['Temperature'] = self.temperature_range
        if self.humidity_range:
            features['Humidity'] = self.humidity_range
        return features
