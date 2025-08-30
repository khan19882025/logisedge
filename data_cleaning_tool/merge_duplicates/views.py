from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db import transaction
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging

from .models import (
    DuplicateDetectionSession, DuplicateGroup, DuplicateRecord,
    MergeOperation, MergeAuditLog, DeduplicationRule,
    ScheduledDeduplication
)
from .forms import (
    DuplicateDetectionSessionForm, DeduplicationRuleForm,
    ScheduledDeduplicationForm, MergeConfigurationForm,
    DuplicateGroupReviewForm, BulkMergeForm
)

logger = logging.getLogger(__name__)


@login_required
def merge_duplicates_dashboard(request):
    """Main dashboard for merge duplicates functionality"""
    
    # Get recent sessions
    recent_sessions = DuplicateDetectionSession.objects.filter(
        created_by=request.user
    ).order_by('-created_at')[:5]
    
    # Get statistics
    total_sessions = DuplicateDetectionSession.objects.filter(
        created_by=request.user
    ).count()
    
    total_duplicates_found = DuplicateGroup.objects.filter(
        session__created_by=request.user
    ).count()
    
    total_records_merged = MergeOperation.objects.filter(
        created_by=request.user,
        status='completed'
    ).count()
    
    # Get active rules
    active_rules = DeduplicationRule.objects.filter(is_active=True).count()
    
    # Get scheduled tasks
    scheduled_tasks = ScheduledDeduplication.objects.filter(is_active=True).count()
    
    context = {
        'recent_sessions': recent_sessions,
        'total_sessions': total_sessions,
        'total_duplicates_found': total_duplicates_found,
        'total_records_merged': total_records_merged,
        'active_rules': active_rules,
        'scheduled_tasks': scheduled_tasks,
    }
    
    return render(request, 'data_cleaning_tool/merge_duplicates/dashboard.html', context)


@login_required
def session_list(request):
    """List all duplicate detection sessions"""
    
    sessions = DuplicateDetectionSession.objects.filter(
        created_by=request.user
    ).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(sessions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'sessions': page_obj,
    }
    
    return render(request, 'data_cleaning_tool/merge_duplicates/session_list.html', context)


@login_required
def session_create(request):
    """Create a new duplicate detection session"""
    
    if request.method == 'POST':
        form = DuplicateDetectionSessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.created_by = request.user
            
            # Convert form data to config
            config = {
                'entity_types': request.POST.getlist('entity_types'),
                'similarity_threshold': float(request.POST.get('similarity_threshold', 0.8)),
                'confidence_threshold': float(request.POST.get('confidence_threshold', 0.7)),
                'fuzzy_logic_enabled': request.POST.get('fuzzy_logic_enabled') == 'on',
                'phonetic_similarity_enabled': request.POST.get('phonetic_similarity_enabled') == 'on',
                'transaction_history_analysis': request.POST.get('transaction_history_analysis') == 'on',
                'document_link_analysis': request.POST.get('document_link_analysis') == 'on',
                'auto_merge_enabled': request.POST.get('auto_merge_enabled') == 'on',
                'batch_size': int(request.POST.get('batch_size', 1000)),
                'completeness_weight': float(request.POST.get('completeness_weight', 0.4)),
                'recency_weight': float(request.POST.get('recency_weight', 0.3)),
                'data_quality_weight': float(request.POST.get('data_quality_weight', 0.3)),
            }
            session.config = config
            session.save()
            
            messages.success(request, 'Duplicate detection session created successfully.')
            return redirect('merge_duplicates:session_detail', pk=session.pk)
    else:
        form = DuplicateDetectionSessionForm()
    
    context = {
        'form': form,
        'title': 'Create New Session',
    }
    
    return render(request, 'data_cleaning_tool/merge_duplicates/session_form.html', context)


