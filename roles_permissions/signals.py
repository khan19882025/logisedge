from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import json

from .models import (
    Role, Permission, UserRole, PermissionGroup, UserPermission,
    Department, CostCenter, AccessLog, RoleAuditLog
)


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def create_audit_log(user, action, target_user=None, role=None, permission=None, 
                    old_values=None, new_values=None, request=None, notes=None):
    """Helper function to create audit logs"""
    try:
        # Get request information if available
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        RoleAuditLog.objects.create(
            user=user,
            action=action,
            target_user=target_user,
            role=role,
            permission=permission,
            old_values=old_values or {},
            new_values=new_values or {},
            ip_address=ip_address,
            user_agent=user_agent,
            notes=notes
        )
    except Exception as e:
        # Log error but don't break the main operation
        print(f"Error creating audit log: {e}")


def create_access_log(user, access_type, success=True, resource_type=None, 
                     resource_id=None, error_message=None, request=None, metadata=None):
    """Helper function to create access logs"""
    try:
        # Get request information if available
        ip_address = None
        user_agent = None
        session_id = None
        
        if request:
            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            session_id = request.session.session_key if request.session else None
        
        AccessLog.objects.create(
            user=user,
            access_type=access_type,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            success=success,
            error_message=error_message,
            metadata=metadata or {}
        )
    except Exception as e:
        # Log error but don't break the main operation
        print(f"Error creating access log: {e}")


# Role signals
@receiver(post_save, sender=Role)
def role_post_save(sender, instance, created, **kwargs):
    """Handle role creation and updates"""
    # Get the request from kwargs if available
    request = kwargs.get('request')
    
    if created:
        create_audit_log(
            user=kwargs.get('user') or User.objects.filter(is_superuser=True).first(),
            action='create',
            role=instance,
            new_values={
                'name': instance.name,
                'description': instance.description,
                'role_type': instance.role_type,
                'department': instance.department,
                'cost_center': instance.cost_center,
                'branch': instance.branch,
                'project': instance.project,
                'location': instance.location,
                'is_active': instance.is_active,
                'is_system_role': instance.is_system_role,
            },
            request=request,
            notes=f"Role '{instance.name}' created"
        )
    else:
        # Get old values from instance
        old_values = {}
        if hasattr(instance, '_old_values'):
            old_values = instance._old_values
        
        create_audit_log(
            user=kwargs.get('user') or User.objects.filter(is_superuser=True).first(),
            action='update',
            role=instance,
            old_values=old_values,
            new_values={
                'name': instance.name,
                'description': instance.description,
                'role_type': instance.role_type,
                'department': instance.department,
                'cost_center': instance.cost_center,
                'branch': instance.branch,
                'project': instance.project,
                'location': instance.location,
                'is_active': instance.is_active,
                'is_system_role': instance.is_system_role,
            },
            request=request,
            notes=f"Role '{instance.name}' updated"
        )


@receiver(pre_save, sender=Role)
def role_pre_save(sender, instance, **kwargs):
    """Store old values before saving"""
    if instance.pk:
        try:
            old_instance = Role.objects.get(pk=instance.pk)
            instance._old_values = {
                'name': old_instance.name,
                'description': old_instance.description,
                'role_type': old_instance.role_type,
                'department': old_instance.department,
                'cost_center': old_instance.cost_center,
                'branch': old_instance.branch,
                'project': old_instance.project,
                'location': old_instance.location,
                'is_active': old_instance.is_active,
                'is_system_role': old_instance.is_system_role,
            }
        except Role.DoesNotExist:
            instance._old_values = {}


@receiver(post_delete, sender=Role)
def role_post_delete(sender, instance, **kwargs):
    """Handle role deletion"""
    request = kwargs.get('request')
    
    create_audit_log(
        user=kwargs.get('user') or User.objects.filter(is_superuser=True).first(),
        action='delete',
        role=instance,
        old_values={
            'name': instance.name,
            'description': instance.description,
            'role_type': instance.role_type,
            'department': instance.department,
            'cost_center': instance.cost_center,
            'branch': instance.branch,
            'project': instance.project,
            'location': instance.location,
            'is_active': instance.is_active,
            'is_system_role': instance.is_system_role,
        },
        request=request,
        notes=f"Role '{instance.name}' deleted"
    )


