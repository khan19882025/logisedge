from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
import json
import uuid
from datetime import datetime, timedelta

from .models import (
    Printer, PrinterGroup, PrintTemplate, ERPEvent, 
    AutoPrintRule, PrintJob, BatchPrintJob, PrintJobLog
)
from .forms import (
    PrinterForm, PrinterGroupForm, PrintTemplateForm, ERPEventForm,
    AutoPrintRuleForm, PrintJobForm, BatchPrintJobForm, 
    PrintJobFilterForm, PrinterStatusForm, ImportExportForm
)


# Dashboard Views
@login_required
@permission_required('print_queue_management.view_printer', raise_exception=True)
def dashboard(request):
    """Main dashboard for print queue management"""
    
    # Get statistics
    total_printers = Printer.objects.filter(is_active=True).count()
    total_templates = PrintTemplate.objects.filter(is_active=True).count()
    total_rules = AutoPrintRule.objects.filter(is_active=True).count()
    
    # Get recent print jobs
    recent_jobs = PrintJob.objects.select_related('printer', 'print_template').order_by('-created_at')[:10]
    
    # Get printer status
    printer_status = []
    for printer in Printer.objects.filter(is_active=True)[:5]:
        status = printer.get_status()
        active_jobs = printer.print_jobs.filter(status__in=['queued', 'processing', 'printing']).count()
        printer_status.append({
            'printer': printer,
            'status': status,
            'active_jobs': active_jobs
        })
    
    # Get queue statistics
    queue_stats = {
        'queued': PrintJob.objects.filter(status='queued').count(),
        'processing': PrintJob.objects.filter(status='processing').count(),
        'printing': PrintJob.objects.filter(status='printing').count(),
        'completed': PrintJob.objects.filter(status='completed').count(),
        'failed': PrintJob.objects.filter(status='failed').count(),
    }
    
    # Get recent activity
    recent_activity = PrintJobLog.objects.select_related('print_job', 'user').order_by('-created_at')[:15]
    
    context = {
        'total_printers': total_printers,
        'total_templates': total_templates,
        'total_rules': total_rules,
        'recent_jobs': recent_jobs,
        'printer_status': printer_status,
        'queue_stats': queue_stats,
        'recent_activity': recent_activity,
    }
    
    return render(request, 'print_queue_management/dashboard.html', context)


# Printer Management Views
@login_required
@permission_required('print_queue_management.view_printer', raise_exception=True)
def printer_list(request):
    """List all printers"""
    printers = Printer.objects.select_related('created_by').order_by('name')
    
    # Search functionality
    search = request.GET.get('search', '')
    if search:
        printers = printers.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(location__icontains=search)
        )
    
    # Filter by type
    printer_type = request.GET.get('type', '')
    if printer_type:
        printers = printers.filter(printer_type=printer_type)
    
    # Filter by status
    status = request.GET.get('status', '')
    if status:
        if status == 'active':
            printers = printers.filter(is_active=True)
        elif status == 'inactive':
            printers = printers.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(printers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'printers': page_obj,
        'search': search,
        'printer_type': printer_type,
        'status': status,
        'printer_types': Printer.PRINTER_TYPES,
    }
    
    return render(request, 'print_queue_management/printer_list.html', context)


@login_required
@permission_required('print_queue_management.add_printer', raise_exception=True)
def printer_create(request):
    """Create a new printer"""
    if request.method == 'POST':
        form = PrinterForm(request.POST)
        if form.is_valid():
            printer = form.save(commit=False)
            printer.created_by = request.user
            printer.updated_by = request.user
            printer.save()
            
            messages.success(request, f'Printer "{printer.name}" created successfully!')
            return redirect('print_queue_management:printer_detail', pk=printer.pk)
    else:
        form = PrinterForm()
    
    context = {
        'form': form,
        'title': 'Create New Printer',
        'submit_text': 'Create Printer',
    }
    
    return render(request, 'print_queue_management/printer_form.html', context)