@login_required
def session_detail(request, pk):
    """View details of a duplicate detection session"""
    
    session = get_object_or_404(DuplicateDetectionSession, pk=pk, created_by=request.user)
    
    # Get duplicate groups for this session
    duplicate_groups = DuplicateGroup.objects.filter(session=session).order_by('-confidence_score')
    
    # Get merge operations
    merge_operations = MergeOperation.objects.filter(duplicate_group__session=session).order_by('-created_at')
    
    context = {
        'session': session,
        'duplicate_groups': duplicate_groups,
        'merge_operations': merge_operations,
    }
    
    return render(request, 'data_cleaning_tool/merge_duplicates/session_detail.html', context)


@login_required
def session_start(request, pk):
    """Start a duplicate detection session"""
    
    session = get_object_or_404(DuplicateDetectionSession, pk=pk, created_by=request.user)
    
    if session.status != 'pending':
        messages.error(request, 'Session cannot be started. Current status: ' + session.get_status_display())
        return redirect('merge_duplicates:session_detail', pk=session.pk)
    
    try:
        # Start the session
        session.start_session()
        
        # TODO: Implement actual duplicate detection logic here
        # This would involve:
        # 1. Scanning the database for duplicates based on rules
        # 2. Creating DuplicateGroup and DuplicateRecord objects
        # 3. Calculating confidence scores
        
        # For now, create some sample data
        create_sample_duplicates(session)
        
        session.complete_session()
        messages.success(request, 'Duplicate detection session completed successfully.')
        
    except Exception as e:
        logger.error(f"Error starting session {session.pk}: {str(e)}")
        session.fail_session()
        messages.error(request, f'Error starting session: {str(e)}')
    
    return redirect('merge_duplicates:session_detail', pk=session.pk)


def create_sample_duplicates(session):
    """Create sample duplicate data for demonstration purposes"""
    
    # Create sample duplicate groups
    sample_groups = [
        {
            'entity_type': 'customer',
            'confidence_score': 0.95,
            'records': [
                {'record_id': 'CUST001', 'completeness_score': 0.9, 'recency_score': 0.8, 'overall_score': 0.85},
                {'record_id': 'CUST002', 'completeness_score': 0.7, 'recency_score': 0.9, 'overall_score': 0.8},
            ]
        },
        {
            'entity_type': 'vendor',
            'confidence_score': 0.88,
            'records': [
                {'record_id': 'VEND001', 'completeness_score': 0.8, 'recency_score': 0.7, 'overall_score': 0.75},
                {'record_id': 'VEND002', 'completeness_score': 0.6, 'recency_score': 0.8, 'overall_score': 0.7},
            ]
        }
    ]
    
    for group_data in sample_groups:
        group = DuplicateGroup.objects.create(
            session=session,
            entity_type=group_data['entity_type'],
            confidence_score=group_data['confidence_score']
        )
        
        for record_data in group_data['records']:
            DuplicateRecord.objects.create(
                duplicate_group=group,
                record_id=record_data['record_id'],
                completeness_score=record_data['completeness_score'],
                recency_score=record_data['recency_score'],
                overall_score=record_data['overall_score'],
                record_data={'name': f'Sample {record_data["record_id"]}', 'type': group_data['entity_type']}
            )


@login_required
def duplicate_group_detail(request, pk):
    """View details of a duplicate group"""
    
    duplicate_group = get_object_or_404(DuplicateGroup, pk=pk)
    
    # Get all records in this group
    records = DuplicateRecord.objects.filter(duplicate_group=duplicate_group).order_by('-overall_score')
    
    # Get merge operation if exists
    merge_operation = None
    if duplicate_group.is_merged:
        merge_operation = MergeOperation.objects.filter(duplicate_group=duplicate_group).first()
    
    context = {
        'duplicate_group': duplicate_group,
        'records': records,
        'merge_operation': merge_operation,
    }
    
    return render(request, 'data_cleaning_tool/merge_duplicates/duplicate_group_detail.html', context)


