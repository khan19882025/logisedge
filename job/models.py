from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
from django.db.models import Max
import re


class JobStatus(models.Model):
    """Job Status model for tracking job progress"""
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#6c757d')  # Hex color code
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Job Status'
        verbose_name_plural = 'Job Statuses'

    def __str__(self):
        return self.name


class JobPriority(models.Model):
    """Job Priority model for setting job importance levels"""
    name = models.CharField(max_length=50, unique=True)
    level = models.IntegerField(unique=True, help_text="Higher number = higher priority")
    color = models.CharField(max_length=7, default='#6c757d')  # Hex color code
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['level']
        verbose_name = 'Job Priority'
        verbose_name_plural = 'Job Priorities'

    def __str__(self):
        return f"{self.name} (Level {self.level})"


class Job(models.Model):
    """Main Job model for managing work orders and tasks"""
    job_code = models.CharField(max_length=20, unique=True, editable=False)
    title = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    
    # Job Classification
    JOB_TYPE_CHOICES = [
        ("Inbound", "Inbound"),
        ("Warehousing", "Warehousing"),
        ("Documentations", "Documentations"),
        ("Cross Stuffing", "Cross Stuffing"),
    ]
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES)
    status = models.ForeignKey(JobStatus, on_delete=models.PROTECT, related_name='jobs', blank=True, null=True)
    priority = models.ForeignKey(JobPriority, on_delete=models.PROTECT, related_name='jobs', blank=True, null=True)

    DOC_TYPE_CHOICES = [
        ("TOO", "TOO"),
        ("Transit IN", "Transit IN"),
        ("Transit OUT", "Transit OUT"),
        ("Import", "Import"),
        ("Export", "Export"),
    ]
    doc_type = models.CharField(max_length=20, choices=DOC_TYPE_CHOICES)

    SHIPMENT_TYPE_CHOICES = [
        ("FCL-FCL", "FCL-FCL"),
        ("FCL-LCL", "FCL-LCL"),
        ("LCL-LCL", "LCL-LCL"),
        ("BULK", "BULK"),
        ("RO-RO", "RO-RO"),
    ]
    shipment_type = models.CharField(max_length=20, choices=SHIPMENT_TYPE_CHOICES)
    
    MODE_CHOICES = [
        ("Sea", "Sea"),
        ("Land", "Land"),
        ("Air", "Air"),
    ]
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default="Sea")
    
    # Customer Information
    customer_name = models.ForeignKey('customer.Customer', on_delete=models.PROTECT, related_name='jobs_as_customer', null=True, blank=True)
    customer_ref = models.CharField(max_length=100)
    shipper = models.ForeignKey('customer.Customer', on_delete=models.PROTECT, related_name='jobs_as_shipper', null=True, blank=True)
    broker = models.ForeignKey('customer.Customer', on_delete=models.PROTECT, related_name='jobs_as_broker', null=True, blank=True)
    
    # Facility
    facility = models.ForeignKey('facility.Facility', on_delete=models.PROTECT, related_name='jobs', null=True, blank=True)
    
    # Assignment
    assigned_to = models.ForeignKey('salesman.Salesman', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_jobs')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_jobs')
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    due_date = models.DateField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Additional Fields
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    actual_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True, help_text="Notes visible only to staff")
    
    # Related Items
    related_items = models.ManyToManyField('items.Item', blank=True, related_name='related_jobs')
    related_facilities = models.ManyToManyField('facility.Facility', blank=True, related_name='related_jobs')
    
    # BL (Bill of Lading) fields
    bl_number = models.CharField(max_length=100, blank=True, null=True)
    bl_shipper = models.CharField(max_length=255, blank=True, null=True)
    bl_consignee = models.CharField(max_length=255, blank=True, null=True)
    bl_notify_party = models.CharField(max_length=255, blank=True, null=True)
    vessel_name = models.CharField(max_length=100, blank=True, null=True)
    voyage_number = models.CharField(max_length=50, blank=True, null=True)
    port_loading = models.CharField(max_length=100, blank=True, null=True)
    port_discharge = models.CharField(max_length=100, blank=True, null=True)

    # BOE (Bill of Entry) fields
    boe_number = models.CharField(max_length=100, blank=True, null=True)
    boe_date = models.DateField(blank=True, null=True)
    boe_value = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    
    # MRN (Movement Reference Number) field
    mrn_number = models.CharField(max_length=100, blank=True, null=True)
    
    # FZ Company field
    fz_company = models.CharField(max_length=200, blank=True, null=True)
    
    # COM-INVOICE field
    com_invoice = models.CharField(max_length=100, blank=True, null=True)
    
    # COM-INVOICE Date field
    com_invoice_date = models.DateField(blank=True, null=True)

    # CNTR (Container) fields
    container_number = models.CharField(max_length=100, blank=True, null=True)
    container_type = models.CharField(max_length=50, blank=True, null=True)
    container_size = models.CharField(max_length=20, blank=True, null=True)
    seal_number = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Job'
        verbose_name_plural = 'Jobs'

    def __str__(self):
        title = self.title or "Untitled Job"
        return f"{self.job_code} - {title}"

    def save(self, *args, **kwargs):
        if not self.job_code:
            # Generate unique job code
            self.job_code = self.generate_job_code()
        
        # Set default status if not provided
        if not self.status:
            default_status = JobStatus.objects.filter(is_active=True).first()
            if default_status:
                self.status = default_status
        
        super().save(*args, **kwargs)

    def generate_job_code(self):
        """Generate a unique job code in format JOB-YEAR-0001"""
        current_year = timezone.now().year
        
        # Find the last job code for this year
        last_job = Job.objects.filter(
            job_code__regex=r'^JOB-' + str(current_year) + r'-\d{4}$'
        ).aggregate(Max('job_code'))
        
        if last_job['job_code__max']:
            # Extract the number part and increment
            match = re.search(r'JOB-' + str(current_year) + r'-(\d{4})', last_job['job_code__max'])
            if match:
                last_number = int(match.group(1))
                new_number = last_number + 1
            else:
                new_number = 1
        else:
            # No jobs for this year yet, start with 0001
            new_number = 1
        
        # Format: JOB-YEAR-0001, JOB-YEAR-0002, etc.
        return f"JOB-{current_year}-{new_number:04d}"

    @property
    def is_overdue(self):
        """Check if job is overdue"""
        if self.due_date and self.status and self.status.name.lower() not in ['completed', 'cancelled']:
            return timezone.now().date() > self.due_date
        return False

    @property
    def duration(self):
        """Calculate job duration in hours"""
        if self.started_at and self.completed_at:
            duration = self.completed_at - self.started_at
            return duration.total_seconds() / 3600
        return None

    @property
    def progress_percentage(self):
        """Calculate job progress percentage based on status"""
        if not self.status:
            return 0
        
        # Define progress percentages for different statuses
        status_progress = {
            'pending': 10,
            'in_progress': 50,
            'review': 80,
            'completed': 100,
            'cancelled': 0
        }
        
        return status_progress.get(self.status.name.lower(), 0)
    
    @property
    def total_quantity(self):
        """Calculate total quantity from cargo items"""
        total = self.cargo_items.aggregate(
            total=models.Sum('quantity')
        )['total']
        return total or 0