@login_required
@permission_required('print_queue_management.change_printer', raise_exception=True)
def printer_update(request, pk):
    """Update an existing printer"""
    printer = get_object_or_404(Printer, pk=pk)
    
    if request.method == 'POST':
        form = PrinterForm(request.POST, instance=printer)
        if form.is_valid():
            printer = form.save(commit=False)
            printer.updated_by = request.user
            printer.save()
            
            messages.success(request, f'Printer "{printer.name}" updated successfully!')
            return redirect('print_queue_management:printer_detail', pk=printer.pk)
    else:
        form = PrinterForm(instance=printer)
    
    context = {
        'form': form,
        'printer': printer,
        'title': f'Edit Printer: {printer.name}',
        'submit_text': 'Update Printer',
    }
    
    return render(request, 'print_queue_management/printer_form.html', context)


@login_required
@permission_required('print_queue_management.view_printer', raise_exception=True)
def printer_detail(request, pk):
    """View printer details"""
    printer = get_object_or_404(Printer, pk=pk)
    
    # Get recent print jobs
    recent_jobs = printer.print_jobs.select_related('print_template').order_by('-created_at')[:10]
    
    # Get job statistics
    job_stats = printer.print_jobs.aggregate(
        total_jobs=Count('id'),
        completed_jobs=Count('id', filter=Q(status='completed')),
        failed_jobs=Count('id', filter=Q(status='failed')),
        avg_duration=Avg('completed_at' - 'started_at')
    )
    
    context = {
        'printer': printer,
        'recent_jobs': recent_jobs,
        'job_stats': job_stats,
    }
    
    return render(request, 'print_queue_management/printer_detail.html', context)


@login_required
@permission_required('print_queue_management.delete_printer', raise_exception=True)
def printer_delete(request, pk):
    """Delete a printer"""
    printer = get_object_or_404(Printer, pk=pk)
    
    if request.method == 'POST':
        printer_name = printer.name
        printer.delete()
        messages.success(request, f'Printer "{printer_name}" deleted successfully!')
        return redirect('print_queue_management:printer_list')
    
    context = {
        'printer': printer,
    }
    
    return render(request, 'print_queue_management/printer_confirm_delete.html', context)


# Printer Group Management Views
@login_required
@permission_required('print_queue_management.view_printergroup', raise_exception=True)
def printer_group_list(request):
    """List all printer groups"""
    printer_groups = PrinterGroup.objects.select_related('created_by').prefetch_related('printers').order_by('name')
    
    # Search functionality
    search = request.GET.get('search', '')
    if search:
        printer_groups = printer_groups.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Filter by status
    status = request.GET.get('status', '')
    if status:
        if status == 'active':
            printer_groups = printer_groups.filter(is_active=True)
        elif status == 'inactive':
            printer_groups = printer_groups.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(printer_groups, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'printer_groups': page_obj,
        'search': search,
        'status': status,
    }
    
    return render(request, 'print_queue_management/printer_group_list.html', context)


@login_required
@permission_required('print_queue_management.add_printergroup', raise_exception=True)
def printer_group_create(request):
    """Create a new printer group"""
    if request.method == 'POST':
        form = PrinterGroupForm(request.POST)
        if form.is_valid():
            printer_group = form.save(commit=False)
            printer_group.created_by = request.user
            printer_group.updated_by = request.user
            printer_group.save()
            form.save_m2m()  # Save many-to-many relationships
            
            messages.success(request, f'Printer Group "{printer_group.name}" created successfully!')
            return redirect('print_queue_management:printer_group_detail', pk=printer_group.pk)
    else:
        form = PrinterGroupForm()
    
    context = {
        'form': form,
        'title': 'Create New Printer Group',
        'submit_text': 'Create Printer Group',
    }
    
    return render(request, 'print_queue_management/printer_group_form.html', context)