# Permission signals
@receiver(post_save, sender=Permission)
def permission_post_save(sender, instance, created, **kwargs):
    """Handle permission creation and updates"""
    request = kwargs.get('request')
    
    if created:
        create_audit_log(
            user=kwargs.get('user') or User.objects.filter(is_superuser=True).first(),
            action='create',
            permission=instance,
            new_values={
                'name': instance.name,
                'codename': instance.codename,
                'description': instance.description,
                'permission_type': instance.permission_type,
                'module': instance.module,
                'feature': instance.feature,
                'is_active': instance.is_active,
            },
            request=request,
            notes=f"Permission '{instance.name}' created"
        )
    else:
        old_values = {}
        if hasattr(instance, '_old_values'):
            old_values = instance._old_values
        
        create_audit_log(
            user=kwargs.get('user') or User.objects.filter(is_superuser=True).first(),
            action='update',
            permission=instance,
            old_values=old_values,
            new_values={
                'name': instance.name,
                'codename': instance.codename,
                'description': instance.description,
                'permission_type': instance.permission_type,
                'module': instance.module,
                'feature': instance.feature,
                'is_active': instance.is_active,
            },
            request=request,
            notes=f"Permission '{instance.name}' updated"
        )


@receiver(pre_save, sender=Permission)
def permission_pre_save(sender, instance, **kwargs):
    """Store old values before saving"""
    if instance.pk:
        try:
            old_instance = Permission.objects.get(pk=instance.pk)
            instance._old_values = {
                'name': old_instance.name,
                'codename': old_instance.codename,
                'description': old_instance.description,
                'permission_type': old_instance.permission_type,
                'module': old_instance.module,
                'feature': old_instance.feature,
                'is_active': old_instance.is_active,
            }
        except Permission.DoesNotExist:
            instance._old_values = {}


@receiver(post_delete, sender=Permission)
def permission_post_delete(sender, instance, **kwargs):
    """Handle permission deletion"""
    request = kwargs.get('request')
    
    create_audit_log(
        user=kwargs.get('user') or User.objects.filter(is_superuser=True).first(),
        action='delete',
        permission=instance,
        old_values={
            'name': instance.name,
            'codename': instance.codename,
            'description': instance.description,
            'permission_type': instance.permission_type,
            'module': instance.module,
            'feature': instance.feature,
            'is_active': instance.is_active,
        },
        request=request,
        notes=f"Permission '{instance.name}' deleted"
    )


# UserRole signals
@receiver(post_save, sender=UserRole)
def user_role_post_save(sender, instance, created, **kwargs):
    """Handle user role assignment"""
    request = kwargs.get('request')
    
    if created:
        create_audit_log(
            user=instance.assigned_by or kwargs.get('user') or User.objects.filter(is_superuser=True).first(),
            action='assign',
            target_user=instance.user,
            role=instance.role,
            new_values={
                'is_primary': instance.is_primary,
                'expires_at': instance.expires_at.isoformat() if instance.expires_at else None,
                'is_active': instance.is_active,
                'conditions': instance.conditions,
                'notes': instance.notes,
            },
            request=request,
            notes=f"Role '{instance.role.name}' assigned to user '{instance.user.username}'"
        )
    else:
        old_values = {}
        if hasattr(instance, '_old_values'):
            old_values = instance._old_values
        
        create_audit_log(
            user=instance.assigned_by or kwargs.get('user') or User.objects.filter(is_superuser=True).first(),
            action='update',
            target_user=instance.user,
            role=instance.role,
            old_values=old_values,
            new_values={
                'is_primary': instance.is_primary,
                'expires_at': instance.expires_at.isoformat() if instance.expires_at else None,
                'is_active': instance.is_active,
                'conditions': instance.conditions,
                'notes': instance.notes,
            },
            request=request,
            notes=f"User role assignment updated for '{instance.user.username}' - '{instance.role.name}'"
        )


