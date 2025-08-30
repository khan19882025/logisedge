from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid

from asset_register.models import Asset
from chart_of_accounts.models import ChartOfAccount


class DisposalType(models.Model):
    """Disposal types: Sold, Scrapped, Donated, Lost"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class DisposalRequest(models.Model):
    """Main disposal request model"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('disposed', 'Disposed'),
        ('reversed', 'Reversed'),
    ]

    request_id = models.CharField(max_length=20, unique=True, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Batch or individual disposal
    is_batch = models.BooleanField(default=False)
    
    # Disposal details
    disposal_type = models.ForeignKey(DisposalType, on_delete=models.PROTECT)
    disposal_date = models.DateField()
    disposal_value = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    reason = models.TextField()
    remarks = models.TextField(blank=True)
    
    # Status and workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    current_approval_level = models.PositiveIntegerField(default=1)
    
    # Financial accounts
    asset_account = models.ForeignKey(
        ChartOfAccount, 
        on_delete=models.PROTECT, 
        related_name='disposal_asset_accounts',
        null=True, blank=True
    )
    disposal_account = models.ForeignKey(
        ChartOfAccount, 
        on_delete=models.PROTECT, 
        related_name='disposal_accounts',
        null=True, blank=True
    )
    bank_account = models.ForeignKey(
        ChartOfAccount, 
        on_delete=models.PROTECT, 
        related_name='disposal_bank_accounts',
        null=True, blank=True
    )
    
    # Audit fields
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='disposal_requests_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='disposal_requests_updated', null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    disposed_at = models.DateTimeField(null=True, blank=True)
    
    # Reversal fields
    reversed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='disposal_requests_reversed', null=True, blank=True)
    reversed_at = models.DateTimeField(null=True, blank=True)
    reversal_reason = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        permissions = [
            ('can_approve_disposal', 'Can approve disposal requests'),
            ('can_dispose_asset', 'Can execute asset disposal'),
            ('can_reverse_disposal', 'Can reverse disposal'),
            ('can_edit_disposal', 'Can edit disposal requests'),
        ]

    def __str__(self):
        return f"{self.request_id} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.request_id:
            self.request_id = f"DR{timezone.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)

    @property
    def total_asset_value(self):
        """Calculate total book value of all assets in this disposal"""
        return sum(item.asset.book_value for item in self.disposal_items.all())

    @property
    def gain_loss_amount(self):
        """Calculate gain or loss on disposal"""
        return self.disposal_value - self.total_asset_value

    @property
    def is_gain(self):
        """Check if disposal results in a gain"""
        return self.gain_loss_amount > 0

    @property
    def is_loss(self):
        """Check if disposal results in a loss"""
        return self.gain_loss_amount < 0


class DisposalItem(models.Model):
    """Individual assets in a disposal request"""
    disposal_request = models.ForeignKey(DisposalRequest, on_delete=models.CASCADE, related_name='disposal_items')
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT)
    
    # Individual disposal details (can override batch settings)
    disposal_value = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    reason = models.TextField(blank=True)
    remarks = models.TextField(blank=True)
    
    # Status tracking
    is_approved = models.BooleanField(default=False)
    is_disposed = models.BooleanField(default=False)
    disposed_at = models.DateTimeField(null=True, blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['disposal_request', 'asset']
        ordering = ['asset__asset_name']

    def __str__(self):
        return f"{self.asset.asset_name} - {self.disposal_request.request_id}"

    @property
    def final_disposal_value(self):
        """Get disposal value (individual or from batch)"""
        return self.disposal_value or self.disposal_request.disposal_value

    @property
    def gain_loss_amount(self):
        """Calculate gain or loss for this specific asset"""
        return self.final_disposal_value - self.asset.book_value


class DisposalDocument(models.Model):
    """Supporting documents for disposal requests"""
    disposal_request = models.ForeignKey(DisposalRequest, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='disposal_documents/%Y/%m/%d/')
    file_type = models.CharField(max_length=50, blank=True)
    file_size = models.PositiveIntegerField(blank=True, null=True)
    
    uploaded_by = models.ForeignKey(User, on_delete=models.PROTECT)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.title} - {self.disposal_request.request_id}"


