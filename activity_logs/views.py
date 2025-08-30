from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Max, Min
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import csv
from datetime import datetime, timedelta

from .models import (
    ActivityLog, AuditTrail, SecurityEvent, ComplianceReport,
    RetentionPolicy, AlertRule
)
from .forms import (
    ActivityLogSearchForm, AuditTrailSearchForm, SecurityEventSearchForm,
    ComplianceReportForm, RetentionPolicyForm, AlertRuleForm,
    SecurityEventResponseForm
)


# Dashboard Views
@login_required
@permission_required('activity_logs.view_activitylog')
def dashboard(request):
    """
    Main dashboard for activity logs and audit trail system
    """
    # Get current date and calculate date ranges
    now = timezone.now()
    today = now.date()
    yesterday = today - timedelta(days=1)
    last_7_days = today - timedelta(days=7)
    last_30_days = today - timedelta(days=30)
    
    # Activity statistics
    total_logs = ActivityLog.objects.count()
    today_logs = ActivityLog.objects.filter(timestamp__date=today).count()
    yesterday_logs = ActivityLog.objects.filter(timestamp__date=yesterday).count()
    last_7_days_logs = ActivityLog.objects.filter(timestamp__date__gte=last_7_days).count()
    last_30_days_logs = ActivityLog.objects.filter(timestamp__date__gte=last_30_days).count()
    
    # Activity by type
    activity_by_type = ActivityLog.objects.values('activity_type').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Top users
    top_users = ActivityLog.objects.values('user__username').annotate(
        count=Count('id')
    ).exclude(user__isnull=True).order_by('-count')[:10]
    
    # Top modules
    top_modules = ActivityLog.objects.values('module').annotate(
        count=Count('id')
    ).exclude(module='').order_by('-count')[:10]
    
    # Security events
    security_events = SecurityEvent.objects.filter(
        is_resolved=False
    ).order_by('-timestamp')[:5]
    
    # Recent activity
    recent_activity = ActivityLog.objects.select_related('user').order_by('-timestamp')[:10]
    
    # Compliance status
    compliance_reports = ComplianceReport.objects.filter(
        is_approved=True
    ).order_by('-generated_at')[:5]
    
    context = {
        'total_logs': total_logs,
        'today_logs': today_logs,
        'yesterday_logs': yesterday_logs,
        'last_7_days_logs': last_7_days_logs,
        'last_30_days_logs': last_30_days_logs,
        'activity_by_type': activity_by_type,
        'top_users': top_users,
        'top_modules': top_modules,
        'security_events': security_events,
        'recent_activity': recent_activity,
        'compliance_reports': compliance_reports,
    }
    
    return render(request, 'activity_logs/dashboard.html', context)


