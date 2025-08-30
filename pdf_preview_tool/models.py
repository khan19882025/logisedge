import uuid
import os
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.utils import timezone
from django.core.exceptions import ValidationError


def validate_file_size(value):
    """Custom validator for file size (2MB limit)"""
    if value.size > 2 * 1024 * 1024:  # 2MB in bytes
        raise ValidationError('File size must be less than 2MB.')


class DocumentType(models.Model):
    """Types of documents that can be previewed"""
    DOCUMENT_CATEGORIES = [
        ('invoice', 'Invoice'),
        ('delivery_note', 'Delivery Note'),
        ('purchase_order', 'Purchase Order'),
        ('sales_order', 'Sales Order'),
        ('receipt', 'Receipt'),
        ('report', 'Report'),
        ('contract', 'Contract'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50, choices=DOCUMENT_CATEGORIES)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=False, help_text="Requires approval before preview")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'Document Type'
        verbose_name_plural = 'Document Types'
    
    def __str__(self):
        return f"{self.get_category_display()} - {self.name}"


class Document(models.Model):
    """Documents available for preview"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('archived', 'Archived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    document_type = models.ForeignKey(DocumentType, on_delete=models.CASCADE, related_name='documents')
    file_path = models.CharField(max_length=500, help_text="Path to the document file")
    file_size = models.BigIntegerField(help_text="File size in bytes")
    page_count = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # ERP Integration fields
    erp_reference = models.CharField(max_length=100, blank=True, help_text="Reference from ERP system")
    erp_module = models.CharField(max_length=50, blank=True, help_text="ERP module source")
    
    # Metadata
    description = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional document metadata")
    
    # Access control
    is_public = models.BooleanField(default=False, help_text="Publicly accessible")
    allowed_roles = models.JSONField(default=list, blank=True, help_text="User roles that can access")
    allowed_users = models.ManyToManyField(User, blank=True, related_name='accessible_documents')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_documents')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updated_documents')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
    
    def __str__(self):
        return f"{self.title} ({self.document_type.name})"
    
    def get_file_extension(self):
        """Get file extension from file path"""
        return os.path.splitext(self.file_path)[1].lower()
    
    def is_accessible_by_user(self, user):
        """Check if user can access this document"""
        if self.is_public:
            return True
        
        if user in self.allowed_users.all():
            return True
        
        # Check user roles (implement based on your role system)
        user_roles = getattr(user, 'roles', [])
        if any(role in self.allowed_roles for role in user_roles):
            return True
        
        return False


class PreviewSession(models.Model):
    """Track document preview sessions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='preview_sessions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='preview_sessions')
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Preview Session'
        verbose_name_plural = 'Preview Sessions'
    
    def __str__(self):
        return f"Preview session for {self.document.title} by {self.user.username}"
    
    def end_session(self):
        """End the preview session and calculate duration"""
        if not self.ended_at:
            self.ended_at = timezone.now()
            duration = self.ended_at - self.started_at
            self.duration_seconds = int(duration.total_seconds())
            self.save()


class PreviewAction(models.Model):
    """Track user actions during preview sessions"""
    ACTION_TYPES = [
        ('zoom_in', 'Zoom In'),
        ('zoom_out', 'Zoom Out'),
        ('page_nav', 'Page Navigation'),
        ('download', 'Download'),
        ('print', 'Print'),
        ('share', 'Share'),
        ('comment', 'Comment'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(PreviewSession, on_delete=models.CASCADE, related_name='actions')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Preview Action'
        verbose_name_plural = 'Preview Actions'
    
    def __str__(self):
        return f"{self.get_action_type_display()} at {self.timestamp}"


class DocumentAccessLog(models.Model):
    """Log all document access attempts"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='access_logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='document_access_logs')
    access_type = models.CharField(max_length=20, choices=[
        ('view', 'View'),
        ('download', 'Download'),
        ('print', 'Print'),
        ('share', 'Share'),
    ])
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Document Access Log'
        verbose_name_plural = 'Document Access Logs'
    
    def __str__(self):
        return f"{self.access_type} access to {self.document.title} by {self.user.username}"


class PreviewSettings(models.Model):
    """User-specific preview settings"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preview_settings')
    default_zoom = models.FloatField(default=100.0, help_text="Default zoom percentage")
    show_thumbnails = models.BooleanField(default=True, help_text="Show page thumbnails by default")
    auto_fit_page = models.BooleanField(default=True, help_text="Auto-fit page to viewport")
    enable_annotations = models.BooleanField(default=False, help_text="Enable annotation tools")
    theme = models.CharField(max_length=20, choices=[
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('auto', 'Auto'),
    ], default='light')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Preview Settings'
        verbose_name_plural = 'Preview Settings'
    
    def __str__(self):
        return f"Settings for {self.user.username}"


class SignatureStamp(models.Model):
    """
    Model to store user signatures and company stamps for PDF documents.
    Each user can have only one signature/stamp image.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='signature_stamp')
    file = models.ImageField(
        upload_to='signatures/',
        validators=[
            FileExtensionValidator(allowed_extensions=['png', 'jpg', 'jpeg']),
            validate_file_size,
        ],
        help_text='Upload PNG, JPG, or JPEG image (max 2MB)'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Signature/Stamp'
        verbose_name_plural = 'Signatures/Stamps'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"Signature/Stamp for {self.user.username}"
    
    def get_upload_path(self, filename):
        """Generate upload path: media/signatures/<username>/<filename>"""
        username = self.user.username
        return f'signatures/{username}/{filename}'
    
    def save(self, *args, **kwargs):
        if self.pk:  # If updating existing record
            try:
                old_instance = SignatureStamp.objects.get(pk=self.pk)
                if old_instance.file and old_instance.file != self.file:
                    # Delete old file
                    if os.path.exists(old_instance.file.path):
                        os.remove(old_instance.file.path)
            except SignatureStamp.DoesNotExist:
                pass
        
        # Set custom upload path
        if self.file:
            filename = os.path.basename(self.file.name)
            self.file.name = self.get_upload_path(filename)
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # Delete file from filesystem
        if self.file:
            if os.path.exists(self.file.path):
                os.remove(self.file.path)
        super().delete(*args, **kwargs)
    
    @property
    def file_size_mb(self):
        """Return file size in MB"""
        if self.file:
            return round(self.file.size / (1024 * 1024), 2)
        return 0
    
    @property
    def file_extension(self):
        """Return file extension"""
        if self.file:
            return os.path.splitext(self.file.name)[1].lower()
        return ''
