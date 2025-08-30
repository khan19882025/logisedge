from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import date, timedelta
import json

from .models import (
    LeaveRequest, LeaveType, LeaveBalance, LeaveApproval, 
    LeavePolicy, LeaveEncashment, LeaveNotification, LeaveCalendar
)
from .forms import (
    LeaveRequestForm, LeaveApprovalForm, LeaveBalanceForm, 
    LeaveTypeForm, LeavePolicyForm, LeaveEncashmentForm,
    LeaveSearchForm, BulkLeaveBalanceForm
)


@login_required
def leave_dashboard(request):
    """Leave Management Dashboard"""
    today = date.today()
    current_year = today.year
    
    # Get user's leave balances
    leave_balances = LeaveBalance.objects.filter(
        employee=request.user,
        year=current_year
    ).select_related('leave_type')
    
    # Get user's leave requests
    user_requests = LeaveRequest.objects.filter(
        employee=request.user
    ).select_related('leave_type').order_by('-submitted_at')[:5]
    
    # Get pending approvals (for managers)
    pending_approvals = []
    if request.user.has_perm('leave_management.can_approve_leave'):
        pending_approvals = LeaveRequest.objects.filter(
            status='pending'
        ).select_related('employee', 'leave_type').order_by('-submitted_at')[:5]
    
    # Get upcoming leaves
    upcoming_leaves = LeaveRequest.objects.filter(
        status='approved',
        start_date__gte=today
    ).select_related('employee', 'leave_type').order_by('start_date')[:10]
    
    # Get leave statistics
    total_requests = LeaveRequest.objects.filter(employee=request.user).count()
    approved_requests = LeaveRequest.objects.filter(
        employee=request.user, 
        status='approved'
    ).count()
    pending_requests = LeaveRequest.objects.filter(
        employee=request.user, 
        status='pending'
    ).count()
    rejected_requests = LeaveRequest.objects.filter(
        employee=request.user, 
        status='rejected'
    ).count()
    
    # Get notifications
    notifications = LeaveNotification.objects.filter(
        recipient=request.user,
        is_read=False
    ).order_by('-created_at')[:5]
    
    context = {
        'leave_balances': leave_balances,
        'user_requests': user_requests,
        'pending_approvals': pending_approvals,
        'upcoming_leaves': upcoming_leaves,
        'total_requests': total_requests,
        'approved_requests': approved_requests,
        'pending_requests': pending_requests,
        'rejected_requests': rejected_requests,
        'notifications': notifications,
        'current_year': current_year,
    }
    
    return render(request, 'leave_management/dashboard.html', context)


@login_required
def leave_request_create(request):
    """Create a new leave request"""
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            leave_request = form.save(commit=False)
            leave_request.employee = request.user
            
            # Set current approver (for now, set to user's manager or admin)
            if request.user.groups.filter(name='Managers').exists():
                leave_request.current_approver = request.user
            else:
                # Find manager or admin to approve
                manager = User.objects.filter(groups__name='Managers').first()
                if manager:
                    leave_request.current_approver = manager
            
            leave_request.save()
            
            # Create notification for approver
            if leave_request.current_approver:
                LeaveNotification.objects.create(
                    recipient=leave_request.current_approver,
                    notification_type='approval_required',
                    title=f'Leave Request from {request.user.get_full_name()}',
                    message=f'{request.user.get_full_name()} has submitted a leave request for {leave_request.leave_type.name}',
                    related_leave_request=leave_request
                )
            
            messages.success(request, 'Leave request submitted successfully!')
            return redirect('leave_management:leave_dashboard')
    else:
        form = LeaveRequestForm(user=request.user)
    
    context = {
        'form': form,
        'title': 'Submit Leave Request'
    }
    return render(request, 'leave_management/leave_request_form.html', context)


@login_required
def leave_request_detail(request, request_id):
    """View leave request details"""
    leave_request = get_object_or_404(LeaveRequest, request_id=request_id)
    
    # Check if user has permission to view this request
    if not (request.user == leave_request.employee or 
            request.user.has_perm('leave_management.can_approve_leave')):
        messages.error(request, 'You do not have permission to view this leave request.')
        return redirect('leave_management:leave_dashboard')
    
    # Get approval history
    approvals = LeaveApproval.objects.filter(leave_request=leave_request)
    
    context = {
        'leave_request': leave_request,
        'approvals': approvals,
    }
    return render(request, 'leave_management/leave_request_detail.html', context)