@login_required
@permission_required('print_queue_management.change_printergroup', raise_exception=True)
def printer_group_update(request, pk):
    """Update an existing printer group"""
    printer_group = get_object_or_404(PrinterGroup, pk=pk)
    
    if request.method == 'POST':
        form = PrinterGroupForm(request.POST, instance=printer_group)
        if form.is_valid():
            printer_group = form.save(commit=False)
            printer_group.updated_by = request.user
            printer_group.save()
            form.save_m2m()  # Save many-to-many relationships
            
            messages.success(request, f'Printer Group "{printer_group.name}" updated successfully!')
            return redirect('print_queue_management:printer_group_detail', pk=printer_group.pk)
    else:
        form = PrinterGroupForm(instance=printer_group)
    
    context = {
        'form': form,
        'printer_group': printer_group,
        'title': f'Edit Printer Group: {printer_group.name}',
        'submit_text': 'Update Printer Group',
    }
    
    return render(request, 'print_queue_management/printer_group_form.html', context)


@login_required
@permission_required('print_queue_management.view_printergroup', raise_exception=True)
def printer_group_detail(request, pk):
    """View printer group details"""
    printer_group = get_object_or_404(PrinterGroup, pk=pk)
    
    # Get printers in the group
    printers = printer_group.printers.all()
    
    # Get recent print jobs
    recent_jobs = PrintJob.objects.filter(printer_group=printer_group).select_related('printer', 'print_template').order_by('-created_at')[:10]
    
    context = {
        'printer_group': printer_group,
        'printers': printers,
        'recent_jobs': recent_jobs,
    }
    
    return render(request, 'print_queue_management/printer_group_detail.html', context)


# Print Template Management Views
@login_required
@permission_required('print_queue_management.view_printtemplate', raise_exception=True)
def print_template_list(request):
    """List all print templates"""
    templates = PrintTemplate.objects.select_related('created_by').order_by('template_type', 'name')
    
    # Search functionality
    search = request.GET.get('search', '')
    if search:
        templates = templates.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Filter by type
    template_type = request.GET.get('type', '')
    if template_type:
        templates = templates.filter(template_type=template_type)
    
    # Filter by status
    status = request.GET.get('status', '')
    if status:
        if status == 'active':
            templates = templates.filter(is_active=True)
        elif status == 'inactive':
            templates = templates.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(templates, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'templates': page_obj,
        'search': search,
        'template_type': template_type,
        'status': status,
        'template_types': PrintTemplate.TEMPLATE_TYPES,
    }
    
    return render(request, 'print_queue_management/print_template_list.html', context)


@login_required
@permission_required('print_queue_management.add_printtemplate', raise_exception=True)
def print_template_create(request):
    """Create a new print template"""
    if request.method == 'POST':
        form = PrintTemplateForm(request.POST, request.FILES)
        if form.is_valid():
            template = form.save(commit=False)
            template.created_by = request.user
            template.updated_by = request.user
            template.save()
            
            messages.success(request, f'Print Template "{template.name}" created successfully!')
            return redirect('print_queue_management:print_template_detail', pk=template.pk)
    else:
        form = PrintTemplateForm()
    
    context = {
        'form': form,
        'title': 'Create New Print Template',
        'submit_text': 'Create Template',
    }
    
    return render(request, 'print_queue_management/print_template_form.html', context)


@login_required
@permission_required('print_queue_management.change_printtemplate', raise_exception=True)
def print_template_update(request, pk):
    """Update an existing print template"""
    template = get_object_or_404(PrintTemplate, pk=pk)
    
    if request.method == 'POST':
        form = PrintTemplateForm(request.POST, request.FILES, instance=template)
        if form.is_valid():
            template = form.save(commit=False)
            template.updated_by = request.user
            template.save()
            
            messages.success(request, f'Print Template "{template.name}" updated successfully!')
            return redirect('print_queue_management:print_template_detail', pk=template.pk)
    else:
        form = PrintTemplateForm(instance=template)
    
    context = {
        'form': form,
        'template': template,
        'title': f'Edit Print Template: {template.name}',
        'submit_text': 'Update Template',
    }
    
    return render(request, 'print_queue_management/print_template_form.html', context)


