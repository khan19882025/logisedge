from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone


class Salesman(models.Model):
    """Salesman model for managing sales personnel"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('on_leave', 'On Leave'),
        ('terminated', 'Terminated'),
    ]
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    # Basic Information
    salesman_code = models.CharField(
        max_length=10, 
        unique=True,
        validators=[RegexValidator(r'^[A-Z0-9]+$', 'Salesman code must contain only uppercase letters and numbers.')],
        help_text="Unique salesman code (e.g., SAL001, SAL002)"
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    
    # Personal Information
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    
    # Employment Information
    hire_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    department = models.CharField(max_length=100, blank=True)
    position = models.CharField(max_length=100, blank=True)
    manager = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='subordinates'
    )
    
    # Commission and Performance
    commission_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        help_text="Commission rate as percentage (e.g., 5.00 for 5%)"
    )
    target_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00,
        help_text="Monthly sales target amount"
    )
    
    # Additional Information
    notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='salesmen_created'
    )
    updated_by = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='salesmen_updated'
    )
    
    class Meta:
        ordering = ['first_name', 'last_name']
        verbose_name = 'Salesman'
        verbose_name_plural = 'Salesmen'
        db_table = 'salesman'
    
    def __str__(self):
        return f"{self.salesman_code} - {self.get_full_name()}"
    
    def get_full_name(self):
        """Return the full name of the salesman"""
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_full_address(self):
        """Return the complete address"""
        address_parts = []
        if self.address:
            address_parts.append(self.address)
        if self.city:
            address_parts.append(self.city)
        if self.state:
            address_parts.append(self.state)
        if self.country:
            address_parts.append(self.country)
        if self.postal_code:
            address_parts.append(self.postal_code)
        return ', '.join(address_parts)
    
    @property
    def is_active(self):
        """Check if salesman is active"""
        return self.status == 'active'
    
    @property
    def display_name(self):
        """Return display name with code"""
        return f"{self.salesman_code} - {self.get_full_name()}"
    
    @property
    def years_of_service(self):
        """Calculate years of service"""
        if self.hire_date:
            today = timezone.now().date()
            return (today - self.hire_date).days // 365
        return 0
