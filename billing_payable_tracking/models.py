from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class Vendor(models.Model):
    """
    Vendor model for billing system
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        
    def __str__(self):
        return self.name


class Bill(models.Model):
    """
    Bill model for payable tracking
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='bills')
    bill_no = models.CharField(max_length=100, unique=True)
    bill_name = models.CharField(max_length=200, default='Bill', help_text="Descriptive name for the bill (e.g., 'Credit Card', 'Electricity Bill')")
    bill_date = models.DateField()
    due_date = models.DateField()
    amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.ForeignKey(
        'multi_currency.Currency', 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True,
        help_text="Currency for this bill amount"
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    confirmed = models.BooleanField(default=False)
    paid_date = models.DateField(blank=True, null=True)
    paid_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    notes = models.TextField(blank=True, null=True)
    attachment = models.FileField(upload_to='bills/attachments/', blank=True, null=True)
    
    # Recurring bill fields
    is_recurring = models.BooleanField(default=False, help_text="Whether this is a recurring bill")
    generate_day = models.PositiveIntegerField(
        blank=True, 
        null=True, 
        help_text="Day of month when bill is generated (1-31)"
    )
    due_days_offset = models.PositiveIntegerField(
        blank=True, 
        null=True, 
        help_text="Number of days after generation when bill is due"
    )
    next_generate_date = models.DateField(
        blank=True, 
        null=True, 
        help_text="Next date when this recurring bill should be generated"
    )
    
    # Audit fields
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_bills')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updated_bills', blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['vendor']),
            models.Index(fields=['bill_no']),
        ]
        
    def __str__(self):
        return f"{self.bill_no} - {self.vendor.name}"
    
    @property
    def is_overdue(self):
        """Check if bill is overdue"""
        if self.status == 'paid':
            return False
        return self.due_date < timezone.now().date()
    
    @property
    def days_until_due(self):
        """Calculate days until due date"""
        if self.status == 'paid':
            return None
        delta = self.due_date - timezone.now().date()
        return delta.days
    
    @property
    def is_due_today(self):
        """Check if bill is due today"""
        if self.status == 'paid':
            return False
        return self.due_date == timezone.now().date()
    
    @property
    def is_due_soon(self):
        """Check if bill is due within 7 days"""
        if self.status == 'paid':
            return False
        days_until = self.days_until_due
        return days_until is not None and 0 <= days_until <= 7
    
    def mark_as_paid(self, paid_amount=None, paid_date=None, user=None):
        """Mark bill as paid"""
        self.status = 'paid'
        self.paid_date = paid_date or timezone.now().date()
        self.paid_amount = paid_amount or self.amount
        if user:
            self.updated_by = user
        self.save()
    
    def mark_as_overdue(self, user=None):
        """Mark bill as overdue"""
        if self.status != 'paid' and self.is_overdue:
            self.status = 'overdue'
            if user:
                self.updated_by = user
            self.save()
    
    def confirm_bill(self, user=None):
        """Confirm the bill"""
        self.confirmed = True
        if user:
            self.updated_by = user
        self.save()


class BillHistory(models.Model):
    """
    Track changes to bills for audit purposes
    """
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('paid', 'Marked as Paid'),
        ('confirmed', 'Confirmed'),
        ('overdue', 'Marked as Overdue'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)
    old_values = models.JSONField(blank=True, null=True)
    new_values = models.JSONField(blank=True, null=True)
    
    class Meta:
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.bill.bill_no} - {self.action} by {self.user.username}"


class BillAlert(models.Model):
    """
    Alert model for bill payable notifications
    """
    ALERT_TYPES = [
        ('generated', 'Bill Generated'),
        ('due_soon', 'Due Soon (4 days before)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='alerts')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bill_alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    show_date = models.DateField(help_text="Date when this alert should be shown")
    is_dismissed = models.BooleanField(default=False)
    dismissed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['bill', 'user', 'alert_type', 'show_date']
        indexes = [
            models.Index(fields=['user', 'is_dismissed', 'show_date']),
            models.Index(fields=['show_date']),
        ]
        
    def __str__(self):
        return f"{self.bill.bill_no} - {self.get_alert_type_display()} for {self.user.username}"
    
    def dismiss(self):
        """Mark alert as dismissed"""
        self.is_dismissed = True
        self.dismissed_at = timezone.now()
        self.save()
    
    def get_alert_message(self):
        """Get the alert message based on type"""
        if self.alert_type == 'generated':
            return f"{self.bill.bill_no} bill generated today"
        elif self.alert_type == 'due_soon':
            return f"{self.bill.bill_no} bill due on {self.bill.due_date.strftime('%m/%d/%Y')}"
        return "Bill alert"


class BillReminder(models.Model):
    """
    Track reminders sent for bills
    """
    REMINDER_TYPES = [
        ('due_today', 'Due Today'),
        ('overdue', 'Overdue'),
        ('upcoming', 'Upcoming (7 days)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='reminders')
    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPES)
    sent_date = models.DateTimeField(auto_now_add=True)
    recipient_email = models.EmailField()
    sent_successfully = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-sent_date']
        
    def __str__(self):
        return f"{self.bill.bill_no} - {self.reminder_type} reminder"
