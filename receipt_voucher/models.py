from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid

class ReceiptVoucher(models.Model):
    """Receipt Voucher model for tracking incoming payments"""
    
    RECEIPT_MODES = [
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('credit_card', 'Credit Card'),
        ('online_payment', 'Online Payment'),
        ('other', 'Other'),
    ]
    
    PAYER_TYPES = [
        ('customer', 'Customer'),
        ('employee', 'Employee'),
        ('vendor', 'Vendor'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic Information
    voucher_number = models.CharField(max_length=50, unique=True, blank=True)
    voucher_date = models.DateField()
    receipt_mode = models.CharField(max_length=20, choices=RECEIPT_MODES)
    payer_type = models.CharField(max_length=20, choices=PAYER_TYPES)
    payer_name = models.CharField(max_length=200)
    payer_code = models.CharField(max_length=50, blank=True, null=True)
    payer_contact = models.CharField(max_length=50, blank=True, null=True)
    payer_email = models.EmailField(blank=True, null=True)
    
    # Financial Information
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.ForeignKey('multi_currency.Currency', on_delete=models.PROTECT)
    account_to_credit = models.ForeignKey('chart_of_accounts.ChartOfAccount', on_delete=models.PROTECT)
    
    # Additional Information
    description = models.TextField(blank=True, null=True)
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    reference_invoices = models.TextField(blank=True, null=True, help_text="Comma-separated invoice numbers")
    
    # Status and Workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    received_at = models.DateTimeField(blank=True, null=True)
    
    # Audit Fields
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='receipt_vouchers_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='receipt_vouchers_updated', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='receipt_vouchers_approved', blank=True, null=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Receipt Voucher'
        verbose_name_plural = 'Receipt Vouchers'
    
    def __str__(self):
        return f"RV-{self.voucher_number} - {self.payer_name}"
    
    def save(self, *args, **kwargs):
        if not self.voucher_number:
            # Generate voucher number
            year = timezone.now().year
            last_voucher = ReceiptVoucher.objects.filter(
                voucher_number__startswith=f'RV-{year}'
            ).order_by('-voucher_number').first()
            
            if last_voucher:
                try:
                    last_number = int(last_voucher.voucher_number.split('-')[-1])
                    new_number = last_number + 1
                except (ValueError, IndexError):
                    new_number = 1
            else:
                new_number = 1
            
            self.voucher_number = f'RV-{year}-{new_number:04d}'
        
        super().save(*args, **kwargs)
    
    @property
    def total_attachments(self):
        return self.attachments.count()
    
    @property
    def can_edit(self):
        return self.status == 'draft'
    
    @property
    def can_approve(self):
        return self.status == 'draft'
    
    @property
    def can_mark_received(self):
        return self.status == 'approved'


class ReceiptVoucherAttachment(models.Model):
    """Attachments for receipt vouchers"""
    
    voucher = models.ForeignKey(ReceiptVoucher, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='receipt_vouchers/attachments/')
    filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50, blank=True)
    file_size = models.IntegerField(blank=True, null=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.PROTECT)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Receipt Voucher Attachment'
        verbose_name_plural = 'Receipt Voucher Attachments'
    
    def __str__(self):
        return f"{self.filename} - {self.voucher.voucher_number}"
    
    def save(self, *args, **kwargs):
        if not self.filename and self.file:
            self.filename = self.file.name.split('/')[-1]
        
        if not self.file_type and self.file:
            self.file_type = self.file.name.split('.')[-1].upper()
        
        if not self.file_size and self.file:
            self.file_size = self.file.size
        
        super().save(*args, **kwargs)


class ReceiptVoucherAudit(models.Model):
    """Audit trail for receipt vouchers"""
    
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('approved', 'Approved'),
        ('marked_received', 'Marked as Received'),
        ('cancelled', 'Cancelled'),
        ('attachment_added', 'Attachment Added'),
        ('attachment_removed', 'Attachment Removed'),
    ]
    
    voucher = models.ForeignKey(ReceiptVoucher, on_delete=models.CASCADE, related_name='audit_trail')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField()
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Receipt Voucher Audit'
        verbose_name_plural = 'Receipt Voucher Audits'
    
    def __str__(self):
        return f"{self.voucher.voucher_number} - {self.action} by {self.user.get_full_name()}"
