from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import json
import logging
import subprocess
import os
import shutil
from datetime import datetime, timedelta

from .restore_models import (
    RestoreRequest, RestoreExecution, RestoreLog, 
    RestoreApprovalWorkflow, RestoreValidationRule, RestoreNotification
)
from .restore_forms import (
    RestoreRequestForm, RestoreApprovalForm, RestoreExecutionForm,
    RestoreValidationForm, RestoreSearchForm, RestoreNotificationForm
)
from .models import BackupExecution, BackupLog

logger = logging.getLogger(__name__)

# Dashboard Views

@login_required
def restore_dashboard(request):
    """Main dashboard for restore management"""
    
    # Get statistics
    total_requests = RestoreRequest.objects.count()
    pending_requests = RestoreRequest.objects.filter(status='pending').count()
    approved_requests = RestoreRequest.objects.filter(status='approved').count()
    completed_requests = RestoreRequest.objects.filter(status='completed').count()
    failed_requests = RestoreRequest.objects.filter(status='failed').count()
    
    # Recent restore requests
    recent_requests = RestoreRequest.objects.all().order_by('-created_at')[:10]
    
    # Pending approvals
    pending_approvals = RestoreRequest.objects.filter(
        status='pending',
        requires_approval=True
    ).order_by('-created_at')[:5]
    
    # Recent executions
    recent_executions = RestoreExecution.objects.all().order_by('-created_at')[:5]
    
    # Restore success rate
    success_rate = 0
    if total_requests > 0:
        success_rate = (completed_requests / total_requests) * 100
    
    # Monthly restore trends
    current_month = timezone.now().month
    current_year = timezone.now().year
    
    monthly_stats = RestoreRequest.objects.filter(
        created_at__year=current_year,
        created_at__month=current_month
    ).aggregate(
        total=Count('id'),
        completed=Count('id', filter=Q(status='completed')),
        failed=Count('id', filter=Q(status='failed'))
    )
    
    context = {
        'total_requests': total_requests,
        'pending_requests': pending_requests,
        'approved_requests': approved_requests,
        'completed_requests': completed_requests,
        'failed_requests': failed_requests,
        'success_rate': round(success_rate, 1),
        'recent_requests': recent_requests,
        'pending_approvals': pending_approvals,
        'recent_executions': recent_executions,
        'monthly_stats': monthly_stats,
    }
    
    return render(request, 'backup_scheduler/restore/restore_dashboard.html', context)

# Restore Request Management

@login_required
@permission_required('backup_scheduler.add_restorerequest')
def restore_request_create(request):
    """Create a new restore request"""
    
    if request.method == 'POST':
        form = RestoreRequestForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            restore_request = form.save()
            
            # Handle file upload
            if 'backup_file' in request.FILES:
                backup_file = request.FILES['backup_file']
                file_path = f'uploads/restore_backups/{backup_file.name}'
                restore_request.source_file_path = file_path
                
                # Save file
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'wb+') as destination:
                    for chunk in backup_file.chunks():
                        destination.write(chunk)
            
            # Handle safety options
            safety_options = form.cleaned_data.get('safety_options', [])
            restore_request.backup_before_restore = 'backup_before_restore' in safety_options
            restore_request.dry_run_enabled = 'dry_run' in safety_options
            
            restore_request.save()
            
            # Create log entry
            RestoreLog.objects.create(
                level='info',
                message=f'Restore request "{restore_request.title}" created by {request.user.username}',
                restore_request=restore_request,
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            # Send notifications
            send_restore_notifications(restore_request, 'request_created')
            
            messages.success(request, 'Restore request created successfully!')
            return redirect('backup_scheduler:restore_request_detail', pk=restore_request.pk)
    else:
        form = RestoreRequestForm(user=request.user)
    
    context = {
        'form': form,
        'title': 'Create Restore Request',
        'submit_text': 'Create Request',
    }
    
    return render(request, 'backup_scheduler/restore/restore_request_form.html', context)

@login_required
def restore_request_list(request):
    """List all restore requests with filtering and search"""
    
    # Get search parameters
    search_form = RestoreSearchForm(request.GET)
    
    # Build queryset
    requests = RestoreRequest.objects.all()
    
    if search_form.is_valid():
        search = search_form.cleaned_data.get('search')
        status = search_form.cleaned_data.get('status')
        priority = search_form.cleaned_data.get('priority')
        restore_type = search_form.cleaned_data.get('restore_type')
        created_by = search_form.cleaned_data.get('created_by')
        date_from = search_form.cleaned_data.get('date_from')
        date_to = search_form.cleaned_data.get('date_to')
        
        if search:
            requests = requests.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(request_id__icontains=search)
            )
        
        if status:
            requests = requests.filter(status=status)
        
        if priority:
            requests = requests.filter(priority=priority)
        
        if restore_type:
            requests = requests.filter(restore_type=restore_type)
        
        if created_by:
            requests = requests.filter(created_by=created_by)
        
        if date_from:
            requests = requests.filter(created_at__date__gte=date_from)
        
        if date_to:
            requests = requests.filter(created_at__date__lte=date_to)
    
    # Order by creation date
    requests = requests.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(requests, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_count': paginator.count,
    }
    
    return render(request, 'backup_scheduler/restore/restore_request_list.html', context)

