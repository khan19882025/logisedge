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
from .models import LogHistory, LogCategory, LogFilter, LogExport, LogRetentionPolicy
from .forms import (
    LogHistorySearchForm, LogHistoryExportForm, LogFilterForm, 
    LogCategoryForm, LogRetentionPolicyForm, BulkActionForm
)


@login_required
@permission_required('log_history.view_loghistory')
def dashboard(request):
    """
    Dashboard view showing log history overview and statistics
    """
    # Get date range from request or default to last 30 days
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Get log statistics
    logs = LogHistory.objects.filter(
        timestamp__range=(start_date, end_date),
        status=LogHistory.STATUS_ACTIVE
    )
    
    # Action type statistics
    action_stats = logs.values('action_type').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Severity statistics
    severity_stats = logs.values('severity').annotate(
        count=Count('id')
    ).order_by('severity')
    
    # User activity statistics
    user_stats = logs.values('user__username').annotate(
        count=Count('id')
    ).exclude(user__isnull=True).order_by('-count')[:10]
    
    # Module statistics
    module_stats = logs.values('module').annotate(
        count=Count('id')
    ).exclude(module='').order_by('-count')[:10]
    
    # Recent activity
    recent_logs = logs.order_by('-timestamp')[:20]
    
    # Error logs (high severity)
    error_logs = logs.filter(
        severity__in=[LogHistory.SEVERITY_HIGH, LogHistory.SEVERITY_CRITICAL]
    ).order_by('-timestamp')[:10]
    
    # Performance metrics
    avg_execution_time = logs.aggregate(
        avg_time=Avg('execution_time')
    )['avg_time'] or 0
    
    context = {
        'days': days,
        'action_stats': action_stats,
        'severity_stats': severity_stats,
        'user_stats': user_stats,
        'module_stats': module_stats,
        'recent_logs': recent_logs,
        'error_logs': error_logs,
        'avg_execution_time': avg_execution_time,
        'total_logs': logs.count(),
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'log_history/dashboard.html', context)


class LogHistoryListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    List view for log history entries with advanced filtering and search
    """
    model = LogHistory
    template_name = 'log_history/log_history_list.html'
    context_object_name = 'logs'
    permission_required = 'log_history.view_loghistory'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = LogHistory.objects.filter(status=LogHistory.STATUS_ACTIVE)
        
        # Apply search filters
        form = LogHistorySearchForm(self.request.GET)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            
            # Date range filter
            if cleaned_data.get('date_from'):
                queryset = queryset.filter(timestamp__date__gte=cleaned_data['date_from'])
            if cleaned_data.get('date_to'):
                queryset = queryset.filter(timestamp__date__lte=cleaned_data['date_to'])
            
            # Action type filter
            if cleaned_data.get('action_type'):
                queryset = queryset.filter(action_type=cleaned_data['action_type'])
            
            # Severity filter
            if cleaned_data.get('severity'):
                queryset = queryset.filter(severity=cleaned_data['severity'])
            
            # User filter
            if cleaned_data.get('user'):
                queryset = queryset.filter(user=cleaned_data['user'])
            
            # Object type filter
            if cleaned_data.get('object_type'):
                queryset = queryset.filter(object_type__icontains=cleaned_data['object_type'])
            
            # Object name filter
            if cleaned_data.get('object_name'):
                queryset = queryset.filter(object_name__icontains=cleaned_data['object_name'])
            
            # Module filter
            if cleaned_data.get('module'):
                queryset = queryset.filter(module__icontains=cleaned_data['module'])
            
            # Function filter
            if cleaned_data.get('function'):
                queryset = queryset.filter(function__icontains=cleaned_data['function'])
            
            # Description filter
            if cleaned_data.get('description'):
                queryset = queryset.filter(description__icontains=cleaned_data['description'])
            
            # Tags filter
            if cleaned_data.get('tags'):
                tags = [tag.strip() for tag in cleaned_data['tags'].split(',')]
                for tag in tags:
                    queryset = queryset.filter(tags__contains=[tag])
        
        return queryset.select_related('user', 'content_type').order_by('-timestamp')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = LogHistorySearchForm(self.request.GET)
        context['bulk_action_form'] = BulkActionForm()
        
        # Get saved filters for current user
        if self.request.user.is_authenticated:
            context['saved_filters'] = LogFilter.objects.filter(
                Q(user=self.request.user) | Q(is_public=True)
            ).order_by('name')
        
        return context


class LogHistoryDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """
    Detail view for individual log history entries
    """
    model = LogHistory
    template_name = 'log_history/log_history_detail.html'
    context_object_name = 'log'
    permission_required = 'log_history.view_loghistory'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get related logs (same user, same object, etc.)
        log = self.get_object()
        
        # Related logs by user
        context['user_logs'] = LogHistory.objects.filter(
            user=log.user,
            timestamp__gte=log.timestamp - timedelta(days=1)
        ).exclude(id=log.id).order_by('-timestamp')[:10]
        
        # Related logs by object
        if log.content_type and log.object_id:
            context['object_logs'] = LogHistory.objects.filter(
                content_type=log.content_type,
                object_id=log.object_id
            ).exclude(id=log.id).order_by('-timestamp')[:10]
        
        # Related logs by module
        if log.module:
            context['module_logs'] = LogHistory.objects.filter(
                module=log.module,
                timestamp__gte=log.timestamp - timedelta(days=7)
            ).exclude(id=log.id).order_by('-timestamp')[:10]
        
        return context


@login_required
@permission_required('log_history.view_loghistory')
def log_history_search(request):
    """
    Advanced search view for log history
    """
    form = LogHistorySearchForm(request.GET)
    logs = []
    
    if form.is_valid():
        logs = LogHistory.objects.filter(status=LogHistory.STATUS_ACTIVE)
        cleaned_data = form.cleaned_data
        
        # Apply all filters
        if cleaned_data.get('date_from'):
            logs = logs.filter(timestamp__date__gte=cleaned_data['date_from'])
        if cleaned_data.get('date_to'):
            logs = logs.filter(timestamp__date__lte=cleaned_data['date_to'])
        if cleaned_data.get('action_type'):
            logs = logs.filter(action_type=cleaned_data['action_type'])
        if cleaned_data.get('severity'):
            logs = logs.filter(severity=cleaned_data['severity'])
        if cleaned_data.get('user'):
            logs = logs.filter(user=cleaned_data['user'])
        if cleaned_data.get('object_type'):
            logs = logs.filter(object_type__icontains=cleaned_data['object_type'])
        if cleaned_data.get('object_name'):
            logs = logs.filter(object_name__icontains=cleaned_data['object_name'])
        if cleaned_data.get('module'):
            logs = logs.filter(module__icontains=cleaned_data['module'])
        if cleaned_data.get('function'):
            logs = logs.filter(function__icontains=cleaned_data['function'])
        if cleaned_data.get('description'):
            logs = logs.filter(description__icontains=cleaned_data['description'])
        if cleaned_data.get('tags'):
            tags = [tag.strip() for tag in cleaned_data['tags'].split(',')]
            for tag in tags:
                logs = logs.filter(tags__contains=[tag])
        
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
    
    return render(request, 'log_history/log_history_search.html', context)


@login_required
@permission_required('log_history.view_loghistory')
def log_history_export(request):
    """
    Export log history data in various formats
    """
    if request.method == 'POST':
        form = LogHistoryExportForm(request.POST)
        if form.is_valid():
            export_format = form.cleaned_data['export_format']
            include_headers = form.cleaned_data['include_headers']
            include_metadata = form.cleaned_data['include_metadata']
            max_records = form.cleaned_data['max_records']
            filename_prefix = form.cleaned_data['filename_prefix']
            
            # Get filtered data from search parameters
            search_form = LogHistorySearchForm(request.POST)
            logs = LogHistory.objects.filter(status=LogHistory.STATUS_ACTIVE)
            
            if search_form.is_valid():
                cleaned_data = search_form.cleaned_data
                # Apply filters (same logic as search)
                if cleaned_data.get('date_from'):
                    logs = logs.filter(timestamp__date__gte=cleaned_data['date_from'])
                if cleaned_data.get('date_to'):
                    logs = logs.filter(timestamp__date__lte=cleaned_data['date_to'])
                if cleaned_data.get('action_type'):
                    logs = logs.filter(action_type=cleaned_data['action_type'])
                if cleaned_data.get('severity'):
                    logs = logs.filter(severity=cleaned_data['severity'])
                if cleaned_data.get('user'):
                    logs = logs.filter(user=cleaned_data['user'])
                if cleaned_data.get('object_type'):
                    logs = logs.filter(object_type__icontains=cleaned_data['object_type'])
                if cleaned_data.get('object_name'):
                    logs = logs.filter(object_name__icontains=cleaned_data['object_name'])
                if cleaned_data.get('module'):
                    logs = logs.filter(module__icontains=cleaned_data['module'])
                if cleaned_data.get('function'):
                    logs = logs.filter(function__icontains=cleaned_data['function'])
                if cleaned_data.get('description'):
                    logs = logs.filter(description__icontains=cleaned_data['description'])
                if cleaned_data.get('tags'):
                    tags = [tag.strip() for tag in cleaned_data['tags'].split(',')]
                    for tag in tags:
                        logs = logs.filter(tags__contains=[tag])
            
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
                return export_to_csv(logs, include_headers, include_metadata, filename_prefix)
            elif export_format == 'JSON':
                return export_to_json(logs, include_metadata, filename_prefix)
            elif export_format == 'XML':
                return export_to_xml(logs, include_metadata, filename_prefix)
            elif export_format == 'PDF':
                return export_to_pdf(logs, include_metadata, filename_prefix)
    
    # GET request - show export form
    form = LogHistoryExportForm()
    search_form = LogHistorySearchForm(request.GET)
    
    context = {
        'form': form,
        'search_form': search_form,
    }
    
    return render(request, 'log_history/log_history_export.html', context)


def export_to_csv(logs, include_headers, include_metadata, filename_prefix):
    """Export logs to CSV format"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename_prefix}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    if include_headers:
        headers = [
            'ID', 'Timestamp', 'Action Type', 'Severity', 'User', 'User IP',
            'Object Type', 'Object Name', 'Description', 'Module', 'Function'
        ]
        if include_metadata:
            headers.extend(['Tags', 'Details', 'Before Values', 'After Values', 'Changed Fields'])
        writer.writerow(headers)
    
    for log in logs:
        row = [
            str(log.id), log.timestamp, log.action_type, log.severity,
            log.user.username if log.user else 'System',
            log.user_ip or '', log.object_type or '', log.object_name or '',
            log.description, log.module or '', log.function or ''
        ]
        
        if include_metadata:
            row.extend([
                ', '.join(log.tags) if log.tags else '',
                json.dumps(log.details) if log.details else '',
                json.dumps(log.before_values) if log.before_values else '',
                json.dumps(log.after_values) if log.after_values else '',
                ', '.join(log.changed_fields) if log.changed_fields else ''
            ])
        
        writer.writerow(row)
    
    return response