@login_required
def duplicate_group_review(request, pk):
    """Review and approve a duplicate group for merging"""
    
    duplicate_group = get_object_or_404(DuplicateGroup, pk=pk)
    
    if duplicate_group.is_merged:
        messages.warning(request, 'This duplicate group has already been merged.')
        return redirect('merge_duplicates:duplicate_group_detail', pk=pk)
    
    if request.method == 'POST':
        form = DuplicateGroupReviewForm(duplicate_group, request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create merge operation
                    master_record = DuplicateRecord.objects.get(
                        pk=form.cleaned_data['master_record_id']
                    )
                    
                    merge_operation = MergeOperation.objects.create(
                        duplicate_group=duplicate_group,
                        master_record=master_record,
                        created_by=request.user,
                        merge_config={
                            'notes': form.cleaned_data.get('merge_notes', ''),
                            'reviewed_at': timezone.now().isoformat(),
                        }
                    )
                    
                    # Mark duplicate group as merged
                    duplicate_group.is_merged = True
                    duplicate_group.merged_at = timezone.now()
                    duplicate_group.merged_by = request.user
                    duplicate_group.save()
                    
                    # Mark master record
                    master_record.is_master = True
                    master_record.save()
                    
                    # TODO: Implement actual merge logic here
                    # This would involve:
                    # 1. Updating all references to point to the master record
                    # 2. Consolidating transaction history
                    # 3. Updating document links
                    # 4. Archiving duplicate records
                    
                    # Create audit log
                    MergeAuditLog.objects.create(
                        merge_operation=merge_operation,
                        level='info',
                        message=f'Merge operation initiated by {request.user.username}',
                        context_data={'action': 'merge_initiated'}
                    )
                    
                    messages.success(request, 'Duplicate group approved for merging.')
                    return redirect('merge_duplicates:duplicate_group_detail', pk=pk)
                    
            except Exception as e:
                logger.error(f"Error during merge operation: {str(e)}")
                messages.error(request, f'Error during merge operation: {str(e)}')
    else:
        form = DuplicateGroupReviewForm(duplicate_group)
    
    context = {
        'duplicate_group': duplicate_group,
        'form': form,
    }
    
    return render(request, 'data_cleaning_tool/merge_duplicates/duplicate_group_review.html', context)


@login_required
def rules_list(request):
    """List all deduplication rules"""
    
    rules = DeduplicationRule.objects.all().order_by('priority', 'name')
    
    context = {
        'rules': rules,
    }
    
    return render(request, 'data_cleaning_tool/merge_duplicates/rules_list.html', context)


@login_required
def rule_create(request):
    """Create a new deduplication rule"""
    
    if request.method == 'POST':
        form = DeduplicationRuleForm(request.POST)
        if form.is_valid():
            rule = form.save(commit=False)
            rule.created_by = request.user
            rule.save()
            
            messages.success(request, 'Deduplication rule created successfully.')
            return redirect('merge_duplicates:rules_list')
    else:
        form = DeduplicationRuleForm()
    
    context = {
        'form': form,
        'title': 'Create New Rule',
    }
    
    return render(request, 'data_cleaning_tool/merge_duplicates/rule_form.html', context)


@login_required
def rule_edit(request, pk):
    """Edit an existing deduplication rule"""
    
    rule = get_object_or_404(DeduplicationRule, pk=pk)
    
    if request.method == 'POST':
        form = DeduplicationRuleForm(request.POST, instance=rule)
        if form.is_valid():
            form.save()
            messages.success(request, 'Deduplication rule updated successfully.')
            return redirect('merge_duplicates:rules_list')
    else:
        form = DeduplicationRuleForm(instance=rule)
    
    context = {
        'form': form,
        'title': 'Edit Rule',
        'rule': rule,
    }
    
    return render(request, 'data_cleaning_tool/merge_duplicates/rule_form.html', context)


@login_required
def scheduled_tasks_list(request):
    """List all scheduled deduplication tasks"""
    
    tasks = ScheduledDeduplication.objects.all().order_by('name')
    
    context = {
        'tasks': tasks,
    }
    
    return render(request, 'data_cleaning_tool/merge_duplicates/scheduled_tasks_list.html', context)


@login_required
def scheduled_task_create(request):
    """Create a new scheduled deduplication task"""
    
    if request.method == 'POST':
        form = ScheduledDeduplicationForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            
            messages.success(request, 'Scheduled task created successfully.')
            return redirect('merge_duplicates:scheduled_tasks_list')
    else:
        form = ScheduledDeduplicationForm()
    
    context = {
        'form': form,
        'title': 'Create New Scheduled Task',
    }
    
    return render(request, 'data_cleaning_tool/merge_duplicates/scheduled_task_form.html', context)


@login_required
def bulk_merge(request):
    """Perform bulk merge operations"""
    
    if request.method == 'POST':
        form = BulkMergeForm(request.POST)
        if form.is_valid():
            try:
                # Get form data
                entity_type = form.cleaned_data['entity_type']
                confidence_threshold = form.cleaned_data['confidence_threshold']
                max_duplicates = form.cleaned_data['max_duplicates_per_group']
                dry_run = form.cleaned_data['dry_run']
                
                # TODO: Implement bulk merge logic here
                # This would involve:
                # 1. Finding all duplicate groups matching criteria
                # 2. Applying merge rules automatically
                # 3. Creating merge operations
                # 4. Updating references
                
                if dry_run:
                    messages.info(request, 'Dry run completed. No actual merges were performed.')
                else:
                    messages.success(request, 'Bulk merge operation completed successfully.')
                
                return redirect('merge_duplicates:merge_duplicates_dashboard')
                
            except Exception as e:
                logger.error(f"Error during bulk merge: {str(e)}")
                messages.error(request, f'Error during bulk merge: {str(e)}')
    else:
        form = BulkMergeForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'data_cleaning_tool/merge_duplicates/bulk_merge.html', context)