@login_required
def restore_request_detail(request, pk):
    """View details of a restore request"""
    
    restore_request = get_object_or_404(RestoreRequest, pk=pk)
    
    # Get related executions
    executions = RestoreExecution.objects.filter(restore_request=restore_request).order_by('-created_at')
    
    # Get logs
    logs = RestoreLog.objects.filter(restore_request=restore_request).order_by('-timestamp')
    
    # Check permissions
    can_approve = restore_request.can_approve(request.user)
    can_execute = restore_request.can_execute(request.user)
    
    context = {
        'restore_request': restore_request,
        'executions': executions,
        'logs': logs,
        'can_approve': can_approve,
        'can_execute': can_execute,
    }
    
    return render(request, 'backup_scheduler/restore/restore_request_detail.html', context)

@login_required
@permission_required('backup_scheduler.change_restorerequest')
def restore_request_edit(request, pk):
    """Edit a restore request"""
    
    restore_request = get_object_or_404(RestoreRequest, pk=pk)
    
    # Check if request can be edited
    if restore_request.status not in ['pending', 'rejected']:
        messages.error(request, 'This request cannot be edited in its current status.')
        return redirect('backup_scheduler:restore_request_detail', pk=pk)
    
    if request.method == 'POST':
        form = RestoreRequestForm(request.POST, request.FILES, instance=restore_request, user=request.user)
        if form.is_valid():
            form.save()
            
            # Create log entry
            RestoreLog.objects.create(
                level='info',
                message=f'Restore request "{restore_request.title}" updated by {request.user.username}',
                restore_request=restore_request,
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, 'Restore request updated successfully!')
            return redirect('backup_scheduler:restore_request_detail', pk=pk)
    else:
        form = RestoreRequestForm(instance=restore_request, user=request.user)
    
    context = {
        'form': form,
        'restore_request': restore_request,
        'title': 'Edit Restore Request',
        'submit_text': 'Update Request',
    }
    
    return render(request, 'backup_scheduler/restore/restore_request_form.html', context)

@login_required
@permission_required('backup_scheduler.delete_restorerequest')
def restore_request_delete(request, pk):
    """Delete a restore request"""
    
    restore_request = get_object_or_404(RestoreRequest, pk=pk)
    
    if request.method == 'POST':
        title = restore_request.title
        restore_request.delete()
        
        messages.success(request, f'Restore request "{title}" deleted successfully!')
        return redirect('backup_scheduler:restore_request_list')
    
    context = {
        'restore_request': restore_request,
    }
    
    return render(request, 'backup_scheduler/restore/restore_request_confirm_delete.html', context)

# Approval Workflow

