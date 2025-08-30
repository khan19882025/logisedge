from django.db import models
from django.contrib.auth.models import User

class Service(models.Model):
    SERVICE_TYPE_CHOICES = [
        ('freight', 'Freight'),
        ('customs', 'Customs Clearance'),
        ('warehousing', 'Warehousing'),
        ('transportation', 'Transportation'),
        ('packaging', 'Packaging'),
        ('consulting', 'Consulting'),
        ('other', 'Other'),
    ]
    
    CURRENCY_CHOICES = [
        ('AED', 'AED (UAE Dirham)'),
        ('USD', 'USD (US Dollar)'),
        ('EUR', 'EUR (Euro)'),
        ('SAR', 'SAR (Saudi Riyal)'),
        ('INR', 'INR (Indian Rupee)'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    ]
    
    # Basic Information
    service_code = models.CharField(max_length=20, unique=True, blank=True)
    service_name = models.CharField(max_length=200)
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPE_CHOICES, default='other')
    description = models.TextField(blank=True)
    short_description = models.CharField(max_length=500, blank=True)
    
    # Pricing
    base_price = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    sale_price = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    cost_price = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='AED')
    pricing_model = models.CharField(max_length=50, blank=True)  # Fixed, Variable, Per Unit, etc.
    has_vat = models.BooleanField(default=True, verbose_name="Has VAT")  # Whether this service is subject to VAT
    
    # Service Details
    duration = models.CharField(max_length=100, blank=True)  # Estimated duration
    requirements = models.TextField(blank=True)  # Service requirements
    deliverables = models.TextField(blank=True)  # What the service delivers
    
    # Status and Configuration
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_featured = models.BooleanField(default=False)
    is_available_online = models.BooleanField(default=True)
    
    # System fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='services_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='services_updated')
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['service_name']
        verbose_name = 'Service'
        verbose_name_plural = 'Services'
    
    def __str__(self):
        return f"{self.service_code} - {self.service_name}"
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('service:service_detail', kwargs={'pk': self.pk})
    
    def save(self, *args, **kwargs):
        # Generate service code if not provided
        if not self.service_code:
            self.service_code = self.generate_service_code()
        super().save(*args, **kwargs)
    
    def generate_service_code(self):
        """Generate service code based on service type and sequence"""
        # Get the first 3 letters of service type
        type_prefix = self.service_type[:3].upper()
        
        # Find the last service with this type
        last_service = Service.objects.filter(
            service_type=self.service_type
        ).order_by('-service_code').first()
        
        if last_service and last_service.service_code:
            # Extract the number part and increment
            try:
                last_number = int(last_service.service_code[3:])
                new_number = last_number + 1
            except ValueError:
                new_number = 1
        else:
            new_number = 1
        
        # Format: TYPE0001, TYPE0002, etc.
        return f"{type_prefix}{new_number:04d}"
