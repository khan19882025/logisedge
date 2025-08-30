from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator
import uuid


class AssetMovementLog(models.Model):
    """Track all asset movements and transfers"""
    MOVEMENT_TYPES = [
        ('transfer', 'Transfer'),
        ('assignment', 'Assignment'),
        ('return', 'Return'),
        ('disposal', 'Disposal'),
        ('maintenance', 'Maintenance'),
        ('inspection', 'Inspection'),
        ('relocation', 'Relocation'),
        ('other', 'Other'),
    ]

    MOVEMENT_REASONS = [
        ('operational', 'Operational Need'),
        ('maintenance', 'Maintenance/Repair'),
        ('inspection', 'Inspection/Audit'),
        ('relocation', 'Office Relocation'),
        ('disposal', 'Asset Disposal'),
        ('assignment', 'Employee Assignment'),
        ('return', 'Asset Return'),
        ('other', 'Other'),
    ]

    # Basic Information
    movement_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.ForeignKey('asset_register.Asset', on_delete=models.CASCADE, related_name='movement_logs')
    
    # Movement Details
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES, default='transfer')
    movement_date = models.DateTimeField(default=timezone.now)
    movement_reason = models.CharField(max_length=20, choices=MOVEMENT_REASONS, default='operational')
    reason_description = models.TextField(blank=True, help_text="Detailed reason for the movement")
    
    # Location Information
    from_location = models.ForeignKey('asset_register.AssetLocation', on_delete=models.PROTECT, 
                                     related_name='movement_logs_from', null=True, blank=True)
    to_location = models.ForeignKey('asset_register.AssetLocation', on_delete=models.PROTECT, 
                                   related_name='movement_logs_to', null=True, blank=True)
    
    # User Information
    moved_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='asset_movement_logs_created')
    from_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                 related_name='asset_movement_logs_from')
    to_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                               related_name='asset_movement_logs_to')
    
    # Additional Information
    notes = models.TextField(blank=True, help_text="Additional notes about the movement")
    estimated_duration = models.PositiveIntegerField(null=True, blank=True, 
                                                   help_text="Estimated duration in days")
    actual_return_date = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_completed = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='asset_movement_logs_approved')
    approved_date = models.DateTimeField(null=True, blank=True)
    
    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='movement_logs_created')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                  related_name='movement_logs_updated')

    class Meta:
        ordering = ['-movement_date']
        verbose_name = "Asset Movement Log"
        verbose_name_plural = "Asset Movement Logs"
        indexes = [
            models.Index(fields=['asset']),
            models.Index(fields=['movement_date']),
            models.Index(fields=['movement_type']),
            models.Index(fields=['from_location']),
            models.Index(fields=['to_location']),
            models.Index(fields=['moved_by']),
        ]

    def __str__(self):
        return f"{self.asset.asset_code} - {self.get_movement_type_display()} - {self.movement_date.strftime('%Y-%m-%d %H:%M')}"

    def save(self, *args, **kwargs):
        # Auto-approve if not specified
        if not self.approved_by and self.is_approved:
            self.approved_by = self.moved_by
            self.approved_date = timezone.now()
        
        super().save(*args, **kwargs)

    @property
    def duration_days(self):
        """Calculate duration in days if return date is set"""
        if self.actual_return_date and self.movement_date:
            return (self.actual_return_date - self.movement_date).days
        return None

    @property
    def is_overdue(self):
        """Check if movement is overdue based on estimated duration"""
        if self.estimated_duration and not self.actual_return_date:
            expected_return = self.movement_date + timezone.timedelta(days=self.estimated_duration)
            return timezone.now() > expected_return
        return False


class AssetMovementTemplate(models.Model):
    """Templates for common asset movements"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    movement_type = models.CharField(max_length=20, choices=AssetMovementLog.MOVEMENT_TYPES)
    movement_reason = models.CharField(max_length=20, choices=AssetMovementLog.MOVEMENT_REASONS)
    default_notes = models.TextField(blank=True)
    estimated_duration = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class AssetMovementSettings(models.Model):
    """Settings for asset movement logging"""
    require_approval = models.BooleanField(default=False, 
                                         help_text="Require approval for asset movements")
    auto_approve_assignments = models.BooleanField(default=True, 
                                                  help_text="Auto-approve asset assignments")
    require_reason = models.BooleanField(default=True, 
                                       help_text="Require reason for all movements")
    max_duration_days = models.PositiveIntegerField(default=365, 
                                                   help_text="Maximum allowed movement duration in days")
    enable_notifications = models.BooleanField(default=True, 
                                              help_text="Enable email notifications for movements")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Asset Movement Setting"
        verbose_name_plural = "Asset Movement Settings"

    def __str__(self):
        return "Asset Movement Settings"

    @classmethod
    def get_settings(cls):
        """Get or create settings instance"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings
