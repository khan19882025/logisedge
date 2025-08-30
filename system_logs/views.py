from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Min, Max, Avg
from django.utils import timezone
from django.urls import reverse_lazy
from django.contrib.contenttypes.models import ContentType
from django.db import connection
import json
import csv
import io
from datetime import datetime, timedelta
from .models import SystemLog, ErrorPattern, DebugSession, LogRetentionPolicy, LogExport
from .forms import (
    SystemLogSearchForm, SystemLogExportForm, ErrorPatternForm, 
    DebugSessionForm, LogRetentionPolicyForm, BulkActionForm,
    SystemLogDetailForm, PerformanceFilterForm, SecurityFilterForm
)


@login_required
@permission_required('system_logs.view_systemlog')
def dashboard(request):
    """
    Dashboard view showing system logs overview and statistics
    """
    # Get date range from request or default to last 30 days
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Get log statistics
    logs = SystemLog.objects.filter(
        timestamp__range=(start_date, end_date)
    )
    
    # Log type statistics
    log_type_stats = logs.values('log_type').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Severity statistics
    severity_stats = logs.values('severity').annotate(
        count=Count('id')
    ).order_by('severity')
    
    # Status statistics
    status_stats = logs.values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Module statistics
    module_stats = logs.values('module').annotate(
        count=Count('id')
    ).exclude(module='').order_by('-count')[:10]
    
    # User activity statistics
    user_stats = logs.values('user__username').annotate(
        count=Count('id')
    ).exclude(user__isnull=True).order_by('-count')[:10]
    
    # Recent critical errors
    critical_logs = logs.filter(
        severity__in=['CRITICAL', 'FATAL']
    ).order_by('-timestamp')[:10]
    
    # Performance metrics
    avg_execution_time = logs.aggregate(
        avg_time=Avg('execution_time')
    )['avg_time'] or 0
    
    # Error patterns
    error_patterns = ErrorPattern.objects.filter(
        last_occurrence__gte=start_date
    ).order_by('-occurrence_count')[:5]
    
    # Active debug sessions
    active_sessions = DebugSession.objects.filter(
        is_active=True
    ).order_by('-started_at')[:5]
    
    context = {
        'days': days,
        'log_type_stats': log_type_stats,
        'severity_stats': severity_stats,
        'status_stats': status_stats,
        'module_stats': module_stats,
        'user_stats': user_stats,
        'critical_logs': critical_logs,
        'avg_execution_time': avg_execution_time,
        'error_patterns': error_patterns,
        'active_sessions': active_sessions,
        'total_logs': logs.count(),
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'system_logs/dashboard.html', context)


class SystemLogListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    List view for system logs with advanced filtering and search
    """
    model = SystemLog
    template_name = 'system_logs/system_log_list.html'
    context_object_name = 'logs'
    permission_required = 'system_logs.view_systemlog'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = SystemLog.objects.all()
        
        # Apply search filters
        form = SystemLogSearchForm(self.request.GET)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            
            # Date range filter
            if cleaned_data.get('date_from'):
                queryset = queryset.filter(timestamp__date__gte=cleaned_data['date_from'])
            if cleaned_data.get('date_to'):
                queryset = queryset.filter(timestamp__date__lte=cleaned_data['date_to'])
            
            # Core filters
            if cleaned_data.get('log_type'):
                queryset = queryset.filter(log_type=cleaned_data['log_type'])
            if cleaned_data.get('severity'):
                queryset = queryset.filter(severity=cleaned_data['severity'])
            if cleaned_data.get('status'):
                queryset = queryset.filter(status=cleaned_data['status'])
            
            # Context filters
            if cleaned_data.get('module'):
                queryset = queryset.filter(module__icontains=cleaned_data['module'])
            if cleaned_data.get('function'):
                queryset = queryset.filter(function__icontains=cleaned_data['function'])
            if cleaned_data.get('user'):
                queryset = queryset.filter(user=cleaned_data['user'])
            
            # Error details
            if cleaned_data.get('error_type'):
                queryset = queryset.filter(error_type__icontains=cleaned_data['error_type'])
            if cleaned_data.get('error_message'):
                queryset = queryset.filter(error_message__icontains=cleaned_data['error_message'])
            
            # Performance filters
            if cleaned_data.get('execution_time_min'):
                queryset = queryset.filter(execution_time__gte=cleaned_data['execution_time_min'])
            if cleaned_data.get('execution_time_max'):
                queryset = queryset.filter(execution_time__lte=cleaned_data['execution_time_max'])
            
            # Tags and context
            if cleaned_data.get('tags'):
                tags = [tag.strip() for tag in cleaned_data['tags'].split(',')]
                for tag in tags:
                    queryset = queryset.filter(tags__contains=[tag])
            if cleaned_data.get('environment'):
                queryset = queryset.filter(environment__icontains=cleaned_data['environment'])
            
            # Advanced filters
            if cleaned_data.get('has_stack_trace'):
                queryset = queryset.exclude(stack_trace='')
            if cleaned_data.get('has_context_data'):
                queryset = queryset.exclude(context_data={})
            if cleaned_data.get('is_resolved'):
                queryset = queryset.filter(status='RESOLVED')
        
        return queryset.select_related('user', 'content_type').order_by('-timestamp')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = SystemLogSearchForm(self.request.GET)
        context['bulk_action_form'] = BulkActionForm()
        
        return context


class SystemLogDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """
    Detail view for individual system log entries
    """
    model = SystemLog
    template_name = 'system_logs/system_log_detail.html'
    context_object_name = 'log'
    permission_required = 'system_logs.view_systemlog'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get related logs (same user, same module, etc.)
        log = self.get_object()
        
        # Related logs by user
        context['user_logs'] = SystemLog.objects.filter(
            user=log.user,
            timestamp__gte=log.timestamp - timedelta(days=1)
        ).exclude(id=log.id).order_by('-timestamp')[:10]
        
        # Related logs by module
        if log.module:
            context['module_logs'] = SystemLog.objects.filter(
                module=log.module,
                timestamp__gte=log.timestamp - timedelta(days=7)
            ).exclude(id=log.id).order_by('-timestamp')[:10]
        
        # Related logs by error type
        if log.error_type:
            context['error_type_logs'] = SystemLog.objects.filter(
                error_type=log.error_type,
                timestamp__gte=log.timestamp - timedelta(days=30)
            ).exclude(id=log.id).order_by('-timestamp')[:10]
        
        # Error patterns
        context['error_patterns'] = ErrorPattern.objects.filter(
            error_type=log.error_type
        ).order_by('-occurrence_count')[:5]
        
        # Debug sessions
        context['debug_sessions'] = DebugSession.objects.filter(
            logs=log
        ).order_by('-started_at')[:5]
        
        return context


@login_required
@permission_required('system_logs.view_systemlog')
def system_log_search(request):
    """
    Advanced search view for system logs
    """
    form = SystemLogSearchForm(request.GET)
    logs = []
    
    if form.is_valid():
        logs = SystemLog.objects.all()
        cleaned_data = form.cleaned_data
        
        # Apply all filters (same logic as ListView)
        if cleaned_data.get('date_from'):
            logs = logs.filter(timestamp__date__gte=cleaned_data['date_from'])
        if cleaned_data.get('date_to'):
            logs = logs.filter(timestamp__date__lte=cleaned_data['date_to'])
        if cleaned_data.get('log_type'):
            logs = logs.filter(log_type=cleaned_data['log_type'])
        if cleaned_data.get('severity'):
            logs = logs.filter(severity=cleaned_data['severity'])
        if cleaned_data.get('status'):
            logs = logs.filter(status=cleaned_data['status'])
        if cleaned_data.get('module'):
            logs = logs.filter(module__icontains=cleaned_data['module'])
        if cleaned_data.get('function'):
            logs = logs.filter(function__icontains=cleaned_data['function'])
        if cleaned_data.get('user'):
            logs = logs.filter(user=cleaned_data['user'])
        if cleaned_data.get('error_type'):
            logs = logs.filter(error_type__icontains=cleaned_data['error_type'])
        if cleaned_data.get('error_message'):
            logs = logs.filter(error_message__icontains=cleaned_data['error_message'])
        if cleaned_data.get('execution_time_min'):
            logs = logs.filter(execution_time__gte=cleaned_data['execution_time_min'])
        if cleaned_data.get('execution_time_max'):
            logs = logs.filter(execution_time__lte=cleaned_data['execution_time_max'])
        if cleaned_data.get('tags'):
            tags = [tag.strip() for tag in cleaned_data['tags'].split(',')]
            for tag in tags:
                logs = logs.filter(tags__contains=[tag])
        if cleaned_data.get('environment'):
            logs = logs.filter(environment__icontains=cleaned_data['environment'])
        if cleaned_data.get('has_stack_trace'):
            logs = logs.exclude(stack_trace='')
        if cleaned_data.get('has_context_data'):
            logs = logs.exclude(context_data={})
        if cleaned_data.get('is_resolved'):
            logs = logs.filter(status='RESOLVED')
        
        logs = logs.select_related('user', 'content_type').order_by('-timestamp')
    
    # Pagination
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'logs': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
    }
    
    return render(request, 'system_logs/system_log_search.html', context)


@login_required
@permission_required('system_logs.view_systemlog')
def system_log_export(request):
    """
    Export system logs data in various formats
    """
    if request.method == 'POST':
        form = SystemLogExportForm(request.POST)
        if form.is_valid():
            export_format = form.cleaned_data['export_format']
            include_headers = form.cleaned_data['include_headers']
            include_metadata = form.cleaned_data['include_metadata']
            include_stack_trace = form.cleaned_data['include_stack_trace']
            include_context_data = form.cleaned_data['include_context_data']
            max_records = form.cleaned_data['max_records']
            filename_prefix = form.cleaned_data['filename_prefix']
            fields_to_include = form.cleaned_data['fields_to_include']
            
            # Get filtered data from search parameters
            search_form = SystemLogSearchForm(request.POST)
            logs = SystemLog.objects.all()
            
            if search_form.is_valid():
                cleaned_data = search_form.cleaned_data
                # Apply filters (same logic as search)
                if cleaned_data.get('date_from'):
                    logs = logs.filter(timestamp__date__gte=cleaned_data['date_from'])
                if cleaned_data.get('date_to'):
                    logs = logs.filter(timestamp__date__lte=cleaned_data['date_to'])
                if cleaned_data.get('log_type'):
                    logs = logs.filter(log_type=cleaned_data['log_type'])
                if cleaned_data.get('severity'):
                    logs = logs.filter(severity=cleaned_data['severity'])
                if cleaned_data.get('status'):
                    logs = logs.filter(status=cleaned_data['status'])
                if cleaned_data.get('module'):
                    logs = logs.filter(module__icontains=cleaned_data['module'])
                if cleaned_data.get('function'):
                    logs = logs.filter(function__icontains=cleaned_data['function'])
                if cleaned_data.get('user'):
                    logs = logs.filter(user=cleaned_data['user'])
                if cleaned_data.get('error_type'):
                    logs = logs.filter(error_type__icontains=cleaned_data['error_type'])
                if cleaned_data.get('error_message'):
                    logs = logs.filter(error_message__icontains=cleaned_data['error_message'])
                if cleaned_data.get('execution_time_min'):
                    logs = logs.filter(execution_time__gte=cleaned_data['execution_time_min'])
                if cleaned_data.get('execution_time_max'):
                    logs = logs.filter(execution_time__lte=cleaned_data['execution_time_max'])
                if cleaned_data.get('tags'):
                    tags = [tag.strip() for tag in cleaned_data['tags'].split(',')]
                    for tag in tags:
                        logs = logs.filter(tags__contains=[tag])
                if cleaned_data.get('environment'):
                    logs = logs.filter(environment__icontains=cleaned_data['environment'])
                if cleaned_data.get('has_stack_trace'):
                    logs = logs.exclude(stack_trace='')
                if cleaned_data.get('has_context_data'):
                    logs = logs.exclude(context_data={})
                if cleaned_data.get('is_resolved'):
                    logs = logs.filter(status='RESOLVED')
            
            # Limit records
            logs = logs[:max_records]
            
            # Create export record
            export_record = LogExport.objects.create(
                user=request.user,
                export_format=export_format,
                filter_criteria=request.POST.dict(),
                record_count=logs.count(),
                status='COMPLETED'
            )
            
            # Generate export file
            if export_format == 'CSV':
                return export_to_csv(logs, include_headers, include_metadata, include_stack_trace, include_context_data, fields_to_include, filename_prefix)
            elif export_format == 'JSON':
                return export_to_json(logs, include_metadata, include_stack_trace, include_context_data, fields_to_include, filename_prefix)
            elif export_format == 'XML':
                return export_to_xml(logs, include_metadata, include_stack_trace, include_context_data, fields_to_include, filename_prefix)
            elif export_format == 'PDF':
                return export_to_pdf(logs, include_metadata, include_stack_trace, include_context_data, fields_to_include, filename_prefix)
    
    # GET request - show export form
    form = SystemLogExportForm()
    search_form = SystemLogSearchForm(request.GET)
    
    context = {
        'form': form,
        'search_form': search_form,
    }
    
    return render(request, 'system_logs/system_log_export.html', context)


def export_to_csv(logs, include_headers, include_metadata, include_stack_trace, include_context_data, fields_to_include, filename_prefix):
    """Export logs to CSV format"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename_prefix}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    if include_headers:
        headers = []
        for field in fields_to_include:
            if field == 'timestamp':
                headers.append('Timestamp')
            elif field == 'log_type':
                headers.append('Log Type')
            elif field == 'severity':
                headers.append('Severity')
            elif field == 'status':
                headers.append('Status')
            elif field == 'error_message':
                headers.append('Error Message')
            elif field == 'error_type':
                headers.append('Error Type')
            elif field == 'module':
                headers.append('Module')
            elif field == 'function':
                headers.append('Function')
            elif field == 'user':
                headers.append('User')
            elif field == 'execution_time':
                headers.append('Execution Time (s)')
            elif field == 'tags':
                headers.append('Tags')
            elif field == 'environment':
                headers.append('Environment')
        
        if include_metadata:
            if include_stack_trace:
                headers.append('Stack Trace')
            if include_context_data:
                headers.append('Context Data')
            headers.extend(['User IP', 'Request Method', 'Request URL'])
        
        writer.writerow(headers)
    
    for log in logs:
        row = []
        for field in fields_to_include:
            if field == 'timestamp':
                row.append(log.timestamp.strftime('%Y-%m-%d %H:%M:%S'))
            elif field == 'log_type':
                row.append(log.get_log_type_display())
            elif field == 'severity':
                row.append(log.get_severity_display())
            elif field == 'status':
                row.append(log.get_status_display())
            elif field == 'error_message':
                row.append(log.error_message)
            elif field == 'error_type':
                row.append(log.error_type or '')
            elif field == 'module':
                row.append(log.module or '')
            elif field == 'function':
                row.append(log.function or '')
            elif field == 'user':
                row.append(log.user.username if log.user else 'System')
            elif field == 'execution_time':
                row.append(float(log.execution_time) if log.execution_time else '')
            elif field == 'tags':
                row.append(', '.join(log.tags) if log.tags else '')
            elif field == 'environment':
                row.append(log.environment or '')
        
        if include_metadata:
            if include_stack_trace:
                row.append(log.stack_trace or '')
            if include_context_data:
                row.append(json.dumps(log.context_data) if log.context_data else '')
            row.extend([
                log.user_ip or '',
                log.request_method or '',
                log.request_url or ''
            ])
        
        writer.writerow(row)
    
    return response