# Activity Log Views
class ActivityLogListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    List view for activity logs with search and filtering
    """
    model = ActivityLog
    template_name = 'activity_logs/activity_log_list.html'
    context_object_name = 'activity_logs'
    permission_required = 'activity_logs.view_activitylog'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = ActivityLog.objects.select_related('user', 'content_type').order_by('-timestamp')
        
        # Get search form
        form = ActivityLogSearchForm(self.request.GET)
        if form.is_valid():
            # Apply filters
            if form.cleaned_data.get('start_date'):
                queryset = queryset.filter(timestamp__date__gte=form.cleaned_data['start_date'])
            
            if form.cleaned_data.get('end_date'):
                queryset = queryset.filter(timestamp__date__lte=form.cleaned_data['end_date'])
            
            if form.cleaned_data.get('user'):
                queryset = queryset.filter(user=form.cleaned_data['user'])
            
            if form.cleaned_data.get('activity_type'):
                queryset = queryset.filter(activity_type=form.cleaned_data['activity_type'])
            
            if form.cleaned_data.get('log_level'):
                queryset = queryset.filter(log_level=form.cleaned_data['log_level'])
            
            if form.cleaned_data.get('module'):
                queryset = queryset.filter(module__icontains=form.cleaned_data['module'])
            
            if form.cleaned_data.get('action'):
                queryset = queryset.filter(action__icontains=form.cleaned_data['action'])
            
            if form.cleaned_data.get('is_sensitive'):
                is_sensitive = form.cleaned_data['is_sensitive'] == 'True'
                queryset = queryset.filter(is_sensitive=is_sensitive)
            
            if form.cleaned_data.get('compliance_category'):
                queryset = queryset.filter(
                    compliance_category__icontains=form.cleaned_data['compliance_category']
                )
            
            if form.cleaned_data.get('user_ip'):
                queryset = queryset.filter(user_ip=form.cleaned_data['user_ip'])
            
            if form.cleaned_data.get('tags'):
                tags = [tag.strip() for tag in form.cleaned_data['tags'].split(',')]
                for tag in tags:
                    queryset = queryset.filter(tags__contains=[tag])
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ActivityLogSearchForm(self.request.GET)
        return context


class ActivityLogDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """
    Detail view for individual activity log entries
    """
    model = ActivityLog
    template_name = 'activity_logs/activity_log_detail.html'
    context_object_name = 'activity_log'
    permission_required = 'activity_logs.view_activitylog'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get related audit trails
        context['audit_trails'] = self.object.audit_trails.all()
        
        # Get related security events
        context['security_events'] = self.object.security_events.all()
        
        return context


class ActivityLogCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Create view for activity logs
    """
    model = ActivityLog
    template_name = 'activity_logs/activity_log_form.html'
    permission_required = 'activity_logs.add_activitylog'
    success_url = reverse_lazy('activity_logs:activity_log_list')
    fields = ['activity_type', 'action', 'description', 'module', 'log_level', 'is_sensitive', 'tags']


class ActivityLogUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Update view for activity logs
    """
    model = ActivityLog
    template_name = 'activity_logs/activity_log_form.html'
    permission_required = 'activity_logs.change_activitylog'
    success_url = reverse_lazy('activity_logs:activity_log_list')
    fields = ['activity_type', 'action', 'description', 'module', 'log_level', 'is_sensitive', 'tags']


class ActivityLogDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Delete view for activity logs
    """
    model = ActivityLog
    template_name = 'activity_logs/activity_log_confirm_delete.html'
    permission_required = 'activity_logs.delete_activitylog'
    success_url = reverse_lazy('activity_logs:activity_log_list')