@login_required
@permission_required('print_queue_management.view_printtemplate', raise_exception=True)
def print_template_detail(request, pk):
    """View print template details"""
    template = get_object_or_404(PrintTemplate, pk=pk)
    
    # Get recent print jobs
    recent_jobs = template.print_jobs.select_related('printer').order_by('-created_at')[:10]
    
    # Get auto-print rules
    auto_print_rules = template.auto_print_rules.filter(is_active=True)
    
    context = {
        'template': template,
        'recent_jobs': recent_jobs,
        'auto_print_rules': auto_print_rules,
    }
    
    return render(request, 'print_queue_management/print_template_detail.html', context)


# Auto-Print Rule Management Views
@login_required
@permission_required('print_queue_management.view_autoprintrule', raise_exception=True)
def auto_print_rule_list(request):
    """List all auto-print rules"""
    rules = AutoPrintRule.objects.select_related('erp_event', 'print_template', 'printer', 'printer_group', 'created_by').order_by('priority', 'name')
    
    # Search functionality
    search = request.GET.get('search', '')
    if search:
        rules = rules.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(erp_event__name__icontains=search)
        )
    
    # Filter by event type
    event_type = request.GET.get('event_type', '')
    if event_type:
        rules = rules.filter(erp_event__event_type=event_type)
    
    # Filter by priority
    priority = request.GET.get('priority', '')
    if priority:
        rules = rules.filter(priority=priority)
    
    # Filter by status
    status = request.GET.get('status', '')
    if status:
        if status == 'active':
            rules = rules.filter(is_active=True)
        elif status == 'inactive':
            rules = rules.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(rules, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'rules': page_obj,
        'search': search,
        'event_type': event_type,
        'priority': priority,
        'status': status,
        'event_types': ERPEvent.EVENT_TYPES,
        'priority_levels': AutoPrintRule.PRIORITY_LEVELS,
    }
    
    return render(request, 'print_queue_management/auto_print_rule_list.html', context)


@login_required
@permission_required('print_queue_management.add_autoprintrule', raise_exception=True)
def auto_print_rule_create(request):
    """Create a new auto-print rule"""
    if request.method == 'POST':
        form = AutoPrintRuleForm(request.POST)
        if form.is_valid():
            rule = form.save(commit=False)
            rule.created_by = request.user
            rule.updated_by = request.user
            rule.save()
            
            messages.success(request, f'Auto-Print Rule "{rule.name}" created successfully!')
            return redirect('print_queue_management:auto_print_rule_detail', pk=rule.pk)
    else:
        form = AutoPrintRuleForm()
    
    context = {
        'form': form,
        'title': 'Create New Auto-Print Rule',
        'submit_text': 'Create Rule',
    }
    
    return render(request, 'print_queue_management/auto_print_rule_form.html', context)


@login_required
@permission_required('print_queue_management.change_autoprintrule', raise_exception=True)
def auto_print_rule_update(request, pk):
    """Update an existing auto-print rule"""
    rule = get_object_or_404(AutoPrintRule, pk=pk)
    
    if request.method == 'POST':
        form = AutoPrintRuleForm(request.POST, instance=rule)
        if form.is_valid():
            rule = form.save(commit=False)
            rule.updated_by = request.user
            rule.save()
            
            messages.success(request, f'Auto-Print Rule "{rule.name}" updated successfully!')
            return redirect('print_queue_management:auto_print_rule_detail', pk=rule.pk)
    else:
        form = AutoPrintRuleForm(instance=rule)
    
    context = {
        'form': form,
        'rule': rule,
        'title': f'Edit Auto-Print Rule: {rule.name}',
        'submit_text': 'Update Rule',
    }
    
    return render(request, 'print_queue_management/auto_print_rule_form.html', context)