def export_to_json(logs, include_metadata, include_stack_trace, include_context_data, fields_to_include, filename_prefix):
    """Export logs to JSON format"""
    data = []
    
    for log in logs:
        log_data = {}
        for field in fields_to_include:
            if field == 'timestamp':
                log_data['timestamp'] = log.timestamp.isoformat()
            elif field == 'log_type':
                log_data['log_type'] = log.get_log_type_display()
            elif field == 'severity':
                log_data['severity'] = log.get_severity_display()
            elif field == 'status':
                log_data['status'] = log.get_status_display()
            elif field == 'error_message':
                log_data['error_message'] = log.error_message
            elif field == 'error_type':
                log_data['error_type'] = log.error_type
            elif field == 'module':
                log_data['module'] = log.module
            elif field == 'function':
                log_data['function'] = log.function
            elif field == 'user':
                log_data['user'] = log.user.username if log.user else 'System'
            elif field == 'execution_time':
                log_data['execution_time'] = float(log.execution_time) if log.execution_time else None
            elif field == 'tags':
                log_data['tags'] = log.tags
            elif field == 'environment':
                log_data['environment'] = log.environment
        
        if include_metadata:
            if include_stack_trace:
                log_data['stack_trace'] = log.stack_trace
            if include_context_data:
                log_data['context_data'] = log.context_data
            log_data.update({
                'user_ip': log.user_ip,
                'request_method': log.request_method,
                'request_url': log.request_url,
                'memory_usage': log.memory_usage,
                'cpu_usage': float(log.cpu_usage) if log.cpu_usage else None,
            })
        
        data.append(log_data)
    
    response = HttpResponse(
        json.dumps(data, indent=2, default=str),
        content_type='application/json'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename_prefix}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json"'
    
    return response


