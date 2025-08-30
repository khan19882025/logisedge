import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class TemplateCategory(models.Model):
    """Categories for organizing notification templates"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default="#007bff", help_text="Hex color code")
    icon = models.CharField(max_length=50, blank=True, help_text="FontAwesome icon class")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Template Category"
        verbose_name_plural = "Template Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class NotificationTemplate(models.Model):
    """Main notification template model"""
    TEMPLATE_TYPES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
        ('in_app', 'In-App Notification'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES)
    category = models.ForeignKey(TemplateCategory, on_delete=models.CASCADE, related_name='templates')
    
    # Content fields
    subject = models.CharField(max_length=255, blank=True, help_text="Email subject or SMS title")
    content = models.TextField(help_text="Template content with placeholders")
    html_content = models.TextField(blank=True, help_text="HTML version for email templates")
    
    # Language and localization
    language = models.CharField(max_length=10, default='en', help_text="Language code (en, ar, ur)")
    is_default_language = models.BooleanField(default=False, help_text="Is this the default language version?")
    parent_template = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, 
                                      related_name='translations', help_text="Parent template for translations")
    
    # Settings and configuration
    priority = models.CharField(max_length=20, choices=PRIORITY_LEVELS, default='normal')
    is_active = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, 
                                  related_name='approved_templates')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    tags = models.JSONField(default=list, blank=True, help_text="Tags for categorization")
    placeholders = models.JSONField(default=list, blank=True, help_text="Available placeholders")
    version = models.PositiveIntegerField(default=1)
    
    # Audit fields
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_notification_templates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updated_notification_templates')
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Notification Template"
        verbose_name_plural = "Notification Templates"
        ordering = ['-updated_at']
        unique_together = ['name', 'language']
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()}) - {self.language.upper()}"
    
    def clean(self):
        """Validate template content and placeholders"""
        if self.template_type == 'email' and not self.html_content:
            raise ValidationError(_("Email templates must have HTML content"))
        
        if self.template_type == 'sms' and len(self.content) > 160:
            raise ValidationError(_("SMS content cannot exceed 160 characters"))
    
    def save(self, *args, **kwargs):
        """Auto-extract placeholders and increment version on content change"""
        if self.pk:
            try:
                old_instance = NotificationTemplate.objects.get(pk=self.pk)
                if old_instance.content != self.content or old_instance.html_content != self.html_content:
                    self.version += 1
            except NotificationTemplate.DoesNotExist:
                pass  # New template being created
        
        # Extract placeholders from content
        import re
        placeholder_pattern = r'\{\{([^}]+)\}\}'
        self.placeholders = list(set(re.findall(placeholder_pattern, self.content)))
        if self.html_content:
            html_placeholders = list(set(re.findall(placeholder_pattern, self.html_content)))
            self.placeholders.extend(html_placeholders)
            self.placeholders = list(set(self.placeholders))
        
        super().save(*args, **kwargs)


class TemplateVersion(models.Model):
    """Version control for template changes"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(NotificationTemplate, on_delete=models.CASCADE, related_name='versions')
    version_number = models.PositiveIntegerField()
    
    # Content snapshots
    content = models.TextField()
    html_content = models.TextField(blank=True)
    subject = models.CharField(max_length=255, blank=True)
    
    # Change metadata
    change_reason = models.CharField(max_length=500, blank=True)
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    changed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Template Version"
        verbose_name_plural = "Template Versions"
        ordering = ['-version_number']
        unique_together = ['template', 'version_number']
    
    def __str__(self):
        return f"{self.template.name} v{self.version_number}"


class TemplatePlaceholder(models.Model):
    """Available placeholders for templates"""
    PLACEHOLDER_TYPES = [
        ('customer', 'Customer Information'),
        ('order', 'Order Information'),
        ('payment', 'Payment Information'),
        ('system', 'System Information'),
        ('custom', 'Custom Field'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    placeholder_type = models.CharField(max_length=20, choices=PLACEHOLDER_TYPES)
    example_value = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    is_required = models.BooleanField(default=False)
    
    # Formatting options
    data_type = models.CharField(max_length=50, default='string', 
                               help_text="Data type (string, number, date, etc.)")
    format_string = models.CharField(max_length=100, blank=True, 
                                   help_text="Format string for dates/numbers")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Template Placeholder"
        verbose_name_plural = "Template Placeholders"
        ordering = ['placeholder_type', 'name']
    
    def __str__(self):
        return f"{{{{{self.name}}}}} - {self.display_name}"


class TemplateTest(models.Model):
    """Test records for templates"""
    TEST_STATUSES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(NotificationTemplate, on_delete=models.CASCADE, related_name='tests')
    
    # Test configuration
    test_data = models.JSONField(default=dict, help_text="Test data for placeholders")
    recipient_email = models.EmailField(blank=True)
    recipient_phone = models.CharField(max_length=20, blank=True)
    
    # Test results
    status = models.CharField(max_length=20, choices=TEST_STATUSES, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    # Error information
    error_message = models.TextField(blank=True)
    error_code = models.CharField(max_length=100, blank=True)
    
    # Test metadata
    tested_by = models.ForeignKey(User, on_delete=models.CASCADE)
    tested_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Template Test"
        verbose_name_plural = "Template Tests"
        ordering = ['-tested_at']
    
    def __str__(self):
        return f"Test of {self.template.name} by {self.tested_by.username}"


class TemplateAuditLog(models.Model):
    """Audit trail for template changes"""
    ACTION_TYPES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('deleted', 'Deleted'),
        ('activated', 'Activated'),
        ('deactivated', 'Deactivated'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('tested', 'Tested'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(NotificationTemplate, on_delete=models.CASCADE, related_name='audit_logs')
    
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Change details
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    change_reason = models.CharField(max_length=500, blank=True)
    
    # Additional context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Template Audit Log"
        verbose_name_plural = "Template Audit Logs"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.action.title()} - {self.template.name} by {self.user.username}"


class TemplatePermission(models.Model):
    """Role-based permissions for templates"""
    PERMISSION_TYPES = [
        ('view', 'View'),
        ('create', 'Create'),
        ('edit', 'Edit'),
        ('delete', 'Delete'),
        ('approve', 'Approve'),
        ('test', 'Test'),
        ('publish', 'Publish'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='template_permissions')
    permission_type = models.CharField(max_length=20, choices=PERMISSION_TYPES)
    
    # Scope (null means all templates, otherwise specific category)
    category = models.ForeignKey(TemplateCategory, null=True, blank=True, on_delete=models.CASCADE)
    
    granted_at = models.DateTimeField(auto_now_add=True)
    granted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='granted_permissions')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Template Permission"
        verbose_name_plural = "Template Permissions"
        unique_together = ['user', 'permission_type', 'category']
    
    def __str__(self):
        scope = self.category.name if self.category else "All Categories"
        return f"{self.user.username} - {self.permission_type} - {scope}"
