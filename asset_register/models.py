from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
import uuid
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from PIL import Image
import barcode
from barcode.writer import ImageWriter
from django.core.files import File


class AssetCategory(models.Model):
    """Asset categories for classification"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent_category = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Asset Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class AssetLocation(models.Model):
    """Physical locations where assets can be stored"""
    name = models.CharField(max_length=100, unique=True)
    building = models.CharField(max_length=100, blank=True)
    floor = models.CharField(max_length=50, blank=True)
    room = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class AssetStatus(models.Model):
    """Asset status options"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#007bff')  # Hex color code
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Asset Statuses"
        ordering = ['name']

    def __str__(self):
        return self.name


class AssetDepreciation(models.Model):
    """Depreciation methods and rates"""
    DEPRECIATION_METHODS = [
        ('straight_line', 'Straight Line'),
        ('declining_balance', 'Declining Balance'),
        ('sum_of_years', 'Sum of Years Digits'),
        ('units_of_production', 'Units of Production'),
        ('none', 'No Depreciation'),
    ]

    name = models.CharField(max_length=100, unique=True)
    method = models.CharField(max_length=20, choices=DEPRECIATION_METHODS, default='straight_line')
    rate_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    useful_life_years = models.PositiveIntegerField(default=0)
    salvage_value_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Asset Depreciation Methods"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_method_display()})"


class Asset(models.Model):
    """Main asset model"""
    # Basic Information
    asset_code = models.CharField(max_length=50, unique=True, help_text="Unique asset identifier")
    asset_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(AssetCategory, on_delete=models.PROTECT)
    location = models.ForeignKey(AssetLocation, on_delete=models.PROTECT)
    status = models.ForeignKey(AssetStatus, on_delete=models.PROTECT)
    
    # Financial Information
    purchase_date = models.DateField()
    purchase_value = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    current_value = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    salvage_value = models.DecimalField(max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    
    # Depreciation
    depreciation_method = models.ForeignKey(AssetDepreciation, on_delete=models.PROTECT)
    useful_life_years = models.PositiveIntegerField(default=0)
    accumulated_depreciation = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    book_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Assignment and Tracking
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    assigned_date = models.DateField(null=True, blank=True)
    
    # QR Code and Barcode
    qr_code = models.ImageField(upload_to='asset_qr_codes/', blank=True, null=True)
    barcode = models.ImageField(upload_to='asset_barcodes/', blank=True, null=True)
    
    # Additional Information
    serial_number = models.CharField(max_length=100, blank=True)
    model_number = models.CharField(max_length=100, blank=True)
    manufacturer = models.CharField(max_length=100, blank=True)
    warranty_expiry = models.DateField(null=True, blank=True)
    insurance_policy = models.CharField(max_length=100, blank=True)
    insurance_expiry = models.DateField(null=True, blank=True)
    
    # Maintenance
    last_maintenance_date = models.DateField(null=True, blank=True)
    next_maintenance_date = models.DateField(null=True, blank=True)
    maintenance_notes = models.TextField(blank=True)
    
    # Disposal Information
    disposal_date = models.DateField(null=True, blank=True)
    disposal_reason = models.TextField(blank=True)
    disposal_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Audit Fields
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='assets_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='assets_updated', null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Soft delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assets_deleted')

    class Meta:
        ordering = ['asset_code']
        indexes = [
            models.Index(fields=['asset_code']),
            models.Index(fields=['category']),
            models.Index(fields=['status']),
            models.Index(fields=['location']),
            models.Index(fields=['assigned_to']),
        ]

    def __str__(self):
        return f"{self.asset_code} - {self.asset_name}"

    def save(self, *args, **kwargs):
        # Auto-generate asset code if not provided
        if not self.asset_code:
            self.asset_code = self.generate_asset_code()
        
        # Calculate book value
        self.book_value = self.current_value - self.accumulated_depreciation
        
        # Generate QR code and barcode if not exists
        if not self.qr_code:
            self.generate_qr_code()
        if not self.barcode:
            self.generate_barcode()
        
        super().save(*args, **kwargs)

    def generate_asset_code(self):
        """Generate unique asset code"""
        prefix = "AST"
        timestamp = timezone.now().strftime("%Y%m")
        # Get count of assets for this month
        count = Asset.objects.filter(
            created_at__year=timezone.now().year,
            created_at__month=timezone.now().month
        ).count() + 1
        return f"{prefix}{timestamp}{count:04d}"

    def generate_qr_code(self):
        """Generate QR code for the asset"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(f"Asset: {self.asset_code}\nName: {self.asset_name}\nLocation: {self.location}")
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        filename = f"qr_{self.asset_code}.png"
        self.qr_code.save(filename, ContentFile(buffer.getvalue()), save=False)

    def generate_barcode(self):
        """Generate barcode for the asset"""
        # Use Code128 format for the asset code
        code128 = barcode.get('code128', self.asset_code, writer=ImageWriter())
        buffer = BytesIO()
        code128.write(buffer)
        filename = f"barcode_{self.asset_code}.png"
        self.barcode.save(filename, ContentFile(buffer.getvalue()), save=False)

    def calculate_depreciation(self, as_of_date=None):
        """Calculate depreciation as of a specific date"""
        if as_of_date is None:
            as_of_date = timezone.now().date()
        
        if self.depreciation_method.method == 'none':
            return 0
        
        # Calculate years since purchase
        years_elapsed = (as_of_date - self.purchase_date).days / 365.25
        
        if years_elapsed <= 0:
            return 0
        
        if self.depreciation_method.method == 'straight_line':
            annual_depreciation = (self.purchase_value - self.salvage_value) / self.useful_life_years
            total_depreciation = annual_depreciation * min(years_elapsed, self.useful_life_years)
            return min(total_depreciation, self.purchase_value - self.salvage_value)
        
        # Add other depreciation methods as needed
        return 0

    def get_status_color(self):
        """Get the color for the status"""
        return self.status.color if self.status else '#007bff'


class AssetMovement(models.Model):
    """Track asset movements between locations"""
    MOVEMENT_TYPES = [
        ('transfer', 'Transfer'),
        ('assignment', 'Assignment'),
        ('return', 'Return'),
        ('disposal', 'Disposal'),
    ]

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    from_location = models.ForeignKey(AssetLocation, on_delete=models.PROTECT, related_name='movements_from', null=True, blank=True)
    to_location = models.ForeignKey(AssetLocation, on_delete=models.PROTECT, related_name='movements_to', null=True, blank=True)
    from_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='asset_movements_from')
    to_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='asset_movements_to')
    movement_date = models.DateTimeField(default=timezone.now)
    reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-movement_date']

    def __str__(self):
        return f"{self.asset.asset_code} - {self.get_movement_type_display()}"


class AssetMaintenance(models.Model):
    """Track asset maintenance records"""
    MAINTENANCE_TYPES = [
        ('preventive', 'Preventive'),
        ('corrective', 'Corrective'),
        ('emergency', 'Emergency'),
        ('inspection', 'Inspection'),
    ]

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='maintenance_records')
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPES)
    maintenance_date = models.DateField()
    description = models.TextField()
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    performed_by = models.CharField(max_length=100, blank=True)
    next_maintenance_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-maintenance_date']

    def __str__(self):
        return f"{self.asset.asset_code} - {self.get_maintenance_type_display()} - {self.maintenance_date}" 