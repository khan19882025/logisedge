from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class ExportLog(models.Model):
    """Model to track all bulk export activities"""
    
    EXPORT_TYPES = [
        ('customers', 'Customers'),
        ('items', 'Items'),
        ('transactions', 'Transactions'),
    ]
    
    EXPORT_FORMATS = [
        ('csv', 'CSV'),
        ('excel', 'Excel'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='export_logs')
    export_type = models.CharField(max_length=20, choices=EXPORT_TYPES)
    export_format = models.CharField(max_length=10, choices=EXPORT_FORMATS)
    filename = models.CharField(max_length=255)
    filters_applied = models.JSONField(default=dict, blank=True)
    records_exported = models.PositiveIntegerField(default=0)
    file_size = models.PositiveIntegerField(default=0)  # in bytes
    created_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default='processing', choices=[
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ])
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Export Log'
        verbose_name_plural = 'Export Logs'
        permissions = [
            ('can_export_data', 'Can export data'),
            ('can_view_export_logs', 'Can view export logs'),
        ]
    
    def __str__(self):
        return f"{self.export_type.title()} Export by {self.user.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def duration(self):
        """Calculate export duration in seconds"""
        if self.completed_at and self.created_at:
            return (self.completed_at - self.created_at).total_seconds()
        return None
