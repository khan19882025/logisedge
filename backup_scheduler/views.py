from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
import json
import os
import subprocess
import threading
import time
from datetime import datetime, timedelta

from .models import (
    BackupType, BackupScope, StorageLocation, BackupSchedule, 
    BackupExecution, BackupRetentionPolicy, BackupAlert,
    DisasterRecoveryPlan, BackupLog
)
from .forms import (
    BackupTypeForm, BackupScopeForm, StorageLocationForm, BackupScheduleForm,
    ManualBackupForm, BackupRetentionPolicyForm, BackupAlertForm,
    DisasterRecoveryPlanForm, BackupFilterForm, BackupScheduleFilterForm
)

@login_required
def dashboard(request):
    """Main dashboard for backup management"""
    # Get recent backup executions
    recent_executions = BackupExecution.objects.all()[:10]
    
    # Get backup statistics
    total_schedules = BackupSchedule.objects.filter(is_active=True).count()
    total_executions = BackupExecution.objects.count()
    successful_executions = BackupExecution.objects.filter(status='completed').count()
    failed_executions = BackupExecution.objects.filter(status='failed').count()
    
    # Get storage usage
    storage_locations = StorageLocation.objects.filter(is_active=True)
    total_storage_gb = sum(loc.max_capacity_gb for loc in storage_locations)
    used_storage_gb = sum(loc.used_capacity_gb for loc in storage_locations)
    storage_percentage = (used_storage_gb / total_storage_gb * 100) if total_storage_gb > 0 else 0
    
    # Get upcoming schedules
    upcoming_schedules = BackupSchedule.objects.filter(is_active=True).order_by('start_date', 'start_time')[:5]
    
    # Get recent logs
    recent_logs = BackupLog.objects.all()[:20]
    
    context = {
        'recent_executions': recent_executions,
        'total_schedules': total_schedules,
        'total_executions': total_executions,
        'successful_executions': successful_executions,
        'failed_executions': failed_executions,
        'storage_percentage': round(storage_percentage, 2),
        'used_storage_gb': used_storage_gb,
        'total_storage_gb': total_storage_gb,
        'upcoming_schedules': upcoming_schedules,
        'recent_logs': recent_logs,
    }
    
    return render(request, 'backup_scheduler/dashboard.html', context)

@login_required
@permission_required('backup_scheduler.add_backupschedule')
def schedule_list(request):
    """List all backup schedules"""
    schedules = BackupSchedule.objects.all().order_by('-created_at')
    
    # Apply filters
    filter_form = BackupScheduleFilterForm(request.GET)
    if filter_form.is_valid():
        if filter_form.cleaned_data['frequency']:
            schedules = schedules.filter(frequency=filter_form.cleaned_data['frequency'])
        if filter_form.cleaned_data['is_active']:
            is_active = filter_form.cleaned_data['is_active'] == 'True'
            schedules = schedules.filter(is_active=is_active)
        if filter_form.cleaned_data['storage_location']:
            schedules = schedules.filter(storage_location=filter_form.cleaned_data['storage_location'])
    
    # Pagination
    paginator = Paginator(schedules, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
    }
    
    return render(request, 'backup_scheduler/schedule_list.html', context)

@login_required
@permission_required('backup_scheduler.add_backupschedule')
def schedule_create(request):
    """Create a new backup schedule"""
    if request.method == 'POST':
        form = BackupScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.created_by = request.user
            schedule.save()
            
            # Log the action
            BackupLog.objects.create(
                level='info',
                message=f'Backup schedule "{schedule.name}" created by {request.user.username}',
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, 'Backup schedule created successfully!')
            return redirect('backup_scheduler:schedule_list')
    else:
        form = BackupScheduleForm()
    
    context = {
        'form': form,
        'title': 'Create Backup Schedule',
    }
    
    return render(request, 'backup_scheduler/schedule_form.html', context)

@login_required
@permission_required('backup_scheduler.change_backupschedule')
def schedule_edit(request, pk):
    """Edit an existing backup schedule"""
    schedule = get_object_or_404(BackupSchedule, pk=pk)
    
    if request.method == 'POST':
        form = BackupScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            
            # Log the action
            BackupLog.objects.create(
                level='info',
                message=f'Backup schedule "{schedule.name}" updated by {request.user.username}',
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, 'Backup schedule updated successfully!')
            return redirect('backup_scheduler:schedule_list')
    else:
        form = BackupScheduleForm(instance=schedule)
    
    context = {
        'form': form,
        'schedule': schedule,
        'title': 'Edit Backup Schedule',
    }
    
    return render(request, 'backup_scheduler/schedule_form.html', context)

