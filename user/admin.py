from django.contrib import admin
from user.user_model import UserProfile, Role, CustomPermission, RolePermission

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    ordering = ['name']

@admin.register(CustomPermission)
class CustomPermissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'codename', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'codename', 'description']
    list_editable = ['is_active']
    ordering = ['name']

@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ['role', 'permission', 'created_at']
    list_filter = ['role', 'permission', 'created_at']
    search_fields = ['role__name', 'permission__name']
    ordering = ['role__name', 'permission__name']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'employee_id', 'department', 'role', 'created_at']
    list_filter = ['role', 'department', 'gender', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'user__email', 'employee_id']
    ordering = ['user__username']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'employee_id', 'phone', 'address', 'date_of_birth', 'gender', 'profile_picture')
        }),
        ('Work Information', {
            'fields': ('department', 'position', 'hire_date', 'salary')
        }),
        ('System Information', {
            'fields': ('role', 'last_login_ip')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at'] 