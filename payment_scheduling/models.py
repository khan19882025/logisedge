from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db.models import Sum, F, Q
from decimal import Decimal
import uuid


class VATConfiguration(models.Model):
    """VAT Configuration for UAE VAT compliance"""
    VAT_RATE_CHOICES = [
        (Decimal('0.00'), '0% - Zero Rated'),
        (Decimal('5.00'), '5% - Standard Rate'),
        (Decimal('100.00'), '100% - Exempt'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    vat_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        choices=VAT_RATE_CHOICES,
        default=Decimal('5.00')
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        verbose_name = 'VAT Configuration'
        verbose_name_plural = 'VAT Configurations'
    
    def __str__(self):
        return f"{self.name} ({self.vat_rate}%)"


class PaymentMethod(models.Model):
    """Payment methods for schedules"""
    PAYMENT_TYPE_CHOICES = [
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('wire_transfer', 'Wire Transfer'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Payment Method'
        verbose_name_plural = 'Payment Methods'
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class PaymentSchedule(models.Model):
    """Main payment schedule model"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('partially_paid', 'Partially Paid'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_TYPE_CHOICES = [
        ('customer', 'Customer Payment'),
        ('vendor', 'Vendor Payment'),
    ]
    
    CURRENCY_CHOICES = [
        ('AED', 'UAE Dirham (AED)'),
        ('USD', 'US Dollar (USD)'),
        ('EUR', 'Euro (EUR)'),
        ('GBP', 'British Pound (GBP)'),
        ('SAR', 'Saudi Riyal (SAR)'),
        ('KWD', 'Kuwaiti Dinar (KWD)'),
        ('BHD', 'Bahraini Dinar (BHD)'),
        ('QAR', 'Qatar Riyal (QAR)'),
        ('OMR', 'Omani Rial (OMR)'),
    ]
    
    # Basic Information
    schedule_number = models.CharField(max_length=50, unique=True, blank=True)
    customer = models.ForeignKey(
        'customer.Customer', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='payment_schedules'
    )
    vendor = models.CharField(max_length=255, blank=True, null=True, help_text="Vendor/Supplier name")
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    
    # Amount Details
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='AED')
    vat_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('5.00'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))]
    )
    vat_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_with_vat = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Payment Details
    due_date = models.DateField()
    installment_count = models.PositiveIntegerField(default=1)
    installment_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    outstanding_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # References
    invoice_reference = models.CharField(max_length=100, blank=True)
    po_reference = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    
    # Status and Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_payment_schedules')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_payment_schedules')
    
    class Meta:
        verbose_name = 'Payment Schedule'
        verbose_name_plural = 'Payment Schedules'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.schedule_number} - {self.get_payment_type_display()}"
    
    def save(self, *args, **kwargs):
        # Generate schedule number if not provided
        if not self.schedule_number:
            self.schedule_number = self.generate_schedule_number()
        
        # Calculate VAT and total amounts
        self.vat_amount = (self.total_amount * self.vat_rate) / Decimal('100.00')
        self.total_with_vat = self.total_amount + self.vat_amount
        
        # Calculate installment amount
        if self.installment_count > 0:
            self.installment_amount = self.total_with_vat / Decimal(self.installment_count)
        
        # Calculate outstanding amount
        self.outstanding_amount = self.total_with_vat - self.paid_amount
        
        # Update status based on payments and due date
        if self.outstanding_amount <= 0:
            self.status = 'paid'
        elif self.paid_amount > 0:
            self.status = 'partially_paid'
        elif self.due_date < timezone.now().date():
            self.status = 'overdue'
        elif self.status == 'draft':
            self.status = 'pending'
        
        super().save(*args, **kwargs)
    
    def generate_schedule_number(self):
        """Generate unique schedule number"""
        year = timezone.now().year
        month = timezone.now().month
        
        # Find the last schedule for this year/month
        last_schedule = PaymentSchedule.objects.filter(
            schedule_number__startswith=f"PS-{year}{month:02d}-"
        ).order_by('-schedule_number').first()
        
        if last_schedule and last_schedule.schedule_number:
            try:
                # Extract sequence number and increment
                last_sequence = int(last_schedule.schedule_number.split('-')[-1])
                new_sequence = last_sequence + 1
            except (ValueError, IndexError):
                new_sequence = 1
        else:
            new_sequence = 1
        
        # Format: PS-YYYYMM-0001
        return f"PS-{year}{month:02d}-{new_sequence:04d}"
    
    @property
    def is_overdue(self):
        """Check if the schedule is overdue"""
        return self.due_date < timezone.now().date() and self.status not in ['paid', 'cancelled']
    
    @property
    def days_overdue(self):
        """Calculate days overdue"""
        if self.is_overdue:
            return (timezone.now().date() - self.due_date).days
        return 0
    
    @property
    def payment_progress(self):
        """Calculate payment progress percentage"""
        if self.total_with_vat > 0:
            return (self.paid_amount / self.total_with_vat) * 100
        return 0


class PaymentInstallment(models.Model):
    """Individual payment installments"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('partially_paid', 'Partially Paid'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
    ]
    
    payment_schedule = models.ForeignKey(PaymentSchedule, on_delete=models.CASCADE, related_name='installments')
    installment_number = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    due_date = models.DateField()
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    paid_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Payment Installment'
        verbose_name_plural = 'Payment Installments'
        unique_together = ['payment_schedule', 'installment_number']
        ordering = ['installment_number']
    
    def __str__(self):
        return f"{self.payment_schedule.schedule_number} - Installment {self.installment_number}"
    
    @property
    def outstanding_amount(self):
        """Calculate outstanding amount for this installment"""
        return self.amount - self.paid_amount
    
    @property
    def is_overdue(self):
        """Check if this installment is overdue"""
        return self.due_date < timezone.now().date() and self.status != 'paid'
    
    def save(self, *args, **kwargs):
        # Update status based on payments
        if self.paid_amount >= self.amount:
            self.status = 'paid'
        elif self.paid_amount > 0:
            self.status = 'partially_paid'
        elif self.due_date < timezone.now().date():
            self.status = 'overdue'
        else:
            self.status = 'pending'
        
        super().save(*args, **kwargs)


class PaymentReminder(models.Model):
    """Payment reminders"""
    REMINDER_TYPE_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
        ('phone', 'Phone Call'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    payment_schedule = models.ForeignKey(PaymentSchedule, on_delete=models.CASCADE, related_name='reminders')
    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPE_CHOICES)
    scheduled_date = models.DateTimeField()
    recipient = models.CharField(max_length=255)
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_date = models.DateTimeField(null=True, blank=True)
    sent_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Payment Reminder'
        verbose_name_plural = 'Payment Reminders'
        ordering = ['-scheduled_date']
    
    def __str__(self):
        return f"{self.payment_schedule.schedule_number} - {self.get_reminder_type_display()}"


class PaymentScheduleHistory(models.Model):
    """History tracking for payment schedules"""
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('status_changed', 'Status Changed'),
        ('payment_received', 'Payment Received'),
        ('reminder_sent', 'Reminder Sent'),
        ('cancelled', 'Cancelled'),
    ]
    
    payment_schedule = models.ForeignKey(PaymentSchedule, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Payment Schedule History'
        verbose_name_plural = 'Payment Schedule History'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.payment_schedule.schedule_number} - {self.get_action_display()} - {self.timestamp}"