class JobCargo(models.Model):
    """Model for storing cargo details for each job"""
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='cargo_items')
    item = models.ForeignKey('items.Item', on_delete=models.PROTECT, related_name='job_cargo_items', null=True, blank=True)
    item_code = models.CharField(max_length=50, blank=True)
    hs_code = models.CharField(max_length=50, blank=True)
    unit = models.CharField(max_length=20)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    coo = models.CharField(max_length=100, blank=True)
    net_weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    gross_weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    remark = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Job Cargo'
        verbose_name_plural = 'Job Cargo'

    def __str__(self):
        return f"{self.job.job_code} - {self.item_code or 'No Item Code'}"

    def save(self, *args, **kwargs):
        # Auto-populate item_code from item if available
        if self.item and not self.item_code:
            self.item_code = self.item.item_code
        super().save(*args, **kwargs)


class JobContainer(models.Model):
    """Model for storing container details for each job"""
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='containers')
    cargo_bond = models.CharField(max_length=100, blank=True, null=True)
    ed_number = models.CharField(max_length=100, blank=True, null=True)
    m1_number = models.CharField(max_length=100, blank=True, null=True)
    container_number = models.CharField(max_length=100, blank=True, null=True)
    container_size = models.CharField(max_length=50, blank=True, null=True)
    seal_number = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Job Container'
        verbose_name_plural = 'Job Containers'

    def __str__(self):
        return f"{self.job.job_code} - {self.container_number or 'No Container'}"