import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone


class Printer(models.Model):
    """Physical or virtual printer configuration"""
    PRINTER_TYPES = [
        ('physical', 'Physical Printer'),
        ('virtual', 'Virtual Printer'),
        ('network', 'Network Printer'),
        ('cloud', 'Cloud Printer'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    printer_type = models.CharField(max_length=20, choices=PRINTER_TYPES, default='physical')
    location = models.CharField(max_length=200, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    port = models.IntegerField(default=9100, blank=True, null=True)
    driver_name = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    max_job_size = models.IntegerField(default=100, help_text="Maximum jobs in queue")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_printers')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updated_printers')
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Printer'
        verbose_name_plural = 'Printers'
    
    def __str__(self):
        return f"{self.name} ({self.get_printer_type_display()})"
    
    def get_status(self):
        """Get current printer status"""
        active_jobs = self.print_jobs.filter(status='printing').count()
        if active_jobs >= self.max_job_size:
            return 'queue_full'
        elif active_jobs > 0:
            return 'busy'
        else:
            return 'idle'


class PrinterGroup(models.Model):
    """Group of printers for load balancing and redundancy"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    printers = models.ManyToManyField(Printer, related_name='printer_groups')
    load_balancing = models.BooleanField(default=True, help_text="Distribute jobs across printers")
    failover = models.BooleanField(default=True, help_text="Failover to next available printer")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_printer_groups')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updated_printer_groups')
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Printer Group'
        verbose_name_plural = 'Printer Groups'
    
    def __str__(self):
        return self.name
    
    def get_available_printer(self):
        """Get next available printer in the group"""
        available_printers = self.printers.filter(is_active=True)
        if not available_printers.exists():
            return None
        
        # Simple round-robin for now, can be enhanced with more sophisticated algorithms
        return available_printers.first()


class PrintTemplate(models.Model):
    """Document templates for printing"""
    TEMPLATE_TYPES = [
        ('invoice', 'Invoice'),
        ('packing_slip', 'Packing Slip'),
        ('grn', 'Goods Received Note'),
        ('purchase_order', 'Purchase Order'),
        ('sales_order', 'Sales Order'),
        ('delivery_order', 'Delivery Order'),
        ('receipt', 'Receipt'),
        ('custom', 'Custom Template'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPES)
    description = models.TextField(blank=True)
    template_file = models.FileField(upload_to='print_templates/', blank=True)
    template_content = models.TextField(blank=True, help_text="Template content or HTML")
    variables = models.JSONField(default=dict, blank=True, help_text="Template variables and placeholders")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_print_templates')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updated_print_templates')
    
    class Meta:
        ordering = ['template_type', 'name']
        verbose_name = 'Print Template'
        verbose_name_plural = 'Print Templates'
        unique_together = ['template_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"


class ERPEvent(models.Model):
    """ERP events that can trigger printing"""
    EVENT_TYPES = [
        ('sales_order_approved', 'Sales Order Approved'),
        ('delivery_order_dispatched', 'Delivery Order Dispatched'),
        ('goods_received', 'Goods Received'),
        ('invoice_generated', 'Invoice Generated'),
        ('payment_received', 'Payment Received'),
        ('purchase_order_created', 'Purchase Order Created'),
        ('inventory_adjusted', 'Inventory Adjusted'),
        ('custom', 'Custom Event'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    description = models.TextField(blank=True)
    event_code = models.CharField(max_length=100, unique=True, help_text="Unique event identifier")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_erp_events')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updated_erp_events')
    
    class Meta:
        ordering = ['event_type', 'name']
        verbose_name = 'ERP Event'
        verbose_name_plural = 'ERP Events'
    
    def __str__(self):
        return f"{self.name} ({self.get_event_type_display()})"


class AutoPrintRule(models.Model):
    """Rules for automatic printing based on ERP events"""
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    erp_event = models.ForeignKey(ERPEvent, on_delete=models.CASCADE, related_name='auto_print_rules')
    print_template = models.ForeignKey(PrintTemplate, on_delete=models.CASCADE, related_name='auto_print_rules')
    printer = models.ForeignKey(Printer, on_delete=models.CASCADE, related_name='auto_print_rules', blank=True, null=True)
    printer_group = models.ForeignKey(PrinterGroup, on_delete=models.CASCADE, related_name='auto_print_rules', blank=True, null=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_LEVELS, default='normal')
    conditions = models.JSONField(default=dict, blank=True, help_text="Printing conditions (warehouse, customer type, etc.)")
    batch_printing = models.BooleanField(default=False, help_text="Enable batch printing")
    batch_schedule = models.CharField(max_length=100, blank=True, help_text="Cron expression for batch schedule")
    preview_required = models.BooleanField(default=False, help_text="Show preview before printing")
    auto_print = models.BooleanField(default=True, help_text="Print automatically without user intervention")
    retry_count = models.IntegerField(default=3, help_text="Number of retry attempts")
    retry_delay = models.IntegerField(default=300, help_text="Delay between retries in seconds")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_auto_print_rules')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updated_auto_print_rules')
    
    class Meta:
        ordering = ['priority', 'name']
        verbose_name = 'Auto Print Rule'
        verbose_name_plural = 'Auto Print Rules'
    
    def __str__(self):
        return f"{self.name} - {self.erp_event.name}"
    
    def clean(self):
        """Validate that either printer or printer_group is set"""
        if not self.printer and not self.printer_group:
            raise ValidationError("Either printer or printer group must be specified")
        if self.printer and self.printer_group:
            raise ValidationError("Cannot specify both printer and printer group")


class PrintJob(models.Model):
    """Individual print job in the queue"""
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('printing', 'Printing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('retrying', 'Retrying'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_number = models.CharField(max_length=50, unique=True, help_text="Human-readable job number")
    auto_print_rule = models.ForeignKey(AutoPrintRule, on_delete=models.CASCADE, related_name='print_jobs', blank=True, null=True)
    print_template = models.ForeignKey(PrintTemplate, on_delete=models.CASCADE, related_name='print_jobs')
    printer = models.ForeignKey(Printer, on_delete=models.CASCADE, related_name='print_jobs')
    printer_group = models.ForeignKey(PrinterGroup, on_delete=models.CASCADE, related_name='print_jobs', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    priority = models.CharField(max_length=20, choices=AutoPrintRule.PRIORITY_LEVELS, default='normal')
    data = models.JSONField(default=dict, help_text="Template data for printing")
    file_path = models.CharField(max_length=500, blank=True, help_text="Path to generated print file")
    pages = models.IntegerField(default=1)
    copies = models.IntegerField(default=1)
    preview_required = models.BooleanField(default=False)
    preview_generated = models.BooleanField(default=False)
    preview_file = models.CharField(max_length=500, blank=True)
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    scheduled_at = models.DateTimeField(blank=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_print_jobs')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updated_print_jobs')
    
    class Meta:
        ordering = ['-priority', 'created_at']
        verbose_name = 'Print Job'
        verbose_name_plural = 'Print Jobs'
    
    def __str__(self):
        return f"Job {self.job_number} - {self.status}"
    
    def save(self, *args, **kwargs):
        """Generate job number if not provided"""
        if not self.job_number:
            self.job_number = f"PJ{timezone.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    def get_estimated_duration(self):
        """Get estimated print duration based on pages and copies"""
        base_time = 30  # seconds per page
        return (self.pages * self.copies * base_time) / 60  # minutes


class PrintJobLog(models.Model):
    """Audit trail for print jobs"""
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('queued', 'Queued'),
        ('started', 'Started'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('retried', 'Retried'),
        ('preview_generated', 'Preview Generated'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    print_job = models.ForeignKey(PrintJob, on_delete=models.CASCADE, related_name='logs', blank=True, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    message = models.TextField(blank=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='print_job_logs')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Print Job Log'
        verbose_name_plural = 'Print Job Logs'
    
    def __str__(self):
        return f"{self.print_job.job_number} - {self.action}"


class BatchPrintJob(models.Model):
    """Batch printing jobs for scheduled printing"""
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    auto_print_rule = models.ForeignKey(AutoPrintRule, on_delete=models.CASCADE, related_name='batch_jobs')
    scheduled_at = models.DateTimeField()
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    total_jobs = models.IntegerField(default=0)
    completed_jobs = models.IntegerField(default=0)
    failed_jobs = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_batch_jobs')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updated_batch_jobs')
    
    class Meta:
        ordering = ['-scheduled_at']
        verbose_name = 'Batch Print Job'
        verbose_name_plural = 'Batch Print Jobs'
    
    def __str__(self):
        return f"{self.name} - {self.status}"
    
    def get_progress_percentage(self):
        """Get completion percentage"""
        if self.total_jobs == 0:
            return 0
        return (self.completed_jobs / self.total_jobs) * 100