@login_required
def leave_request_list(request):
    """List all leave requests"""
    search_form = LeaveSearchForm(request.GET)
    leave_requests = LeaveRequest.objects.all()
    
    # Apply filters
    if search_form.is_valid():
        if search_form.cleaned_data.get('employee'):
            leave_requests = leave_requests.filter(
                employee=search_form.cleaned_data['employee']
            )
        if search_form.cleaned_data.get('leave_type'):
            leave_requests = leave_requests.filter(
                leave_type_id=search_form.cleaned_data['leave_type']
            )
        if search_form.cleaned_data.get('status'):
            leave_requests = leave_requests.filter(
                status=search_form.cleaned_data['status']
            )
        if search_form.cleaned_data.get('start_date_from'):
            leave_requests = leave_requests.filter(
                start_date__gte=search_form.cleaned_data['start_date_from']
            )
        if search_form.cleaned_data.get('start_date_to'):
            leave_requests = leave_requests.filter(
                start_date__lte=search_form.cleaned_data['start_date_to']
            )
    
    # Filter by user permissions
    if not request.user.has_perm('leave_management.can_view_all_requests'):
        leave_requests = leave_requests.filter(employee=request.user)
    
    leave_requests = leave_requests.select_related('employee', 'leave_type').order_by('-submitted_at')
    
    # Pagination
    paginator = Paginator(leave_requests, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
    }
    return render(request, 'leave_management/leave_request_list.html', context)


@login_required
@permission_required('leave_management.can_approve_leave')
def leave_approval(request, request_id):
    """Approve or reject leave request"""
    leave_request = get_object_or_404(LeaveRequest, request_id=request_id)
    
    if request.method == 'POST':
        form = LeaveApprovalForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            comments = form.cleaned_data['comments']
            
            # Create approval record
            LeaveApproval.objects.create(
                leave_request=leave_request,
                approver=request.user,
                action=action,
                comments=comments
            )
            
            # Update leave request status
            if action == 'approve':
                leave_request.status = 'approved'
                leave_request.approved_by = request.user
                leave_request.approved_at = timezone.now()
                leave_request.approval_comments = comments
                
                # Update leave balance
                balance, created = LeaveBalance.objects.get_or_create(
                    employee=leave_request.employee,
                    leave_type=leave_request.leave_type,
                    year=date.today().year,
                    defaults={'allocated_days': 0, 'used_days': 0}
                )
                balance.used_days += leave_request.total_days
                balance.save()
                
                # Create notification for employee
                LeaveNotification.objects.create(
                    recipient=leave_request.employee,
                    notification_type='request_approved',
                    title='Leave Request Approved',
                    message=f'Your leave request for {leave_request.leave_type.name} has been approved.',
                    related_leave_request=leave_request
                )
                
                messages.success(request, 'Leave request approved successfully!')
                
            elif action == 'reject':
                leave_request.status = 'rejected'
                leave_request.approval_comments = comments
                
                # Create notification for employee
                LeaveNotification.objects.create(
                    recipient=leave_request.employee,
                    notification_type='request_rejected',
                    title='Leave Request Rejected',
                    message=f'Your leave request for {leave_request.leave_type.name} has been rejected.',
                    related_leave_request=leave_request
                )
                
                messages.success(request, 'Leave request rejected.')
            
            leave_request.save()
            return redirect('leave_management:leave_request_detail', request_id=request_id)
    else:
        form = LeaveApprovalForm()
    
    context = {
        'leave_request': leave_request,
        'form': form,
    }
    return render(request, 'leave_management/leave_approval.html', context)


@login_required
def leave_balance_list(request):
    """List leave balances"""
    current_year = date.today().year
    
    if request.user.has_perm('leave_management.can_view_all_balances'):
        balances = LeaveBalance.objects.filter(year=current_year)
    else:
        balances = LeaveBalance.objects.filter(
            employee=request.user,
            year=current_year
        )
    
    balances = balances.select_related('employee', 'leave_type').order_by('employee__first_name')
    
    # Pagination
    paginator = Paginator(balances, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'current_year': current_year,
    }
    return render(request, 'leave_management/leave_balance_list.html', context)


@login_required
@permission_required('leave_management.can_manage_balances')
def leave_balance_edit(request, balance_id):
    """Edit leave balance"""
    balance = get_object_or_404(LeaveBalance, id=balance_id)
    
    if request.method == 'POST':
        form = LeaveBalanceForm(request.POST, instance=balance)
        if form.is_valid():
            form.save()
            messages.success(request, 'Leave balance updated successfully!')
            return redirect('leave_management:leave_balance_list')
    else:
        form = LeaveBalanceForm(instance=balance)
    
    context = {
        'form': form,
        'balance': balance,
    }
    return render(request, 'leave_management/leave_balance_form.html', context)


@login_required
@permission_required('leave_management.can_manage_balances')
def bulk_leave_balance(request):
    """Bulk leave balance operations"""
    if request.method == 'POST':
        form = BulkLeaveBalanceForm(request.POST)
        if form.is_valid():
            operation = form.cleaned_data['operation']
            leave_type = form.cleaned_data['leave_type']
            year = form.cleaned_data['year']
            employees = form.cleaned_data['employees']
            days = form.cleaned_data['days']
            reason = form.cleaned_data['reason']
            
            success_count = 0
            for employee in employees:
                balance, created = LeaveBalance.objects.get_or_create(
                    employee=employee,
                    leave_type=leave_type,
                    year=year,
                    defaults={'allocated_days': 0, 'used_days': 0}
                )
                
                if operation == 'allocate':
                    balance.allocated_days += days
                elif operation == 'adjust':
                    balance.allocated_days = days
                elif operation == 'carry_forward':
                    balance.carried_forward_days += days
                
                balance.save()
                success_count += 1
            
            messages.success(request, f'Successfully processed {success_count} employee(s).')
            return redirect('leave_management:leave_balance_list')
    else:
        form = BulkLeaveBalanceForm()
    
    context = {
        'form': form,
    }
    return render(request, 'leave_management/bulk_leave_balance.html', context)