@receiver(pre_save, sender=UserRole)
def user_role_pre_save(sender, instance, **kwargs):
    """Store old values before saving"""
    if instance.pk:
        try:
            old_instance = UserRole.objects.get(pk=instance.pk)
            instance._old_values = {
                'is_primary': old_instance.is_primary,
                'expires_at': old_instance.expires_at.isoformat() if old_instance.expires_at else None,
                'is_active': old_instance.is_active,
                'conditions': old_instance.conditions,
                'notes': old_instance.notes,
            }
        except UserRole.DoesNotExist:
            instance._old_values = {}


@receiver(post_delete, sender=UserRole)
def user_role_post_delete(sender, instance, **kwargs):
    """Handle user role removal"""
    request = kwargs.get('request')
    
    create_audit_log(
        user=kwargs.get('user') or User.objects.filter(is_superuser=True).first(),
        action='revoke',
        target_user=instance.user,
        role=instance.role,
        old_values={
            'is_primary': instance.is_primary,
            'expires_at': instance.expires_at.isoformat() if instance.expires_at else None,
            'is_active': instance.is_active,
            'conditions': instance.conditions,
            'notes': instance.notes,
        },
        request=request,
        notes=f"Role '{instance.role.name}' revoked from user '{instance.user.username}'"
    )


# UserPermission signals
@receiver(post_save, sender=UserPermission)
def user_permission_post_save(sender, instance, created, **kwargs):
    """Handle direct user permission assignment"""
    request = kwargs.get('request')
    
    if created:
        create_audit_log(
            user=instance.granted_by or kwargs.get('user') or User.objects.filter(is_superuser=True).first(),
            action='assign' if instance.is_granted else 'revoke',
            target_user=instance.user,
            permission=instance.permission,
            new_values={
                'is_granted': instance.is_granted,
                'expires_at': instance.expires_at.isoformat() if instance.expires_at else None,
                'conditions': instance.conditions,
                'reason': instance.reason,
            },
            request=request,
            notes=f"Permission '{instance.permission.name}' {'granted to' if instance.is_granted else 'revoked from'} user '{instance.user.username}'"
        )
    else:
        old_values = {}
        if hasattr(instance, '_old_values'):
            old_values = instance._old_values
        
        create_audit_log(
            user=instance.granted_by or kwargs.get('user') or User.objects.filter(is_superuser=True).first(),
            action='update',
            target_user=instance.user,
            permission=instance.permission,
            old_values=old_values,
            new_values={
                'is_granted': instance.is_granted,
                'expires_at': instance.expires_at.isoformat() if instance.expires_at else None,
                'conditions': instance.conditions,
                'reason': instance.reason,
            },
            request=request,
            notes=f"User permission updated for '{instance.user.username}' - '{instance.permission.name}'"
        )


@receiver(pre_save, sender=UserPermission)
def user_permission_pre_save(sender, instance, **kwargs):
    """Store old values before saving"""
    if instance.pk:
        try:
            old_instance = UserPermission.objects.get(pk=instance.pk)
            instance._old_values = {
                'is_granted': old_instance.is_granted,
                'expires_at': old_instance.expires_at.isoformat() if old_instance.expires_at else None,
                'conditions': old_instance.conditions,
                'reason': old_instance.reason,
            }
        except UserPermission.DoesNotExist:
            instance._old_values = {}


@receiver(post_delete, sender=UserPermission)
def user_permission_post_delete(sender, instance, **kwargs):
    """Handle direct user permission removal"""
    request = kwargs.get('request')
    
    create_audit_log(
        user=kwargs.get('user') or User.objects.filter(is_superuser=True).first(),
        action='revoke',
        target_user=instance.user,
        permission=instance.permission,
        old_values={
            'is_granted': instance.is_granted,
            'expires_at': instance.expires_at.isoformat() if instance.expires_at else None,
            'conditions': instance.conditions,
            'reason': instance.reason,
        },
        request=request,
        notes=f"Direct permission '{instance.permission.name}' removed from user '{instance.user.username}'"
    )


