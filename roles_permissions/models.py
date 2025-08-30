from django.db import models
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
import uuid


class Permission(models.Model):
    """Model for defining granular permissions"""
    PERMISSION_TYPES = [
        ('view', 'View'),
        ('create', 'Create'),
        ('edit', 'Edit'),
        ('delete', 'Delete'),
        ('approve', 'Approve'),
        ('export', 'Export'),
        ('import', 'Import'),
        ('print', 'Print'),
        ('share', 'Share'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    codename = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    permission_type = models.CharField(max_length=20, choices=PERMISSION_TYPES)
    module = models.CharField(max_length=50)  # e.g., 'finance', 'hr', 'procurement'
    feature = models.CharField(max_length=50)  # e.g., 'invoices', 'employees', 'purchase_orders'
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['module', 'feature', 'permission_type']
        verbose_name = 'Permission'
        verbose_name_plural = 'Permissions'
    
    def __str__(self):
        return f"{self.module}.{self.feature}.{self.permission_type}"


class PermissionGroup(models.Model):
    """Model for grouping permissions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(Permission, related_name='permission_groups')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Permission Group'
        verbose_name_plural = 'Permission Groups'
    
    def __str__(self):
        return self.name


class Role(models.Model):
    """Model for defining roles with hierarchical support"""
    ROLE_TYPES = [
        ('system', 'System Role'),
        ('custom', 'Custom Role'),
        ('department', 'Department Role'),
        ('project', 'Project Role'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    role_type = models.CharField(max_length=20, choices=ROLE_TYPES, default='custom')
    parent_role = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='child_roles')
    permissions = models.ManyToManyField(Permission, through='RolePermission', related_name='roles')
    permission_groups = models.ManyToManyField(PermissionGroup, blank=True, related_name='roles')
    department = models.CharField(max_length=100, blank=True)
    cost_center = models.CharField(max_length=50, blank=True)
    branch = models.CharField(max_length=100, blank=True)
    project = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    is_system_role = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'
    
    def __str__(self):
        return self.name
    
    def get_all_permissions(self):
        """Get all permissions including inherited ones"""
        permissions = set(self.permissions.all())
        
        # Add permissions from permission groups
        for group in self.permission_groups.all():
            permissions.update(group.permissions.all())
        
        # Add inherited permissions from parent role
        if self.parent_role:
            permissions.update(self.parent_role.get_all_permissions())
        
        return permissions


class RolePermission(models.Model):
    """Intermediate model for role-permission relationship with conditions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='role_permissions')
    is_granted = models.BooleanField(default=True)
    conditions = models.JSONField(default=dict, blank=True)  # Store conditional logic
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['role', 'permission']
        verbose_name = 'Role Permission'
        verbose_name_plural = 'Role Permissions'
    
    def __str__(self):
        return f"{self.role.name} - {self.permission.name}"


class UserRole(models.Model):
    """Model for assigning roles to users with conditions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='user_roles')
    is_primary = models.BooleanField(default=False)  # Primary role for the user
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='role_assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    conditions = models.JSONField(default=dict, blank=True)  # Store conditional logic
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['user', 'role']
        ordering = ['-is_primary', '-assigned_at']
        verbose_name = 'User Role'
        verbose_name_plural = 'User Roles'
    
    def __str__(self):
        return f"{self.user.username} - {self.role.name}"
    
    @property
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class UserPermission(models.Model):
    """Model for direct user permissions (overrides role permissions)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rp_user_permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='user_permissions')
    is_granted = models.BooleanField(default=True)
    granted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='permission_grants')
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    conditions = models.JSONField(default=dict, blank=True)
    reason = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['user', 'permission']
        verbose_name = 'User Permission'
        verbose_name_plural = 'User Permissions'
    
    def __str__(self):
        return f"{self.user.username} - {self.permission.name}"


class AccessLog(models.Model):
    """Model for logging user access attempts"""
    ACCESS_TYPES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('view', 'View'),
        ('create', 'Create'),
        ('edit', 'Edit'),
        ('delete', 'Delete'),
        ('approve', 'Approve'),
        ('export', 'Export'),
        ('import', 'Import'),
        ('print', 'Print'),
        ('share', 'Share'),
        ('denied', 'Access Denied'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='access_logs')
    access_type = models.CharField(max_length=20, choices=ACCESS_TYPES)
    resource_type = models.CharField(max_length=50, blank=True)  # e.g., 'invoice', 'employee'
    resource_id = models.CharField(max_length=50, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_id = models.CharField(max_length=100, blank=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Access Log'
        verbose_name_plural = 'Access Logs'
    
    def __str__(self):
        return f"{self.user.username} - {self.access_type} - {self.timestamp}"


class RoleAuditLog(models.Model):
    """Model for auditing role and permission changes"""
    ACTION_TYPES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('assign', 'Assign'),
        ('revoke', 'Revoke'),
        ('activate', 'Activate'),
        ('deactivate', 'Deactivate'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='role_audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='target_audit_logs')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, null=True, blank=True, related_name='audit_logs')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, null=True, blank=True, related_name='audit_logs')
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Role Audit Log'
        verbose_name_plural = 'Role Audit Logs'
    
    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.timestamp}"


class Department(models.Model):
    """Model for department-based grouping"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    parent_department = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='child_departments')
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_departments')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'
    
    def __str__(self):
        return self.name


class CostCenter(models.Model):
    """Model for cost center-based access control"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='cost_centers')
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_rp_cost_centers')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Cost Center'
        verbose_name_plural = 'Cost Centers'
    
    def __str__(self):
        return f"{self.code} - {self.name}"
