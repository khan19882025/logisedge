from django.db import models
from django.contrib.auth.models import User as DjangoUser
from django.utils import timezone

class Role(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Role Name")
    description = models.TextField(blank=True, verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        verbose_name = "Role"
        verbose_name_plural = "Roles"
        ordering = ['name']

    def __str__(self):
        return self.name

class CustomPermission(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Permission Name")
    codename = models.CharField(max_length=100, unique=True, verbose_name="Code Name")
    description = models.TextField(blank=True, verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")

    class Meta:
        verbose_name = "Custom Permission"
        verbose_name_plural = "Custom Permissions"
        ordering = ['name']

    def __str__(self):
        return self.name

class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_permissions')
    permission = models.ForeignKey(CustomPermission, on_delete=models.CASCADE, related_name='role_permissions')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['role', 'permission']
        verbose_name = "Role Permission"
        verbose_name_plural = "Role Permissions"

    def __str__(self):
        return f"{self.role.name} - {self.permission.name}"

class UserProfile(models.Model):
    user = models.OneToOneField(DjangoUser, on_delete=models.CASCADE, related_name='profile')
    
    # Basic Information
    employee_id = models.CharField(max_length=20, unique=True, verbose_name="Employee ID")
    phone = models.CharField(max_length=20, verbose_name="Phone Number")
    address = models.TextField(blank=True, verbose_name="Address")
    date_of_birth = models.DateField(null=True, blank=True, verbose_name="Date of Birth")
    gender = models.CharField(max_length=10, choices=[
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other')
    ], blank=True, verbose_name="Gender")
    
    # Work Information
    department = models.CharField(max_length=100, blank=True, verbose_name="Department")
    position = models.CharField(max_length=100, blank=True, verbose_name="Position")
    hire_date = models.DateField(null=True, blank=True, verbose_name="Hire Date")
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Salary")
    
    # System Information
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Role")
    last_login_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name="Last Login IP")
    profile_picture = models.ImageField(upload_to='user_profiles/', null=True, blank=True, verbose_name="Profile Picture")
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
        ordering = ['user__username']

    def __str__(self):
        return f"{self.user.username} - {self.user.get_full_name()}"

    def get_full_name(self):
        return self.user.get_full_name()

    def has_permission(self, permission_codename):
        """Check if user has specific permission through their role"""
        if self.role:
            return self.role.role_permissions.filter(
                permission__codename=permission_codename,
                permission__is_active=True
            ).exists()
        return False

    def get_permissions(self):
        """Get all permissions for the user through their role"""
        if self.role:
            return CustomPermission.objects.filter(
                role_permissions__role=self.role,
                is_active=True
            )
        return CustomPermission.objects.none() 