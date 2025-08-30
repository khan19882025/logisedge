from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.conf import settings
import json
import logging

from .models import (
    BackupConfiguration, BackupSession, BackupStep, 
    BackupAuditLog, BackupStorageLocation, BackupRetentionPolicy
)
from .forms import (
    BackupConfigurationForm, BackupSessionForm, BackupSessionUpdateForm,
    BackupStepForm, BackupAuditLogForm, BackupStorageLocationForm,
    BackupRetentionPolicyForm, BackupSearchForm
)

logger = logging.getLogger(__name__)


@login_required
def dashboard(request):
    """Main dashboard view for the manual backup system"""
    
    # Get recent backup statistics
    recent_backups = BackupSession.objects.filter(
        status='completed'
    ).order_by('-completed_at')[:5]
    
    # Get backup statistics
    total_backups = BackupSession.objects.count()
    successful_backups = BackupSession.objects.filter(status='completed').count()
    failed_backups = BackupSession.objects.filter(status='failed').count()
    in_progress_backups = BackupSession.objects.filter(status='in_progress').count()
    
    # Get storage usage
    total_storage_used = BackupSession.objects.filter(
        status='completed'
    ).aggregate(
        total=Sum('file_size_bytes')
    )['total'] or 0
    
    # Get last successful backup
    last_backup = BackupSession.objects.filter(
        status='completed'
    ).order_by('-completed_at').first()
    
    # Get backup configurations
    backup_configs = BackupConfiguration.objects.filter(is_active=True)[:5]
    
    # Get storage locations
    storage_locations = BackupStorageLocation.objects.filter(is_active=True)
    
    context = {
        'recent_backups': recent_backups,
        'total_backups': total_backups,
        'successful_backups': successful_backups,
        'failed_backups': failed_backups,
        'in_progress_backups': in_progress_backups,
        'total_storage_used': total_storage_used,
        'last_backup': last_backup,
        'backup_configs': backup_configs,
        'storage_locations': storage_locations,
    }
    
    return render(request, 'manual_backup/dashboard.html', context)


@login_required
def backup_history(request):
    """View for displaying backup history with filtering and search"""
    
    search_form = BackupSearchForm(request.GET)
    backups = BackupSession.objects.all()
    
    if search_form.is_valid():
        cleaned_data = search_form.cleaned_data
        
        # Apply search filters
        if cleaned_data.get('search_query'):
            query = cleaned_data['search_query']
            search_field = cleaned_data.get('search_field', 'name')
            
            if search_field == 'name':
                backups = backups.filter(name__icontains=query)
            elif search_field == 'reason':
                backups = backups.filter(reason__icontains=query)
            elif search_field == 'description':
                backups = backups.filter(description__icontains=query)
            elif search_field == 'created_by':
                backups = backups.filter(created_by__username__icontains=query)
        
        # Apply status filter
        if cleaned_data.get('status'):
            backups = backups.filter(status=cleaned_data['status'])
        
        # Apply reason filter
        if cleaned_data.get('reason'):
            backups = backups.filter(reason=cleaned_data['reason'])
        
        # Apply priority filter
        if cleaned_data.get('priority'):
            backups = backups.filter(priority=cleaned_data['priority'])
        
        # Apply date filters
        if cleaned_data.get('date_from'):
            backups = backups.filter(created_at__gte=cleaned_data['date_from'])
        
        if cleaned_data.get('date_to'):
            backups = backups.filter(created_at__lte=cleaned_data['date_to'])
        
        # Apply user filter
        if cleaned_data.get('created_by'):
            backups = backups.filter(created_by=cleaned_data['created_by'])
    
    # Pagination
    paginator = Paginator(backups, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'search_form': search_form,
        'page_obj': page_obj,
        'total_backups': backups.count(),
    }
    
    return render(request, 'manual_backup/backup_history.html', context)


