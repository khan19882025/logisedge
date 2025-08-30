from django.db import models
from django.contrib.auth.models import User

class CustomerType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Customer Type'
        verbose_name_plural = 'Customer Types'
    
    def __str__(self):
        return self.name

class Customer(models.Model):
    # Basic Information
    customer_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    customer_name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    mobile = models.CharField(max_length=20, blank=True)
    fax = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    customer_types = models.ManyToManyField(CustomerType, blank=True)
    salesman = models.ForeignKey('salesman.Salesman', on_delete=models.SET_NULL, null=True, blank=True, related_name='customers')
    industry = models.CharField(max_length=100, blank=True)
    tax_number = models.CharField(max_length=50, blank=True)
    registration_number = models.CharField(max_length=50, blank=True)
    
    # Addresses
    billing_address = models.TextField(blank=True)
    billing_city = models.CharField(max_length=100, blank=True)
    billing_state = models.CharField(max_length=100, blank=True)
    billing_country = models.CharField(max_length=100, blank=True)
    billing_postal_code = models.CharField(max_length=20, blank=True)
    
    shipping_address = models.TextField(blank=True)
    shipping_city = models.CharField(max_length=100, blank=True)
    shipping_state = models.CharField(max_length=100, blank=True)
    shipping_country = models.CharField(max_length=100, blank=True)
    shipping_postal_code = models.CharField(max_length=20, blank=True)
    
    # Financial
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    payment_terms = models.CharField(max_length=100, blank=True)
    currency = models.CharField(max_length=3, default='AED')
    tax_exempt = models.BooleanField(default=False)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Customer Portal
    portal_username = models.CharField(max_length=50, unique=True, null=True, blank=True)
    portal_password = models.CharField(max_length=128, blank=True)
    portal_active = models.BooleanField(default=False)
    portal_last_login = models.DateTimeField(null=True, blank=True)
    
    # System fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='customers_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='customers_updated')
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['customer_name']
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
    
    def __str__(self):
        return f"{self.customer_code} - {self.customer_name}"
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('customer:customer_detail', kwargs={'pk': self.pk})
    
    def save(self, *args, **kwargs):
        # Handle customer_code generation and unique constraint
        if not self.customer_code:
            # Set to None to avoid unique constraint issues with blank strings
            self.customer_code = None
        
        # Save the customer
        super().save(*args, **kwargs)
    
    def generate_customer_code(self):
        """Generate customer code based on primary customer type and sequence"""
        # Get the first customer type (primary type)
        primary_type = self.customer_types.first()
        if primary_type:
            type_prefix = primary_type.code[:3].upper()
        else:
            type_prefix = "CUS"  # Default prefix
        
        # Find the highest number for this exact prefix
        import re
        pattern = rf"^{re.escape(type_prefix)}(\d+)$"
        
        customers_with_prefix = Customer.objects.filter(
            customer_code__regex=pattern
        ).exclude(pk=self.pk if self.pk else None)
        
        max_number = 0
        for customer in customers_with_prefix:
            if customer.customer_code:
                try:
                    number = int(customer.customer_code[len(type_prefix):])
                    max_number = max(max_number, number)
                except ValueError:
                    continue
        
        new_number = max_number + 1
        
        # Generate unique code and check for conflicts
        while True:
            new_code = f"{type_prefix}{new_number:04d}"
            if not Customer.objects.filter(customer_code=new_code).exclude(pk=self.pk if self.pk else None).exists():
                return new_code
            new_number += 1
    
    def get_customer_types_display(self):
        """Get comma-separated list of customer types"""
        return ", ".join([ct.name for ct in self.customer_types.all()])
