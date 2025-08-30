from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponse
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.core.paginator import Paginator
from django.db import transaction
import json

from .models import (
    Role, Permission, UserRole, PermissionGroup, UserPermission,
    Department, CostCenter, AccessLog, RoleAuditLog
)
from .forms import (
    RoleForm, PermissionForm, UserRoleForm, PermissionGroupForm,
    UserPermissionForm, DepartmentForm, CostCenterForm,
    RoleSearchForm, UserRoleSearchForm, PermissionSearchForm,
    BulkRoleAssignmentForm, RolePermissionBulkForm
)


@login_required
def dashboard(request):
    """Main dashboard for Roles & Permissions module"""
    # Get statistics
    total_roles = Role.objects.count()
    active_roles = Role.objects.filter(is_active=True).count()
    total_users = User.objects.filter(is_active=True).count()
    total_permissions = Permission.objects.count()
    total_departments = Department.objects.count()
    
    # Recent activities
    recent_audit_logs = RoleAuditLog.objects.select_related('user', 'target_user', 'role').order_by('-timestamp')[:10]
    recent_access_logs = AccessLog.objects.select_related('user').order_by('-timestamp')[:10]
    
    # Role distribution
    role_distribution = Role.objects.values('role_type').annotate(count=Count('id'))
    
    # User role assignments
    user_role_stats = UserRole.objects.values('role__name').annotate(count=Count('user')).order_by('-count')[:5]
    
    context = {
        'total_roles': total_roles,
        'active_roles': active_roles,
        'total_users': total_users,
        'total_permissions': total_permissions,
        'total_departments': total_departments,
        'recent_audit_logs': recent_audit_logs,
        'recent_access_logs': recent_access_logs,
        'role_distribution': role_distribution,
        'user_role_stats': user_role_stats,
    }
    
    return render(request, 'roles_permissions/dashboard.html', context)


