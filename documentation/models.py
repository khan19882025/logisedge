from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from customer.models import Customer
from port.models import Port


class Documentation(models.Model):
    """Model for storing documentation"""
    
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
        ('', 'Select Country'),
        ('AE', 'United Arab Emirates'),
        ('SA', 'Saudi Arabia'),
        ('IN', 'India'),
        ('US', 'United States'),
        ('CN', 'China'),
        ('GB', 'United Kingdom'),
        ('DE', 'Germany'),
        ('FR', 'France'),
        ('SG', 'Singapore'),
        ('JP', 'Japan'),
        ('AU', 'Australia'),
        ('CA', 'Canada'),
        ('BR', 'Brazil'),
        ('MX', 'Mexico'),
        ('IT', 'Italy'),
        ('ES', 'Spain'),
        ('NL', 'Netherlands'),
        ('KR', 'South Korea'),
        ('RU', 'Russia'),
        ('TR', 'Turkey'),
        ('EG', 'Egypt'),
        ('ZA', 'South Africa'),
        ('TH', 'Thailand'),
        ('MY', 'Malaysia'),
        ('ID', 'Indonesia'),
        ('PH', 'Philippines'),
        ('VN', 'Vietnam'),
        ('BD', 'Bangladesh'),
        ('PK', 'Pakistan'),
        ('LK', 'Sri Lanka'),
        ('KE', 'Kenya'),
        ('NG', 'Nigeria'),
        ('GH', 'Ghana'),
        ('MA', 'Morocco'),
        ('TN', 'Tunisia'),
        ('DZ', 'Algeria'),
        ('LB', 'Lebanon'),
        ('JO', 'Jordan'),
        ('KW', 'Kuwait'),
        ('QA', 'Qatar'),
        ('BH', 'Bahrain'),
        ('OM', 'Oman'),
        ('YE', 'Yemen'),
        ('IQ', 'Iraq'),
        ('IR', 'Iran'),
        ('AF', 'Afghanistan'),
        ('UZ', 'Uzbekistan'),
        ('KZ', 'Kazakhstan'),
        ('KG', 'Kyrgyzstan'),
        ('TJ', 'Tajikistan'),
        ('TM', 'Turkmenistan'),
        ('AZ', 'Azerbaijan'),
        ('GE', 'Georgia'),
        ('AM', 'Armenia'),
        ('CY', 'Cyprus'),
        ('MT', 'Malta'),
        ('GR', 'Greece'),
        ('PT', 'Portugal'),
        ('IE', 'Ireland'),
        ('BE', 'Belgium'),
        ('AT', 'Austria'),
        ('CH', 'Switzerland'),
        ('SE', 'Sweden'),
        ('NO', 'Norway'),
        ('DK', 'Denmark'),
        ('FI', 'Finland'),
        ('PL', 'Poland'),
        ('CZ', 'Czech Republic'),
        ('HU', 'Hungary'),
        ('RO', 'Romania'),
        ('BG', 'Bulgaria'),
        ('HR', 'Croatia'),
        ('SI', 'Slovenia'),
        ('SK', 'Slovakia'),
        ('LT', 'Lithuania'),
        ('LV', 'Latvia'),
        ('EE', 'Estonia'),
        ('LU', 'Luxembourg'),
        ('IS', 'Iceland'),
        ('NZ', 'New Zealand'),
        ('CL', 'Chile'),
        ('AR', 'Argentina'),
        ('PE', 'Peru'),
        ('CO', 'Colombia'),
        ('VE', 'Venezuela'),
        ('EC', 'Ecuador'),
        ('UY', 'Uruguay'),
        ('PY', 'Paraguay'),
        ('BO', 'Bolivia'),
        ('GY', 'Guyana'),
        ('SR', 'Suriname'),
        ('GF', 'French Guiana'),
        ('FK', 'Falkland Islands'),
        ('GS', 'South Georgia'),
        ('AI', 'Anguilla'),
        ('AG', 'Antigua and Barbuda'),
        ('AW', 'Aruba'),
        ('BS', 'Bahamas'),
        ('BB', 'Barbados'),
        ('BZ', 'Belize'),
        ('BM', 'Bermuda'),
        ('VG', 'British Virgin Islands'),
        ('KY', 'Cayman Islands'),
        ('CR', 'Costa Rica'),
        ('CU', 'Cuba'),
        ('DM', 'Dominica'),
        ('DO', 'Dominican Republic'),
        ('SV', 'El Salvador'),
        ('GD', 'Grenada'),
        ('GP', 'Guadeloupe'),
        ('GT', 'Guatemala'),
        ('HT', 'Haiti'),
        ('HN', 'Honduras'),
        ('JM', 'Jamaica'),
        ('MQ', 'Martinique'),
        ('MS', 'Montserrat'),
        ('NI', 'Nicaragua'),
        ('PA', 'Panama'),
        ('PR', 'Puerto Rico'),
        ('BL', 'Saint Barthélemy'),
        ('KN', 'Saint Kitts and Nevis'),
        ('LC', 'Saint Lucia'),
        ('MF', 'Saint Martin'),
        ('PM', 'Saint Pierre and Miquelon'),
        ('VC', 'Saint Vincent and the Grenadines'),
        ('TT', 'Trinidad and Tobago'),
        ('TC', 'Turks and Caicos Islands'),
        ('VI', 'U.S. Virgin Islands'),
    ]
    
    # Left column fields
    document_no = models.CharField(max_length=50, unique=True, blank=True, help_text="Document number")
    job_no = models.CharField(max_length=50, blank=True, help_text="Job number")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='documentations', null=True, blank=True)
    document_type = models.CharField(
        max_length=20, 
        choices=DOCUMENT_TYPE_CHOICES,
        blank=True, 
        help_text="Type of document"
    )
    bill_to = models.CharField(max_length=200, blank=True, help_text="Bill to party")
    bill_to_address = models.TextField(blank=True, help_text="Bill to address")
    deliver_to = models.ForeignKey(
        Customer, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='delivery_documentations',
        help_text="Customer for delivery"
    )
    deliver_to_address = models.TextField(blank=True, help_text="Delivery address")
    port_of_loading = models.ForeignKey(
        Port, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='loading_documentations',
        help_text="Port of loading"
    )
    discharge_port = models.ForeignKey(
        Port, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='discharge_documentations',
        help_text="Port of discharge"
    )
    
    # Right column fields
    date = models.DateField(null=True, blank=True, help_text="Document date")
    payment_mode = models.CharField(
        max_length=20,
        choices=PAYMENT_MODE_CHOICES,
        blank=True,
        help_text="Payment mode"
    )
    container = models.CharField(max_length=50, blank=True, help_text="Container number")
    bl_number = models.CharField(max_length=100, blank=True, help_text="Bill of Lading number")
    boe = models.CharField(max_length=50, blank=True, help_text="Bill of Entry number")
    exit_point = models.ForeignKey(
        Port, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='exit_documentations',
        help_text="Exit point"
    )
    destination = models.CharField(
        max_length=3,
        choices=COUNTRY_CHOICES,
        blank=True,
        help_text="Final destination country"
    )
    ship_mode = models.CharField(
        max_length=20,
        choices=SHIP_MODE_CHOICES,
        blank=True,
        help_text="Shipping mode"
    )
    ship_date = models.DateField(null=True, blank=True, help_text="Ship date")
    vessel = models.CharField(max_length=100, blank=True, help_text="Vessel name")
    voyage = models.CharField(max_length=50, blank=True, help_text="Voyage number")
    delivery_terms = models.CharField(max_length=100, blank=True, help_text="Delivery terms")
    
    # System fields
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Documentation'
        verbose_name_plural = 'Documentation'
    
    def save(self, *args, **kwargs):
        # Auto-generate document_no if not provided
        if not self.document_no:
            # Get the last documentation number
            last_doc = Documentation.objects.order_by('-document_no').first()
            if last_doc and last_doc.document_no:
                try:
                    # Extract number from last document_no (e.g., "DOC-2024-001" -> 1)
                    last_number = int(last_doc.document_no.split('-')[-1])
                    new_number = last_number + 1
                except (ValueError, IndexError):
                    new_number = 1
            else:
                new_number = 1
            
            # Format: DOC-YYYY-NNN
            year = timezone.now().year
            self.document_no = f"DOC-{year}-{new_number:03d}"
        
        # Auto-populate job_no from cargo items if not set
        if not self.job_no and self.pk:
            job_no_from_cargo = self.job_number_from_cargo
            if job_no_from_cargo:
                self.job_no = job_no_from_cargo
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.document_no} - {self.customer.customer_name if self.customer else 'No Customer'}"
    
    @property
    def items_summary(self):
        """Get a summary of item names"""
        items = self.cargo_items.values_list('item_name', flat=True)
        if items:
            return ', '.join(filter(None, items))[:50] + ('...' if len(', '.join(filter(None, items))) > 50 else '')
        return '-'
    
    @property
    def hs_codes(self):
        """Get a summary of HS codes"""
        codes = self.cargo_items.values_list('hs_code', flat=True)
        if codes:
            return ', '.join(filter(None, codes))[:30] + ('...' if len(', '.join(filter(None, codes))) > 30 else '')
        return '-'
    
    @property
    def coo_summary(self):
        """Get a summary of COO values"""
        coos = self.cargo_items.values_list('coo', flat=True)
        if coos:
            return ', '.join(filter(None, coos))[:30] + ('...' if len(', '.join(filter(None, coos))) > 30 else '')
        return '-'
    
    @property
    def units_summary(self):
        """Get a summary of units"""
        units = self.cargo_items.values_list('unit', flat=True)
        if units:
            return ', '.join(filter(None, units))[:20] + ('...' if len(', '.join(filter(None, units))) > 20 else '')
        return '-'
    
    @property
    def quantities_summary(self):
        """Get summary of quantities from cargo items"""
        cargo_items = self.cargo_items.all()
        if cargo_items:
            quantities = [str(item.quantity) for item in cargo_items if item.quantity]
            return ', '.join(quantities)
        return '-'

    @property
    def job_number_from_cargo(self):
        """Get job number from the first cargo item's job"""
        first_cargo = self.cargo_items.first()
        if first_cargo and first_cargo.job_cargo and first_cargo.job_cargo.job:
            return first_cargo.job_cargo.job.job_code
        return None

    @property
    def display_job_no(self):
        """Display job number, falling back to cargo items if not set"""
        if self.job_no:
            return self.job_no
        return self.job_number_from_cargo or '-'

    def update_job_no_from_cargo(self):
        """Update job_no field from cargo items if not set"""
        if not self.job_no:
            job_no_from_cargo = self.job_number_from_cargo
            if job_no_from_cargo:
                self.job_no = job_no_from_cargo
                self.save(update_fields=['job_no'])
                return True
        return False


class DocumentationCargo(models.Model):
    """Model for storing cargo items selected for documentation"""
    documentation = models.ForeignKey(Documentation, on_delete=models.CASCADE, related_name='cargo_items')
    job_cargo = models.ForeignKey('job.JobCargo', on_delete=models.CASCADE, related_name='documentation_items')
    
    # Store the values as they were when selected (in case original cargo changes)
    item_name = models.CharField(max_length=200, blank=True)
    item_code = models.CharField(max_length=50, blank=True)
    hs_code = models.CharField(max_length=50, blank=True)
    unit = models.CharField(max_length=20, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    coo = models.CharField(max_length=100, blank=True)
    net_weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    gross_weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Documentation Cargo'
        verbose_name_plural = 'Documentation Cargo'
    
    def __str__(self):
        return f"{self.documentation.document_no} - {self.item_name}" 