def export_to_xml(logs, include_metadata, include_stack_trace, include_context_data, fields_to_include, filename_prefix):
    """Export logs to XML format"""
    from xml.etree.ElementTree import Element, SubElement, tostring
    from xml.dom import minidom
    
    root = Element('system_logs')
    root.set('exported_at', timezone.now().isoformat())
    root.set('total_records', str(logs.count()))
    
    for log in logs:
        log_elem = SubElement(root, 'log_entry')
        
        for field in fields_to_include:
            if field == 'timestamp':
                SubElement(log_elem, 'timestamp').text = log.timestamp.isoformat()
            elif field == 'log_type':
                SubElement(log_elem, 'log_type').text = log.get_log_type_display()
            elif field == 'severity':
                SubElement(log_elem, 'severity').text = log.get_severity_display()
            elif field == 'status':
                SubElement(log_elem, 'status').text = log.get_status_display()
            elif field == 'error_message':
                SubElement(log_elem, 'error_message').text = log.error_message
            elif field == 'error_type':
                if log.error_type:
                    SubElement(log_elem, 'error_type').text = log.error_type
            elif field == 'module':
                if log.module:
                    SubElement(log_elem, 'module').text = log.module
            elif field == 'function':
                if log.function:
                    SubElement(log_elem, 'function').text = log.function
            elif field == 'user':
                SubElement(log_elem, 'user').text = log.user.username if log.user else 'System'
            elif field == 'execution_time':
                if log.execution_time:
                    SubElement(log_elem, 'execution_time').text = str(log.execution_time)
            elif field == 'tags':
                if log.tags:
                    tags_elem = SubElement(log_elem, 'tags')
                    for tag in log.tags:
                        SubElement(tags_elem, 'tag').text = tag
            elif field == 'environment':
                if log.environment:
                    SubElement(log_elem, 'environment').text = log.environment
        
        if include_metadata:
            if include_stack_trace and log.stack_trace:
                SubElement(log_elem, 'stack_trace').text = log.stack_trace
            if include_context_data and log.context_data:
                SubElement(log_elem, 'context_data').text = json.dumps(log.context_data)
    
    # Pretty print XML
    rough_string = tostring(root, 'unicode')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    response = HttpResponse(pretty_xml, content_type='application/xml')
    response['Content-Disposition'] = f'attachment; filename="{filename_prefix}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xml"'
    
    return response


