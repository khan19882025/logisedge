"""
Signals for automatic logging in the log_history app
"""
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.core.exceptions import ObjectDoesNotExist
from .models import LogHistory
import json


@receiver(post_save)
def log_model_changes(sender, instance, created, **kwargs):
    """
    Automatically log model changes (create, update)
    """
    # Skip logging for our own models to avoid infinite loops
    if sender in [LogHistory, User, ContentType]:
        return
    
    # Skip if instance doesn't have a user field or request context
    if not hasattr(instance, 'user') and not hasattr(instance, 'created_by'):
        return
    
    try:
        # Determine the user who made the change
        user = None
        if hasattr(instance, 'user'):
            user = instance.user
        elif hasattr(instance, 'created_by'):
            user = instance.created_by
        elif hasattr(instance, 'updated_by'):
            user = instance.updated_by
        
        # Determine action type
        if created:
            action_type = LogHistory.ACTION_CREATE
            description = f"Created {sender._meta.verbose_name}"
        else:
            action_type = LogHistory.ACTION_UPDATE
            description = f"Updated {sender._meta.verbose_name}"
        
        # Get object details
        object_name = str(instance)
        object_type = sender._meta.verbose_name
        
        # Create log entry
        LogHistory.objects.create(
            action_type=action_type,
            user=user,
            object_name=object_name,
            object_type=object_type,
            description=description,
            module=sender._meta.app_label,
            content_type=ContentType.objects.get_for_model(sender),
            object_id=str(instance.pk) if hasattr(instance, 'pk') else None,
        )
    except Exception as e:
        # Don't let logging errors break the main functionality
        pass


@receiver(post_delete)
def log_model_deletions(sender, instance, **kwargs):
    """
    Automatically log model deletions
    """
    # Skip logging for our own models
    if sender in [LogHistory, User, ContentType]:
        return
    
    try:
        # Determine the user who made the change
        user = None
        if hasattr(instance, 'user'):
            user = instance.user
        elif hasattr(instance, 'deleted_by'):
            user = instance.deleted_by
        
        # Get object details
        object_name = str(instance)
        object_type = sender._meta.verbose_name
        
        # Create log entry
        LogHistory.objects.create(
            action_type=LogHistory.ACTION_DELETE,
            user=user,
            object_name=object_name,
            object_type=object_type,
            description=f"Deleted {sender._meta.verbose_name}",
            module=sender._meta.app_label,
            content_type=ContentType.objects.get_for_model(sender),
            object_id=str(instance.pk) if hasattr(instance, 'pk') else None,
        )
    except Exception as e:
        # Don't let logging errors break the main functionality
        pass


@receiver(user_logged_in)
def log_user_login(sender, user, request, **kwargs):
    """
    Log user login events
    """
    try:
        user_ip = None
        user_agent = None
        
        if request:
            user_ip = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        LogHistory.objects.create(
            action_type=LogHistory.ACTION_LOGIN,
            user=user,
            user_ip=user_ip,
            user_agent=user_agent,
            description=f"User {user.username} logged in",
            module='accounts',
            severity=LogHistory.SEVERITY_INFO,
        )
    except Exception as e:
        # Don't let logging errors break the main functionality
        pass


@receiver(user_logged_out)
def log_user_logout(sender, user, request, **kwargs):
    """
    Log user logout events
    """
    try:
        user_ip = None
        user_agent = None
        
        if request:
            user_ip = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        LogHistory.objects.create(
            action_type=LogHistory.ACTION_LOGOUT,
            user=user,
            user_ip=user_ip,
            user_agent=user_agent,
            description=f"User {user.username} logged out",
            module='accounts',
            severity=LogHistory.SEVERITY_INFO,
        )
    except Exception as e:
        # Don't let logging errors break the main functionality
        pass


def log_custom_action(action_type, user, description, module='system', 
                     object_instance=None, severity=LogHistory.SEVERITY_LOW,
                     details=None, **kwargs):
    """
    Utility function to log custom actions
    """
    try:
        log_data = {
            'action_type': action_type,
            'user': user,
            'description': description,
            'module': module,
            'severity': severity,
        }
        
        if details:
            log_data['details'] = details
        
        if object_instance:
            log_data.update({
                'object_name': str(object_instance),
                'object_type': object_instance._meta.verbose_name,
                'content_type': ContentType.objects.get_for_model(object_instance),
                'object_id': str(object_instance.pk) if hasattr(object_instance, 'pk') else None,
            })
        
        LogHistory.objects.create(**log_data)
        return True
    except Exception as e:
        # Don't let logging errors break the main functionality
        return False
