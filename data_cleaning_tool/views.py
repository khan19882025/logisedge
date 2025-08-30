from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import json
import logging

from .models import (
    DataCleaningSession, DataCleaningRule, DataCleaningAuditLog,
    DataQualityReport, AutomatedCleaningSchedule
)
from .forms import (
    DataCleaningSessionForm, DataCleaningRuleForm, AutomatedCleaningScheduleForm,
    DataCleaningConfigurationForm, DataCleaningFilterForm
)

logger = logging.getLogger(__name__)


@login_required
def dashboard(request):
    """Main dashboard for data cleaning tool"""
    # Get recent sessions
    recent_sessions = DataCleaningSession.objects.filter(
        created_by=request.user
    ).order_by('-created_at')[:5]
    
    # Get active rules
    active_rules = DataCleaningRule.objects.filter(is_active=True).count()
    
    # Get scheduled cleanings
    scheduled_cleanings = AutomatedCleaningSchedule.objects.filter(is_active=True).count()
    
    # Get recent audit logs
    recent_audits = DataCleaningAuditLog.objects.select_related('session').order_by('-created_at')[:10]
    
    # Get statistics
    total_sessions = DataCleaningSession.objects.count()
    total_records_cleaned = sum(session.total_records_cleaned for session in DataCleaningSession.objects.all())
    total_errors_found = sum(session.total_errors_found for session in DataCleaningSession.objects.all())
    
    context = {
        'recent_sessions': recent_sessions,
        'active_rules': active_rules,
        'scheduled_cleanings': scheduled_cleanings,
        'recent_audits': recent_audits,
        'total_sessions': total_sessions,
        'total_records_cleaned': total_records_cleaned,
        'total_errors_found': total_errors_found,
    }
    
    return render(request, 'data_cleaning_tool/dashboard.html', context)


@login_required
def session_list(request):
    """List all data cleaning sessions"""
    sessions = DataCleaningSession.objects.filter(created_by=request.user).order_by('-created_at')
    
    # Filtering
    form = DataCleaningFilterForm(request.GET)
    if form.is_valid():
        if form.cleaned_data.get('date_from'):
            sessions = sessions.filter(created_at__gte=form.cleaned_data['date_from'])
        if form.cleaned_data.get('date_to'):
            sessions = sessions.filter(created_at__lte=form.cleaned_data['date_to'])
        if form.cleaned_data.get('severity'):
            sessions = sessions.filter(status=form.cleaned_data['severity'])
    
    # Pagination
    paginator = Paginator(sessions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'form': form,
    }
    
    return render(request, 'data_cleaning_tool/session_list.html', context)


@login_required
def session_create(request):
    """Create a new data cleaning session"""
    if request.method == 'POST':
        form = DataCleaningSessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.created_by = request.user
            session.save()
            messages.success(request, 'Data cleaning session created successfully!')
            return redirect('data_cleaning_tool:session_detail', pk=session.pk)
    else:
        form = DataCleaningSessionForm()
    
    context = {
        'form': form,
        'title': 'Create New Data Cleaning Session'
    }
    
    return render(request, 'data_cleaning_tool/session_form.html', context)


@login_required
def session_detail(request, pk):
    """View details of a data cleaning session"""
    session = get_object_or_404(DataCleaningSession, pk=pk, created_by=request.user)
    
    # Get audit logs for this session
    audit_logs = DataCleaningAuditLog.objects.filter(session=session).order_by('-created_at')
    
    # Get quality report if exists
    try:
        quality_report = DataQualityReport.objects.get(session=session)
    except DataQualityReport.DoesNotExist:
        quality_report = None
    
    context = {
        'session': session,
        'audit_logs': audit_logs,
        'quality_report': quality_report,
    }
    
    return render(request, 'data_cleaning_tool/session_detail.html', context)


@login_required
def session_configure(request, pk):
    """Configure and start a data cleaning session"""
    session = get_object_or_404(DataCleaningSession, pk=pk, created_by=request.user)
    
    if request.method == 'POST':
        config_form = DataCleaningConfigurationForm(request.POST)
        if config_form.is_valid():
            # Start the cleaning process
            session.status = 'running'
            session.started_at = timezone.now()
            session.save()
            
            # Here you would typically start a background task
            # For now, we'll simulate the process
            messages.success(request, 'Data cleaning session started!')
            return redirect('data_cleaning_tool:session_detail', pk=session.pk)
    else:
        config_form = DataCleaningConfigurationForm()
    
    context = {
        'session': session,
        'config_form': config_form,
    }
    
    return render(request, 'data_cleaning_tool/session_configure.html', context)


