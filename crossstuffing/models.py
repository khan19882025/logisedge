from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from job.models import Job, JobCargo
from customer.models import Customer
from facility.models import Facility
from port.models import Port
from django.contrib.auth.models import User


class CrossStuffing(models.Model):
    """Model for managing cross stuffing operations"""
    
    CROSS_STUFFING_STATUS = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Document Type Choices
    DOCUMENT_TYPE_CHOICES = [
        ('TOO', 'TOO'),
        ('TRANSIT_OUT', 'Transit Out'),
        ('IMPORT_LOCAL', 'Import to local from FZ'),
    ]
    
    # Payment Mode Choices
    PAYMENT_MODE_CHOICES = [
        ('CASH', 'Cash'),
        ('BANK_TT', 'Bank TT'),
        ('CREDIT', 'Credit'),
    ]
    
    # Ship Mode Choices
    SHIP_MODE_CHOICES = [
        ('SEA', 'Sea'),
        ('AIR', 'Air'),
        ('LAND', 'Land'),
    ]
    
    # Country Choices
    COUNTRY_CHOICES = [
        ('UAE', 'United Arab Emirates'),
        ('SAU', 'Saudi Arabia'),
        ('KWT', 'Kuwait'),
        ('QAT', 'Qatar'),
        ('BHR', 'Bahrain'),
        ('OMN', 'Oman'),
        ('USA', 'United States'),
        ('GBR', 'United Kingdom'),
        ('DEU', 'Germany'),
        ('FRA', 'France'),
        ('ITA', 'Italy'),
        ('ESP', 'Spain'),
        ('NLD', 'Netherlands'),
        ('BEL', 'Belgium'),
        ('CHE', 'Switzerland'),
        ('AUT', 'Austria'),
        ('SWE', 'Sweden'),
        ('NOR', 'Norway'),
        ('DNK', 'Denmark'),
        ('FIN', 'Finland'),
        ('CHN', 'China'),
        ('JPN', 'Japan'),
        ('KOR', 'South Korea'),
        ('IND', 'India'),
        ('PAK', 'Pakistan'),
        ('BGD', 'Bangladesh'),
        ('LKA', 'Sri Lanka'),
        ('THA', 'Thailand'),
        ('VNM', 'Vietnam'),
        ('MYS', 'Malaysia'),
        ('SGP', 'Singapore'),
        ('IDN', 'Indonesia'),
        ('PHL', 'Philippines'),
        ('AUS', 'Australia'),
        ('NZL', 'New Zealand'),
        ('CAN', 'Canada'),
        ('MEX', 'Mexico'),
        ('BRA', 'Brazil'),
        ('ARG', 'Argentina'),
        ('CHL', 'Chile'),
        ('COL', 'Colombia'),
        ('PER', 'Peru'),
        ('VEN', 'Venezuela'),
        ('ZAF', 'South Africa'),
        ('EGY', 'Egypt'),
        ('MAR', 'Morocco'),
        ('TUN', 'Tunisia'),
        ('ALG', 'Algeria'),
        ('LBY', 'Libya'),
        ('SDN', 'Sudan'),
        ('ETH', 'Ethiopia'),
        ('KEN', 'Kenya'),
        ('NGA', 'Nigeria'),
        ('GHA', 'Ghana'),
        ('CIV', 'Ivory Coast'),
        ('SEN', 'Senegal'),
        ('MLI', 'Mali'),
        ('BFA', 'Burkina Faso'),
        ('NER', 'Niger'),
        ('TCD', 'Chad'),
        ('CMR', 'Cameroon'),
        ('GAB', 'Gabon'),
        ('COG', 'Republic of the Congo'),
        ('COD', 'Democratic Republic of the Congo'),
        ('CAF', 'Central African Republic'),
        ('TZA', 'Tanzania'),
        ('UGA', 'Uganda'),
        ('RWA', 'Rwanda'),
        ('BDI', 'Burundi'),
        ('MWI', 'Malawi'),
        ('ZMB', 'Zambia'),
        ('ZWE', 'Zimbabwe'),
        ('BWA', 'Botswana'),
        ('NAM', 'Namibia'),
        ('LSO', 'Lesotho'),
        ('SWZ', 'Eswatini'),
        ('MDG', 'Madagascar'),
        ('MUS', 'Mauritius'),
        ('SYC', 'Seychelles'),
        ('COM', 'Comoros'),
        ('DJI', 'Djibouti'),
        ('SOM', 'Somalia'),
        ('ERI', 'Eritrea'),
        ('SSD', 'South Sudan'),
        ('RUS', 'Russia'),
        ('UKR', 'Ukraine'),
        ('BLR', 'Belarus'),
        ('POL', 'Poland'),
        ('CZE', 'Czech Republic'),
        ('SVK', 'Slovakia'),
        ('HUN', 'Hungary'),
        ('ROU', 'Romania'),
        ('BGR', 'Bulgaria'),
        ('HRV', 'Croatia'),
        ('SVN', 'Slovenia'),
        ('BIH', 'Bosnia and Herzegovina'),
        ('SRB', 'Serbia'),
        ('MNE', 'Montenegro'),
        ('MKD', 'North Macedonia'),
        ('ALB', 'Albania'),
        ('GRC', 'Greece'),
        ('TUR', 'Turkey'),
        ('CYP', 'Cyprus'),
        ('MLT', 'Malta'),
        ('ISL', 'Iceland'),
        ('IRL', 'Ireland'),
        ('PRT', 'Portugal'),
        ('LUX', 'Luxembourg'),
        ('LIE', 'Liechtenstein'),
        ('MCO', 'Monaco'),
        ('AND', 'Andorra'),
        ('SMR', 'San Marino'),
        ('VAT', 'Vatican City'),
    ]
    
    # Basic Information
    cs_number = models.CharField(max_length=20, unique=True, blank=True, verbose_name="CS Number")
    title = models.CharField(max_length=200, blank=True, verbose_name="Title")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    
    # Related Records
    job = models.ForeignKey(Job, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Related Job")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="Customer")
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Facility")
    
    # Left section fields
    document_type = models.CharField(
        max_length=20, 
        choices=DOCUMENT_TYPE_CHOICES,
        blank=True, 
        verbose_name="Document Type"
    )
    bill_to = models.CharField(max_length=200, blank=True, verbose_name="Bill To")
    bill_to_customer = models.ForeignKey(
        Customer, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='crossstuffing_as_bill_to',
        verbose_name="Bill To Customer"
    )
    bill_to_address = models.TextField(blank=True, verbose_name="Bill to Address")
    deliver_to_customer = models.ForeignKey(
        Customer, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='crossstuffing_as_deliver_to',
        verbose_name="Deliver To Customer"
    )
    deliver_to_address = models.TextField(blank=True, verbose_name="Deliver to Address")
    port_of_loading = models.ForeignKey(
        Port, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='loading_crossstuffing',
        verbose_name="Port of Loading"
    )
    discharge_port = models.ForeignKey(
        Port, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='discharge_crossstuffing',
        verbose_name="Discharge Port"
    )
    
    # Right section fields
    cs_date = models.DateField(default=timezone.now, verbose_name="Date")
    payment_mode = models.CharField(
        max_length=20,
        choices=PAYMENT_MODE_CHOICES,
        blank=True,
        verbose_name="Payment Mode"
    )
    container_number = models.CharField(max_length=20, verbose_name="Container")
    bl_number = models.CharField(max_length=100, blank=True, verbose_name="BL Number")
    boe = models.CharField(max_length=50, blank=True, verbose_name="BOE")
    exit_point = models.ForeignKey(
        Port, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='exit_crossstuffing',
        verbose_name="Exit Point"
    )
    destination = models.CharField(
        max_length=3,
        choices=COUNTRY_CHOICES,
        blank=True,
        verbose_name="Destination"
    )
    ship_mode = models.CharField(
        max_length=20,
        choices=SHIP_MODE_CHOICES,
        blank=True,
        verbose_name="Ship Mode"
    )
    ship_date = models.DateField(blank=True, null=True, verbose_name="Ship Date")
    vessel = models.CharField(max_length=100, blank=True, verbose_name="Vessel")
    voyage = models.CharField(max_length=50, blank=True, verbose_name="Voyage")
    delivery_terms = models.CharField(max_length=100, blank=True, verbose_name="Delivery Terms")
    
    # Additional dates
    scheduled_date = models.DateField(blank=True, null=True, verbose_name="Scheduled Date")
    completed_date = models.DateField(blank=True, null=True, verbose_name="Completed Date")
    
    # Status and Priority
    status = models.CharField(max_length=20, choices=CROSS_STUFFING_STATUS, default='pending', verbose_name="Status")
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], default='medium', verbose_name="Priority")
    
    # Container Information
    container_size = models.CharField(max_length=10, choices=[
        ('20', '20ft'),
        ('40', '40ft'),
        ('40HC', '40ft HC'),
        ('45', '45ft'),
    ], blank=True, verbose_name="Container Size")
    container_type = models.CharField(max_length=20, choices=[
        ('GP', 'General Purpose'),
        ('RF', 'Reefer'),
        ('OT', 'Open Top'),
        ('FR', 'Flat Rack'),
        ('TK', 'Tank'),
    ], blank=True, verbose_name="Container Type")
    
    # Cargo Details
    cargo_description = models.TextField(blank=True, verbose_name="Cargo Description")
    total_packages = models.IntegerField(validators=[MinValueValidator(1)], blank=True, null=True, verbose_name="Total Packages")
    total_weight = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Total Weight (KGS)")
    total_volume = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Total Volume (CBM)")
    
    # Charges
    charges = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Charges")
    currency = models.CharField(max_length=3, choices=[
        ('AED', 'AED'),
        ('USD', 'USD'),
        ('EUR', 'EUR'),
    ], default='AED', verbose_name="Currency")
    
    # Notes and Additional Info
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")
    special_instructions = models.TextField(blank=True, null=True, verbose_name="Special Instructions")
    
    # Audit Fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_crossstuffing', verbose_name="Created By")
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_crossstuffing', verbose_name="Assigned To")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    class Meta:
        verbose_name = "Cross Stuffing"
        verbose_name_plural = "Cross Stuffings"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.cs_number} - {self.title}"
    
    def save(self, *args, **kwargs):
        # Auto-generate CS number if not provided
        if not self.cs_number:
            last_cs = CrossStuffing.objects.order_by('-id').first()
            if last_cs:
                last_number = int(last_cs.cs_number.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            self.cs_number = f"CS-{timezone.now().year}-{new_number:04d}"
        
        super().save(*args, **kwargs)
    
    @property
    def is_overdue(self):
        """Check if the cross stuffing is overdue"""
        if self.status in ['completed', 'cancelled']:
            return False
        if self.scheduled_date is None:
            return False
        return self.scheduled_date < timezone.now().date()
    
    @property
    def is_completed(self):
        """Check if the cross stuffing is completed"""
        return self.status == 'completed'
    
    def complete(self):
        """Mark the cross stuffing as completed"""
        self.status = 'completed'
        self.completed_date = timezone.now().date()
        self.save()


class CrossStuffingCargo(models.Model):
    """Model for linking CrossStuffing to cargo items"""
    crossstuffing = models.ForeignKey(CrossStuffing, on_delete=models.CASCADE, related_name='cargo_items')
    job_cargo = models.ForeignKey(JobCargo, on_delete=models.CASCADE, related_name='crossstuffing_items')
    
    # Additional fields for cross stuffing specific data
    quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Quantity")
    rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Rate")
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Amount")
    net_weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Net Weight")
    gross_weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Gross Weight")
    ed_number = models.CharField(max_length=50, blank=True, verbose_name="ED Number")
    remark = models.TextField(blank=True, verbose_name="Remark")
    
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    class Meta:
        verbose_name = "Cross Stuffing Cargo Item"
        verbose_name_plural = "Cross Stuffing Cargo Items"
        unique_together = ['crossstuffing', 'job_cargo']
    
    def __str__(self):
        return f"{self.crossstuffing.cs_number} - {self.job_cargo.item_code}"
    
    @property
    def job_code(self):
        return self.job_cargo.job.job_code if self.job_cargo.job else ''
    
    @property
    def item_code(self):
        return self.job_cargo.item_code
    
    @property
    def item_name(self):
        return self.job_cargo.item.item_name if self.job_cargo.item else ''
    
    @property
    def hs_code(self):
        return self.job_cargo.hs_code
    
    @property
    def unit(self):
        return self.job_cargo.unit
    
    @property
    def coo(self):
        return self.job_cargo.coo


class CrossStuffingSummary(models.Model):
    """Model for storing CS Summary data"""
    crossstuffing = models.ForeignKey(CrossStuffing, on_delete=models.CASCADE, related_name='summary_items')
    job_no = models.CharField(max_length=50, blank=True, verbose_name="Job No")
    items = models.CharField(max_length=200, blank=True, verbose_name="Items")
    qty = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Qty")
    imp_cntr = models.CharField(max_length=50, blank=True, verbose_name="Imp CNTR")
    size = models.CharField(max_length=20, blank=True, verbose_name="Size")
    seal = models.CharField(max_length=50, blank=True, verbose_name="Seal")
    exp_cntr = models.CharField(max_length=50, blank=True, verbose_name="Exp CNTR")
    exp_size = models.CharField(max_length=20, blank=True, verbose_name="Exp Size")
    exp_seal = models.CharField(max_length=50, blank=True, verbose_name="Exp Seal")
    remarks = models.TextField(blank=True, verbose_name="Remarks")
    
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    class Meta:
        verbose_name = "Cross Stuffing Summary Item"
        verbose_name_plural = "Cross Stuffing Summary Items"
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.crossstuffing.cs_number} - {self.job_no} - {self.items}" 