@login_required
@permission_required('backup_scheduler.delete_backupschedule')
def schedule_delete(request, pk):
    """Delete a backup schedule"""
    schedule = get_object_or_404(BackupSchedule, pk=pk)
    
    if request.method == 'POST':
        schedule_name = schedule.name
        schedule.delete()
        
        # Log the action
        BackupLog.objects.create(
            level='info',
            message=f'Backup schedule "{schedule_name}" deleted by {request.user.username}',
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        messages.success(request, 'Backup schedule deleted successfully!')
        return redirect('backup_scheduler:schedule_list')
    
    context = {
        'schedule': schedule,
    }
    
    return render(request, 'backup_scheduler/schedule_confirm_delete.html', context)

@login_required
@permission_required('backup_scheduler.add_backupexecution')
def manual_backup(request):
    """Trigger a manual backup"""
    if request.method == 'POST':
        form = ManualBackupForm(request.POST)
        if form.is_valid():
            execution = form.save(commit=False)
            execution.triggered_by = request.user
            execution.is_manual = True
            execution.status = 'pending'
            execution.save()
            
            # Start backup in background thread
            thread = threading.Thread(target=execute_backup, args=(execution.pk,))
            thread.daemon = True
            thread.start()
            
            # Log the action
            BackupLog.objects.create(
                level='info',
                message=f'Manual backup triggered by {request.user.username}',
                execution=execution,
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, 'Manual backup started successfully!')
            return redirect('backup_scheduler:execution_list')
    else:
        form = ManualBackupForm()
    
    context = {
        'form': form,
        'title': 'Manual Backup',
    }
    
    return render(request, 'backup_scheduler/manual_backup.html', context)

@login_required
def execution_list(request):
    """List all backup executions"""
    executions = BackupExecution.objects.all().order_by('-created_at')
    
    # Apply filters
    filter_form = BackupFilterForm(request.GET)
    if filter_form.is_valid():
        if filter_form.cleaned_data['status']:
            executions = executions.filter(status=filter_form.cleaned_data['status'])
        if filter_form.cleaned_data['backup_type']:
            executions = executions.filter(backup_type=filter_form.cleaned_data['backup_type'])
        if filter_form.cleaned_data['backup_scope']:
            executions = executions.filter(backup_scope=filter_form.cleaned_data['backup_scope'])
        if filter_form.cleaned_data['date_from']:
            executions = executions.filter(created_at__date__gte=filter_form.cleaned_data['date_from'])
        if filter_form.cleaned_data['date_to']:
            executions = executions.filter(created_at__date__lte=filter_form.cleaned_data['date_to'])
        if filter_form.cleaned_data['is_manual']:
            is_manual = filter_form.cleaned_data['is_manual'] == 'True'
            executions = executions.filter(is_manual=is_manual)
    
    # Pagination
    paginator = Paginator(executions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
    }
    
    return render(request, 'backup_scheduler/execution_list.html', context)

@login_required
def execution_detail(request, pk):
    """View details of a backup execution"""
    execution = get_object_or_404(BackupExecution, pk=pk)
    
    # Get related logs
    logs = BackupLog.objects.filter(execution=execution).order_by('-timestamp')
    
    context = {
        'execution': execution,
        'logs': logs,
    }
    
    return render(request, 'backup_scheduler/execution_detail.html', context)

@login_required
@permission_required('backup_scheduler.change_backupexecution')
def execution_cancel(request, pk):
    """Cancel a running backup execution"""
    execution = get_object_or_404(BackupExecution, pk=pk)
    
    if execution.status == 'running':
        execution.status = 'cancelled'
        execution.completed_at = timezone.now()
        execution.save()
        
        # Log the action
        BackupLog.objects.create(
            level='info',
            message=f'Backup execution cancelled by {request.user.username}',
            execution=execution,
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        messages.success(request, 'Backup execution cancelled successfully!')
    else:
        messages.error(request, 'Only running backups can be cancelled!')
    
    return redirect('backup_scheduler:execution_detail', pk=pk)

@login_required
@permission_required('backup_scheduler.add_backuptype')
def backup_type_list(request):
    """List all backup types"""
    backup_types = BackupType.objects.all().order_by('name')
    
    context = {
        'backup_types': backup_types,
    }
    
    return render(request, 'backup_scheduler/backup_type_list.html', context)

@login_required
@permission_required('backup_scheduler.add_backupscope')
def backup_scope_list(request):
    """List all backup scopes"""
    backup_scopes = BackupScope.objects.all().order_by('name')
    
    context = {
        'backup_scopes': backup_scopes,
    }
    
    return render(request, 'backup_scheduler/backup_scope_list.html', context)

@login_required
@permission_required('backup_scheduler.add_storagelocation')
def storage_location_list(request):
    """List all storage locations"""
    storage_locations = StorageLocation.objects.all().order_by('name')
    
    context = {
        'storage_locations': storage_locations,
    }
    
    return render(request, 'backup_scheduler/storage_location_list.html', context)

@login_required
@permission_required('backup_scheduler.add_backupretentionpolicy')
def retention_policy_list(request):
    """List all retention policies"""
    retention_policies = BackupRetentionPolicy.objects.all().order_by('name')
    
    context = {
        'retention_policies': retention_policies,
    }
    
    return render(request, 'backup_scheduler/retention_policy_list.html', context)

@login_required
@permission_required('backup_scheduler.add_backupalert')
def alert_list(request):
    """List all backup alerts"""
    alerts = BackupAlert.objects.all().order_by('name')
    
    context = {
        'alerts': alerts,
    }
    
    return render(request, 'backup_scheduler/alert_list.html', context)

@login_required
@permission_required('backup_scheduler.add_disasterrecoveryplan')
def disaster_recovery_list(request):
    """List all disaster recovery plans"""
    recovery_plans = DisasterRecoveryPlan.objects.all().order_by('name')
    
    context = {
        'recovery_plans': recovery_plans,
    }
    
    return render(request, 'backup_scheduler/disaster_recovery_list.html', context)

@login_required
def logs_list(request):
    """List all backup logs"""
    logs = BackupLog.objects.all().order_by('-timestamp')
    
    # Pagination
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    
    return render(request, 'backup_scheduler/logs_list.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def backup_status_webhook(request):
    """Webhook endpoint for backup status updates"""
    try:
        data = json.loads(request.body)
        execution_id = data.get('execution_id')
        status = data.get('status')
        message = data.get('message')
        
        execution = get_object_or_404(BackupExecution, execution_id=execution_id)
        execution.status = status
        
        if status == 'completed':
            execution.completed_at = timezone.now()
            if execution.started_at:
                duration = (execution.completed_at - execution.started_at).total_seconds()
                execution.duration_seconds = int(duration)
        
        execution.save()
        
        # Log the status update
        BackupLog.objects.create(
            level='info',
            message=message or f'Backup status updated to {status}',
            execution=execution
        )
        
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

def execute_backup(execution_id):
    """Execute a backup in a background thread"""
    try:
        execution = BackupExecution.objects.get(pk=execution_id)
        execution.status = 'running'
        execution.started_at = timezone.now()
        execution.save()
        
        # Log start
        BackupLog.objects.create(
            level='info',
            message='Backup execution started',
            execution=execution
        )
        
        # Simulate backup process (replace with actual backup logic)
        time.sleep(5)  # Simulate backup time
        
        # Update execution status
        execution.status = 'completed'
        execution.completed_at = timezone.now()
        execution.duration_seconds = 5
        execution.file_path = f'/backups/backup_{execution.execution_id}.sql'
        execution.file_size_mb = 10.5
        execution.checksum = 'abc123def456'
        execution.save()
        
        # Log completion
        BackupLog.objects.create(
            level='info',
            message='Backup execution completed successfully',
            execution=execution
        )
        
    except Exception as e:
        # Log error
        BackupLog.objects.create(
            level='error',
            message=f'Backup execution failed: {str(e)}',
            execution=execution
        )
        
        execution.status = 'failed'
        execution.error_message = str(e)
        execution.completed_at = timezone.now()
        execution.save()

@login_required
def api_backup_status(request):
    """API endpoint for backup status"""
    executions = BackupExecution.objects.all()[:10]
    
    data = []
    for execution in executions:
        data.append({
            'id': execution.execution_id,
            'status': execution.status,
            'backup_type': execution.backup_type.name,
            'backup_scope': execution.backup_scope.name,
            'started_at': execution.started_at.isoformat() if execution.started_at else None,
            'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
            'duration_seconds': execution.duration_seconds,
            'is_manual': execution.is_manual,
        })
    
    return JsonResponse({'executions': data})

@login_required
def api_storage_usage(request):
    """API endpoint for storage usage statistics"""
    storage_locations = StorageLocation.objects.filter(is_active=True)
    
    data = []
    total_used = 0
    total_capacity = 0
    
    for location in storage_locations:
        total_used += location.used_capacity_gb
        total_capacity += location.max_capacity_gb
        
        data.append({
            'name': location.name,
            'type': location.storage_type,
            'used_gb': location.used_capacity_gb,
            'capacity_gb': location.max_capacity_gb,
            'usage_percentage': round((location.used_capacity_gb / location.max_capacity_gb) * 100, 2) if location.max_capacity_gb > 0 else 0,
        })
    
    return JsonResponse({
        'locations': data,
        'total_used_gb': total_used,
        'total_capacity_gb': total_capacity,
        'overall_usage_percentage': round((total_used / total_capacity) * 100, 2) if total_capacity > 0 else 0,
    })