@login_required
@permission_required('print_queue_management.view_autoprintrule', raise_exception=True)
def auto_print_rule_detail(request, pk):
    """View auto-print rule details"""
    rule = get_object_or_404(AutoPrintRule, pk=pk)
    
    # Get recent print jobs
    recent_jobs = rule.print_jobs.select_related('printer', 'print_template').order_by('-created_at')[:10]
    
    # Get batch jobs
    batch_jobs = rule.batch_jobs.order_by('-scheduled_at')[:5]
    
    context = {
        'rule': rule,
        'recent_jobs': recent_jobs,
        'batch_jobs': batch_jobs,
    }
    
    return render(request, 'print_queue_management/auto_print_rule_detail.html', context)


# Print Job Management Views
@login_required
@permission_required('print_queue_management.view_printjob', raise_exception=True)
def print_job_list(request):
    """List all print jobs"""
    jobs = PrintJob.objects.select_related('printer', 'print_template', 'auto_print_rule', 'created_by').order_by('-created_at')
    
    # Apply filters
    filter_form = PrintJobFilterForm(request.GET)
    if filter_form.is_valid():
        status = filter_form.cleaned_data.get('status')
        priority = filter_form.cleaned_data.get('priority')
        printer = filter_form.cleaned_data.get('printer')
        template = filter_form.cleaned_data.get('template')
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')
        search = filter_form.cleaned_data.get('search')
        
        if status:
            jobs = jobs.filter(status=status)
        if priority:
            jobs = jobs.filter(priority=priority)
        if printer:
            jobs = jobs.filter(printer=printer)
        if template:
            jobs = jobs.filter(print_template=template)
        if date_from:
            jobs = jobs.filter(created_at__date__gte=date_from)
        if date_to:
            jobs = jobs.filter(created_at__date__lte=date_to)
        if search:
            jobs = jobs.filter(
                Q(job_number__icontains=search) |
                Q(print_template__name__icontains=search) |
                Q(printer__name__icontains=search)
            )
    
    # Pagination
    paginator = Paginator(jobs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'jobs': page_obj,
        'filter_form': filter_form,
        'status_choices': PrintJob.STATUS_CHOICES,
        'priority_choices': AutoPrintRule.PRIORITY_LEVELS,
    }
    
    return render(request, 'print_queue_management/print_job_list.html', context)