@login_required
def rule_list(request):
    """List all data cleaning rules"""
    rules = DataCleaningRule.objects.all().order_by('priority', 'name')
    
    # Filtering
    rule_type = request.GET.get('rule_type')
    if rule_type:
        rules = rules.filter(rule_type=rule_type)
    
    # Pagination
    paginator = Paginator(rules, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'rule_types': DataCleaningRule.RULE_TYPE,
        'selected_type': rule_type,
    }
    
    return render(request, 'data_cleaning_tool/rule_list.html', context)


@login_required
def rule_create(request):
    """Create a new data cleaning rule"""
    if request.method == 'POST':
        form = DataCleaningRuleForm(request.POST)
        if form.is_valid():
            rule = form.save()
            messages.success(request, 'Data cleaning rule created successfully!')
            return redirect('data_cleaning_tool:rule_list')
    else:
        form = DataCleaningRuleForm()
    
    context = {
        'form': form,
        'title': 'Create New Data Cleaning Rule'
    }
    
    return render(request, 'data_cleaning_tool/rule_form.html', context)


@login_required
def rule_edit(request, pk):
    """Edit an existing data cleaning rule"""
    rule = get_object_or_404(DataCleaningRule, pk=pk)
    
    if request.method == 'POST':
        form = DataCleaningRuleForm(request.POST, instance=rule)
        if form.is_valid():
            form.save()
            messages.success(request, 'Data cleaning rule updated successfully!')
            return redirect('data_cleaning_tool:rule_list')
    else:
        form = DataCleaningRuleForm(instance=rule)
    
    context = {
        'form': form,
        'rule': rule,
        'title': 'Edit Data Cleaning Rule'
    }
    
    return render(request, 'data_cleaning_tool/rule_form.html', context)


@login_required
def rule_delete(request, pk):
    """Delete a data cleaning rule"""
    rule = get_object_or_404(DataCleaningRule, pk=pk)
    
    if request.method == 'POST':
        rule.delete()
        messages.success(request, 'Data cleaning rule deleted successfully!')
        return redirect('data_cleaning_tool:rule_list')
    
    context = {
        'rule': rule,
    }
    
    return render(request, 'data_cleaning_tool/rule_confirm_delete.html', context)


@login_required
def schedule_list(request):
    """List all automated cleaning schedules"""
    schedules = AutomatedCleaningSchedule.objects.all().order_by('name')
    
    context = {
        'schedules': schedules,
    }
    
    return render(request, 'data_cleaning_tool/schedule_list.html', context)


@login_required
def schedule_create(request):
    """Create a new automated cleaning schedule"""
    if request.method == 'POST':
        form = AutomatedCleaningScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.created_by = request.user
            schedule.save()
            messages.success(request, 'Automated cleaning schedule created successfully!')
            return redirect('data_cleaning_tool:schedule_list')
    else:
        form = AutomatedCleaningScheduleForm()
    
    context = {
        'form': form,
        'title': 'Create New Automated Schedule'
    }
    
    return render(request, 'data_cleaning_tool/schedule_form.html', context)


@login_required
def schedule_edit(request, pk):
    """Edit an existing automated cleaning schedule"""
    schedule = get_object_or_404(AutomatedCleaningSchedule, pk=pk)
    
    if request.method == 'POST':
        form = AutomatedCleaningScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            messages.success(request, 'Automated cleaning schedule updated successfully!')
            return redirect('data_cleaning_tool:schedule_list')
    else:
        form = AutomatedCleaningScheduleForm(instance=schedule)
    
    context = {
        'form': form,
        'schedule': schedule,
        'title': 'Edit Automated Schedule'
    }
    
    return render(request, 'data_cleaning_tool/schedule_form.html', context)


@login_required
def audit_logs(request):
    """View audit logs for data cleaning activities"""
    logs = DataCleaningAuditLog.objects.select_related('session', 'rule').order_by('-created_at')
    
    # Filtering
    form = DataCleaningFilterForm(request.GET)
    if form.is_valid():
        if form.cleaned_data.get('date_from'):
            logs = logs.filter(created_at__gte=form.cleaned_data['date_from'])
        if form.cleaned_data.get('date_to'):
            logs = logs.filter(created_at__lte=form.cleaned_data['date_to'])
        if form.cleaned_data.get('severity'):
            logs = logs.filter(severity=form.cleaned_data['severity'])
        if form.cleaned_data.get('action_type'):
            logs = logs.filter(action_type=form.cleaned_data['action_type'])
        if form.cleaned_data.get('target_model'):
            logs = logs.filter(target_model__icontains=form.cleaned_data['target_model'])
    
    # Pagination
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'form': form,
    }
    
    return render(request, 'data_cleaning_tool/audit_logs.html', context)


@login_required
def reports(request):
    """View data quality reports"""
    reports_list = DataQualityReport.objects.select_related('session').order_by('-generated_at')
    
    context = {
        'reports': reports_list,
    }
    
    return render(request, 'data_cleaning_tool/reports.html', context)