@login_required
def leave_calendar(request):
    """Calendar view of leaves"""
    year = request.GET.get('year', date.today().year)
    month = request.GET.get('month', date.today().month)
    
    # Get leaves for the specified month
    start_date = date(int(year), int(month), 1)
    if int(month) == 12:
        end_date = date(int(year) + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(int(year), int(month) + 1, 1) - timedelta(days=1)
    
    leaves = LeaveRequest.objects.filter(
        status='approved',
        start_date__lte=end_date,
        end_date__gte=start_date
    ).select_related('employee', 'leave_type')
    
    # Filter by user permissions
    if not request.user.has_perm('leave_management.can_view_all_requests'):
        leaves = leaves.filter(employee=request.user)
    
    context = {
        'leaves': leaves,
        'year': int(year),
        'month': int(month),
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'leave_management/leave_calendar.html', context)


@login_required
def leave_encashment_create(request):
    """Create leave encashment request"""
    if request.method == 'POST':
        form = LeaveEncashmentForm(request.POST, user=request.user)
        if form.is_valid():
            encashment = form.save(commit=False)
            encashment.employee = request.user
            encashment.save()
            
            messages.success(request, 'Encashment request submitted successfully!')
            return redirect('leave_management:leave_dashboard')
    else:
        form = LeaveEncashmentForm(user=request.user)
    
    context = {
        'form': form,
    }
    return render(request, 'leave_management/leave_encashment_form.html', context)


@login_required
@permission_required('leave_management.can_approve_encashment')
def leave_encashment_approval(request, encashment_id):
    """Approve/reject encashment request"""
    encashment = get_object_or_404(LeaveEncashment, id=encashment_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action in ['approve', 'reject']:
            encashment.status = action
            encashment.approved_by = request.user
            encashment.approved_at = timezone.now()
            encashment.save()
            
            if action == 'approve':
                # Update leave balance
                balance = LeaveBalance.objects.get(
                    employee=encashment.employee,
                    leave_type=encashment.leave_type,
                    year=encashment.encashment_year
                )
                balance.encashed_days += encashment.days_to_encash
                balance.save()
                
                messages.success(request, 'Encashment request approved!')
            else:
                messages.success(request, 'Encashment request rejected.')
            
            return redirect('leave_management:leave_encashment_list')
    
    context = {
        'encashment': encashment,
    }
    return render(request, 'leave_management/leave_encashment_approval.html', context)


@login_required
def leave_encashment_list(request):
    """List encashment requests"""
    if request.user.has_perm('leave_management.can_view_all_encashments'):
        encashments = LeaveEncashment.objects.all()
    else:
        encashments = LeaveEncashment.objects.filter(employee=request.user)
    
    encashments = encashments.select_related('employee', 'leave_type').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(encashments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'leave_management/leave_encashment_list.html', context)


@login_required
def leave_notifications(request):
    """List user notifications"""
    notifications = LeaveNotification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')
    
    # Mark as read
    if request.method == 'POST':
        notification_id = request.POST.get('notification_id')
        if notification_id:
            notification = get_object_or_404(LeaveNotification, id=notification_id, recipient=request.user)
            notification.is_read = True
            notification.save()
            return JsonResponse({'status': 'success'})
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'leave_management/leave_notifications.html', context)


@login_required
@permission_required('leave_management.can_manage_leave_types')
def leave_type_list(request):
    """List leave types"""
    leave_types = LeaveType.objects.all().order_by('name')
    
    context = {
        'leave_types': leave_types,
    }
    return render(request, 'leave_management/leave_type_list.html', context)


@login_required
@permission_required('leave_management.can_manage_leave_types')
def leave_type_create(request):
    """Create new leave type"""
    if request.method == 'POST':
        form = LeaveTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Leave type created successfully!')
            return redirect('leave_management:leave_type_list')
    else:
        form = LeaveTypeForm()
    
    context = {
        'form': form,
        'title': 'Create Leave Type'
    }
    return render(request, 'leave_management/leave_type_form.html', context)


@login_required
@permission_required('leave_management.can_manage_leave_types')
def leave_type_edit(request, type_id):
    """Edit leave type"""
    leave_type = get_object_or_404(LeaveType, id=type_id)
    
    if request.method == 'POST':
        form = LeaveTypeForm(request.POST, instance=leave_type)
        if form.is_valid():
            form.save()
            messages.success(request, 'Leave type updated successfully!')
            return redirect('leave_management:leave_type_list')
    else:
        form = LeaveTypeForm(instance=leave_type)
    
    context = {
        'form': form,
        'leave_type': leave_type,
        'title': 'Edit Leave Type'
    }
    return render(request, 'leave_management/leave_type_form.html', context)


@login_required
@permission_required('leave_management.can_manage_policies')
def leave_policy_list(request):
    """List leave policies"""
    policies = LeavePolicy.objects.filter(is_active=True).order_by('name')
    
    context = {
        'policies': policies,
    }
    return render(request, 'leave_management/leave_policy_list.html', context)


@login_required
@permission_required('leave_management.can_manage_policies')
def leave_policy_create(request):
    """Create new leave policy"""
    if request.method == 'POST':
        form = LeavePolicyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Leave policy created successfully!')
            return redirect('leave_management:leave_policy_list')
    else:
        form = LeavePolicyForm()
    
    context = {
        'form': form,
        'title': 'Create Leave Policy'
    }
    return render(request, 'leave_management/leave_policy_form.html', context)


@login_required
@permission_required('leave_management.can_manage_policies')
def leave_policy_edit(request, policy_id):
    """Edit leave policy"""
    policy = get_object_or_404(LeavePolicy, id=policy_id)
    
    if request.method == 'POST':
        form = LeavePolicyForm(request.POST, instance=policy)
        if form.is_valid():
            form.save()
            messages.success(request, 'Leave policy updated successfully!')
            return redirect('leave_management:leave_policy_list')
    else:
        form = LeavePolicyForm(instance=policy)
    
    context = {
        'form': form,
        'policy': policy,
        'title': 'Edit Leave Policy'
    }
    return render(request, 'leave_management/leave_policy_form.html', context)


@login_required
def leave_reports(request):
    """Leave Management Reports"""
    # Implementation for reports
    context = {
        'title': 'Leave Reports',
    }
    return render(request, 'leave_management/reports.html', context)


@login_required
def leave_balance(request):
    """Get leave balance for a specific leave type (AJAX endpoint)"""
    leave_type_id = request.GET.get('leave_type')
    employee_id = request.GET.get('employee')
    
    if not leave_type_id:
        return JsonResponse({'error': 'Leave type ID is required'}, status=400)
    
    # Determine which employee's balance to check
    if employee_id:
        # HR/Manager is checking another employee's balance
        try:
            employee = User.objects.get(id=employee_id)
            # Check if current user has permission to view this employee's balance
            if not (request.user.is_superuser or 
                   request.user.has_perm('leave_management.can_manage_leave_types') or
                   request.user.has_perm('leave_management.can_approve_leave') or
                   request.user.groups.filter(name__in=['HR', 'Managers', 'Administrators']).exists()):
                return JsonResponse({'error': 'Permission denied'}, status=403)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Employee not found'}, status=404)
    else:
        # Regular employee checking their own balance
        employee = request.user
    
    try:
        balance = LeaveBalance.objects.get(
            employee=employee,
            leave_type_id=leave_type_id,
            year=date.today().year
        )
        
        data = {
            'balance': {
                'leave_type_name': balance.leave_type.name,
                'total_days': balance.total_balance,
                'used_days': balance.used_days,
                'available_days': balance.available_days,
                'carry_forward_days': balance.carried_forward_days,
            }
        }
        return JsonResponse(data)
    except LeaveBalance.DoesNotExist:
        return JsonResponse({'error': 'Leave balance not found'}, status=404)


@login_required
def leave_policy(request):
    """Get leave policy information (AJAX endpoint)"""
    try:
        # Get the default policy or the first available policy
        policy = LeavePolicy.objects.filter(is_active=True).first()
        
        if policy:
            data = {
                'policy': {
                    'advance_notice_days': 3,  # Default value
                    'max_duration_days': 30,   # Default value
                    'carry_forward_days': policy.carry_forward_percentage,
                    'allow_encashment': policy.encashment_allowed,
                    'probation_period_days': policy.probation_period_months * 30,  # Convert months to days
                }
            }
        else:
            data = {'policy': None}
        
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
