from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class RFUser(models.Model):
    """RF Scanner User Profile"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='rf_profile')
    employee_id = models.CharField(max_length=50, unique=True)
    department = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.employee_id}"


class ScanSession(models.Model):
    """RF Scanner Session"""
    SESSION_TYPES = [
        ('inbound', 'Inbound'),
        ('outbound', 'Outbound'),
        ('location_change', 'Location Change'),
        ('physical_check', 'Physical Check'),
    ]
    
    user = models.ForeignKey(RFUser, on_delete=models.CASCADE)
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.employee_id} - {self.get_session_type_display()} - {self.start_time}"


class ScanRecord(models.Model):
    """Individual Scan Record"""
    session = models.ForeignKey(ScanSession, on_delete=models.CASCADE, related_name='scans')
    barcode = models.CharField(max_length=100)
    item_code = models.CharField(max_length=50, blank=True)
    item_name = models.CharField(max_length=200, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    location = models.CharField(max_length=100, blank=True)
    scan_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default='scanned')
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.barcode} - {self.scan_time}"


class Location(models.Model):
    """Warehouse Locations"""
    location_code = models.CharField(max_length=50, unique=True)
    location_name = models.CharField(max_length=200)
    location_type = models.CharField(max_length=50)  # Aisle, Rack, Bin, etc.
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.location_code} - {self.location_name}"


class Item(models.Model):
    """Items that can be scanned"""
    item_code = models.CharField(max_length=50, unique=True)
    item_name = models.CharField(max_length=200)
    barcode = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    unit = models.CharField(max_length=20, default='PCS')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.item_code} - {self.item_name}"