@login_required
def report_detail(request, pk):
    """View details of a specific data quality report"""
    report = get_object_or_404(DataQualityReport, pk=pk)
    
    context = {
        'report': report,
    }
    
    return render(request, 'data_cleaning_tool/report_detail.html', context)


@csrf_exempt
@login_required
def api_start_cleaning(request, pk):
    """API endpoint to start data cleaning process"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        session = get_object_or_404(DataCleaningSession, pk=pk, created_by=request.user)
        
        # Update session status
        session.status = 'running'
        session.started_at = timezone.now()
        session.save()
        
        # Here you would typically start a background task using Celery or similar
        # For demonstration, we'll simulate the process
        
        return JsonResponse({
            'success': True,
            'message': 'Data cleaning started successfully',
            'session_id': session.pk
        })
        
    except Exception as e:
        logger.error(f"Error starting data cleaning: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@login_required
def api_cleaning_progress(request, pk):
    """API endpoint to get cleaning progress"""
    try:
        session = get_object_or_404(DataCleaningSession, pk=pk, created_by=request.user)
        
        return JsonResponse({
            'session_id': session.pk,
            'status': session.status,
            'total_records_scanned': session.total_records_scanned,
            'total_records_cleaned': session.total_records_cleaned,
            'total_errors_found': session.total_errors_found,
            'total_warnings_found': session.total_warnings_found,
        })
        
    except Exception as e:
        logger.error(f"Error getting cleaning progress: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def quick_clean(request):
    """Quick data cleaning interface"""
    if request.method == 'POST':
        config_form = DataCleaningConfigurationForm(request.POST)
        if config_form.is_valid():
            # Create a quick session
            session = DataCleaningSession.objects.create(
                name=f"Quick Clean - {timezone.now().strftime('%Y-%m-%d %H:%M')}",
                description="Quick data cleaning session",
                cleaning_type='comprehensive',
                created_by=request.user,
                status='running',
                started_at=timezone.now()
            )
            
            messages.success(request, 'Quick data cleaning started!')
            return redirect('data_cleaning_tool:session_detail', pk=session.pk)
    else:
        config_form = DataCleaningConfigurationForm()
    
    context = {
        'config_form': config_form,
    }
    
    return render(request, 'data_cleaning_tool/quick_clean.html', context)


@login_required
def session_export(request, pk):
    """Export session results in various formats"""
    try:
        session = DataCleaningSession.objects.get(pk=pk)
    except DataCleaningSession.DoesNotExist:
        messages.error(request, 'Session not found.')
        return redirect('data_cleaning_tool:session_list')
    
    format_type = request.GET.get('format', 'csv')
    
    if format_type == 'pdf':
        # PDF export logic would go here
        messages.info(request, 'PDF export functionality coming soon.')
        return redirect('data_cleaning_tool:session_detail', pk=session.pk)
    elif format_type == 'excel':
        # Excel export logic would go here
        messages.info(request, 'Excel export functionality coming soon.')
        return redirect('data_cleaning_tool:session_detail', pk=session.pk)
    else:
        # CSV export logic would go here
        messages.info(request, 'CSV export functionality coming soon.')
        return redirect('data_cleaning_tool:session_detail', pk=session.pk)


@login_required
def session_rerun(request, pk):
    """Rerun a completed data cleaning session"""
    try:
        session = DataCleaningSession.objects.get(pk=pk)
    except DataCleaningSession.DoesNotExist:
        messages.error(request, 'Session not found.')
        return redirect('data_cleaning_tool:session_detail', pk=session.pk)
    
    if session.status != 'completed':
        messages.error(request, 'Only completed sessions can be rerun.')
        return redirect('data_cleaning_tool:session_detail', pk=session.pk)
    
    # Create a new session based on the current one
    new_session = DataCleaningSession.objects.create(
        name=f"{session.name} (Rerun)",
        description=session.description,
        cleaning_type=session.cleaning_type,
        priority=session.priority,
        date_from=session.date_from,
        date_to=session.date_to,
        batch_size=session.batch_size,
        remove_duplicates=session.remove_duplicates,
        fill_mandatory=session.fill_mandatory,
        standardize_format=session.standardize_format,
        validate_data=session.validate_data,
        archive_old=session.archive_old,
        create_backup=session.create_backup,
        custom_rules=session.custom_rules,
        email_notifications=session.email_notifications,
        sms_notifications=session.sms_notifications,
        notification_email=session.notification_email,
        created_by=request.user
    )
    
    messages.success(request, f'New session "{new_session.name}" created successfully.')
    return redirect('data_cleaning_tool:session_detail', pk=new_session.pk)