def export_to_pdf(logs, include_metadata, include_stack_trace, include_context_data, fields_to_include, filename_prefix):
    """Export logs to PDF format"""
    # This would require a PDF library like reportlab or weasyprint
    # For now, return a simple text response
    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="{filename_prefix}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.txt"'
    
    content = f"System Logs Export\n"
    content += f"Generated: {timezone.now()}\n"
    content += f"Total Records: {logs.count()}\n\n"
    
    for log in logs:
        content += f"Timestamp: {log.timestamp}\n"
        content += f"Log Type: {log.get_log_type_display()}\n"
        content += f"Severity: {log.get_severity_display()}\n"
        content += f"Status: {log.get_status_display()}\n"
        content += f"Error Message: {log.error_message}\n"
        if log.module:
            content += f"Module: {log.module}\n"
        if log.function:
            content += f"Function: {log.function}\n"
        if log.user:
            content += f"User: {log.user.username}\n"
        if log.execution_time:
            content += f"Execution Time: {log.execution_time}s\n"
        if log.tags:
            content += f"Tags: {', '.join(log.tags)}\n"
        content += "-" * 50 + "\n"
    
    response.write(content)
    return response


@login_required
@permission_required('system_logs.view_systemlog')
def system_log_chart_data(request):
    """
    AJAX endpoint for chart data
    """
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Get daily activity data
    daily_stats = SystemLog.objects.filter(
        timestamp__range=(start_date, end_date)
    ).extra(
        select={'date': 'DATE(timestamp)'}
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    # Get log type distribution
    log_type_stats = SystemLog.objects.filter(
        timestamp__range=(start_date, end_date)
    ).values('log_type').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Get severity distribution
    severity_stats = SystemLog.objects.filter(
        timestamp__range=(start_date, end_date)
    ).values('severity').annotate(
        count=Count('id')
    ).order_by('severity')
    
    # Get module distribution
    module_stats = SystemLog.objects.filter(
        timestamp__range=(start_date, end_date)
    ).values('module').annotate(
        count=Count('id')
    ).exclude(module='').order_by('-count')[:10]
    
    data = {
        'daily_stats': list(daily_stats),
        'log_type_stats': list(log_type_stats),
        'severity_stats': list(severity_stats),
        'module_stats': list(module_stats),
    }
    
    return JsonResponse(data)


@login_required
@permission_required('system_logs.change_systemlog')
def bulk_action(request):
    """
    Handle bulk actions on system logs
    """
    if request.method == 'POST':
        form = BulkActionForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            selected_logs = form.cleaned_data['selected_logs']
            
            if not selected_logs:
                messages.error(request, 'No logs selected for bulk action.')
                return redirect('system_logs:system_log_list')
            
            try:
                log_ids = json.loads(selected_logs)
                logs = SystemLog.objects.filter(id__in=log_ids)
                
                if action == 'resolve':
                    notes = form.cleaned_data.get('resolution_notes', '')
                    for log in logs:
                        log.resolve(request.user, notes)
                    messages.success(request, f'{logs.count()} logs marked as resolved.')
                
                elif action == 'ignore':
                    logs.update(status='IGNORED')
                    messages.success(request, f'{logs.count()} logs marked as ignored.')
                
                elif action == 'escalate':
                    level = form.cleaned_data.get('escalation_level', 1)
                    for log in logs:
                        log.escalate(level)
                    messages.success(request, f'{logs.count()} logs escalated to level {level}.')
                
                elif action == 'archive':
                    logs.update(status='ARCHIVED')
                    messages.success(request, f'{logs.count()} logs archived successfully.')
                
                elif action == 'delete':
                    logs.delete()
                    messages.success(request, f'{logs.count()} logs deleted successfully.')
                
                elif action == 'export':
                    # Redirect to export with selected IDs
                    return redirect(f"{reverse_lazy('system_logs:system_log_export')}?selected_ids={selected_logs}")
                
                elif action == 'add_tags':
                    tags = [tag.strip() for tag in form.cleaned_data['tags'].split(',')]
                    for log in logs:
                        for tag in tags:
                            log.add_tag(tag)
                    messages.success(request, f'Tags added to {logs.count()} logs successfully.')
                
                elif action == 'remove_tags':
                    tags = [tag.strip() for tag in form.cleaned_data['tags'].split(',')]
                    for log in logs:
                        for tag in tags:
                            log.remove_tag(tag)
                    messages.success(request, f'Tags removed from {logs.count()} logs successfully.')
                
                elif action == 'assign_user':
                    user = form.cleaned_data.get('assign_user')
                    if user:
                        logs.update(resolved_by=user)
                        messages.success(request, f'{logs.count()} logs assigned to {user.username}.')
                
            except (json.JSONDecodeError, ValueError):
                messages.error(request, 'Invalid log selection data.')
            
        else:
            messages.error(request, 'Invalid bulk action form data.')
    
    return redirect('system_logs:system_log_list')


# Error Pattern Views
class ErrorPatternListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = ErrorPattern
    template_name = 'system_logs/error_pattern_list.html'
    context_object_name = 'patterns'
    permission_required = 'system_logs.view_errorpattern'
    paginate_by = 20


class ErrorPatternDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = ErrorPattern
    template_name = 'system_logs/error_pattern_detail.html'
    context_object_name = 'pattern'
    permission_required = 'system_logs.view_errorpattern'


class ErrorPatternCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = ErrorPattern
    template_name = 'system_logs/error_pattern_form.html'
    form_class = ErrorPatternForm
    permission_required = 'system_logs.add_errorpattern'
    success_url = reverse_lazy('system_logs:error_pattern_list')


class ErrorPatternUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = ErrorPattern
    template_name = 'system_logs/error_pattern_form.html'
    form_class = ErrorPatternForm
    permission_required = 'system_logs.change_errorpattern'
    success_url = reverse_lazy('system_logs:error_pattern_list')


class ErrorPatternDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = ErrorPattern
    template_name = 'system_logs/error_pattern_confirm_delete.html'
    permission_required = 'system_logs.delete_errorpattern'
    success_url = reverse_lazy('system_logs:error_pattern_list')


# Debug Session Views
class DebugSessionListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = DebugSession
    template_name = 'system_logs/debug_session_list.html'
    context_object_name = 'sessions'
    permission_required = 'system_logs.view_debugsession'
    paginate_by = 20


class DebugSessionDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = DebugSession
    template_name = 'system_logs/debug_session_detail.html'
    context_object_name = 'session'
    permission_required = 'system_logs.view_debugsession'


class DebugSessionCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = DebugSession
    template_name = 'system_logs/debug_session_form.html'
    form_class = DebugSessionForm
    permission_required = 'system_logs.add_debugsession'
    success_url = reverse_lazy('system_logs:debug_session_list')


class DebugSessionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = DebugSession
    template_name = 'system_logs/debug_session_form.html'
    form_class = DebugSessionForm
    permission_required = 'system_logs.change_debugsession'
    success_url = reverse_lazy('system_logs:debug_session_list')


class DebugSessionDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = DebugSession
    template_name = 'system_logs/debug_session_confirm_delete.html'
    permission_required = 'system_logs.delete_debugsession'
    success_url = reverse_lazy('system_logs:debug_session_list')


# Log Retention Policy Views
class LogRetentionPolicyListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = LogRetentionPolicy
    template_name = 'system_logs/log_retention_policy_list.html'
    context_object_name = 'policies'
    permission_required = 'system_logs.view_logretentionpolicy'
    paginate_by = 20


class LogRetentionPolicyCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = LogRetentionPolicy
    template_name = 'system_logs/log_retention_policy_form.html'
    form_class = LogRetentionPolicyForm
    permission_required = 'system_logs.add_logretentionpolicy'
    success_url = reverse_lazy('system_logs:log_retention_policy_list')


class LogRetentionPolicyUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = LogRetentionPolicy
    template_name = 'system_logs/log_retention_policy_form.html'
    form_class = LogRetentionPolicyForm
    permission_required = 'system_logs.change_logretentionpolicy'
    success_url = reverse_lazy('system_logs:log_retention_policy_list')


class LogRetentionPolicyDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = LogRetentionPolicy
    template_name = 'system_logs/log_retention_policy_confirm_delete.html'
    permission_required = 'system_logs.delete_logretentionpolicy'
    success_url = reverse_lazy('system_logs:log_retention_policy_list')


@login_required
@permission_required('system_logs.view_systemlog')
def log_retention_cleanup(request):
    """
    Manual trigger for log retention cleanup
    """
    if request.method == 'POST':
        # Get active retention policies
        policies = LogRetentionPolicy.objects.filter(is_active=True)
        
        cleaned_count = 0
        for policy in policies:
            if policy.retention_type == 'TIME_BASED' and policy.retention_value > 0:
                cutoff_date = timezone.now() - timedelta(days=policy.retention_value)
                
                # Build filter based on policy criteria
                filter_kwargs = {'timestamp__lt': cutoff_date}
                
                if policy.severity_levels:
                    filter_kwargs['severity__in'] = policy.severity_levels
                if policy.log_types:
                    filter_kwargs['log_type__in'] = policy.log_types
                if policy.modules:
                    filter_kwargs['module__in'] = policy.modules
                if policy.tags:
                    # Complex tag filtering
                    tag_filter = Q()
                    for tag in policy.tags:
                        tag_filter |= Q(tags__contains=[tag])
                    filter_kwargs = {**filter_kwargs, **{'tags__contains': policy.tags}}
                
                # Apply policy action
                old_logs = SystemLog.objects.filter(**filter_kwargs)
                
                if policy.action_type == 'ARCHIVE':
                    archived_count = old_logs.update(status='ARCHIVED')
                    cleaned_count += archived_count
                elif policy.action_type == 'DELETE':
                    deleted_count = old_logs.count()
                    old_logs.delete()
                    cleaned_count += deleted_count
                elif policy.action_type == 'COMPRESS':
                    # This would require additional implementation for compression
                    pass
                
                # Update policy statistics
                policy.last_executed = timezone.now()
                policy.last_processed_count = old_logs.count()
                policy.total_processed += old_logs.count()
                policy.save()
        
        messages.success(request, f'{cleaned_count} logs processed based on retention policies.')
    
    return redirect('system_logs:dashboard')