@login_required
def backup_detail(request, backup_id):
    """Detailed view of a specific backup session"""
    
    backup = get_object_or_404(BackupSession, backup_id=backup_id)
    backup_steps = backup.steps.all().order_by('order')
    audit_logs = backup.audit_logs.all().order_by('-timestamp')
    
    context = {
        'backup': backup,
        'backup_steps': backup_steps,
        'audit_logs': audit_logs,
    }
    
    return render(request, 'manual_backup/backup_detail.html', context)


@login_required
def initiate_backup(request):
    """View for initiating a new backup session"""
    
    if request.method == 'POST':
        form = BackupSessionForm(request.POST)
        if form.is_valid():
            try:
                # Create backup session
                backup_session = form.save(commit=False)
                backup_session.created_by = request.user
                backup_session.status = 'pending'
                backup_session.save()
                
                # Log the backup initiation
                BackupAuditLog.objects.create(
                    backup_session=backup_session,
                    level='info',
                    message=f'Backup session initiated by {request.user.username}',
                    details={
                        'reason': backup_session.reason,
                        'priority': backup_session.priority,
                        'user_ip': request.META.get('REMOTE_ADDR'),
                        'user_agent': request.META.get('HTTP_USER_AGENT', '')
                    },
                    user=request.user,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                messages.success(request, 'Backup session initiated successfully.')
                return redirect('manual_backup:backup_detail', backup_id=backup_session.backup_id)
                
            except Exception as e:
                logger.error(f"Error initiating backup: {str(e)}")
                messages.error(request, f'Error initiating backup: {str(e)}')
    else:
        form = BackupSessionForm()
    
    # Get available configurations
    configurations = BackupConfiguration.objects.filter(is_active=True)
    
    context = {
        'form': form,
        'configurations': configurations,
    }
    
    return render(request, 'manual_backup/initiate_backup.html', context)


@login_required
def backup_configurations(request):
    """View for managing backup configurations"""
    
    configurations = BackupConfiguration.objects.all().order_by('-created_at')
    
    context = {
        'configurations': configurations,
    }
    
    return render(request, 'manual_backup/backup_configurations.html', context)


@login_required
def create_configuration(request):
    """View for creating a new backup configuration"""
    
    if request.method == 'POST':
        form = BackupConfigurationForm(request.POST)
        if form.is_valid():
            configuration = form.save()
            messages.success(request, 'Backup configuration created successfully.')
            return redirect('manual_backup:backup_configurations')
    else:
        form = BackupConfigurationForm()
    
    context = {
        'form': form,
        'action': 'Create',
    }
    
    return render(request, 'manual_backup/configuration_form.html', context)


@login_required
def edit_configuration(request, config_id):
    """View for editing an existing backup configuration"""
    
    configuration = get_object_or_404(BackupConfiguration, id=config_id)
    
    if request.method == 'POST':
        form = BackupConfigurationForm(request.POST, instance=configuration)
        if form.is_valid():
            form.save()
            messages.success(request, 'Backup configuration updated successfully.')
            return redirect('manual_backup:backup_configurations')
    else:
        form = BackupConfigurationForm(instance=configuration)
    
    context = {
        'form': form,
        'configuration': configuration,
        'action': 'Edit',
    }
    
    return render(request, 'manual_backup/configuration_form.html', context)


@login_required
def storage_locations(request):
    """View for managing backup storage locations"""
    
    locations = BackupStorageLocation.objects.all().order_by('-created_at')
    
    context = {
        'locations': locations,
    }
    
    return render(request, 'manual_backup/storage_locations.html', context)


@login_required
def create_storage_location(request):
    """View for creating a new storage location"""
    
    if request.method == 'POST':
        form = BackupStorageLocationForm(request.POST)
        if form.is_valid():
            location = form.save()
            messages.success(request, 'Storage location created successfully.')
            return redirect('manual_backup:storage_locations')
    else:
        form = BackupStorageLocationForm()
    
    context = {
        'form': form,
        'action': 'Create',
    }
    
    return render(request, 'manual_backup/storage_location_form.html', context)


@login_required
def edit_storage_location(request, location_id):
    """View for editing an existing storage location"""
    
    location = get_object_or_404(BackupStorageLocation, id=location_id)
    
    if request.method == 'POST':
        form = BackupStorageLocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
            messages.success(request, 'Storage location updated successfully.')
            return redirect('manual_backup:storage_locations')
    else:
        form = BackupStorageLocationForm(instance=location)
    
    context = {
        'form': form,
        'location': location,
        'action': 'Edit',
    }
    
    return render(request, 'manual_backup/storage_location_form.html', context)


@login_required
def audit_log(request):
    """View for displaying the backup audit log"""
    
    # Get audit logs with optional filtering
    level_filter = request.GET.get('level', '')
    user_filter = request.GET.get('user', '')
    
    audit_logs = BackupAuditLog.objects.all()
    
    if level_filter:
        audit_logs = audit_logs.filter(level=level_filter)
    
    if user_filter:
        audit_logs = audit_logs.filter(user__username__icontains=user_filter)
    
    # Pagination
    paginator = Paginator(audit_logs.order_by('-timestamp'), 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'level_filter': level_filter,
        'user_filter': user_filter,
        'log_levels': BackupAuditLog.LOG_LEVELS,
    }
    
    return render(request, 'manual_backup/audit_log.html', context)


@login_required
def restore_options(request):
    """View for displaying restore options and available backups"""
    
    # Get completed backups that can be restored
    restorable_backups = BackupSession.objects.filter(
        status='completed',
        integrity_verified=True
    ).order_by('-completed_at')
    
    context = {
        'restorable_backups': restorable_backups,
    }
    
    return render(request, 'manual_backup/restore_options.html', context)


# API Views for AJAX requests

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def start_backup_api(request):
    """API endpoint for starting a backup process"""
    
    try:
        data = json.loads(request.body)
        backup_id = data.get('backup_id')
        
        backup = get_object_or_404(BackupSession, backup_id=backup_id)
        
        # Update backup status
        backup.status = 'in_progress'
        backup.started_at = timezone.now()
        backup.save()
        
        # Create backup steps
        steps_data = [
            ('preparation', 'Preparing backup environment', 1),
            ('database_backup', 'Backing up databases', 2),
            ('file_backup', 'Backing up files', 3),
            ('checksum_generation', 'Generating checksums', 4),
            ('encryption', 'Encrypting backup', 5),
            ('storage', 'Storing backup', 6),
            ('verification', 'Verifying integrity', 7),
        ]
        
        for step_type, step_name, order in steps_data:
            BackupStep.objects.create(
                backup_session=backup,
                step_type=step_type,
                step_name=step_name,
                order=order
            )
        
        # Log the backup start
        BackupAuditLog.objects.create(
            backup_session=backup,
            level='info',
            message='Backup process started',
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Backup started successfully',
            'backup_id': str(backup.backup_id)
        })
        
    except Exception as e:
        logger.error(f"Error starting backup: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def backup_progress_api(request, backup_id):
    """API endpoint for getting backup progress"""
    
    try:
        backup = get_object_or_404(BackupSession, backup_id=backup_id)
        steps = backup.steps.all().order_by('order')
        
        progress_data = {
            'backup_id': str(backup.backup_id),
            'status': backup.status,
            'progress_percentage': backup.progress_percentage,
            'current_step': backup.current_step,
            'steps': []
        }
        
        for step in steps:
            step_data = {
                'id': step.id,
                'type': step.step_type,
                'name': step.step_name,
                'status': step.status,
                'order': step.order,
                'progress': step.progress_percentage,
                'details': step.details,
                'error_message': step.error_message,
            }
            progress_data['steps'].append(step_data)
        
        return JsonResponse(progress_data)
        
    except Exception as e:
        logger.error(f"Error getting backup progress: {str(e)}")
        return JsonResponse({
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def update_step_progress_api(request, backup_id, step_id):
    """API endpoint for updating step progress"""
    
    try:
        data = json.loads(request.body)
        step = get_object_or_404(BackupStep, id=step_id, backup_session__backup_id=backup_id)
        
        # Update step status and progress
        if 'status' in data:
            step.status = data['status']
        
        if 'progress_percentage' in data:
            step.progress_percentage = data['progress_percentage']
        
        if 'details' in data:
            step.details = data['details']
        
        if 'error_message' in data:
            step.error_message = data['error_message']
        
        # Update timing
        if data.get('status') == 'in_progress' and not step.started_at:
            step.started_at = timezone.now()
        elif data.get('status') == 'completed' and not step.completed_at:
            step.completed_at = timezone.now()
            if step.started_at:
                step.duration_seconds = int((step.completed_at - step.started_at).total_seconds())
        
        step.save()
        
        # Update overall backup progress
        backup = step.backup_session
        completed_steps = backup.steps.filter(status='completed').count()
        total_steps = backup.steps.count()
        
        if total_steps > 0:
            backup.progress_percentage = int((completed_steps / total_steps) * 100)
            backup.current_step = step.step_name
            backup.save()
        
        return JsonResponse({
            'success': True,
            'step_progress': step.progress_percentage,
            'overall_progress': backup.progress_percentage
        })
        
    except Exception as e:
        logger.error(f"Error updating step progress: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def complete_backup_api(request, backup_id):
    """API endpoint for completing a backup process"""
    
    try:
        data = json.loads(request.body)
        backup = get_object_or_404(BackupSession, backup_id=backup_id)
        
        # Update backup status
        backup.status = 'completed'
        backup.completed_at = timezone.now()
        if backup.started_at:
            backup.duration_seconds = int((backup.completed_at - backup.started_at).total_seconds())
        
        # Update file information if provided
        if 'file_size_bytes' in data:
            backup.file_size_bytes = data['file_size_bytes']
        
        if 'file_path' in data:
            backup.file_path = data['file_path']
        
        if 'checksum_sha256' in data:
            backup.checksum_sha256 = data['checksum_sha256']
        
        if 'primary_storage_path' in data:
            backup.primary_storage_path = data['primary_storage_path']
        
        if 'secondary_storage_path' in data:
            backup.secondary_storage_path = data['secondary_storage_path']
        
        backup.save()
        
        # Log the backup completion
        BackupAuditLog.objects.create(
            backup_session=backup,
            level='info',
            message='Backup completed successfully',
            details={
                'file_size': backup.file_size_bytes,
                'file_path': backup.file_path,
                'checksum': backup.checksum_sha256,
                'duration': backup.duration_seconds
            },
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Backup completed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error completing backup: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def dashboard_stats_api(request):
    """API endpoint for getting dashboard statistics"""
    
    try:
        # Get backup statistics
        total_backups = BackupSession.objects.count()
        successful_backups = BackupSession.objects.filter(status='completed').count()
        failed_backups = BackupSession.objects.filter(status='failed').count()
        in_progress_backups = BackupSession.objects.filter(status='in_progress').count()
        
        # Get storage usage
        total_storage_used = BackupSession.objects.filter(
            status='completed'
        ).aggregate(
            total=Sum('file_size_bytes')
        )['total'] or 0
        
        # Get last backup
        last_backup = BackupSession.objects.filter(
            status='completed'
        ).order_by('-completed_at').first()
        
        stats = {
            'total_backups': total_backups,
            'successful_backups': successful_backups,
            'failed_backups': failed_backups,
            'in_progress_backups': in_progress_backups,
            'total_storage_used': total_storage_used,
            'last_backup': {
                'name': last_backup.name if last_backup else None,
                'completed_at': last_backup.completed_at.isoformat() if last_backup else None,
                'file_size': last_backup.file_size_formatted if last_backup else None,
            } if last_backup else None
        }
        
        return JsonResponse(stats)
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {str(e)}")
        return JsonResponse({
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def test_configuration_api(request, config_id):
    """API endpoint for testing a backup configuration"""
    
    try:
        config = get_object_or_404(BackupConfiguration, id=config_id)
        
        # Create a test backup session
        test_backup = BackupSession.objects.create(
            name=f"Test Backup - {config.name}",
            reason='manual',
            description=f"Test backup using configuration: {config.name}",
            priority='low',
            configuration=config,
            created_by=request.user
        )
        
        # Log the test backup creation
        BackupAuditLog.objects.create(
            backup_session=test_backup,
            level='info',
            message=f'Test backup created for configuration: {config.name}',
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Test backup created successfully',
            'redirect_url': f'/utilities/manual-backup/detail/{test_backup.backup_id}/'
        })
        
    except Exception as e:
        logger.error(f"Error creating test backup: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def activate_configuration_api(request, config_id):
    """API endpoint for activating a backup configuration"""
    
    try:
        config = get_object_or_404(BackupConfiguration, id=config_id)
        
        # Deactivate all other configurations of the same type
        BackupConfiguration.objects.filter(
            backup_type=config.backup_type
        ).update(is_active=False)
        
        # Activate this configuration
        config.is_active = True
        config.save()
        
        # Log the activation
        BackupAuditLog.objects.create(
            level='info',
            message=f'Configuration activated: {config.name}',
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Configuration activated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error activating configuration: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def deactivate_configuration_api(request, config_id):
    """API endpoint for deactivating a backup configuration"""
    
    try:
        config = get_object_or_404(BackupConfiguration, id=config_id)
        
        config.is_active = False
        config.save()
        
        # Log the deactivation
        BackupAuditLog.objects.create(
            level='info',
            message=f'Configuration deactivated: {config.name}',
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Configuration deactivated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deactivating configuration: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def restore_details_api(request, backup_id):
    """API endpoint for getting backup details for restore confirmation"""
    
    try:
        backup = get_object_or_404(BackupSession, backup_id=backup_id)
        
        # Check if backup is restorable
        if backup.status != 'completed' or not backup.integrity_verified:
            return JsonResponse({
                'success': False,
                'error': 'Backup is not available for restoration'
            }, status=400)
        
        backup_data = {
            'name': backup.name,
            'reason': backup.get_reason_display(),
            'file_size': backup.file_size_formatted,
            'created_at': backup.created_at.strftime('%B %d, %Y at %H:%M'),
            'description': backup.description or 'No description provided'
        }
        
        return JsonResponse({
            'success': True,
            'backup': backup_data
        })
        
    except Exception as e:
        logger.error(f"Error getting restore details: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def start_restore_api(request, backup_id):
    """API endpoint for starting a restore process"""
    
    try:
        backup = get_object_or_404(BackupSession, backup_id=backup_id)
        
        # Check if backup is restorable
        if backup.status != 'completed' or not backup.integrity_verified:
            return JsonResponse({
                'success': False,
                'error': 'Backup is not available for restoration'
            }, status=400)
        
        # Create a restore session
        restore_session = BackupSession.objects.create(
            name=f"Restore from {backup.name}",
            reason='emergency',
            description=f"Restore operation from backup: {backup.name}",
            priority='critical',
            created_by=request.user
        )
        
        # Log the restore start
        BackupAuditLog.objects.create(
            backup_session=restore_session,
            level='info',
            message=f'Restore process started from backup: {backup.name}',
            details={
                'source_backup_id': str(backup.backup_id),
                'source_backup_name': backup.name,
                'restore_type': 'full_system'
            },
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Restore process started successfully',
            'redirect_url': f'/utilities/manual-backup/detail/{restore_session.backup_id}/'
        })
        
    except Exception as e:
        logger.error(f"Error starting restore: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