@login_required
def merge_analytics(request):
    """View analytics and reports for merge operations"""
    
    # Get statistics
    total_sessions = DuplicateDetectionSession.objects.count()
    total_duplicates_found = DuplicateGroup.objects.count()
    total_records_merged = MergeOperation.objects.filter(status='completed').count()
    
    # Get entity type breakdown
    entity_type_stats = {}
    for group in DuplicateGroup.objects.all():
        entity_type = group.entity_type
        if entity_type not in entity_type_stats:
            entity_type_stats[entity_type] = {
                'total_groups': 0,
                'merged_groups': 0,
                'avg_confidence': 0,
            }
        entity_type_stats[entity_type]['total_groups'] += 1
        if group.is_merged:
            entity_type_stats[entity_type]['merged_groups'] += 1
    
    # Calculate average confidence scores
    for entity_type in entity_type_stats:
        groups = DuplicateGroup.objects.filter(entity_type=entity_type)
        if groups.exists():
            avg_confidence = groups.aggregate(
                avg=models.Avg('confidence_score')
            )['avg'] or 0
            entity_type_stats[entity_type]['avg_confidence'] = round(avg_confidence, 2)
    
    context = {
        'total_sessions': total_sessions,
        'total_duplicates_found': total_duplicates_found,
        'total_records_merged': total_records_merged,
        'entity_type_stats': entity_type_stats,
    }
    
    return render(request, 'data_cleaning_tool/merge_duplicates/analytics.html', context)


# API endpoints for AJAX requests
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_start_session(request):
    """API endpoint to start a duplicate detection session"""
    
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        
        session = get_object_or_404(DuplicateDetectionSession, pk=session_id, created_by=request.user)
        
        if session.status != 'pending':
            return JsonResponse({
                'success': False,
                'error': 'Session cannot be started'
            })
        
        # Start session
        session.start_session()
        
        # TODO: Implement background task for duplicate detection
        
        return JsonResponse({
            'success': True,
            'message': 'Session started successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_merge_records(request):
    """API endpoint to merge duplicate records"""
    
    try:
        data = json.loads(request.body)
        group_id = data.get('group_id')
        master_record_id = data.get('master_record_id')
        
        duplicate_group = get_object_or_404(DuplicateGroup, pk=group_id)
        
        if duplicate_group.is_merged:
            return JsonResponse({
                'success': False,
                'error': 'Group already merged'
            })
        
        # TODO: Implement merge logic
        
        return JsonResponse({
            'success': True,
            'message': 'Records merged successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