def export_to_csv(queryset, fields):
    """Export queryset to CSV format"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="activity_logs_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    header = []
    for field in fields:
        if field == 'user':
            header.append('Username')
        elif field == 'old_values':
            header.append('Old Values')
        elif field == 'new_values':
            header.append('New Values')
        elif field == 'tags':
            header.append('Tags')
        else:
            header.append(field.replace('_', ' ').title())
    
    writer.writerow(header)
    
    # Write data
    for log in queryset:
        row = []
        for field in fields:
            if field == 'user':
                row.append(log.user.username if log.user else 'System')
            elif field == 'timestamp':
                row.append(log.timestamp.strftime('%Y-%m-%d %H:%M:%S'))
            elif field == 'old_values':
                row.append(json.dumps(log.old_values) if log.old_values else '')
            elif field == 'new_values':
                row.append(json.dumps(log.new_values) if log.new_values else '')
            elif field == 'tags':
                row.append(', '.join(log.tags) if log.tags and isinstance(log.tags, list) else '')
            else:
                value = getattr(log, field, '')
                row.append(str(value) if value is not None else '')
        
        writer.writerow(row)
    
    return response


def export_to_json(queryset, fields):
    """Export queryset to JSON format"""
    response = HttpResponse(content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="activity_logs_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json"'
    
    data = []
    for log in queryset:
        log_data = {}
        for field in fields:
            if field == 'user':
                log_data[field] = log.user.username if log.user else 'System'
            elif field == 'timestamp':
                log_data[field] = log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            elif field == 'old_values':
                log_data[field] = log.old_values if log.old_values else None
            elif field == 'new_values':
                log_data[field] = log.new_values if log.new_values else None
            elif field == 'tags':
                log_data[field] = log.tags if log.tags and isinstance(log.tags, list) else []
            else:
                log_data[field] = getattr(log, field, None)
        data.append(log_data)
    
    response.write(json.dumps(data, indent=2, default=str))
    return response


@login_required
@permission_required('activity_logs.view_activitylog')
def activity_log_export_csv(request):
    """Direct CSV export of activity logs with current filters"""
    # Get filtered queryset based on request parameters
    queryset = ActivityLog.objects.select_related('user').order_by('-timestamp')
    
    # Apply filters from request parameters
    user_id = request.GET.get('user')
    if user_id:
        queryset = queryset.filter(user_id=user_id)
    
    activity_type = request.GET.get('activity_type')
    if activity_type:
        queryset = queryset.filter(activity_type=activity_type)
    
    log_level = request.GET.get('log_level')
    if log_level:
        queryset = queryset.filter(log_level=log_level)
    
    module = request.GET.get('module')
    if module:
        queryset = queryset.filter(module__icontains=module)
    
    action = request.GET.get('action')
    if action:
        queryset = queryset.filter(action__icontains=action)
    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date and end_date:
        queryset = queryset.filter(timestamp__date__range=[start_date, end_date])
    
    # Default fields for CSV export
    fields = ['timestamp', 'user', 'activity_type', 'action', 'module', 'description']
    
    return export_to_csv(queryset, fields)


@login_required
@permission_required('activity_logs.view_activitylog')
def activity_log_export_json(request):
    """Direct JSON export of activity logs with current filters"""
    # Get filtered queryset based on request parameters
    queryset = ActivityLog.objects.select_related('user').order_by('-timestamp')
    
    # Apply filters from request parameters
    user_id = request.GET.get('user')
    if user_id:
        queryset = queryset.filter(user_id=user_id)
    
    activity_type = request.GET.get('activity_type')
    if activity_type:
        queryset = queryset.filter(activity_type=activity_type)
    
    log_level = request.GET.get('log_level')
    if log_level:
        queryset = queryset.filter(log_level=log_level)
    
    module = request.GET.get('module')
    if module:
        queryset = queryset.filter(module__icontains=module)
    
    action = request.GET.get('action')
    if action:
        queryset = queryset.filter(action__icontains=action)
    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date and end_date:
        queryset = queryset.filter(timestamp__date__range=[start_date, end_date])
    
    # Default fields for JSON export
    fields = ['timestamp', 'user', 'activity_type', 'action', 'module', 'description', 'user_ip', 'tags']
    
    return export_to_json(queryset, fields)


def export_to_xml(queryset, fields):
    """Export queryset to XML format"""
    response = HttpResponse(content_type='application/xml')
    response['Content-Disposition'] = f'attachment; filename="activity_logs_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xml"'
    
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<activity_logs>\n'
    
    for log in queryset:
        xml_content += '  <log>\n'
        for field in fields:
            if field == 'user':
                value = log.user.username if log.user else 'System'
            elif field == 'timestamp':
                value = log.timestamp.isoformat()
            elif field in ['old_values', 'new_values']:
                value = json.dumps(getattr(log, field)) if getattr(log, field) else ''
            elif field == 'tags':
                value = ', '.join(log.tags) if log.tags and isinstance(log.tags, list) else ''
            else:
                value = str(getattr(log, field, '')) if getattr(log, field) is not None else ''
            
            xml_content += f'    <{field}>{value}</{field}>\n'
        
        xml_content += '  </log>\n'
    
    xml_content += '</activity_logs>'
    response.write(xml_content)
    return response


def export_to_pdf(queryset, fields):
    """Export queryset to PDF format"""
    # This would require a PDF library like ReportLab or WeasyPrint
    # For now, return a simple message
    response = HttpResponse("PDF export not yet implemented", content_type='text/plain')
    return response


# Audit Trail Views
class AuditTrailListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    List view for audit trails
    """
    model = AuditTrail
    template_name = 'activity_logs/audit_trail_list.html'
    context_object_name = 'audit_trails'
    permission_required = 'activity_logs.view_audittrail'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = AuditTrail.objects.select_related('content_type').prefetch_related('activity_logs').order_by('-start_date')
        
        # Get search form
        form = AuditTrailSearchForm(self.request.GET)
        if form.is_valid():
            if form.cleaned_data.get('trail_name'):
                queryset = queryset.filter(trail_name__icontains=form.cleaned_data['trail_name'])
            
            if form.cleaned_data.get('trail_type'):
                queryset = queryset.filter(trail_type=form.cleaned_data['trail_type'])
            
            if form.cleaned_data.get('start_date'):
                queryset = queryset.filter(start_date__date__gte=form.cleaned_data['start_date'])
            
            if form.cleaned_data.get('end_date'):
                queryset = queryset.filter(start_date__date__lte=form.cleaned_data['end_date'])
            
            if form.cleaned_data.get('content_type'):
                queryset = queryset.filter(content_type=form.cleaned_data['content_type'])
            
            if form.cleaned_data.get('object_id'):
                queryset = queryset.filter(object_id=form.cleaned_data['object_id'])
            
            if form.cleaned_data.get('compliance_requirements'):
                queryset = queryset.filter(
                    compliance_requirements__contains=form.cleaned_data['compliance_requirements']
                )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = AuditTrailSearchForm(self.request.GET)
        return context


class AuditTrailDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """
    Detail view for audit trails
    """
    model = AuditTrail
    template_name = 'activity_logs/audit_trail_detail.html'
    context_object_name = 'audit_trail'
    permission_required = 'activity_logs.view_audittrail'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get related activity logs
        context['activity_logs'] = self.object.activity_logs.select_related('user').order_by('-timestamp')
        
        return context


class AuditTrailCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Create view for audit trails
    """
    model = AuditTrail
    template_name = 'activity_logs/audit_trail_form.html'
    permission_required = 'activity_logs.add_audittrail'
    success_url = reverse_lazy('activity_logs:audit_trail_list')
    fields = ['trail_name', 'trail_type', 'description', 'content_type', 'object_id']


class AuditTrailUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Update view for audit trails
    """
    model = AuditTrail
    template_name = 'activity_logs/audit_trail_form.html'
    permission_required = 'activity_logs.change_audittrail'
    success_url = reverse_lazy('activity_logs:audit_trail_list')
    fields = ['trail_name', 'trail_type', 'description', 'content_type', 'object_id']


class AuditTrailDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Delete view for audit trails
    """
    model = AuditTrail
    template_name = 'activity_logs/audit_trail_confirm_delete.html'
    permission_required = 'activity_logs.delete_audittrail'
    success_url = reverse_lazy('activity_logs:audit_trail_list')


# Security Event Views
class SecurityEventListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    List view for security events
    """
    model = SecurityEvent
    template_name = 'activity_logs/security_event_list.html'
    context_object_name = 'security_events'
    permission_required = 'activity_logs.view_securityevent'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = SecurityEvent.objects.select_related('user', 'resolved_by').order_by('-timestamp')
        
        # Get search form
        form = SecurityEventSearchForm(self.request.GET)
        if form.is_valid():
            if form.cleaned_data.get('event_type'):
                queryset = queryset.filter(event_type=form.cleaned_data['event_type'])
            
            if form.cleaned_data.get('severity'):
                queryset = queryset.filter(severity=form.cleaned_data['severity'])
            
            if form.cleaned_data.get('start_date'):
                queryset = queryset.filter(timestamp__date__gte=form.cleaned_data['start_date'])
            
            if form.cleaned_data.get('end_date'):
                queryset = queryset.filter(timestamp__date__lte=form.cleaned_data['end_date'])
            
            if form.cleaned_data.get('user'):
                queryset = queryset.filter(user=form.cleaned_data['user'])
            
            if form.cleaned_data.get('source_ip'):
                queryset = queryset.filter(source_ip=form.cleaned_data['source_ip'])
            
            if form.cleaned_data.get('is_resolved'):
                is_resolved = form.cleaned_data['is_resolved'] == 'True'
                queryset = queryset.filter(is_resolved=is_resolved)
            
            if form.cleaned_data.get('title'):
                queryset = queryset.filter(title__icontains=form.cleaned_data['title'])
            
            if form.cleaned_data.get('description'):
                queryset = queryset.filter(description__icontains=form.cleaned_data['description'])
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = SecurityEventSearchForm(self.request.GET)
        return context


class SecurityEventDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """
    Detail view for security events
    """
    model = SecurityEvent
    template_name = 'activity_logs/security_event_detail.html'
    context_object_name = 'security_event'
    permission_required = 'activity_logs.view_securityevent'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get related activity logs
        context['related_logs'] = self.object.related_logs.select_related('user').order_by('-timestamp')
        
        # Get response form
        context['response_form'] = SecurityEventResponseForm()
        
        return context


@login_required
@permission_required('activity_logs.change_securityevent')
def security_event_response(request, pk):
    """
    Handle security event response actions
    """
    security_event = get_object_or_404(SecurityEvent, pk=pk)
    
    if request.method == 'POST':
        form = SecurityEventResponseForm(request.POST)
        if form.is_valid():
            response_action = form.cleaned_data['response_action']
            resolution_notes = form.cleaned_data['resolution_notes']
            
            # Handle different response actions
            if response_action == 'mark_resolved':
                security_event.is_resolved = True
                security_event.resolution_notes = resolution_notes
                security_event.resolved_by = request.user
                security_event.resolved_at = timezone.now()
                security_event.save()
                
                messages.success(request, 'Security event marked as resolved.')
                
            elif response_action == 'escalate':
                # Create a new security event for escalation
                SecurityEvent.objects.create(
                    event_type='ANOMALOUS_ACTIVITY',
                    severity='HIGH',
                    title=f'Escalated: {security_event.title}',
                    description=f'Event escalated from {security_event.event_type}. Original: {security_event.description}',
                    source_ip=security_event.source_ip,
                    user=request.user
                )
                
                messages.success(request, 'Security event escalated.')
                
            elif response_action == 'custom':
                custom_action = form.cleaned_data['custom_action']
                security_event.resolution_notes = f"Custom action: {custom_action}\n\n{resolution_notes}"
                security_event.save()
                
                messages.success(request, 'Custom action recorded.')
            
            # Notify selected users if any
            notify_users = form.cleaned_data.get('notify_users', [])
            if notify_users:
                # This would integrate with your notification system
                pass
            
            return redirect('activity_logs:security_event_detail', pk=pk)
    
    return redirect('activity_logs:security_event_detail', pk=pk)


class SecurityEventCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Create view for security events
    """
    model = SecurityEvent
    template_name = 'activity_logs/security_event_form.html'
    permission_required = 'activity_logs.add_securityevent'
    success_url = reverse_lazy('activity_logs:security_event_list')
    fields = ['event_type', 'severity', 'title', 'description', 'source_ip', 'source_location', 'details']


class SecurityEventUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Update view for security events
    """
    model = SecurityEvent
    template_name = 'activity_logs/security_event_form.html'
    permission_required = 'activity_logs.change_securityevent'
    success_url = reverse_lazy('activity_logs:security_event_list')
    fields = ['event_type', 'severity', 'title', 'description', 'source_ip', 'source_location', 'details']


class SecurityEventDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Delete view for security events
    """
    model = SecurityEvent
    template_name = 'activity_logs/security_event_confirm_delete.html'
    permission_required = 'activity_logs.delete_securityevent'
    success_url = reverse_lazy('activity_logs:security_event_list')


# Compliance Report Views
class ComplianceReportListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    List view for compliance reports
    """
    model = ComplianceReport
    template_name = 'activity_logs/compliance_report_list.html'
    context_object_name = 'compliance_reports'
    permission_required = 'activity_logs.view_compliancereport'
    paginate_by = 20


class ComplianceReportDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """
    Detail view for compliance reports
    """
    model = ComplianceReport
    template_name = 'activity_logs/compliance_report_detail.html'
    context_object_name = 'compliance_report'
    permission_required = 'activity_logs.view_compliancereport'


class ComplianceReportCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Create view for compliance reports
    """
    model = ComplianceReport
    form_class = ComplianceReportForm
    template_name = 'activity_logs/compliance_report_form.html'
    permission_required = 'activity_logs.add_compliancereport'
    success_url = reverse_lazy('activity_logs:compliance_report_list')
    
    def form_valid(self, form):
        form.instance.generated_by = self.request.user
        return super().form_valid(form)


class ComplianceReportUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Update view for compliance reports
    """
    model = ComplianceReport
    form_class = ComplianceReportForm
    template_name = 'activity_logs/compliance_report_form.html'
    permission_required = 'activity_logs.change_compliancereport'
    success_url = reverse_lazy('activity_logs:compliance_report_list')


class ComplianceReportDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Delete view for compliance reports
    """
    model = ComplianceReport
    template_name = 'activity_logs/compliance_report_confirm_delete.html'
    permission_required = 'activity_logs.delete_compliancereport'
    success_url = reverse_lazy('activity_logs:compliance_report_list')


# Retention Policy Views
class RetentionPolicyListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    List view for retention policies
    """
    model = RetentionPolicy
    template_name = 'activity_logs/retention_policy_list.html'
    context_object_name = 'retention_policies'
    permission_required = 'activity_logs.view_retentionpolicy'


class RetentionPolicyDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """
    Detail view for retention policies
    """
    model = RetentionPolicy
    template_name = 'activity_logs/retention_policy_detail.html'
    context_object_name = 'retention_policy'
    permission_required = 'activity_logs.view_retentionpolicy'


class RetentionPolicyCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Create view for retention policies
    """
    model = RetentionPolicy
    form_class = RetentionPolicyForm
    template_name = 'activity_logs/retention_policy_form.html'
    permission_required = 'activity_logs.add_retentionpolicy'
    success_url = reverse_lazy('activity_logs:retention_policy_list')


class RetentionPolicyUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Update view for retention policies
    """
    model = RetentionPolicy
    form_class = RetentionPolicyForm
    template_name = 'activity_logs/retention_policy_form.html'
    permission_required = 'activity_logs.change_retentionpolicy'
    success_url = reverse_lazy('activity_logs:retention_policy_list')


class RetentionPolicyDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Delete view for retention policies
    """
    model = RetentionPolicy
    template_name = 'activity_logs/retention_policy_confirm_delete.html'
    permission_required = 'activity_logs.delete_retentionpolicy'
    success_url = reverse_lazy('activity_logs:retention_policy_list')


# Alert Rule Views
class AlertRuleListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    List view for alert rules
    """
    model = AlertRule
    template_name = 'activity_logs/alert_rule_list.html'
    context_object_name = 'alert_rules'
    permission_required = 'activity_logs.view_alertrule'


class AlertRuleDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """
    Detail view for alert rules
    """
    model = AlertRule
    template_name = 'activity_logs/alert_rule_detail.html'
    context_object_name = 'alert_rule'
    permission_required = 'activity_logs.view_alertrule'


class AlertRuleCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Create view for alert rules
    """
    model = AlertRule
    form_class = AlertRuleForm
    template_name = 'activity_logs/alert_rule_form.html'
    permission_required = 'activity_logs.add_alertrule'
    success_url = reverse_lazy('activity_logs:alert_rule_list')


class AlertRuleUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Update view for alert rules
    """
    model = AlertRule
    form_class = AlertRuleForm
    template_name = 'activity_logs/alert_rule_form.html'
    permission_required = 'activity_logs.change_alertrule'
    success_url = reverse_lazy('activity_logs:alert_rule_list')


class AlertRuleDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Delete view for alert rules
    """
    model = AlertRule
    template_name = 'activity_logs/alert_rule_confirm_delete.html'
    permission_required = 'activity_logs.delete_alertrule'
    success_url = reverse_lazy('activity_logs:alert_rule_list')


# API Views for AJAX
@login_required
@permission_required('activity_logs.view_activitylog')
def activity_log_chart_data(request):
    """
    AJAX endpoint for chart data
    """
    # Get date range from request
    days = int(request.GET.get('days', 30))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Get activity counts by date
    activity_data = ActivityLog.objects.filter(
        timestamp__date__range=[start_date, end_date]
    ).extra(
        select={'date': 'date(timestamp)'}
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    # Format data for chart
    dates = []
    counts = []
    
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date.strftime('%Y-%m-%d'))
        
        # Find count for this date
        count = 0
        for item in activity_data:
            if item['date'] == current_date.strftime('%Y-%m-%d'):
                count = item['count']
                break
        
        counts.append(count)
        current_date += timedelta(days=1)
    
    return JsonResponse({
        'dates': dates,
        'counts': counts
    })


@login_required
@permission_required('activity_logs.view_securityevent')
def security_event_chart_data(request):
    """
    AJAX endpoint for security event chart data
    """
    # Get date range from request
    days = int(request.GET.get('days', 30))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Get security events by severity
    severity_data = SecurityEvent.objects.filter(
        timestamp__date__range=[start_date, end_date]
    ).values('severity').annotate(
        count=Count('id')
    ).order_by('severity')
    
    # Get security events by type
    type_data = SecurityEvent.objects.filter(
        timestamp__date__range=[start_date, end_date]
    ).values('event_type').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    return JsonResponse({
        'severity_data': list(severity_data),
        'type_data': list(type_data)
    })


# Utility Views
@login_required
@permission_required('activity_logs.view_activitylog')
def object_audit_trail(request, content_type_id, object_id):
    """
    View audit trail for a specific object
    """
    content_type = get_object_or_404(ContentType, id=content_type_id)
    
    # Get all activity logs for this object
    activity_logs = ActivityLog.objects.filter(
        content_type=content_type,
        object_id=object_id
    ).select_related('user').order_by('-timestamp')
    
    # Get or create audit trail
    audit_trail, created = AuditTrail.objects.get_or_create(
        content_type=content_type,
        object_id=object_id,
        defaults={
            'trail_name': f"Audit Trail for {content_type.model} #{object_id}",
            'trail_type': 'DATA',
            'description': f"Complete audit trail for {content_type.model} with ID {object_id}"
        }
    )
    
    # Add activity logs to audit trail
    audit_trail.activity_logs.add(*activity_logs)
    
    context = {
        'content_type': content_type,
        'object_id': object_id,
        'activity_logs': activity_logs,
        'audit_trail': audit_trail,
    }
    
    return render(request, 'activity_logs/object_audit_trail.html', context)


@login_required
@permission_required('activity_logs.view_activitylog')
def user_activity_summary(request, user_id):
    """
    View activity summary for a specific user
    """
    user = get_object_or_404(User, id=user_id)
    
    # Get user's activity logs
    activity_logs = ActivityLog.objects.filter(user=user).order_by('-timestamp')
    
    # Get activity statistics
    activity_stats = activity_logs.values('activity_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Get module statistics
    module_stats = activity_logs.values('module').annotate(
        count=Count('id')
    ).exclude(module='').order_by('-count')
    
    # Get recent activity
    recent_activity = activity_logs[:20]
    
    context = {
        'user': user,
        'activity_logs': activity_logs,
        'activity_stats': activity_stats,
        'module_stats': module_stats,
        'recent_activity': recent_activity,
    }
    
    return render(request, 'activity_logs/user_activity_summary.html', context)
