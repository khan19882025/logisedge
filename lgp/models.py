from django.db import models
from django.contrib.auth.models import User
from customer.models import Customer
from facility.models import Facility
from decimal import Decimal


class PackageType(models.Model):
    """Model for package types used in LGP items"""
    
    name = models.CharField(max_length=50, unique=True, verbose_name='Package Type Name')
    code = models.CharField(max_length=20, unique=True, verbose_name='Package Code')
    description = models.TextField(blank=True, verbose_name='Description')
    is_active = models.BooleanField(default=True, verbose_name='Active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Package Type'
        verbose_name_plural = 'Package Types'
    
    def __str__(self):
        return self.name


class LGP(models.Model):
    """Model for LGP (Local Goods Permit) documents"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('dispatched', 'Dispatched'),
        ('cancelled', 'Cancelled'),
    ]
    
    PURPOSE_OF_ENTRY_CHOICES = [
        ('storage', 'Storage'),
        ('office_user', 'Office User'),
        ('export', 'Export'),
    ]
    
    PACKAGE_TYPE_CHOICES = [
        ('box', 'Box'),
        ('carton', 'Carton'),
        ('pallet', 'Pallet'),
        ('bag', 'Bag'),
        ('drum', 'Drum'),
        ('container', 'Container'),
        ('bundle', 'Bundle'),
        ('roll', 'Roll'),
        ('piece', 'Piece'),
        ('other', 'Other'),
    ]
    
    # Auto-generated fields
    lgp_number = models.CharField(max_length=50, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_lgps')
    
    # Top Left fields
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='lgps')
    dpw_ref_no = models.CharField(max_length=100, verbose_name='DPW Ref No')
    document_date = models.DateField()
    document_validity_date = models.DateField()
    warehouse = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='lgps')
    
    # Top Right fields
    free_zone_company_name = models.CharField(max_length=200)
    local_company_name = models.CharField(max_length=200)
    goods_coming_from = models.CharField(max_length=200)
    purpose_of_entry = models.CharField(max_length=20, choices=PURPOSE_OF_ENTRY_CHOICES)
    
    # Status and workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    dispatch_date = models.DateTimeField(null=True, blank=True)
    dispatched_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='dispatched_lgps')
    
    # Additional fields
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'LGP'
        verbose_name_plural = 'LGPs'
    
    def __str__(self):
        if self.customer_id and hasattr(self, 'customer'):
            try:
                return f"{self.lgp_number} - {self.customer.customer_name}"
            except:
                return f"{self.lgp_number} - Customer ID: {self.customer_id}"
        return f"{self.lgp_number or 'New LGP'} - No Customer"
    
    def save(self, *args, **kwargs):
        if not self.lgp_number:
            # Generate LGP number
            from django.utils import timezone
            year = timezone.now().year
            last_lgp = LGP.objects.filter(
                lgp_number__startswith=f'LGP-{year}'
            ).order_by('-lgp_number').first()
            
            if last_lgp:
                last_number = int(last_lgp.lgp_number.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.lgp_number = f'LGP-{year}-{new_number:04d}'
        
        super().save(*args, **kwargs)
    
    @property
    def total_quantity(self):
        return sum(item.quantity for item in self.items.all())
    
    @property
    def total_weight(self):
        return sum(item.weight for item in self.items.all())
    
    @property
    def total_volume(self):
        return sum(item.volume or 0 for item in self.items.all())
    
    @property
    def total_value(self):
        return sum(item.value for item in self.items.all())


class LGPItem(models.Model):
    """LGP Item model for the editable table lines"""
    
    # Keep legacy choices for backward compatibility
    PACKAGE_TYPE_CHOICES = [
        ('box', 'Box'),
        ('carton', 'Carton'),
        ('pallet', 'Pallet'),
        ('bag', 'Bag'),
        ('drum', 'Drum'),
        ('container', 'Container'),
        ('bundle', 'Bundle'),
        ('roll', 'Roll'),
        ('piece', 'Piece'),
        ('other', 'Other'),
    ]
    
    lgp = models.ForeignKey(LGP, on_delete=models.CASCADE, related_name='items')
    
    # Item details
    hs_code = models.CharField(max_length=20, verbose_name='HS Code')
    good_description = models.TextField(verbose_name='Good Description')
    marks_and_nos = models.CharField(max_length=200, verbose_name='Marks & Nos', blank=True)
    # Use ForeignKey to PackageType for new implementation
    package_type_new = models.ForeignKey(PackageType, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Package Type')
    # Keep old field for backward compatibility
    package_type = models.CharField(max_length=20, choices=PACKAGE_TYPE_CHOICES, verbose_name='Package Type (Legacy)', blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    weight = models.DecimalField(max_digits=10, decimal_places=3, help_text='Weight in KG')
    volume = models.DecimalField(max_digits=10, decimal_places=3, help_text='Volume in CBM', blank=True, null=True)
    value = models.DecimalField(max_digits=15, decimal_places=2, help_text='Value in currency')
    customs_declaration = models.TextField(blank=True)
    remarks = models.TextField(blank=True)
    
    # Ordering
    line_number = models.PositiveIntegerField(default=1)
    
    class Meta:
        ordering = ['line_number']
        verbose_name = 'LGP Item'
        verbose_name_plural = 'LGP Items'
    
    def __str__(self):
        return f"{self.lgp.lgp_number} - Line {self.line_number}: {self.good_description[:50]}"
    
    @property
    def get_package_type_display(self):
        """Get package type display name, prioritizing new field over legacy"""
        if self.package_type_new:
            return self.package_type_new.name
        elif self.package_type:
            return dict(self.PACKAGE_TYPE_CHOICES).get(self.package_type, self.package_type)
        return ''
    
    @property
    def get_package_type_value(self):
        """Get package type value for forms, prioritizing new field over legacy"""
        if self.package_type_new:
            return self.package_type_new.code
        return self.package_type or ''


class LGPDispatch(models.Model):
    """Dispatch header for one or more LGP items (can span multiple LGPs for a customer)."""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='lgp_dispatches')
    dispatch_date = models.DateField()
    note = models.TextField(blank=True)
    driver_name = models.CharField(max_length=100, blank=True)
    vehicle_no = models.CharField(max_length=50, blank=True)
    mobile_no = models.CharField(max_length=50, blank=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_lgp_dispatches')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'LGP Dispatch'
        verbose_name_plural = 'LGP Dispatches'

    def __str__(self):
        return f"Dispatch {self.id} - {self.customer.customer_name} on {self.dispatch_date}"

    @property
    def total_weight(self):
        return self.items.aggregate(total=models.Sum('weight'))['total'] or Decimal('0.000')

    @property
    def total_value(self):
        return self.items.aggregate(total=models.Sum('value'))['total'] or Decimal('0.00')


class LGPDispatchItem(models.Model):
    """Line item dispatched under a header. Snapshot of LGP item at dispatch time."""
    dispatch = models.ForeignKey(LGPDispatch, on_delete=models.CASCADE, related_name='items')
    lgp = models.ForeignKey(LGP, on_delete=models.CASCADE, related_name='dispatch_items')
    lgp_item = models.ForeignKey(LGPItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='dispatched_rows')

    line_number = models.PositiveIntegerField(default=1)
    hs_code = models.CharField(max_length=20)
    good_description = models.TextField()
    package_type = models.CharField(max_length=20)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    weight = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    value = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['dispatch_id', 'line_number']
        verbose_name = 'LGP Dispatch Item'
        verbose_name_plural = 'LGP Dispatch Items'

    def __str__(self):
        return f"Dispatch {self.dispatch_id} - {self.lgp.lgp_number} line {self.line_number}"
