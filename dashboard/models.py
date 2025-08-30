from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class ActivityLog(models.Model):
    """Model to track system activities for the daily activity log"""
    
    ACTIVITY_TYPES = [
        ('CREATE', 'Created'),
        ('UPDATE', 'Updated'),
        ('DELETE', 'Deleted'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('POST', 'Posted'),
        ('CANCEL', 'Cancelled'),
        ('APPROVE', 'Approved'),
        ('REJECT', 'Rejected'),
    ]
    
    # Basic Information
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    description = models.TextField()
    model_name = models.CharField(max_length=100, help_text="Name of the model being acted upon")
    object_id = models.PositiveIntegerField(null=True, blank=True, help_text="ID of the object being acted upon")
    
    # User Information
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='activity_logs')
    
    # Generic Foreign Key for related object
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Additional Data
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['activity_type', 'created_at']),
            models.Index(fields=['model_name', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_activity_type_display()} - {self.model_name} - {self.user.username if self.user else 'System'} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    @classmethod
    def log_activity(cls, activity_type, description, user=None, model_name=None, object_id=None, content_object=None, ip_address=None, user_agent=None):
        """Helper method to log activities"""
        if content_object:
            content_type = ContentType.objects.get_for_model(content_object)
            object_id = content_object.id
            model_name = content_object._meta.verbose_name.title()
        
        return cls.objects.create(
            activity_type=activity_type,
            description=description,
            user=user,
            model_name=model_name,
            object_id=object_id,
            content_type=content_type,
            ip_address=ip_address,
            user_agent=user_agent
        )