# Department signals
@receiver(post_save, sender=Department)
def department_post_save(sender, instance, created, **kwargs):
    """Handle department creation and updates"""
    request = kwargs.get('request')
    
    if created:
        create_audit_log(
            user=kwargs.get('user') or User.objects.filter(is_superuser=True).first(),
            action='create',
            new_values={
                'name': instance.name,
                'code': instance.code,
                'description': instance.description,
                'parent_department': instance.parent_department.name if instance.parent_department else None,
                'manager': instance.manager.username if instance.manager else None,
                'is_active': instance.is_active,
            },
            request=request,
            notes=f"Department '{instance.name}' created"
        )
    else:
        old_values = {}
        if hasattr(instance, '_old_values'):
            old_values = instance._old_values
        
        create_audit_log(
            user=kwargs.get('user') or User.objects.filter(is_superuser=True).first(),
            action='update',
            old_values=old_values,
            new_values={
                'name': instance.name,
                'code': instance.code,
                'description': instance.description,
                'parent_department': instance.parent_department.name if instance.parent_department else None,
                'manager': instance.manager.username if instance.manager else None,
                'is_active': instance.is_active,
            },
            request=request,
            notes=f"Department '{instance.name}' updated"
        )


@receiver(pre_save, sender=Department)
def department_pre_save(sender, instance, **kwargs):
    """Store old values before saving"""
    if instance.pk:
        try:
            old_instance = Department.objects.get(pk=instance.pk)
            instance._old_values = {
                'name': old_instance.name,
                'code': old_instance.code,
                'description': old_instance.description,
                'parent_department': old_instance.parent_department.name if old_instance.parent_department else None,
                'manager': old_instance.manager.username if old_instance.manager else None,
                'is_active': old_instance.is_active,
            }
        except Department.DoesNotExist:
            instance._old_values = {}


# CostCenter signals
@receiver(post_save, sender=CostCenter)
def cost_center_post_save(sender, instance, created, **kwargs):
    """Handle cost center creation and updates"""
    request = kwargs.get('request')
    
    if created:
        create_audit_log(
            user=kwargs.get('user') or User.objects.filter(is_superuser=True).first(),
            action='create',
            new_values={
                'name': instance.name,
                'code': instance.code,
                'description': instance.description,
                'department': instance.department.name if instance.department else None,
                'manager': instance.manager.username if instance.manager else None,
                'is_active': instance.is_active,
            },
            request=request,
            notes=f"Cost Center '{instance.name}' created"
        )
    else:
        old_values = {}
        if hasattr(instance, '_old_values'):
            old_values = instance._old_values
        
        create_audit_log(
            user=kwargs.get('user') or User.objects.filter(is_superuser=True).first(),
            action='update',
            old_values=old_values,
            new_values={
                'name': instance.name,
                'code': instance.code,
                'description': instance.description,
                'department': instance.department.name if instance.department else None,
                'manager': instance.manager.username if instance.manager else None,
                'is_active': instance.is_active,
            },
            request=request,
            notes=f"Cost Center '{instance.name}' updated"
        )


@receiver(pre_save, sender=CostCenter)
def cost_center_pre_save(sender, instance, **kwargs):
    """Store old values before saving"""
    if instance.pk:
        try:
            old_instance = CostCenter.objects.get(pk=instance.pk)
            instance._old_values = {
                'name': old_instance.name,
                'code': old_instance.code,
                'description': old_instance.description,
                'department': old_instance.department.name if old_instance.department else None,
                'manager': old_instance.manager.username if old_instance.manager else None,
                'is_active': old_instance.is_active,
            }
        except CostCenter.DoesNotExist:
            instance._old_values = {}
