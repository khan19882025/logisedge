import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal


class HBL(models.Model):
    """Model for House Bill of Lading documents"""
    
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Original', 'Original'),
        ('SEAWAY BILL', 'SEAWAY BILL'),
    ]
    
    TERMS_CHOICES = [
        ('FCL/FCL', 'FCL/FCL'),
        ('FCL/LCL', 'FCL/LCL'),
        ('LCL/LCL', 'LCL/LCL'),
        ('LCL/FCL', 'LCL/FCL'),
        ('RO-RO', 'RO-RO'),
        ('Break Bulk', 'Break Bulk'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic Information
    hbl_number = models.CharField(max_length=50, unique=True, help_text="Unique HBL number")
    mbl_number = models.CharField(max_length=50, blank=True, help_text="Master Bill of Lading number")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    
    # Dates
    shipped_on_board = models.DateField(null=True, blank=True)
    issue_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Parties
    shipper = models.ForeignKey('customer.Customer', on_delete=models.CASCADE, related_name='hbls_as_shipper', null=True, blank=True)
    consignee = models.ForeignKey('customer.Customer', on_delete=models.CASCADE, related_name='hbls_as_consignee', null=True, blank=True)
    notify_party = models.ForeignKey('customer.Customer', on_delete=models.CASCADE, related_name='hbls_as_notify_party', null=True, blank=True)
    
    # Shipping Information
    pre_carriage_by = models.CharField(max_length=100, default='BY SEA')
    place_of_receipt = models.CharField(max_length=200, blank=True)
    ocean_vessel = models.CharField(max_length=200, blank=True)
    port_of_loading = models.CharField(max_length=200, blank=True)
    port_of_discharge = models.CharField(max_length=200, blank=True)
    place_of_delivery = models.CharField(max_length=200, blank=True)
    terms = models.CharField(max_length=20, choices=TERMS_CHOICES, blank=True)
    
    # Cargo Information
    description_of_goods = models.TextField(blank=True)
    number_of_packages = models.IntegerField(default=0)
    package_type = models.CharField(max_length=50, blank=True)
    gross_weight = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Weight in KGS")
    measurement = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Volume in CBM")
    
    # Freight Information
    freight_prepaid = models.BooleanField(default=False)
    freight_collect = models.BooleanField(default=False)
    freight_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=3, default='USD')
    
    # Additional Information
    remarks = models.TextField(blank=True)
    special_instructions = models.TextField(blank=True)
    
    # Audit fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_hbls')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_hbls')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'House Bill of Lading'
        verbose_name_plural = 'House Bills of Lading'
    
    def generate_hbl_number(self):
        """Generate unique HBL number in the format AFS-YEAR-AEJEA-00001"""
        import datetime
        current_year = datetime.datetime.now().year
        prefix = f'AFS-{current_year}-AEJEA-'

        # Get the last HBL number for the current year with the new prefix
        last_hbl = (
            HBL.objects.filter(hbl_number__startswith=prefix)
            .order_by('hbl_number')
            .last()
        )

        if last_hbl:
            # Extract the sequence number from the last HBL
            try:
                last_sequence_str = last_hbl.hbl_number.rsplit('-', 1)[-1]
                last_sequence = int(last_sequence_str)
                new_sequence = last_sequence + 1
            except (ValueError, IndexError):
                new_sequence = 1
        else:
            new_sequence = 1

        # Five-digit sequence as per requested 00001 format
        return f'{prefix}{new_sequence:05d}'
    
    def save(self, *args, **kwargs):
        # Generate HBL number if not provided
        if not self.hbl_number:
            self.hbl_number = self.generate_hbl_number()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"HBL-{self.hbl_number}"
    
    @property
    def total_cargo_weight(self):
        """Calculate total weight from cargo items"""
        return self.cargo_items.aggregate(
            total=models.Sum('gross_weight')
        )['total'] or Decimal('0.00')
    
    @property
    def total_cargo_measurement(self):
        """Calculate total measurement from cargo items"""
        return self.cargo_items.aggregate(
            total=models.Sum('measurement')
        )['total'] or Decimal('0.00')
    
    @property
    def total_packages(self):
        """Calculate total packages from cargo items"""
        return self.cargo_items.aggregate(
            total=models.Sum('number_of_packages')
        )['total'] or 0


class HBLItem(models.Model):
    """Model for individual cargo items in an HBL"""
    
    CONTAINER_SIZE_CHOICES = [
        ('20STD', '20STD'),
        ('40STD', '40STD'),
        ('40HC', '40HC'),
        ('45HC', '45HC'),
    ]
    
    PACKAGE_TYPE_CHOICES = [
        ('CTN', 'CTN'),
        ('PLT', 'PLT'),
        ('CASE', 'CASE'),
        ('PCS', 'PCS'),
        ('OTHER', 'OTHER'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hbl = models.ForeignKey(HBL, on_delete=models.CASCADE, related_name='cargo_items')
    
    # Container Information
    container_no = models.CharField(max_length=50, blank=True)
    container_size = models.CharField(max_length=10, choices=CONTAINER_SIZE_CHOICES, blank=True)
    seal_no = models.CharField(max_length=50, blank=True)
    
    # Cargo Details
    number_of_packages = models.IntegerField(validators=[MinValueValidator(1)], default=1)
    package_type = models.CharField(max_length=20, choices=PACKAGE_TYPE_CHOICES, blank=True)
    custom_package_type = models.CharField(max_length=50, blank=True)
    description = models.TextField()
    
    # Weights and Measurements
    gross_weight = models.DecimalField(max_digits=10, decimal_places=2, help_text="Weight in KGS")
    net_weight = models.DecimalField(max_digits=10, decimal_places=2, help_text="Weight in KGS")
    measurement = models.DecimalField(max_digits=10, decimal_places=2, help_text="Volume in CBM")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'HBL Cargo Item'
        verbose_name_plural = 'HBL Cargo Items'
    
    def __str__(self):
        return f"{self.container_no} - {self.description[:50]}"


class HBLCharge(models.Model):
    """Model for charges associated with HBL"""
    
    CHARGE_TYPE_CHOICES = [
        ('freight', 'Freight'),
        ('thc', 'THC'),
        ('doc_fee', 'Documentation Fee'),
        ('cfs', 'CFS'),
        ('customs', 'Customs'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hbl = models.ForeignKey(HBL, on_delete=models.CASCADE, related_name='charges')
    
    charge_type = models.CharField(max_length=20, choices=CHARGE_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'HBL Charge'
        verbose_name_plural = 'HBL Charges'
    
    def __str__(self):
        return f"{self.get_charge_type_display()} - {self.amount} {self.currency}"


class HBLHistory(models.Model):
    """Model for tracking changes to HBL"""
    
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('status_changed', 'Status Changed'),
        ('cargo_added', 'Cargo Added'),
        ('cargo_updated', 'Cargo Updated'),
        ('cargo_deleted', 'Cargo Deleted'),
        ('charges_added', 'Charges Added'),
        ('charges_updated', 'Charges Updated'),
        ('charges_deleted', 'Charges Deleted'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hbl = models.ForeignKey(HBL, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    old_values = models.JSONField(blank=True, null=True)
    new_values = models.JSONField(blank=True, null=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'HBL History'
        verbose_name_plural = 'HBL History'
    
    def __str__(self):
        return f"{self.hbl.hbl_number} - {self.action} - {self.timestamp}"


class HBLReport(models.Model):
    """Model for storing generated HBL reports"""
    
    REPORT_TYPE_CHOICES = [
        ('summary', 'Summary Report'),
        ('detailed', 'Detailed Report'),
        ('custom', 'Custom Report'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    filters = models.JSONField(default=dict, help_text="Report filters applied")
    report_data = models.JSONField(default=dict, help_text="Stored report data")
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-generated_at']
        verbose_name = 'HBL Report'
        verbose_name_plural = 'HBL Reports'
    
    def __str__(self):
        return f"{self.report_name} - {self.report_type}"