def export_to_json(logs, include_metadata, filename_prefix):
    """Export logs to JSON format"""
    data = []
    
    for log in logs:
        log_data = {
            'id': str(log.id),
            'timestamp': log.timestamp.isoformat(),
            'action_type': log.action_type,
            'severity': log.severity,
            'user': log.user.username if log.user else 'System',
            'user_ip': log.user_ip,
            'object_type': log.object_type,
            'object_name': log.object_name,
            'description': log.description,
            'module': log.module,
            'function': log.function,
        }
        
        if include_metadata:
            log_data.update({
                'tags': log.tags,
                'details': log.details,
                'before_values': log.before_values,
                'after_values': log.after_values,
                'changed_fields': log.changed_fields,
                'execution_time': float(log.execution_time) if log.execution_time else None,
                'memory_usage': log.memory_usage,
            })
        
        data.append(log_data)
    
    response = HttpResponse(
        json.dumps(data, indent=2, default=str),
        content_type='application/json'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename_prefix}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json"'
    
    return response


def export_to_xml(logs, include_metadata, filename_prefix):
    """Export logs to XML format"""
    from xml.etree.ElementTree import Element, SubElement, tostring
    from xml.dom import minidom
    
    root = Element('log_history')
    root.set('exported_at', timezone.now().isoformat())
    root.set('total_records', str(logs.count()))
    
    for log in logs:
        log_elem = SubElement(root, 'log_entry')
        SubElement(log_elem, 'id').text = str(log.id)
        SubElement(log_elem, 'timestamp').text = log.timestamp.isoformat()
        SubElement(log_elem, 'action_type').text = log.action_type
        SubElement(log_elem, 'severity').text = log.severity
        SubElement(log_elem, 'user').text = log.user.username if log.user else 'System'
        SubElement(log_elem, 'description').text = log.description
        
        if include_metadata:
            if log.tags:
                tags_elem = SubElement(log_elem, 'tags')
                for tag in log.tags:
                    SubElement(tags_elem, 'tag').text = tag
            
            if log.details:
                SubElement(log_elem, 'details').text = json.dumps(log.details)
    
    # Pretty print XML
    rough_string = tostring(root, 'unicode')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    response = HttpResponse(pretty_xml, content_type='application/xml')
    response['Content-Disposition'] = f'attachment; filename="{filename_prefix}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xml"'
    
    return response