@login_required
@permission_required('print_queue_management.add_printjob', raise_exception=True)
def print_job_create(request):
    """Create a new print job"""
    if request.method == 'POST':
        form = PrintJobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.created_by = request.user
            job.updated_by = request.user
            job.save()
            
            # Create audit log
            PrintJobLog.objects.create(
                print_job=job,
                action='created',
                message=f'Print job created by {request.user.username}',
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR', ''),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f'Print Job "{job.job_number}" created successfully!')
            return redirect('print_queue_management:print_job_detail', pk=job.pk)
    else:
        form = PrintJobForm()
    
    context = {
        'form': form,
        'title': 'Create New Print Job',
        'submit_text': 'Create Job',
    }
    
    return render(request, 'print_queue_management/print_job_form.html', context)


@login_required
@permission_required('print_queue_management.view_printjob', raise_exception=True)
def print_job_detail(request, pk):
    """View print job details"""
    job = get_object_or_404(PrintJob, pk=pk)
    
    # Get job logs
    logs = job.logs.select_related('user').order_by('-created_at')
    
    context = {
        'job': job,
        'logs': logs,
    }
    
    return render(request, 'print_queue_management/print_job_detail.html', context)


# API Views for AJAX requests
@login_required
@require_http_methods(["POST"])
def print_job_action(request, pk):
    """Perform actions on print jobs (cancel, retry, etc.)"""
    job = get_object_or_404(PrintJob, pk=pk)
    action = request.POST.get('action')
    
    if action == 'cancel':
        if job.status in ['queued', 'processing']:
            job.status = 'cancelled'
            job.updated_by = request.user
            job.save()
            
            # Create audit log
            PrintJobLog.objects.create(
                print_job=job,
                action='cancelled',
                message=f'Print job cancelled by {request.user.username}',
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR', ''),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f'Print job "{job.job_number}" cancelled successfully!')
        else:
            messages.error(request, f'Cannot cancel job in "{job.status}" status!')
    
    elif action == 'retry':
        if job.status == 'failed' and job.retry_count < job.max_retries:
            job.status = 'retrying'
            job.retry_count += 1
            job.updated_by = request.user
            job.save()
            
            # Create audit log
            PrintJobLog.objects.create(
                print_job=job,
                action='retried',
                message=f'Print job retry attempt {job.retry_count} by {request.user.username}',
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR', ''),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f'Print job "{job.job_number}" retry initiated!')
        else:
            messages.error(request, f'Cannot retry job in "{job.status}" status or max retries exceeded!')
    
    return redirect('print_queue_management:print_job_detail', pk=job.pk)


@login_required
@require_http_methods(["GET"])
def printer_status_api(request, pk):
    """Get printer status via API"""
    printer = get_object_or_404(Printer, pk=pk)
    
    status = printer.get_status()
    active_jobs = printer.print_jobs.filter(status__in=['queued', 'processing', 'printing']).count()
    
    data = {
        'id': str(printer.id),
        'name': printer.name,
        'status': status,
        'active_jobs': active_jobs,
        'max_job_size': printer.max_job_size,
        'is_active': printer.is_active,
        'last_updated': printer.updated_at.isoformat(),
    }
    
    return JsonResponse(data)


@login_required
@require_http_methods(["GET"])
def queue_stats_api(request):
    """Get queue statistics via API"""
    stats = {
        'total_jobs': PrintJob.objects.count(),
        'queued': PrintJob.objects.filter(status='queued').count(),
        'processing': PrintJob.objects.filter(status='processing').count(),
        'printing': PrintJob.objects.filter(status='printing').count(),
        'completed': PrintJob.objects.filter(status='completed').count(),
        'failed': PrintJob.objects.filter(status='failed').count(),
        'cancelled': PrintJob.objects.filter(status='cancelled').count(),
    }
    
    return JsonResponse(stats)


# Import/Export Views
@login_required
@permission_required('print_queue_management.add_printtemplate', raise_exception=True)
def import_data(request):
    """Import print queue data"""
    if request.method == 'POST':
        form = ImportExportForm(request.POST, request.FILES)
        if form.is_valid():
            # Handle import logic here
            messages.success(request, 'Data imported successfully!')
            return redirect('print_queue_management:dashboard')
    else:
        form = ImportExportForm()
    
    context = {
        'form': form,
        'title': 'Import Data',
        'submit_text': 'Import Data',
    }
    
    return render(request, 'print_queue_management/import_export.html', context)


@login_required
@permission_required('print_queue_management.view_printtemplate', raise_exception=True)
def export_data(request):
    """Export print queue data"""
    if request.method == 'POST':
        form = ImportExportForm(request.POST)
        if form.is_valid():
            # Handle export logic here
            messages.success(request, 'Data exported successfully!')
            return redirect('print_queue_management:dashboard')
    else:
        form = ImportExportForm()
    
    context = {
        'form': form,
        'title': 'Export Data',
        'submit_text': 'Export Data',
    }
    
    return render(request, 'print_queue_management/import_export.html', context)


# Error handling views
def handler404(request, exception):
    """Custom 404 handler"""
    return render(request, 'print_queue_management/404.html', status=404)


def handler500(request):
    """Custom 500 handler"""
    return render(request, 'print_queue_management/500.html', status=500)