@login_required
@permission_required('roles_permissions.view_accesslog')
def access_logs(request):
    """View access logs"""
    from django.db.models import Q
    from datetime import datetime, timedelta
    
    # Get access logs
    logs = AccessLog.objects.select_related('user').order_by('-timestamp')
    
    # Apply filters
    action = request.GET.get('action')
    user_id = request.GET.get('user')
    success_filter = request.GET.get('status')  # Keep 'status' for UI compatibility
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search = request.GET.get('search')
    
    # Apply action filter
    if action:
        logs = logs.filter(access_type=action)
    
    # Apply user filter
    if user_id:
        logs = logs.filter(user_id=user_id)
    
    # Apply success filter (convert 'status' to 'success' boolean)
    if success_filter:
        if success_filter == 'success':
            logs = logs.filter(success=True)
        elif success_filter == 'failed':
            logs = logs.filter(success=False)
    
    # Apply date filters
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            logs = logs.filter(timestamp__date__gte=date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            logs = logs.filter(timestamp__date__lte=date_to_obj)
        except ValueError:
            pass
    
    # Apply search filter
    if search:
        logs = logs.filter(
            Q(access_type__icontains=search) |
            Q(resource_type__icontains=search) |
            Q(user__username__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(ip_address__icontains=search)
        )
    
    # Calculate statistics
    total_logs = logs.count()
    successful_access = logs.filter(success=True).count()
    failed_access = logs.filter(success=False).count()
    unique_users = logs.values('user').distinct().count()
    
    # Pagination
    page_size = int(request.GET.get('page_size', 25))
    paginator = Paginator(logs, page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'logs': page_obj,
        'users': User.objects.filter(is_active=True),
        'total_logs': total_logs,
        'successful_access': successful_access,
        'failed_access': failed_access,
        'unique_users': unique_users,
    }
    
    return render(request, 'roles_permissions/access_logs.html', context)


@login_required
@permission_required('roles_permissions.view_accesslog')
def access_log_details(request, log_id):
    """Get detailed information about a specific access log entry"""
    try:
        log = AccessLog.objects.select_related('user').get(id=log_id)
    except AccessLog.DoesNotExist:
        return JsonResponse({'error': 'Access log not found'}, status=404)
    
    # Prepare response data
    data = {
        'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'user_name': log.user.get_full_name() if log.user else 'Anonymous',
        'action': log.access_type,
        'status': 'Success' if log.success else 'Failed',
        'ip_address': log.ip_address or 'N/A',
        'user_agent': log.user_agent or 'N/A',
        'resource': f"{log.resource_type}: {log.resource_id}" if log.resource_type and log.resource_id else 'N/A',
        'session_id': log.session_id or 'N/A',
        'details': log.metadata if log.metadata else None,
        'error_message': log.error_message or None,
    }
    
    return JsonResponse(data)


@login_required
@permission_required('roles_permissions.delete_accesslog')
def clear_old_access_logs(request):
    """Clear access logs older than 90 days"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        from datetime import timedelta
        cutoff_date = timezone.now() - timedelta(days=90)
        
        # Count logs to be deleted
        old_logs_count = AccessLog.objects.filter(timestamp__lt=cutoff_date).count()
        
        # Delete old logs
        deleted_count = AccessLog.objects.filter(timestamp__lt=cutoff_date).delete()[0]
        
        return JsonResponse({
            'success': True,
            'cleared_count': deleted_count,
            'message': f'Successfully cleared {deleted_count} old access logs'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def cost_center_list(request):
    """List cost centers"""
    cost_centers = CostCenter.objects.select_related('department', 'manager').all()
    
    # Apply search
    search = request.GET.get('search')
    if search:
        cost_centers = cost_centers.filter(
            Q(name__icontains=search) | Q(code__icontains=search)
        )
    
    # Calculate statistics
    total_cost_centers = cost_centers.count()
    active_cost_centers = cost_centers.filter(is_active=True).count()
    cost_centers_with_managers = cost_centers.filter(manager__isnull=False).count()
    cost_centers_with_departments = cost_centers.filter(department__isnull=False).count()
    
    context = {
        'cost_centers': cost_centers,
        'search': search,
        'total_cost_centers': total_cost_centers,
        'active_cost_centers': active_cost_centers,
        'cost_centers_with_managers': cost_centers_with_managers,
        'cost_centers_with_departments': cost_centers_with_departments,
    }
    
    return render(request, 'roles_permissions/cost_center_list.html', context)


@login_required
@permission_required('roles_permissions.add_costcenter')
def cost_center_create(request):
    """Create a new cost center"""
    if request.method == 'POST':
        form = CostCenterForm(request.POST)
        if form.is_valid():
            cost_center = form.save()
            messages.success(request, f'Cost center "{cost_center.name}" created successfully.')
            return redirect('roles_permissions:cost_center_list')
    else:
        form = CostCenterForm()
    
    context = {
        'form': form,
        'title': 'Create Cost Center',
        'submit_text': 'Create Cost Center',
    }
    
    return render(request, 'roles_permissions/cost_center_form.html', context)


@login_required
def cost_center_detail(request, pk):
    """View cost center details"""
    cost_center = get_object_or_404(CostCenter, pk=pk)
    
    context = {
        'cost_center': cost_center,
    }
    
    return render(request, 'roles_permissions/cost_center_detail.html', context)


@login_required
@permission_required('roles_permissions.change_costcenter')
def cost_center_update(request, pk):
    """Update a cost center"""
    cost_center = get_object_or_404(CostCenter, pk=pk)
    
    if request.method == 'POST':
        form = CostCenterForm(request.POST, instance=cost_center)
        if form.is_valid():
            cost_center = form.save()
            messages.success(request, f'Cost center "{cost_center.name}" updated successfully.')
            return redirect('roles_permissions:cost_center_list')
    else:
        form = CostCenterForm(instance=cost_center)
    
    context = {
        'form': form,
        'cost_center': cost_center,
        'title': 'Edit Cost Center',
        'submit_text': 'Update Cost Center',
    }
    
    return render(request, 'roles_permissions/cost_center_form.html', context)


@login_required
@permission_required('roles_permissions.delete_costcenter')
def cost_center_delete(request, pk):
    """Delete a cost center"""
    cost_center = get_object_or_404(CostCenter, pk=pk)
    
    if request.method == 'POST':
        name = cost_center.name
        cost_center.delete()
        messages.success(request, f'Cost center "{name}" deleted successfully.')
        return redirect('roles_permissions:cost_center_list')
    
    context = {
        'cost_center': cost_center,
    }
    
    return render(request, 'roles_permissions/cost_center_confirm_delete.html', context)


@login_required
def dashboard(request):
    """Main dashboard for Roles & Permissions module"""
    # Get statistics
    total_roles = Role.objects.count()
    active_roles = Role.objects.filter(is_active=True).count()
    total_users = User.objects.filter(is_active=True).count()
    total_permissions = Permission.objects.count()
    total_departments = Department.objects.count()
    
    # Recent activities
    recent_audit_logs = RoleAuditLog.objects.select_related('user', 'target_user', 'role').order_by('-timestamp')[:10]
    recent_access_logs = AccessLog.objects.select_related('user').order_by('-timestamp')[:10]
    
    # Role distribution
    role_distribution = Role.objects.values('role_type').annotate(count=Count('id'))
    
    # User role assignments
    user_role_stats = UserRole.objects.values('role__name').annotate(count=Count('user')).order_by('-count')[:5]
    
    context = {
        'total_roles': total_roles,
        'active_roles': active_roles,
        'total_users': total_users,
        'total_permissions': total_permissions,
        'total_departments': total_departments,
        'recent_audit_logs': recent_audit_logs,
        'recent_access_logs': recent_access_logs,
        'role_distribution': role_distribution,
        'user_role_stats': user_role_stats,
    }
    
    return render(request, 'roles_permissions/dashboard.html', context)


class RoleListView(LoginRequiredMixin, ListView):
    """List view for roles with search and filter functionality"""
    model = Role
    template_name = 'roles_permissions/role_list.html'
    context_object_name = 'roles'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Role.objects.select_related('parent_role').all()
        
        # Apply search filters
        form = RoleSearchForm(self.request.GET)
        if form.is_valid():
            name = form.cleaned_data.get('name')
            role_type = form.cleaned_data.get('role_type')
            department = form.cleaned_data.get('department')
            is_active = form.cleaned_data.get('is_active')
            
            if name:
                queryset = queryset.filter(name__icontains=name)
            if role_type:
                queryset = queryset.filter(role_type=role_type)
            if department:
                queryset = queryset.filter(department__icontains=department)
            if is_active:
                queryset = queryset.filter(is_active=is_active == 'True')
        
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = RoleSearchForm(self.request.GET)
        return context


class RoleDetailView(LoginRequiredMixin, DetailView):
    """Detail view for roles"""
    model = Role
    template_name = 'roles_permissions/role_detail.html'
    context_object_name = 'role'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        role = self.get_object()
        
        # Get role permissions
        context['role_permissions'] = role.role_permissions.select_related('permission').all()
        context['all_permissions'] = role.get_all_permissions()
        
        # Get users with this role
        context['user_roles'] = role.user_roles.select_related('user').all()
        
        # Get child roles
        context['child_roles'] = role.child_roles.all()
        
        # Get audit logs
        context['audit_logs'] = role.audit_logs.select_related('user').order_by('-timestamp')[:20]
        
        return context


class RoleCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Create view for roles"""
    model = Role
    form_class = RoleForm
    template_name = 'roles_permissions/role_form.html'
    permission_required = 'roles_permissions.add_role'
    
    def get_success_url(self):
        messages.success(self.request, 'Role created successfully.')
        return reverse('roles_permissions:role_detail', kwargs={'pk': self.object.pk})


class RoleUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Update view for roles"""
    model = Role
    form_class = RoleForm
    template_name = 'roles_permissions/role_form.html'
    permission_required = 'roles_permissions.change_role'
    
    def get_success_url(self):
        messages.success(self.request, 'Role updated successfully.')
        return reverse('roles_permissions:role_detail', kwargs={'pk': self.object.pk})


class RoleDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Delete view for roles"""
    model = Role
    template_name = 'roles_permissions/role_confirm_delete.html'
    permission_required = 'roles_permissions.delete_role'
    success_url = reverse_lazy('roles_permissions:role_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Role deleted successfully.')
        return super().delete(request, *args, **kwargs)


class PermissionListView(LoginRequiredMixin, ListView):
    """List view for permissions with search and filter functionality"""
    model = Permission
    template_name = 'roles_permissions/permission_list.html'
    context_object_name = 'permissions'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Permission.objects.all()
        
        # Apply search filters
        form = PermissionSearchForm(self.request.GET)
        if form.is_valid():
            name = form.cleaned_data.get('name')
            module = form.cleaned_data.get('module')
            feature = form.cleaned_data.get('feature')
            permission_type = form.cleaned_data.get('permission_type')
            is_active = form.cleaned_data.get('is_active')
            
            if name:
                queryset = queryset.filter(name__icontains=name)
            if module:
                queryset = queryset.filter(module__icontains=module)
            if feature:
                queryset = queryset.filter(feature__icontains=feature)
            if permission_type:
                queryset = queryset.filter(permission_type=permission_type)
            if is_active:
                queryset = queryset.filter(is_active=is_active == 'True')
        
        return queryset.order_by('module', 'feature', 'permission_type')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = PermissionSearchForm(self.request.GET)
        return context


class PermissionCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Create view for permissions"""
    model = Permission
    form_class = PermissionForm
    template_name = 'roles_permissions/permission_form.html'
    permission_required = 'roles_permissions.add_permission'
    
    def get_success_url(self):
        messages.success(self.request, 'Permission created successfully.')
        return reverse('roles_permissions:permission_list')


class PermissionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Update view for permissions"""
    model = Permission
    form_class = PermissionForm
    template_name = 'roles_permissions/permission_form.html'
    permission_required = 'roles_permissions.change_permission'
    
    def get_success_url(self):
        messages.success(self.request, 'Permission updated successfully.')
        return reverse('roles_permissions:permission_list')


class UserRoleListView(LoginRequiredMixin, ListView):
    """List view for user role assignments"""
    model = UserRole
    template_name = 'roles_permissions/user_role_list.html'
    context_object_name = 'user_roles'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = UserRole.objects.select_related('user', 'role', 'assigned_by').all()
        
        # Apply search filters
        form = UserRoleSearchForm(self.request.GET)
        if form.is_valid():
            user = form.cleaned_data.get('user')
            role = form.cleaned_data.get('role')
            is_primary = form.cleaned_data.get('is_primary')
            is_active = form.cleaned_data.get('is_active')
            
            if user:
                queryset = queryset.filter(user=user)
            if role:
                queryset = queryset.filter(role=role)
            if is_primary:
                queryset = queryset.filter(is_primary=is_primary == 'True')
            if is_active:
                queryset = queryset.filter(is_active=is_active == 'True')
        
        return queryset.order_by('-assigned_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = UserRoleSearchForm(self.request.GET)
        context['roles'] = Role.objects.filter(is_active=True).order_by('name')
        return context


class UserRoleCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Create view for user role assignments"""
    model = UserRole
    form_class = UserRoleForm
    template_name = 'roles_permissions/user_role_form.html'
    permission_required = 'roles_permissions.add_userrole'
    
    def form_valid(self, form):
        form.instance.assigned_by = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        messages.success(self.request, 'User role assigned successfully.')
        return reverse('roles_permissions:user_role_list')


class UserRoleUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Update view for user role assignments"""
    model = UserRole
    form_class = UserRoleForm
    template_name = 'roles_permissions/user_role_form.html'
    permission_required = 'roles_permissions.change_userrole'
    
    def get_success_url(self):
        messages.success(self.request, 'User role updated successfully.')
        return reverse('roles_permissions:user_role_list')


class UserRoleDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Delete view for user role assignments"""
    model = UserRole
    template_name = 'roles_permissions/user_role_confirm_delete.html'
    permission_required = 'roles_permissions.delete_userrole'
    success_url = reverse_lazy('roles_permissions:user_role_list')
    
    def delete(self, request, *args, **kwargs):
        user_role = self.get_object()
        messages.success(request, f'Role "{user_role.role.name}" removed from user "{user_role.user.get_full_name() or user_role.user.username}".')
        return super().delete(request, *args, **kwargs)


@login_required
@permission_required('roles_permissions.add_userrole')
def bulk_role_assignment(request):
    """Bulk role assignment view"""
    if request.method == 'POST':
        form = BulkRoleAssignmentForm(request.POST)
        if form.is_valid():
            users = form.cleaned_data['users']
            role = form.cleaned_data['role']
            is_primary = form.cleaned_data['is_primary']
            expires_at = form.cleaned_data['expires_at']
            notes = form.cleaned_data['notes']
            
            created_count = 0
            with transaction.atomic():
                for user in users:
                    # Check if user already has this role
                    user_role, created = UserRole.objects.get_or_create(
                        user=user,
                        role=role,
                        defaults={
                            'is_primary': is_primary,
                            'expires_at': expires_at,
                            'notes': notes,
                            'assigned_by': request.user,
                        }
                    )
                    if created:
                        created_count += 1
                    else:
                        # Update existing assignment
                        user_role.is_primary = is_primary
                        user_role.expires_at = expires_at
                        user_role.notes = notes
                        user_role.save()
            
            messages.success(request, f'Successfully assigned role to {created_count} users.')
            return redirect('roles_permissions:user_role_list')
    else:
        form = BulkRoleAssignmentForm()
    
    return render(request, 'roles_permissions/bulk_role_assignment.html', {'form': form})


@login_required
@permission_required('roles_permissions.change_role')
def role_permissions(request, pk):
    """Manage role permissions"""
    role = get_object_or_404(Role, pk=pk)
    
    if request.method == 'POST':
        # Handle permission updates
        permissions_data = request.POST.getlist('permissions')
        role.permissions.clear()
        
        for permission_id in permissions_data:
            permission = get_object_or_404(Permission, pk=permission_id)
            role.permissions.add(permission)
        
        messages.success(request, 'Role permissions updated successfully.')
        return redirect('roles_permissions:role_detail', pk=pk)
    
    # Get all permissions grouped by module and feature
    permissions = Permission.objects.filter(is_active=True).order_by('module', 'feature', 'permission_type')
    role_permissions = set(role.permissions.values_list('id', flat=True))
    
    # Group permissions by module and feature
    grouped_permissions = {}
    for permission in permissions:
        module = permission.module
        feature = permission.feature
        if module not in grouped_permissions:
            grouped_permissions[module] = {}
        if feature not in grouped_permissions[module]:
            grouped_permissions[module][feature] = []
        grouped_permissions[module][feature].append(permission)
    
    context = {
        'role': role,
        'grouped_permissions': grouped_permissions,
        'role_permissions': role_permissions,
    }
    
    return render(request, 'roles_permissions/role_permissions.html', context)


@login_required
@permission_required('roles_permissions.view_accesslog')
def access_logs(request):
    """View access logs"""
    from django.db.models import Q
    from datetime import datetime, timedelta
    
    # Get access logs
    logs = AccessLog.objects.select_related('user').order_by('-timestamp')
    
    # Apply filters
    action = request.GET.get('action')
    user_id = request.GET.get('user')
    success_filter = request.GET.get('status')  # Keep 'status' for UI compatibility
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search = request.GET.get('search')
    
    # Apply action filter
    if action:
        logs = logs.filter(access_type=action)
    
    # Apply user filter
    if user_id:
        logs = logs.filter(user_id=user_id)
    
    # Apply success filter (convert 'status' to 'success' boolean)
    if success_filter:
        if success_filter == 'success':
            logs = logs.filter(success=True)
        elif success_filter == 'failed':
            logs = logs.filter(success=False)
    
    # Apply date filters
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            logs = logs.filter(timestamp__date__gte=date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            logs = logs.filter(timestamp__date__lte=date_to_obj)
        except ValueError:
            pass
    
    # Apply search filter
    if search:
        logs = logs.filter(
            Q(access_type__icontains=search) |
            Q(resource_type__icontains=search) |
            Q(user__username__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(ip_address__icontains=search)
        )
    
    # Calculate statistics
    total_logs = logs.count()
    successful_access = logs.filter(success=True).count()
    failed_access = logs.filter(success=False).count()
    unique_users = logs.values('user').distinct().count()
    
    # Pagination
    page_size = int(request.GET.get('page_size', 25))
    paginator = Paginator(logs, page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'logs': page_obj,
        'users': User.objects.filter(is_active=True),
        'total_logs': total_logs,
        'successful_access': successful_access,
        'failed_access': failed_access,
        'unique_users': unique_users,
    }
    
    return render(request, 'roles_permissions/access_logs.html', context)


@login_required
@permission_required('roles_permissions.view_roleauditlog')
def audit_logs(request):
    """View audit logs"""
    from django.db.models import Q
    from datetime import datetime, timedelta
    
    # Get logs from both AccessLog and RoleAuditLog
    access_logs = AccessLog.objects.select_related('user').order_by('-timestamp')
    role_logs = RoleAuditLog.objects.select_related('user', 'target_user', 'role', 'permission').order_by('-timestamp')
    
    # Apply filters
    log_type = request.GET.get('log_type')
    user_id = request.GET.get('user')
    status = request.GET.get('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search = request.GET.get('search')
    
    # Filter by log type
    if log_type == 'access':
        logs = access_logs
        log_model = 'access'
    elif log_type == 'role':
        logs = role_logs
        log_model = 'role'
    else:
        # Combine both types
        logs = list(access_logs) + list(role_logs)
        logs.sort(key=lambda x: x.timestamp, reverse=True)
        log_model = 'all'
    
    # Apply user filter
    if user_id:
        if log_model == 'access':
            logs = logs.filter(user_id=user_id)
        elif log_model == 'role':
            logs = logs.filter(user_id=user_id)
        else:
            logs = [log for log in logs if log.user and log.user.id == int(user_id)]
    
    # Apply status filter
    if status:
        if log_model == 'access':
            logs = logs.filter(success=True if status == 'success' else False)
        elif log_model == 'role':
            # Role logs don't have status, filter by action
            if status == 'success':
                logs = logs.exclude(action__in=['role_removed', 'permission_revoked'])
            elif status == 'failed':
                logs = logs.filter(action__in=['role_removed', 'permission_revoked'])
        else:
            if status == 'success':
                logs = [log for log in logs if (hasattr(log, 'success') and log.success) or 
                       (hasattr(log, 'action') and log.action not in ['role_removed', 'permission_revoked'])]
            elif status == 'failed':
                logs = [log for log in logs if (hasattr(log, 'success') and not log.success) or 
                       (hasattr(log, 'action') and log.action in ['role_removed', 'permission_revoked'])]
    
    # Apply date filters
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            if log_model == 'access':
                logs = logs.filter(timestamp__date__gte=date_from_obj)
            elif log_model == 'role':
                logs = logs.filter(timestamp__date__gte=date_from_obj)
            else:
                logs = [log for log in logs if log.timestamp.date() >= date_from_obj]
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            if log_model == 'access':
                logs = logs.filter(timestamp__date__lte=date_to_obj)
            elif log_model == 'role':
                logs = logs.filter(timestamp__date__lte=date_to_obj)
            else:
                logs = [log for log in logs if log.timestamp.date() <= date_to_obj]
        except ValueError:
            pass
    
    # Apply search filter
    if search:
        if log_model == 'access':
            logs = logs.filter(
                Q(access_type__icontains=search) | 
                Q(resource_type__icontains=search) | 
                Q(user__username__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search)
            )
        elif log_model == 'role':
            logs = logs.filter(
                Q(action__icontains=search) | 
                Q(user__username__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(target_user__username__icontains=search) |
                Q(role__name__icontains=search) |
                Q(permission__name__icontains=search)
            )
        else:
            logs = [log for log in logs if (
                search.lower() in getattr(log, 'access_type', getattr(log, 'action', '')).lower() or
                (hasattr(log, 'resource_type') and search.lower() in log.resource_type.lower()) or
                (log.user and search.lower() in log.user.username.lower()) or
                (log.user and search.lower() in (log.user.first_name or '').lower()) or
                (log.user and search.lower() in (log.user.last_name or '').lower()) or
                (hasattr(log, 'target_user') and log.target_user and search.lower() in log.target_user.username.lower()) or
                (hasattr(log, 'role') and log.role and search.lower() in log.role.name.lower()) or
                (hasattr(log, 'permission') and log.permission and search.lower() in log.permission.name.lower())
            )]
    
    # Calculate statistics
    total_logs = len(logs)
    successful_access = len([log for log in logs if hasattr(log, 'success') and log.success])
    failed_access = len([log for log in logs if hasattr(log, 'success') and not log.success])
    role_changes = len([log for log in logs if hasattr(log, 'action') and 'role' in log.action])
    
    # Pagination
    page_size = int(request.GET.get('page_size', 25))
    paginator = Paginator(logs, page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'logs': page_obj,
        'users': User.objects.filter(is_active=True),
        'total_logs': total_logs,
        'successful_access': successful_access,
        'failed_access': failed_access,
        'role_changes': role_changes,
    }
    
    return render(request, 'roles_permissions/audit_logs.html', context)


@login_required
@permission_required('roles_permissions.view_roleauditlog')
def log_details(request, log_id):
    """Get detailed information about a specific log entry"""
    try:
        # Try to find the log in AccessLog first
        log = AccessLog.objects.select_related('user').get(id=log_id)
        log_type = 'access'
    except AccessLog.DoesNotExist:
        try:
            # Try to find the log in RoleAuditLog
            log = RoleAuditLog.objects.select_related('user', 'target_user', 'role', 'permission').get(id=log_id)
            log_type = 'role'
        except RoleAuditLog.DoesNotExist:
            return JsonResponse({'error': 'Log not found'}, status=404)
    
    # Prepare response data
    data = {
        'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'user_name': log.user.get_full_name() if log.user else 'Anonymous',
        'action': getattr(log, 'access_type', getattr(log, 'action', 'N/A')),
        'status': 'Success' if getattr(log, 'success', True) else 'Failed',
        'ip_address': getattr(log, 'ip_address', 'N/A'),
        'user_agent': getattr(log, 'user_agent', 'N/A'),
        'resource': f"{getattr(log, 'resource_type', '')}: {getattr(log, 'resource_id', '')}" if getattr(log, 'resource_type', None) and getattr(log, 'resource_id', None) else 'N/A',
        'session_id': getattr(log, 'session_id', 'N/A'),
        'details': getattr(log, 'metadata', getattr(log, 'old_values', None)),
        'error_message': getattr(log, 'error_message', None),
    }
    
    # Add role-specific information
    if log_type == 'role':
        data.update({
            'target_user': log.target_user.get_full_name() if log.target_user else 'N/A',
            'role_name': log.role.name if log.role else 'N/A',
            'permission_name': log.permission.name if log.permission else 'N/A',
            'changes': getattr(log, 'new_values', None),
        })
    
    return JsonResponse(data)


@login_required
@permission_required('roles_permissions.view_accesslog')
def access_log_details(request, log_id):
    """Get detailed information about a specific access log entry"""
    try:
        log = AccessLog.objects.select_related('user').get(id=log_id)
    except AccessLog.DoesNotExist:
        return JsonResponse({'error': 'Access log not found'}, status=404)
    
    # Prepare response data
    data = {
        'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'user_name': log.user.get_full_name() if log.user else 'Anonymous',
        'action': log.access_type,
        'status': 'Success' if log.success else 'Failed',
        'ip_address': log.ip_address or 'N/A',
        'user_agent': log.user_agent or 'N/A',
        'resource': f"{log.resource_type}: {log.resource_id}" if log.resource_type and log.resource_id else 'N/A',
        'session_id': log.session_id or 'N/A',
        'details': log.metadata if log.metadata else None,
        'error_message': log.error_message or None,
    }
    
    return JsonResponse(data)


@login_required
@permission_required('roles_permissions.delete_accesslog')
def clear_old_access_logs(request):
    """Clear access logs older than 90 days"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        from datetime import timedelta
        cutoff_date = timezone.now() - timedelta(days=90)
        
        # Count logs to be deleted
        old_logs_count = AccessLog.objects.filter(timestamp__lt=cutoff_date).count()
        
        # Delete old logs
        deleted_count = AccessLog.objects.filter(timestamp__lt=cutoff_date).delete()[0]
        
        return JsonResponse({
            'success': True,
            'cleared_count': deleted_count,
            'message': f'Successfully cleared {deleted_count} old access logs'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def user_permissions(request, user_id):
    """View user's permissions"""
    user = get_object_or_404(User, pk=user_id)
    
    # Get user's roles and their permissions
    user_roles = user.user_roles.select_related('role').filter(is_active=True)
    all_permissions = set()
    
    for user_role in user_roles:
        if not user_role.is_expired:
            role_permissions = user_role.role.get_all_permissions()
            all_permissions.update(role_permissions)
    
    # Get direct user permissions
    direct_permissions = user.rp_user_permissions.select_related('permission').filter(is_active=True)
    
    # Group permissions by module and feature
    grouped_permissions = {}
    for permission in all_permissions:
        module = permission.module
        feature = permission.feature
        if module not in grouped_permissions:
            grouped_permissions[module] = {}
        if feature not in grouped_permissions[module]:
            grouped_permissions[module][feature] = []
        grouped_permissions[module][feature].append(permission)
    
    context = {
        'user': user,
        'user_roles': user_roles,
        'direct_permissions': direct_permissions,
        'grouped_permissions': grouped_permissions,
        'all_permissions': all_permissions,
    }
    
    return render(request, 'roles_permissions/user_permissions.html', context)


@login_required
def department_list(request):
    """List departments"""
    departments = Department.objects.select_related('parent_department', 'manager').all()
    
    # Apply search
    search = request.GET.get('search')
    if search:
        departments = departments.filter(
            Q(name__icontains=search) | Q(code__icontains=search)
        )
    
    # Calculate statistics
    total_departments = departments.count()
    active_departments = departments.filter(is_active=True).count()
    departments_with_managers = departments.filter(manager__isnull=False).count()
    child_departments = departments.filter(parent_department__isnull=False).count()
    
    # Pagination
    page_size = int(request.GET.get('page_size', 25))
    paginator = Paginator(departments, page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'departments': page_obj,
        'search': search,
        'total_departments': total_departments,
        'active_departments': active_departments,
        'departments_with_managers': departments_with_managers,
        'child_departments': child_departments,
    }
    
    return render(request, 'roles_permissions/department_list.html', context)


@login_required
@permission_required('roles_permissions.add_department')
def department_create(request):
    """Create a new department"""
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            department = form.save()
            messages.success(request, f'Department "{department.name}" created successfully.')
            return redirect('roles_permissions:department_list')
    else:
        form = DepartmentForm()
    
    context = {
        'form': form,
        'title': 'Create Department',
        'submit_text': 'Create Department',
    }
    
    return render(request, 'roles_permissions/department_form.html', context)


@login_required
def department_detail(request, pk):
    """View department details"""
    department = get_object_or_404(Department, pk=pk)
    
    # Get child departments
    child_departments = department.child_departments.all()
    
    # Get cost centers in this department
    cost_centers = department.cost_centers.all()
    
    context = {
        'department': department,
        'child_departments': child_departments,
        'cost_centers': cost_centers,
    }
    
    return render(request, 'roles_permissions/department_detail.html', context)


@login_required
@permission_required('roles_permissions.change_department')
def department_update(request, pk):
    """Update a department"""
    department = get_object_or_404(Department, pk=pk)
    
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            department = form.save()
            messages.success(request, f'Department "{department.name}" updated successfully.')
            return redirect('roles_permissions:department_list')
    else:
        form = DepartmentForm(instance=department)
    
    context = {
        'form': form,
        'department': department,
        'title': 'Edit Department',
        'submit_text': 'Update Department',
    }
    
    return render(request, 'roles_permissions/department_form.html', context)


@login_required
@permission_required('roles_permissions.delete_department')
def department_delete(request, pk):
    """Delete a department"""
    department = get_object_or_404(Department, pk=pk)
    
    if request.method == 'POST':
        name = department.name
        department.delete()
        messages.success(request, f'Department "{name}" deleted successfully.')
        return redirect('roles_permissions:department_list')
    
    context = {
        'department': department,
    }
    
    return render(request, 'roles_permissions/department_confirm_delete.html', context)


@login_required
def cost_center_list(request):
    """List cost centers"""
    cost_centers = CostCenter.objects.select_related('department', 'manager').all()
    
    # Apply search
    search = request.GET.get('search')
    if search:
        cost_centers = cost_centers.filter(
            Q(name__icontains=search) | Q(code__icontains=search)
        )
    
    # Calculate statistics
    total_cost_centers = cost_centers.count()
    active_cost_centers = cost_centers.filter(is_active=True).count()
    cost_centers_with_managers = cost_centers.filter(manager__isnull=False).count()
    cost_centers_with_departments = cost_centers.filter(department__isnull=False).count()
    
    context = {
        'cost_centers': cost_centers,
        'search': search,
        'total_cost_centers': total_cost_centers,
        'active_cost_centers': active_cost_centers,
        'cost_centers_with_managers': cost_centers_with_managers,
        'cost_centers_with_departments': cost_centers_with_departments,
    }
    
    return render(request, 'roles_permissions/cost_center_list.html', context)


@login_required
@permission_required('roles_permissions.add_costcenter')
def cost_center_create(request):
    """Create a new cost center"""
    if request.method == 'POST':
        form = CostCenterForm(request.POST)
        if form.is_valid():
            cost_center = form.save()
            messages.success(request, f'Cost center "{cost_center.name}" created successfully.')
            return redirect('roles_permissions:cost_center_list')
    else:
        form = CostCenterForm()
    
    context = {
        'form': form,
        'title': 'Create Cost Center',
        'submit_text': 'Create Cost Center',
    }
    
    return render(request, 'roles_permissions/cost_center_form.html', context)


@login_required
def cost_center_detail(request, pk):
    """View cost center details"""
    cost_center = get_object_or_404(CostCenter, pk=pk)
    
    context = {
        'cost_center': cost_center,
    }
    
    return render(request, 'roles_permissions/cost_center_detail.html', context)


@login_required
@permission_required('roles_permissions.change_costcenter')
def cost_center_update(request, pk):
    """Update a cost center"""
    cost_center = get_object_or_404(CostCenter, pk=pk)
    
    if request.method == 'POST':
        form = CostCenterForm(request.POST, instance=cost_center)
        if form.is_valid():
            cost_center = form.save()
            messages.success(request, f'Cost center "{cost_center.name}" updated successfully.')
            return redirect('roles_permissions:cost_center_list')
    else:
        form = CostCenterForm(instance=cost_center)
    
    context = {
        'form': form,
        'cost_center': cost_center,
        'title': 'Edit Cost Center',
        'submit_text': 'Update Cost Center',
    }
    
    return render(request, 'roles_permissions/cost_center_form.html', context)


@login_required
@permission_required('roles_permissions.delete_costcenter')
def cost_center_delete(request, pk):
    """Delete a cost center"""
    cost_center = get_object_or_404(CostCenter, pk=pk)
    
    if request.method == 'POST':
        name = cost_center.name
        cost_center.delete()
        messages.success(request, f'Cost center "{name}" deleted successfully.')
        return redirect('roles_permissions:cost_center_list')
    
    context = {
        'cost_center': cost_center,
    }
    
    return render(request, 'roles_permissions/cost_center_confirm_delete.html', context)


# API views for AJAX requests
@login_required
def get_user_permissions(request, user_id):
    """Get user permissions for AJAX requests"""
    user = get_object_or_404(User, pk=user_id)
    
    # Get all permissions for the user
    permissions = set()
    user_roles = user.user_roles.select_related('role').filter(is_active=True)
    
    for user_role in user_roles:
        if not user_role.is_expired:
            role_permissions = user_role.role.get_all_permissions()
            permissions.update(role_permissions)
    
    # Add direct permissions
    direct_permissions = user.rp_user_permissions.select_related('permission').filter(is_active=True)
    for user_perm in direct_permissions:
        if user_perm.is_granted:
            permissions.add(user_perm.permission)
        else:
            permissions.discard(user_perm.permission)
    
    permission_data = [
        {
            'id': str(perm.id),
            'name': perm.name,
            'codename': perm.codename,
            'module': perm.module,
            'feature': perm.feature,
            'permission_type': perm.permission_type,
        }
        for perm in permissions
    ]
    
    return JsonResponse({'permissions': permission_data})


@login_required
def check_permission(request):
    """Check if user has specific permission"""
    permission_codename = request.GET.get('permission')
    user_id = request.GET.get('user_id')
    
    if not permission_codename:
        return JsonResponse({'has_permission': False, 'error': 'Permission codename required'})
    
    if user_id:
        user = get_object_or_404(User, pk=user_id)
    else:
        user = request.user
    
    # Check if user has the permission
    has_permission = False
    user_roles = user.user_roles.select_related('role').filter(is_active=True)
    
    for user_role in user_roles:
        if not user_role.is_expired:
            role_permissions = user_role.role.get_all_permissions()
            if any(perm.codename == permission_codename for perm in role_permissions):
                has_permission = True
                break
    
    # Check direct permissions
    direct_permission = user.rp_user_permissions.filter(
        permission__codename=permission_codename,
        is_active=True
    ).first()
    
    if direct_permission:
        has_permission = direct_permission.is_granted
    
    return JsonResponse({'has_permission': has_permission})
