from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from .models import (
    Role, Permission, UserRole, PermissionGroup, UserPermission,
    Department, CostCenter, RolePermission
)


class RoleForm(forms.ModelForm):
    """Form for creating and editing roles"""
    class Meta:
        model = Role
        fields = [
            'name', 'description', 'role_type', 'parent_role',
            'department', 'cost_center', 'branch', 'project', 'location',
            'is_active', 'is_system_role'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter role name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter role description'
            }),
            'role_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'parent_role': forms.Select(attrs={
                'class': 'form-select'
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Department'
            }),
            'cost_center': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Cost Center'
            }),
            'branch': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Branch'
            }),
            'project': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Project'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Location'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_system_role': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter out system roles from parent role choices
        if self.instance.pk:
            self.fields['parent_role'].queryset = Role.objects.exclude(
                pk=self.instance.pk
            ).filter(is_active=True)
        else:
            self.fields['parent_role'].queryset = Role.objects.filter(is_active=True)


class PermissionForm(forms.ModelForm):
    """Form for creating and editing permissions"""
    class Meta:
        model = Permission
        fields = [
            'name', 'codename', 'description', 'permission_type',
            'module', 'feature', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter permission name'
            }),
            'codename': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter permission codename'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter permission description'
            }),
            'permission_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'module': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Module (e.g., finance, hr)'
            }),
            'feature': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Feature (e.g., invoices, employees)'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def clean_codename(self):
        codename = self.cleaned_data['codename']
        if not codename.islower() or ' ' in codename:
            raise forms.ValidationError(
                "Codename must be lowercase and contain no spaces."
            )
        return codename


class PermissionGroupForm(forms.ModelForm):
    """Form for creating and editing permission groups"""
    class Meta:
        model = PermissionGroup
        fields = ['name', 'description', 'permissions', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter group name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter group description'
            }),
            'permissions': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': 10
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class UserRoleForm(forms.ModelForm):
    """Form for assigning roles to users"""
    class Meta:
        model = UserRole
        fields = [
            'user', 'role', 'is_primary', 'expires_at',
            'is_active', 'conditions', 'notes'
        ]
        widgets = {
            'user': forms.Select(attrs={
                'class': 'form-select'
            }),
            'role': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_primary': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'expires_at': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'conditions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter conditional logic (JSON format)'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter notes'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = User.objects.filter(is_active=True)
        self.fields['role'].queryset = Role.objects.filter(is_active=True)

    def clean_expires_at(self):
        expires_at = self.cleaned_data.get('expires_at')
        if expires_at and expires_at <= timezone.now():
            raise forms.ValidationError(
                "Expiration date must be in the future."
            )
        return expires_at


class UserPermissionForm(forms.ModelForm):
    """Form for direct user permissions"""
    class Meta:
        model = UserPermission
        fields = [
            'user', 'permission', 'is_granted', 'expires_at',
            'conditions', 'reason'
        ]
        widgets = {
            'user': forms.Select(attrs={
                'class': 'form-select'
            }),
            'permission': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_granted': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'expires_at': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'conditions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter conditional logic (JSON format)'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter reason for this permission'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = User.objects.filter(is_active=True)
        self.fields['permission'].queryset = Permission.objects.filter(is_active=True)

    def clean_expires_at(self):
        expires_at = self.cleaned_data.get('expires_at')
        if expires_at and expires_at <= timezone.now():
            raise forms.ValidationError(
                "Expiration date must be in the future."
            )
        return expires_at


class DepartmentForm(forms.ModelForm):
    """Form for creating and editing departments"""
    class Meta:
        model = Department
        fields = [
            'name', 'code', 'description', 'parent_department',
            'manager', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter department name'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter department code'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter department description'
            }),
            'parent_department': forms.Select(attrs={
                'class': 'form-select'
            }),
            'manager': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['manager'].queryset = User.objects.filter(is_active=True)
        if self.instance.pk:
            self.fields['parent_department'].queryset = Department.objects.exclude(
                pk=self.instance.pk
            ).filter(is_active=True)
        else:
            self.fields['parent_department'].queryset = Department.objects.filter(is_active=True)


class CostCenterForm(forms.ModelForm):
    """Form for creating and editing cost centers"""
    class Meta:
        model = CostCenter
        fields = [
            'name', 'code', 'description', 'department',
            'manager', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter cost center name'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter cost center code'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter cost center description'
            }),
            'department': forms.Select(attrs={
                'class': 'form-select'
            }),
            'manager': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['manager'].queryset = User.objects.filter(is_active=True)
        self.fields['department'].queryset = Department.objects.filter(is_active=True)


class RolePermissionForm(forms.ModelForm):
    """Form for managing role permissions"""
    class Meta:
        model = RolePermission
        fields = ['role', 'permission', 'is_granted', 'conditions']
        widgets = {
            'role': forms.Select(attrs={
                'class': 'form-select'
            }),
            'permission': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_granted': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'conditions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter conditional logic (JSON format)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].queryset = Role.objects.filter(is_active=True)
        self.fields['permission'].queryset = Permission.objects.filter(is_active=True)


class RoleSearchForm(forms.Form):
    """Form for searching and filtering roles"""
    name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by role name'
        })
    )
    role_type = forms.ChoiceField(
        choices=[('', 'All Types')] + Role.ROLE_TYPES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    department = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filter by department'
        })
    )
    is_active = forms.ChoiceField(
        choices=[('', 'All'), ('True', 'Active'), ('False', 'Inactive')],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )


class UserRoleSearchForm(forms.Form):
    """Form for searching and filtering user roles"""
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    role = forms.ModelChoiceField(
        queryset=Role.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    is_primary = forms.ChoiceField(
        choices=[('', 'All'), ('True', 'Primary'), ('False', 'Secondary')],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    is_active = forms.ChoiceField(
        choices=[('', 'All'), ('True', 'Active'), ('False', 'Inactive')],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )


class PermissionSearchForm(forms.Form):
    """Form for searching and filtering permissions"""
    name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by permission name'
        })
    )
    module = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filter by module'
        })
    )
    feature = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filter by feature'
        })
    )
    permission_type = forms.ChoiceField(
        choices=[('', 'All Types')] + Permission.PERMISSION_TYPES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    is_active = forms.ChoiceField(
        choices=[('', 'All'), ('True', 'Active'), ('False', 'Inactive')],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )


class BulkRoleAssignmentForm(forms.Form):
    """Form for bulk role assignment"""
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'size': 10
        })
    )
    role = forms.ModelChoiceField(
        queryset=Role.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    is_primary = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    expires_at = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        })
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter notes for bulk assignment'
        })
    )


class RolePermissionBulkForm(forms.Form):
    """Form for bulk permission assignment to roles"""
    roles = forms.ModelMultipleChoiceField(
        queryset=Role.objects.filter(is_active=True),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'size': 8
        })
    )
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.filter(is_active=True),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'size': 10
        })
    )
    is_granted = forms.BooleanField(
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    conditions = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter conditional logic (JSON format)'
        })
    )