def export_to_pdf(logs, include_metadata, filename_prefix):
    """Export logs to PDF format"""
    # This would require a PDF library like reportlab or weasyprint
    # For now, return a simple text response
    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="{filename_prefix}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.txt"'
    
    content = f"Log History Export\n"
    content += f"Generated: {timezone.now()}\n"
    content += f"Total Records: {logs.count()}\n\n"
    
    for log in logs:
        content += f"ID: {log.id}\n"
        content += f"Timestamp: {log.timestamp}\n"
        content += f"Action: {log.action_type}\n"
        content += f"Severity: {log.severity}\n"
        content += f"User: {log.user.username if log.user else 'System'}\n"
        content += f"Description: {log.description}\n"
        content += f"Module: {log.module or 'N/A'}\n"
        content += "-" * 50 + "\n"
    
    response.write(content)
    return response


@login_required
@permission_required('log_history.view_loghistory')
def log_history_chart_data(request):
    """
    AJAX endpoint for chart data
    """
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Get daily activity data
    daily_stats = LogHistory.objects.filter(
        timestamp__range=(start_date, end_date),
        status=LogHistory.STATUS_ACTIVE
    ).extra(
        select={'date': 'DATE(timestamp)'}
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    # Get action type distribution
    action_stats = LogHistory.objects.filter(
        timestamp__range=(start_date, end_date),
        status=LogHistory.STATUS_ACTIVE
    ).values('action_type').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Get severity distribution
    severity_stats = LogHistory.objects.filter(
        timestamp__range=(start_date, end_date),
        status=LogHistory.STATUS_ACTIVE
    ).values('severity').annotate(
        count=Count('id')
    ).order_by('severity')
    
    data = {
        'daily_stats': list(daily_stats),
        'action_stats': list(action_stats),
        'severity_stats': list(severity_stats),
    }
    
    return JsonResponse(data)


@login_required
@permission_required('log_history.change_loghistory')
def bulk_action(request):
    """
    Handle bulk actions on log entries
    """
    if request.method == 'POST':
        form = BulkActionForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            selected_logs = form.cleaned_data['selected_logs']
            
            if not selected_logs:
                messages.error(request, 'No logs selected for bulk action.')
                return redirect('log_history:log_history_list')
            
            try:
                log_ids = json.loads(selected_logs)
                logs = LogHistory.objects.filter(id__in=log_ids)
                
                if action == 'archive':
                    logs.update(status=LogHistory.STATUS_ARCHIVED)
                    messages.success(request, f'{logs.count()} logs archived successfully.')
                
                elif action == 'delete':
                    logs.update(status=LogHistory.STATUS_DELETED)
                    messages.success(request, f'{logs.count()} logs deleted successfully.')
                
                elif action == 'export':
                    # Redirect to export with selected IDs
                    return redirect(f"{reverse_lazy('log_history:log_history_export')}?selected_ids={selected_logs}")
                
                elif action == 'tag':
                    tags = [tag.strip() for tag in form.cleaned_data['tags'].split(',')]
                    for log in logs:
                        current_tags = log.tags or []
                        for tag in tags:
                            if tag not in current_tags:
                                current_tags.append(tag)
                        log.tags = current_tags
                        log.save(update_fields=['tags', 'updated_at'])
                    messages.success(request, f'Tags added to {logs.count()} logs successfully.')
                
                elif action == 'untag':
                    tags = [tag.strip() for tag in form.cleaned_data['tags'].split(',')]
                    for log in logs:
                        current_tags = log.tags or []
                        for tag in tags:
                            if tag in current_tags:
                                current_tags.remove(tag)
                        log.tags = current_tags
                        log.save(update_fields=['tags', 'updated_at'])
                    messages.success(request, f'Tags removed from {logs.count()} logs successfully.')
                
            except (json.JSONDecodeError, ValueError):
                messages.error(request, 'Invalid log selection data.')
            
        else:
            messages.error(request, 'Invalid bulk action form data.')
    
    return redirect('log_history:log_history_list')


# Management Views
class LogCategoryListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = LogCategory
    template_name = 'log_history/log_category_list.html'
    context_object_name = 'categories'
    permission_required = 'log_history.view_logcategory'
    paginate_by = 20


class LogCategoryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = LogCategory
    template_name = 'log_history/log_category_form.html'
    form_class = LogCategoryForm
    permission_required = 'log_history.add_logcategory'
    success_url = reverse_lazy('log_history:log_category_list')


class LogCategoryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = LogCategory
    template_name = 'log_history/log_category_form.html'
    form_class = LogCategoryForm
    permission_required = 'log_history.change_logcategory'
    success_url = reverse_lazy('log_history:log_category_list')


class LogCategoryDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = LogCategory
    template_name = 'log_history/log_category_confirm_delete.html'
    permission_required = 'log_history.delete_logcategory'
    success_url = reverse_lazy('log_history:log_category_list')


class LogRetentionPolicyListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = LogRetentionPolicy
    template_name = 'log_history/log_retention_policy_list.html'
    context_object_name = 'policies'
    permission_required = 'log_history.view_logretentionpolicy'
    paginate_by = 20


class LogRetentionPolicyCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = LogRetentionPolicy
    template_name = 'log_history/log_retention_policy_form.html'
    form_class = LogRetentionPolicyForm
    permission_required = 'log_history.add_logretentionpolicy'
    success_url = reverse_lazy('log_history:log_retention_policy_list')


class LogRetentionPolicyUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = LogRetentionPolicy
    template_name = 'log_history/log_retention_policy_form.html'
    form_class = LogRetentionPolicyForm
    permission_required = 'log_history.change_logretentionpolicy'
    success_url = reverse_lazy('log_history:log_retention_policy_list')


class LogRetentionPolicyDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = LogRetentionPolicy
    template_name = 'log_history/log_retention_policy_confirm_delete.html'
    permission_required = 'log_history.delete_logretentionpolicy'
    success_url = reverse_lazy('log_history:log_retention_policy_list')


@login_required
@permission_required('log_history.view_loghistory')
def log_retention_cleanup(request):
    """
    Manual trigger for log retention cleanup
    """
    if request.method == 'POST':
        # Get active retention policies
        policies = LogRetentionPolicy.objects.filter(is_active=True)
        
        cleaned_count = 0
        for policy in policies:
            if policy.retention_period > 0:  # Skip forever policies
                cutoff_date = timezone.now() - timedelta(days=policy.retention_period)
                
                # Build filter based on policy criteria
                filter_kwargs = {'timestamp__lt': cutoff_date}
                
                if policy.action_type:
                    filter_kwargs['action_type'] = policy.action_type
                if policy.severity:
                    filter_kwargs['severity'] = policy.severity
                if policy.module:
                    filter_kwargs['module'] = policy.module
                
                # Archive old logs
                old_logs = LogHistory.objects.filter(**filter_kwargs)
                archived_count = old_logs.update(status=LogHistory.STATUS_ARCHIVED)
                cleaned_count += archived_count
        
        messages.success(request, f'{cleaned_count} logs archived based on retention policies.')
    
    return redirect('log_history:dashboard')
