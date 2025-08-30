from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
from datetime import datetime
import uuid

class PaymentVoucher(models.Model):
    """Payment Voucher model for managing payment transactions"""
    
    PAYMENT_MODES = [
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('credit_card', 'Credit Card'),
        ('other', 'Other'),
    ]
    
    PAYEE_TYPES = [
        ('vendor', 'Vendor'),
        ('employee', 'Employee'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic Information
    voucher_number = models.CharField(max_length=20, unique=True, blank=True, help_text="Auto-generated voucher number")
    voucher_date = models.DateField(help_text="Date of the payment voucher")
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODES, default='bank_transfer')
    
    # Payee Information
    payee_type = models.CharField(max_length=20, choices=PAYEE_TYPES, default='vendor')
    payee_name = models.CharField(max_length=200, help_text="Name of the payee")
    payee_id = models.CharField(max_length=50, blank=True, null=True, help_text="ID/Code of the payee")
    
    # Financial Information
    amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Payment amount"
    )
    currency = models.ForeignKey('multi_currency.Currency', on_delete=models.CASCADE, default=1)
    
    # Account Information
    account_to_debit = models.ForeignKey(
        'chart_of_accounts.ChartOfAccount', 
        on_delete=models.CASCADE,
        related_name='payment_vouchers_debited',
        help_text="Account to be debited for this payment"
    )
    
    # Description and References
    description = models.TextField(blank=True, help_text="Description or remarks for the payment")
    reference_invoices = models.TextField(blank=True, help_text="Reference to related invoices")
    reference_number = models.CharField(max_length=100, blank=True, help_text="External reference number")
    
    # Status and Approval
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='payment_vouchers_approved'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Audit Trail
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='payment_vouchers_created'
    )
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='payment_vouchers_updated'
    )
    
    class Meta:
        ordering = ['-voucher_date', '-created_at']
        verbose_name = 'Payment Voucher'
        verbose_name_plural = 'Payment Vouchers'
    
    def __str__(self):
        return f"{self.voucher_number} - {self.payee_name} - {self.amount}"
    
    def save(self, *args, **kwargs):
        # Generate voucher number if not provided
        if not self.voucher_number:
            self.voucher_number = self.generate_voucher_number()
        
        super().save(*args, **kwargs)
    
    def generate_voucher_number(self):
        """Generate unique voucher number"""
        year = self.voucher_date.year if self.voucher_date else datetime.now().year
        # Get the last voucher number for this year
        last_voucher = PaymentVoucher.objects.filter(
            voucher_number__startswith=f'PV-{year}-'
        ).order_by('-voucher_number').first()
        
        if last_voucher:
            try:
                last_number = int(last_voucher.voucher_number.split('-')[-1])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1
        
        return f'PV-{year}-{new_number:04d}'
    
    @property
    def formatted_amount(self):
        """Return formatted amount with currency"""
        return f"{self.currency.symbol}{self.amount:,.2f}"
    
    @property
    def is_approved(self):
        """Check if voucher is approved"""
        return self.status == 'approved'
    
    @property
    def is_paid(self):
        """Check if voucher is paid"""
        return self.status == 'paid'
    
    @property
    def can_approve(self):
        """Check if voucher can be approved"""
        return self.status == 'draft'
    
    @property
    def can_pay(self):
        """Check if voucher can be paid"""
        return self.status == 'approved'


class PaymentVoucherAttachment(models.Model):
    """Model for storing payment voucher attachments"""
    
    ATTACHMENT_TYPES = [
        ('invoice', 'Invoice'),
        ('receipt', 'Receipt'),
        ('contract', 'Contract'),
        ('other', 'Other'),
    ]
    
    voucher = models.ForeignKey(
        PaymentVoucher, 
        on_delete=models.CASCADE, 
        related_name='attachments'
    )
    file = models.FileField(upload_to='payment_vouchers/attachments/')
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, choices=ATTACHMENT_TYPES, default='other')
    description = models.CharField(max_length=500, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='voucher_attachments_uploaded'
    )
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Payment Voucher Attachment'
        verbose_name_plural = 'Payment Voucher Attachments'
    
    def __str__(self):
        return f"{self.voucher.voucher_number} - {self.file_name}"
    
    @property
    def file_extension(self):
        """Get file extension"""
        return self.file_name.split('.')[-1].lower() if '.' in self.file_name else ''
    
    @property
    def is_image(self):
        """Check if file is an image"""
        image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
        return self.file_extension in image_extensions
    
    @property
    def is_pdf(self):
        """Check if file is a PDF"""
        return self.file_extension == 'pdf'


class PaymentVoucherAudit(models.Model):
    """Audit trail for payment voucher changes"""
    
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
        ('attachment_added', 'Attachment Added'),
        ('attachment_removed', 'Attachment Removed'),
    ]
    
    voucher = models.ForeignKey(
        PaymentVoucher, 
        on_delete=models.CASCADE, 
        related_name='audit_trail'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField(blank=True)
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='voucher_audit_actions'
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Payment Voucher Audit'
        verbose_name_plural = 'Payment Voucher Audits'
    
    def __str__(self):
        return f"{self.voucher.voucher_number} - {self.action} - {self.timestamp}"
