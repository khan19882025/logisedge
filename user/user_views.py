from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from user.user_model import UserProfile, Role, CustomPermission, RolePermission
from user.user_form import UserForm, RoleForm, CustomPermissionForm
import json

@login_required
def user_list(request):
    """Display list of users with search and pagination"""
    users = User.objects.select_related('profile').all().order_by('username')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(profile__employee_id__icontains=search_query) |
            Q(profile__department__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(users, 10)  # Show 10 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_users': users.count(),
    }
    return render(request, 'user/user_list.html', context)

@login_required
def user_create(request):
    """Create a new user"""
    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User "{user.username}" created successfully!')
            return redirect('user:user_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserForm()
    
    context = {
        'form': form,
        'action': 'Create',
        'title': 'Create New User'
    }
    return render(request, 'user/user_form.html', context)

@login_required
def user_update(request, pk):
    """Update an existing user"""
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User "{user.username}" updated successfully!')
            return redirect('user:user_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserForm(instance=user)
    
    context = {
        'form': form,
        'user': user,
        'action': 'Update',
        'title': f'Update User: {user.username}'
    }
    return render(request, 'user/user_form.html', context)

@login_required
def user_delete(request, pk):
    """Delete a user"""
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User "{username}" deleted successfully!')
        return redirect('user:user_list')
    
    context = {
        'user': user,
        'title': f'Delete User: {user.username}'
    }
    return render(request, 'user/user_confirm_delete.html', context)

@login_required
def user_detail(request, pk):
    """Display user details"""
    user = get_object_or_404(User, pk=pk)
    
    context = {
        'user': user,
        'title': f'User Details: {user.username}'
    }
    return render(request, 'user/user_detail.html', context)

# Role Management Views
@login_required
def role_list(request):
    """Display list of roles"""
    roles = Role.objects.all().order_by('name')
    
    search_query = request.GET.get('search', '')
    if search_query:
        roles = roles.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    paginator = Paginator(roles, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_roles': roles.count(),
    }
    return render(request, 'user/role_list.html', context)

@login_required
def role_create(request):
    """Create a new role"""
    if request.method == 'POST':
        form = RoleForm(request.POST)
        if form.is_valid():
            role = form.save()
            messages.success(request, f'Role "{role.name}" created successfully!')
            return redirect('user:role_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RoleForm()
    
    context = {
        'form': form,
        'action': 'Create',
        'title': 'Create New Role'
    }
    return render(request, 'user/role_form.html', context)

@login_required
def role_update(request, pk):
    """Update an existing role"""
    role = get_object_or_404(Role, pk=pk)
    
    if request.method == 'POST':
        form = RoleForm(request.POST, instance=role)
        if form.is_valid():
            role = form.save()
            messages.success(request, f'Role "{role.name}" updated successfully!')
            return redirect('user:role_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RoleForm(instance=role)
    
    context = {
        'form': form,
        'role': role,
        'action': 'Update',
        'title': f'Update Role: {role.name}'
    }
    return render(request, 'user/role_form.html', context)

# Permission Management Views
@login_required
def permission_list(request):
    """Display list of permissions"""
    permissions = CustomPermission.objects.all().order_by('name')
    
    search_query = request.GET.get('search', '')
    if search_query:
        permissions = permissions.filter(
            Q(name__icontains=search_query) |
            Q(codename__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    paginator = Paginator(permissions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_permissions': permissions.count(),
    }
    return render(request, 'user/permission_list.html', context)

@login_required
def permission_create(request):
    """Create a new permission"""
    if request.method == 'POST':
        form = CustomPermissionForm(request.POST)
        if form.is_valid():
            permission = form.save()
            messages.success(request, f'Permission "{permission.name}" created successfully!')
            return redirect('user:permission_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomPermissionForm()
    
    context = {
        'form': form,
        'action': 'Create',
        'title': 'Create New Permission'
    }
    return render(request, 'user/permission_form.html', context)

@login_required
def permission_update(request, pk):
    """Update an existing permission"""
    permission = get_object_or_404(CustomPermission, pk=pk)
    
    if request.method == 'POST':
        form = CustomPermissionForm(request.POST, instance=permission)
        if form.is_valid():
            permission = form.save()
            messages.success(request, f'Permission "{permission.name}" updated successfully!')
            return redirect('user:permission_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomPermissionForm(instance=permission)
    
    context = {
        'form': form,
        'permission': permission,
        'action': 'Update',
        'title': f'Update Permission: {permission.name}'
    }
    return render(request, 'user/permission_form.html', context)

# AJAX views for dynamic functionality
@login_required
def get_role_permissions(request, role_id):
    """Get permissions for a specific role via AJAX"""
    try:
        role = Role.objects.get(id=role_id)
        permissions = role.role_permissions.values_list('permission_id', flat=True)
        return JsonResponse({'permissions': list(permissions)})
    except Role.DoesNotExist:
        return JsonResponse({'permissions': []})

@login_required
def update_role_permissions(request, role_id):
    """Update permissions for a specific role via AJAX"""
    if request.method == 'POST':
        try:
            role = Role.objects.get(id=role_id)
            permission_ids = request.POST.getlist('permissions[]')
            
            # Clear existing permissions
            role.role_permissions.all().delete()
            
            # Add new permissions
            for permission_id in permission_ids:
                try:
                    permission = CustomPermission.objects.get(id=permission_id)
                    role.role_permissions.create(permission=permission)
                except CustomPermission.DoesNotExist:
                    continue
            
            return JsonResponse({'success': True})
        except Role.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Role not found'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def change_password(request, pk):
    """Change user password"""
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        # Validate current password
        if not user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
            return redirect('user:user_edit', pk=pk)

@login_required
def permissions_management(request):
    """User Permissions Management Page with three-panel interface"""
    
    # Define main menu modules and their submenus based on base.html navigation
    menu_structure = {
        'Master': [
            {'name': 'Customer', 'codename': 'master_customer'},
            {'name': 'Items', 'codename': 'master_items'},
            {'name': 'Port', 'codename': 'master_port'},
            {'name': 'Service', 'codename': 'master_service'},
            {'name': 'Charges', 'codename': 'master_charges'},
            {'name': 'Salesman', 'codename': 'master_salesman'},
            {'name': 'Facility', 'codename': 'master_facility'},
            {'name': 'Payment Sources', 'codename': 'master_payment_sources'},
            {'name': 'Chart of Account', 'codename': 'master_chart_of_account'},
            {'name': 'Ledger', 'codename': 'master_ledger'},
        ],
        'Warehouse': [
            {'name': 'Quotation', 'codename': 'warehouse_quotation'},
            {'name': 'New Job', 'codename': 'warehouse_new_job'},
            {'name': 'GRN', 'codename': 'warehouse_grn'},
            {'name': 'Putaways', 'codename': 'warehouse_putaways'},
            {'name': 'Documentation', 'codename': 'warehouse_documentation'},
            {'name': 'Cross Stuffing', 'codename': 'warehouse_cross_stuffing'},
            {'name': 'Delivery Order', 'codename': 'warehouse_delivery_order'},
            {'name': 'Picklist', 'codename': 'warehouse_picklist'},
            {'name': 'Dispatch Note', 'codename': 'warehouse_dispatch_note'},
            {'name': 'Stock Transfer', 'codename': 'warehouse_stock_transfer'},
            {'name': 'Location Transfer', 'codename': 'warehouse_location_transfer'},
            {'name': 'Storage Invoice', 'codename': 'warehouse_storage_invoice'},
            {'name': 'Invoice', 'codename': 'warehouse_invoice'},
            {'name': 'Pro-Forma Invoice', 'codename': 'warehouse_pro_forma_invoice'},
            {'name': 'LGP', 'codename': 'warehouse_lgp'},
        ],
        'Freight': [
            {'name': 'Freight Quotation', 'codename': 'freight_quotation'},
            {'name': 'Freight Booking', 'codename': 'freight_booking'},
            {'name': 'Container Management', 'codename': 'freight_container_management'},
            {'name': 'Bill of Lading', 'codename': 'freight_bill_of_lading'},
            {'name': 'Tracking & Status Update', 'codename': 'freight_tracking_status'},
            {'name': 'Freight Invoice', 'codename': 'freight_invoice'},
            {'name': 'Vendor Freight Bills', 'codename': 'freight_vendor_bills'},
        ],
        'Accounting': [
            {'name': 'Credit Notes', 'codename': 'accounting_credit_notes'},
            {'name': 'Customer Payments', 'codename': 'accounting_customer_payments'},
            {'name': 'Dunning Letters', 'codename': 'accounting_dunning_letters'},
            {'name': 'Supplier Bills', 'codename': 'accounting_supplier_bills'},
            {'name': 'Debit Notes', 'codename': 'accounting_debit_notes'},
            {'name': 'Supplier Payments', 'codename': 'accounting_supplier_payments'},
            {'name': 'Payment Scheduling', 'codename': 'accounting_payment_scheduling'},
            {'name': 'General Journal', 'codename': 'accounting_general_journal'},
            {'name': 'Payment Voucher', 'codename': 'accounting_payment_voucher'},
            {'name': 'Receipt Voucher', 'codename': 'accounting_receipt_voucher'},
            {'name': 'Contra Entry', 'codename': 'accounting_contra_entry'},
            {'name': 'Bank Accounts', 'codename': 'accounting_bank_accounts'},
            {'name': 'Bank Reconciliation', 'codename': 'accounting_bank_reconciliation'},
            {'name': 'Tax Settings (VAT)', 'codename': 'accounting_tax_settings'},
            {'name': 'Tax Invoices', 'codename': 'accounting_tax_invoices'},
            {'name': 'Asset Register', 'codename': 'accounting_asset_register'},
            {'name': 'Depreciation Schedule', 'codename': 'accounting_depreciation_schedule'},
        ],
        'HR': [
            {'name': 'Employee Management', 'codename': 'hr_employee_management'},
            {'name': 'Attendance & Time Tracking', 'codename': 'hr_attendance_time_tracking'},
            {'name': 'Leave Management', 'codename': 'hr_leave_management'},
            {'name': 'Payroll', 'codename': 'hr_payroll'},
            {'name': 'Recruitment', 'codename': 'hr_recruitment'},
            {'name': 'Disciplinary & Grievance', 'codename': 'hr_disciplinary_grievance'},
            {'name': 'HR Letters & Documents', 'codename': 'hr_letters_documents'},
            {'name': 'Exit Management', 'codename': 'hr_exit_management'},
        ],
        'Admin': [
            {'name': 'Company', 'codename': 'admin_company'},
            {'name': 'User', 'codename': 'admin_user'},
            {'name': 'Permissions Management', 'codename': 'admin_permissions_management'},
        ],
        'Settings': [
            {'name': 'Fiscal Year Settings', 'codename': 'settings_fiscal_year'},
            {'name': 'Multi-Currency Setup', 'codename': 'settings_multi_currency'},
            {'name': 'Approval Workflows', 'codename': 'settings_approval_workflows'},
            {'name': 'Roles & Permissions', 'codename': 'settings_roles_permissions'},
        ],
        'Utilities': [
            {'name': 'Import Master Data', 'codename': 'utilities_import_master_data'},
            {'name': 'Bulk Export', 'codename': 'utilities_bulk_export'},
            {'name': 'Data Cleaning Tool', 'codename': 'utilities_data_cleaning'},
            {'name': 'Merge Duplicates', 'codename': 'utilities_merge_duplicates'},
            {'name': 'Backup & Restore', 'codename': 'utilities_backup_restore'},
            {'name': 'System Health Check', 'codename': 'utilities_system_health_check'},
        ],
        'Reports': [
            {'name': 'Item Master List', 'codename': 'reports_item_master_list'},
            {'name': 'Customer & Supplier Master', 'codename': 'reports_customer_supplier_master'},
            {'name': 'Inventory Reports', 'codename': 'reports_inventory'},
            {'name': 'Financial Reports', 'codename': 'reports_financial'},
            {'name': 'HR Reports', 'codename': 'reports_hr'},
        ]
    }
    
    # Permission types
    permission_types = ['view', 'new', 'edit', 'delete', 'print']
    
    # Get all users for the left panel
    users = User.objects.select_related('profile').filter(is_active=True).order_by('username')
    
    # Handle AJAX requests
    if request.method == 'POST':
        try:
            # Parse JSON data
            data = json.loads(request.body)
            user_id = data.get('user_id')
            permissions_data = data.get('permissions', {})
            
            user = User.objects.get(id=user_id)
            
            # Create or get user role (for simplicity, create individual roles)
            role_name = f"{user.username}_role"
            role, created = Role.objects.get_or_create(
                name=role_name,
                defaults={'description': f'Individual role for {user.username}'}
            )
            
            # Update user profile role
            if hasattr(user, 'profile'):
                user.profile.role = role
                user.profile.save()
            else:
                # Create profile if it doesn't exist
                UserProfile.objects.create(user=user, role=role)
            
            # Clear existing role permissions
            RolePermission.objects.filter(role=role).delete()
            
            # Add new permissions
            for perm_code, is_enabled in permissions_data.items():
                if is_enabled:  # Only add permissions that are enabled
                    permission, created = CustomPermission.objects.get_or_create(
                        codename=perm_code,
                        defaults={'name': perm_code.replace('_', ' ').title()}
                    )
                    RolePermission.objects.create(role=role, permission=permission)
            
            return JsonResponse({
                'success': True,
                'message': f'Permissions updated for {user.get_full_name() or user.username}'
            })
            
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'User not found'})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    # Get user permissions for JavaScript
    user_permissions = {}
    for user in users:
        user_perms = {}
        if hasattr(user, 'profile') and user.profile.role:
            role_permissions = user.profile.role.role_permissions.select_related('permission')
            for rp in role_permissions:
                user_perms[rp.permission.codename] = True
        user_permissions[str(user.id)] = user_perms
    
    context = {
        'users': users,
        'menu_structure': menu_structure,
        'menu_structure_json': json.dumps(menu_structure),
        'user_permissions': json.dumps(user_permissions),
        'permission_types': json.dumps(permission_types),
    }
    
    return render(request, 'user/permissions_management.html', context)

@login_required
def reset_password(request, pk):
    """Reset user password to temporary password"""
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        admin_password = request.POST.get('admin_password')
        temporary_password = request.POST.get('temporary_password')
        
        # Validate admin password
        if not request.user.check_password(admin_password):
            messages.error(request, 'Your admin password is incorrect.')
            return redirect('user:user_edit', pk=pk)
        
        # Validate temporary password
        if not temporary_password or len(temporary_password) < 8:
            messages.error(request, 'Please generate a valid temporary password.')
            return redirect('user:user_edit', pk=pk)
        
        # Reset password
        user.set_password(temporary_password)
        user.save()
        
        messages.success(request, f'Password for user "{user.username}" has been reset. Temporary password: {temporary_password}')
        return redirect('user:user_edit', pk=pk)
    
    return redirect('user:user_edit', pk=pk)