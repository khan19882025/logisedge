from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Role, Permission, UserRole, PermissionGroup, UserPermission,
    Department, CostCenter, AccessLog, RoleAuditLog
)
from django.utils import timezone
import json


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'codename', 'module', 'feature', 'permission_type', 'is_active', 'created_at']
    list_filter = ['module', 'feature', 'permission_type', 'is_active', 'created_at']
    search_fields = ['name', 'codename', 'module', 'feature', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['module', 'feature', 'permission_type']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'codename', 'description', 'permission_type')
        }),
        ('Module & Feature', {
            'fields': ('module', 'feature')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PermissionGroup)
class PermissionGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'permission_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    filter_horizontal = ['permissions']
    
    def permission_count(self, obj):
        return obj.permissions.count()
    permission_count.short_description = 'Permissions'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description')
        }),
        ('Permissions', {
            'fields': ('permissions',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'role_type', 'parent_role', 'department', 'is_active', 'user_count', 'created_at']
    list_filter = ['role_type', 'is_active', 'is_system_role', 'created_at']
    search_fields = ['name', 'description', 'department', 'cost_center', 'branch', 'project', 'location']
    readonly_fields = ['id', 'created_at', 'updated_at']
    filter_horizontal = ['permission_groups']
    
    def user_count(self, obj):
        return obj.user_roles.filter(is_active=True).count()
    user_count.short_description = 'Users'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'role_type')
        }),
        ('Hierarchy', {
            'fields': ('parent_role',)
        }),
        ('Organizational Context', {
            'fields': ('department', 'cost_center', 'branch', 'project', 'location')
        }),
        ('Permissions', {
            'fields': ('permission_groups',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_system_role')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'is_primary', 'is_active', 'assigned_by', 'assigned_at', 'expires_at', 'is_expired']
    list_filter = ['is_primary', 'is_active', 'role__role_type', 'assigned_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'role__name', 'notes']
    readonly_fields = ['id', 'assigned_at']
    date_hierarchy = 'assigned_at'
    
    def is_expired(self, obj):
        if obj.is_expired:
            return format_html('<span style="color: red;">Expired</span>')
        return format_html('<span style="color: green;">Active</span>')
    is_expired.short_description = 'Status'
    
    fieldsets = (
        ('Assignment', {
            'fields': ('user', 'role', 'is_primary')
        }),
        ('Timing', {
            'fields': ('assigned_at', 'expires_at')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Conditions & Notes', {
            'fields': ('conditions', 'notes')
        }),
        ('Metadata', {
            'fields': ('id', 'assigned_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set assigned_by on creation
            obj.assigned_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(UserPermission)
class UserPermissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'permission', 'is_granted', 'granted_by', 'granted_at', 'expires_at', 'is_expired']
    list_filter = ['is_granted', 'permission__module', 'permission__feature', 'granted_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'permission__name', 'reason']
    readonly_fields = ['id', 'granted_at']
    date_hierarchy = 'granted_at'
    
    def is_expired(self, obj):
        if obj.expires_at and obj.expires_at < timezone.now():
            return format_html('<span style="color: red;">Expired</span>')
        return format_html('<span style="color: green;">Active</span>')
    is_expired.short_description = 'Status'
    
    fieldsets = (
        ('Permission', {
            'fields': ('user', 'permission', 'is_granted')
        }),
        ('Timing', {
            'fields': ('granted_at', 'expires_at')
        }),
        ('Details', {
            'fields': ('conditions', 'reason')
        }),
        ('Metadata', {
            'fields': ('id', 'granted_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set granted_by on creation
            obj.granted_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'parent_department', 'manager', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'description')
        }),
        ('Hierarchy', {
            'fields': ('parent_department', 'manager')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CostCenter)
class CostCenterAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'department', 'manager', 'is_active', 'created_at']
    list_filter = ['is_active', 'department', 'created_at']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'description')
        }),
        ('Organization', {
            'fields': ('department', 'manager')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'access_type', 'resource_type', 'resource_id', 'ip_address', 'success', 'timestamp']
    list_filter = ['access_type', 'success', 'timestamp', 'resource_type']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'resource_type', 'resource_id', 'error_message']
    readonly_fields = ['id', 'timestamp', 'user', 'access_type', 'resource_type', 'resource_id', 'ip_address', 'user_agent', 'session_id', 'success', 'error_message', 'metadata']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    fieldsets = (
        ('Access Information', {
            'fields': ('user', 'access_type', 'success')
        }),
        ('Resource', {
            'fields': ('resource_type', 'resource_id')
        }),
        ('Technical Details', {
            'fields': ('ip_address', 'user_agent', 'session_id')
        }),
        ('Error Information', {
            'fields': ('error_message', 'metadata'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'timestamp'),
            'classes': ('collapse',)
        }),
    )


@admin.register(RoleAuditLog)
class RoleAuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'target_user', 'role', 'permission', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['user__username', 'target_user__username', 'role__name', 'permission__name', 'notes']
    readonly_fields = ['id', 'timestamp', 'user', 'action', 'target_user', 'role', 'permission', 'old_values', 'new_values', 'ip_address', 'user_agent', 'notes']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def old_values_display(self, obj):
        if obj.old_values:
            return format_html('<pre>{}</pre>', json.dumps(obj.old_values, indent=2))
        return '-'
    old_values_display.short_description = 'Old Values'
    
    def new_values_display(self, obj):
        if obj.new_values:
            return format_html('<pre>{}</pre>', json.dumps(obj.new_values, indent=2))
        return '-'
    new_values_display.short_description = 'New Values'
    
    fieldsets = (
        ('Audit Information', {
            'fields': ('user', 'action', 'timestamp')
        }),
        ('Target Objects', {
            'fields': ('target_user', 'role', 'permission')
        }),
        ('Changes', {
            'fields': ('old_values_display', 'new_values_display')
        }),
        ('Technical Details', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('id',),
            'classes': ('collapse',)
        }),
    )


# Custom admin site configuration
admin.site.site_header = "LogisEdge ERP - Roles & Permissions Administration"
admin.site.site_title = "Roles & Permissions Admin"
admin.site.index_title = "Welcome to Roles & Permissions Administration"