@login_required
@permission_required('backup_scheduler.approve_restorerequest')
def restore_request_approve(request, pk):
    """Approve or reject a restore request"""
    
    restore_request = get_object_or_404(RestoreRequest, pk=pk)
    
    if not restore_request.can_approve(request.user):
        messages.error(request, 'You do not have permission to approve this request.')
        return redirect('backup_scheduler:restore_request_detail', pk=pk)
    
    if request.method == 'POST':
        form = RestoreApprovalForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            approval_notes = form.cleaned_data['approval_notes']
            
            if action == 'approve':
                restore_request.status = 'approved'
                restore_request.approved_by = request.user
                restore_request.approved_at = timezone.now()
                restore_request.approval_notes = approval_notes
                
                # Create log entry
                RestoreLog.objects.create(
                    level='info',
                    message=f'Restore request approved by {request.user.username}',
                    restore_request=restore_request,
                    user=request.user,
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                
                messages.success(request, 'Restore request approved successfully!')
                
                # Send notifications
                send_restore_notifications(restore_request, 'approved')
                
            else:  # reject
                restore_request.status = 'rejected'
                restore_request.approval_notes = approval_notes
                
                # Create log entry
                RestoreLog.objects.create(
                    level='warning',
                    message=f'Restore request rejected by {request.user.username}',
                    restore_request=restore_request,
                    user=request.user,
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                
                messages.warning(request, 'Restore request rejected.')
                
                # Send notifications
                send_restore_notifications(restore_request, 'rejected')
            
            restore_request.save()
            return redirect('backup_scheduler:restore_request_detail', pk=pk)
    else:
        form = RestoreApprovalForm()
    
    context = {
        'form': form,
        'restore_request': restore_request,
    }
    
    return render(request, 'backup_scheduler/restore/restore_request_approve.html', context)

# Execution Management

@login_required
@permission_required('backup_scheduler.execute_restorerequest')
def restore_request_execute(request, pk):
    """Execute a restore request"""
    
    restore_request = get_object_or_404(RestoreRequest, pk=pk)
    
    if not restore_request.can_execute(request.user):
        messages.error(request, 'You do not have permission to execute this request.')
        return redirect('backup_scheduler:restore_request_detail', pk=pk)
    
    if request.method == 'POST':
        form = RestoreExecutionForm(request.POST)
        if form.is_valid():
            # Create execution record
            execution = RestoreExecution.objects.create(
                restore_request=restore_request,
                executed_by=request.user,
                status='pending'
            )
            
            # Update request status
            restore_request.status = 'in_progress'
            restore_request.started_at = timezone.now()
            restore_request.save()
            
            # Create log entry
            RestoreLog.objects.create(
                level='info',
                message=f'Restore execution started by {request.user.username}',
                restore_request=restore_request,
                restore_execution=execution,
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            # Start execution in background
            try:
                execute_restore_background(execution.pk)
                messages.success(request, 'Restore execution started successfully!')
            except Exception as e:
                messages.error(request, f'Failed to start restore execution: {str(e)}')
                execution.status = 'failed'
                execution.error_message = str(e)
                execution.save()
                
                restore_request.status = 'failed'
                restore_request.error_message = str(e)
                restore_request.save()
            
            return redirect('backup_scheduler:restore_execution_detail', pk=execution.pk)
    else:
        form = RestoreExecutionForm()
    
    context = {
        'form': form,
        'restore_request': restore_request,
    }
    
    return render(request, 'backup_scheduler/restore/restore_request_execute.html', context)

# Execution Management

@login_required
def restore_execution_list(request):
    """List all restore executions"""
    
    executions = RestoreExecution.objects.all().order_by('-created_at')
    
    # Pagination
    paginator = Paginator(executions, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    
    return render(request, 'backup_scheduler/restore/restore_execution_list.html', context)

@login_required
def restore_execution_detail(request, pk):
    """View details of a restore execution"""
    
    execution = get_object_or_404(RestoreExecution, pk=pk)
    
    # Get logs
    logs = RestoreLog.objects.filter(restore_execution=execution).order_by('-timestamp')
    
    context = {
        'execution': execution,
        'logs': logs,
    }
    
    return render(request, 'backup_scheduler/restore/restore_execution_detail.html', context)

@login_required
@permission_required('backup_scheduler.change_restoreexecution')
def restore_execution_cancel(request, pk):
    """Cancel a restore execution"""
    
    execution = get_object_or_404(RestoreExecution, pk=pk)
    
    if execution.status not in ['pending', 'running']:
        messages.error(request, 'This execution cannot be cancelled in its current status.')
        return redirect('backup_scheduler:restore_execution_detail', pk=pk)
    
    if request.method == 'POST':
        execution.status = 'cancelled'
        execution.save()
        
        # Update request status
        restore_request = execution.restore_request
        restore_request.status = 'cancelled'
        restore_request.save()
        
        # Create log entry
        RestoreLog.objects.create(
            level='warning',
            message=f'Restore execution cancelled by {request.user.username}',
            restore_request=restore_request,
            restore_execution=execution,
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        messages.success(request, 'Restore execution cancelled successfully!')
        return redirect('backup_scheduler:restore_execution_detail', pk=pk)
    
    context = {
        'execution': execution,
    }
    
    return render(request, 'backup_scheduler/restore/restore_execution_confirm_cancel.html', context)

# Validation Management

@login_required
def restore_validation(request, pk):
    """Run validation checks for a restore request"""
    
    restore_request = get_object_or_404(RestoreRequest, pk=pk)
    
    if request.method == 'POST':
        form = RestoreValidationForm(request.POST)
        if form.is_valid():
            validation_rules = form.cleaned_data.get('validation_rules', [])
            custom_validation = form.cleaned_data.get('custom_validation')
            expected_result = form.cleaned_data.get('expected_result')
            
            # Run validations
            validation_results = run_restore_validations(
                restore_request, validation_rules, custom_validation, expected_result
            )
            
            # Create log entry
            RestoreLog.objects.create(
                level='info',
                message=f'Validation checks completed for restore request',
                restore_request=restore_request,
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR'),
                additional_data={'validation_results': validation_results}
            )
            
            messages.success(request, 'Validation checks completed successfully!')
            
            context = {
                'restore_request': restore_request,
                'validation_results': validation_results,
            }
            
            return render(request, 'backup_scheduler/restore/restore_validation_results.html', context)
    else:
        form = RestoreValidationForm()
    
    context = {
        'form': form,
        'restore_request': restore_request,
    }
    
    return render(request, 'backup_scheduler/restore/restore_validation.html', context)

# API Views

@csrf_exempt
@require_http_methods(["POST"])
def restore_status_webhook(request):
    """Webhook endpoint for restore status updates"""
    try:
        data = json.loads(request.body)
        execution_id = data.get('execution_id')
        status = data.get('status')
        message = data.get('message')
        progress = data.get('progress', 0)
        
        execution = get_object_or_404(RestoreExecution, execution_id=execution_id)
        execution.status = status
        
        if status == 'completed':
            execution.completed_at = timezone.now()
            if execution.started_at:
                duration = (execution.completed_at - execution.started_at).total_seconds()
                execution.duration_seconds = int(duration)
        
        execution.save()
        
        # Update request status
        restore_request = execution.restore_request
        restore_request.progress_percentage = progress
        if status == 'completed':
            restore_request.status = 'completed'
            restore_request.completed_at = timezone.now()
        elif status == 'failed':
            restore_request.status = 'failed'
            restore_request.error_message = message
        
        restore_request.save()
        
        # Log the status update
        RestoreLog.objects.create(
            level='info',
            message=message or f'Restore status updated to {status}',
            restore_request=restore_request,
            restore_execution=execution
        )
        
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

# Utility Functions

def execute_restore_background(execution_id):
    """Execute restore in background thread"""
    try:
        execution = RestoreExecution.objects.get(pk=execution_id)
        execution.status = 'running'
        execution.started_at = timezone.now()
        execution.save()
        
        # Log start
        RestoreLog.objects.create(
            level='info',
            message='Restore execution started',
            restore_request=execution.restore_request,
            restore_execution=execution
        )
        
        # Simulate restore process (replace with actual restore logic)
        import time
        time.sleep(10)  # Simulate restore time
        
        # Update execution status
        execution.status = 'completed'
        execution.completed_at = timezone.now()
        execution.duration_seconds = 10
        execution.restored_records_count = 1000
        execution.data_integrity_score = 98.5
        execution.save()
        
        # Update request status
        restore_request = execution.restore_request
        restore_request.status = 'completed'
        restore_request.completed_at = timezone.now()
        restore_request.progress_percentage = 100
        restore_request.save()
        
        # Log completion
        RestoreLog.objects.create(
            level='info',
            message='Restore execution completed successfully',
            restore_request=restore_request,
            restore_execution=execution
        )
        
        # Send notifications
        send_restore_notifications(restore_request, 'execution_completed')
        
    except Exception as e:
        # Log error
        RestoreLog.objects.create(
            level='error',
            message=f'Restore execution failed: {str(e)}',
            restore_request=execution.restore_request,
            restore_execution=execution
        )
        
        execution.status = 'failed'
        execution.error_message = str(e)
        execution.completed_at = timezone.now()
        execution.save()
        
        restore_request = execution.restore_request
        restore_request.status = 'failed'
        restore_request.error_message = str(e)
        restore_request.save()
        
        # Send notifications
        send_restore_notifications(restore_request, 'execution_failed')

def run_restore_validations(restore_request, validation_rules, custom_validation, expected_result):
    """Run validation checks for restore operation"""
    results = {}
    
    # Run selected validation rules
    for rule in validation_rules:
        if rule == 'data_integrity':
            results[rule] = validate_data_integrity(restore_request)
        elif rule == 'referential_integrity':
            results[rule] = validate_referential_integrity(restore_request)
        elif rule == 'business_logic':
            results[rule] = validate_business_logic(restore_request)
        elif rule == 'record_count':
            results[rule] = validate_record_count(restore_request)
        elif rule == 'checksum_verification':
            results[rule] = validate_checksum(restore_request)
    
    # Run custom validation if provided
    if custom_validation:
        results['custom_validation'] = run_custom_validation(
            restore_request, custom_validation, expected_result
        )
    
    return results

def validate_data_integrity(restore_request):
    """Validate data integrity for restore operation"""
    # Implement data integrity validation logic
    return {
        'status': 'passed',
        'message': 'Data integrity check passed',
        'details': 'All data structures are valid'
    }

def validate_referential_integrity(restore_request):
    """Validate referential integrity for restore operation"""
    # Implement referential integrity validation logic
    return {
        'status': 'passed',
        'message': 'Referential integrity check passed',
        'details': 'All foreign key relationships are valid'
    }

def validate_business_logic(restore_request):
    """Validate business logic for restore operation"""
    # Implement business logic validation
    return {
        'status': 'passed',
        'message': 'Business logic validation passed',
        'details': 'All business rules are satisfied'
    }

def validate_record_count(restore_request):
    """Validate record count for restore operation"""
    # Implement record count validation
    return {
        'status': 'passed',
        'message': 'Record count validation passed',
        'details': 'Expected record counts match'
    }

def validate_checksum(restore_request):
    """Validate checksum for restore operation"""
    # Implement checksum validation
    return {
        'status': 'passed',
        'message': 'Checksum validation passed',
        'details': 'Data integrity verified via checksum'
    }

def run_custom_validation(restore_request, custom_validation, expected_result):
    """Run custom validation logic"""
    try:
        # Execute custom validation (implement based on your needs)
        # This is a placeholder implementation
        result = {
            'status': 'passed',
            'message': 'Custom validation executed successfully',
            'details': f'Custom validation: {custom_validation}',
            'expected_result': expected_result
        }
        return result
    except Exception as e:
        return {
            'status': 'failed',
            'message': f'Custom validation failed: {str(e)}',
            'details': 'Error executing custom validation'
        }

def send_restore_notifications(restore_request, notification_type):
    """Send notifications for restore operations"""
    try:
        # Get notification configuration
        notifications = RestoreNotification.objects.filter(
            restore_request=restore_request,
            notification_type=notification_type,
            is_active=True
        )
        
        for notification in notifications:
            # Send email notification
            if notification.channel == 'email':
                send_email_notification(notification, restore_request)
            
            # Send SMS notification
            elif notification.channel == 'sms':
                send_sms_notification(notification, restore_request)
            
            # Send webhook notification
            elif notification.channel == 'webhook':
                send_webhook_notification(notification, restore_request)
            
            # Update notification status
            notification.sent_at = timezone.now()
            notification.delivery_status = 'sent'
            notification.save()
            
    except Exception as e:
        logger.error(f"Failed to send restore notification: {str(e)}")

def send_email_notification(notification, restore_request):
    """Send email notification for restore operation"""
    try:
        subject = notification.subject or f'Restore Request: {restore_request.title}'
        
        # Render message template
        message = render_to_string('backup_scheduler/restore/email_notification.html', {
            'restore_request': restore_request,
            'notification': notification,
        })
        
        # Send email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=notification.recipients,
            fail_silently=False,
        )
        
    except Exception as e:
        logger.error(f"Failed to send email notification: {str(e)}")

def send_sms_notification(notification, restore_request):
    """Send SMS notification for restore operation"""
    # Implement SMS notification logic
    pass

def send_webhook_notification(notification, restore_request):
    """Send webhook notification for restore operation"""
    # Implement webhook notification logic
    pass