class ApprovalLevel(models.Model):
    """Configurable approval levels for disposal workflow"""
    name = models.CharField(max_length=100)
    level = models.PositiveIntegerField(unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    # Role-based approval
    required_role = models.CharField(max_length=100, blank=True)  # Can be linked to Django groups
    min_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    max_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['level']

    def __str__(self):
        return f"Level {self.level}: {self.name}"


class DisposalApproval(models.Model):
    """Approval records for disposal requests"""
    ACTION_CHOICES = [
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('return', 'Return for Revision'),
    ]

    disposal_request = models.ForeignKey(DisposalRequest, on_delete=models.CASCADE, related_name='approvals')
    approval_level = models.ForeignKey(ApprovalLevel, on_delete=models.PROTECT)
    
    # Approval details
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    comments = models.TextField(blank=True)
    
    # Approver details
    approver = models.ForeignKey(User, on_delete=models.PROTECT)
    approved_at = models.DateTimeField(auto_now_add=True)
    
    # IP address for audit
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['approval_level__level', '-approved_at']
        unique_together = ['disposal_request', 'approval_level', 'approver']

    def __str__(self):
        return f"{self.disposal_request.request_id} - Level {self.approval_level.level} - {self.action}"


class DisposalJournalEntry(models.Model):
    """Journal entries generated for disposal transactions"""
    disposal_request = models.ForeignKey(DisposalRequest, on_delete=models.CASCADE, related_name='journal_entries')
    
    # Journal entry details
    entry_date = models.DateField()
    reference = models.CharField(max_length=100)
    description = models.TextField()
    
    # Financial impact
    total_debit = models.DecimalField(max_digits=15, decimal_places=2)
    total_credit = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Status
    is_posted = models.BooleanField(default=False)
    posted_at = models.DateTimeField(null=True, blank=True)
    posted_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    
    # Reversal tracking
    is_reversed = models.BooleanField(default=False)
    reversed_at = models.DateTimeField(null=True, blank=True)
    reversed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='reversed_journal_entries', null=True, blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='disposal_journal_entries_created')

    class Meta:
        ordering = ['-entry_date', '-created_at']

    def __str__(self):
        return f"{self.reference} - {self.disposal_request.request_id}"


class DisposalJournalLine(models.Model):
    """Individual lines in disposal journal entries"""
    journal_entry = models.ForeignKey(DisposalJournalEntry, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey(ChartOfAccount, on_delete=models.PROTECT)
    
    # Line details
    description = models.CharField(max_length=200)
    debit_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    credit_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Asset reference (for tracking)
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, null=True, blank=True)
    
    # Line number for ordering
    line_number = models.PositiveIntegerField()

    class Meta:
        ordering = ['line_number']
        unique_together = ['journal_entry', 'line_number']

    def __str__(self):
        return f"{self.journal_entry.reference} - Line {self.line_number}"


class DisposalAuditLog(models.Model):
    """Comprehensive audit log for all disposal activities"""
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('submit', 'Submit'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('dispose', 'Dispose'),
        ('reverse', 'Reverse'),
        ('delete', 'Delete'),
    ]

    disposal_request = models.ForeignKey(DisposalRequest, on_delete=models.CASCADE, related_name='audit_logs')
    
    # Action details
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField()
    
    # User and system details
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Additional data (JSON field for flexibility)
    additional_data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.disposal_request.request_id} - {self.action} - {self.timestamp}"


class DisposalNotification(models.Model):
    """Notifications for disposal workflow"""
    NOTIFICATION_TYPES = [
        ('submission', 'Request Submitted'),
        ('approval_required', 'Approval Required'),
        ('approved', 'Request Approved'),
        ('rejected', 'Request Rejected'),
        ('disposed', 'Asset Disposed'),
        ('reversed', 'Disposal Reversed'),
    ]

    disposal_request = models.ForeignKey(DisposalRequest, on_delete=models.CASCADE, related_name='notifications')
    
    # Notification details
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Recipients
    recipient = models.ForeignKey(User, on_delete=models.PROTECT)
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Delivery
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.notification_type} - {self.recipient.username} - {self.created_at}"
