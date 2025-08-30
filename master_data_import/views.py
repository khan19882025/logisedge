import json
import pandas as pd
import hashlib
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.core.paginator import Paginator
from django.db import transaction, models
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
import tempfile
from datetime import datetime, timedelta

from .models import (
    ImportTemplate, ImportJob, ImportValidationRule, 
    ImportAuditLog, ImportDataError, ImportFile
)
from .forms import (
    ImportFileUploadForm, ImportTemplateForm, ImportValidationRuleForm,
    ColumnMappingForm, ImportPreviewForm, ImportJobFilterForm
)
from .utils import (
    validate_data, process_import, generate_template_file,
    get_client_ip, create_audit_log
)


@login_required
@permission_required('master_data_import.view_importjob')
def dashboard(request):
    """Main dashboard for Master Data Import module"""
    # Get statistics
    total_jobs = ImportJob.objects.count()
    completed_jobs = ImportJob.objects.filter(status='completed').count()
    failed_jobs = ImportJob.objects.filter(status='failed').count()
    pending_jobs = ImportJob.objects.filter(status='pending').count()
    
    # Recent jobs
    recent_jobs = ImportJob.objects.select_related('template', 'created_by').order_by('-created_at')[:10]
    
    # Job statistics by data type
    job_stats_by_type = ImportJob.objects.values('template__data_type').annotate(
        total=models.Count('id'),
        completed=models.Count('id', filter=models.Q(status='completed')),
        failed=models.Count('id', filter=models.Q(status='failed'))
    )
    
    # Recent audit logs
    recent_audit_logs = ImportAuditLog.objects.select_related('import_job').order_by('-timestamp')[:10]
    
    context = {
        'total_jobs': total_jobs,
        'completed_jobs': completed_jobs,
        'failed_jobs': failed_jobs,
        'pending_jobs': pending_jobs,
        'recent_jobs': recent_jobs,
        'job_stats_by_type': job_stats_by_type,
        'recent_audit_logs': recent_audit_logs,
    }
    
    return render(request, 'master_data_import/dashboard.html', context)


@login_required
@permission_required('master_data_import.add_importjob')
def upload_file(request):
    """Handle file upload and initial validation"""
    if request.method == 'POST':
        form = ImportFileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            template = form.cleaned_data['template']
            import_file = form.cleaned_data['import_file']
            job_name = form.cleaned_data['job_name']
            skip_errors = form.cleaned_data['skip_errors']
            preview_only = form.cleaned_data['preview_only']
            
            try:
                # Create import job
                import_job = ImportJob.objects.create(
                    job_name=job_name,
                    template=template,
                    file_name=import_file.name,
                    file_size=import_file.size,
                    created_by=request.user
                )
                
                # Save file
                import_file_obj = ImportFile.objects.create(
                    import_job=import_job,
                    file=import_file,
                    original_filename=import_file.name
                )
                
                # Create audit log
                create_audit_log(
                    import_job=import_job,
                    action='upload',
                    message=f'File uploaded: {import_file.name}',
                    request=request
                )
                
                # Read and validate file
                file_extension = os.path.splitext(import_file.name)[1].lower()
                
                if file_extension == '.csv':
                    df = pd.read_csv(import_file, encoding='utf-8')
                elif file_extension in ['.xlsx', '.xls']:
                    df = pd.read_excel(import_file)
                else:
                    raise ValueError("Unsupported file format")
                
                # Update job with row count
                import_job.total_rows = len(df)
                import_job.save()
                
                # Store file data in session for preview
                request.session['import_data'] = {
                    'job_id': str(import_job.id),
                    'columns': df.columns.tolist(),
                    'preview_data': df.head(10).to_dict('records'),
                    'total_rows': len(df),
                    'skip_errors': skip_errors,
                    'preview_only': preview_only
                }
                
                messages.success(request, f'File uploaded successfully. Found {len(df)} rows.')
                return redirect('master_data_import:column_mapping')
                
            except Exception as e:
                messages.error(request, f'Error uploading file: {str(e)}')
                if 'import_job' in locals():
                    import_job.delete()
    else:
        form = ImportFileUploadForm()
    
    context = {
        'form': form,
        'templates': ImportTemplate.objects.filter(is_active=True)
    }
    
    return render(request, 'master_data_import/upload.html', context)


@login_required
@permission_required('master_data_import.add_importjob')
def column_mapping(request):
    """Handle column mapping for uploaded file"""
    import_data = request.session.get('import_data')
    if not import_data:
        messages.error(request, 'No import data found. Please upload a file first.')
        return redirect('master_data_import:upload_file')
    
    import_job = get_object_or_404(ImportJob, id=import_data['job_id'])
    columns = import_data['columns']
    template_fields = list(import_job.template.column_mappings.keys())
    
    if request.method == 'POST':
        form = ColumnMappingForm(request.POST, columns=columns, template_fields=template_fields)
        if form.is_valid():
            # Create column mapping
            column_mapping = {}
            for column in columns:
                mapped_field = form.cleaned_data[f'map_{column}']
                if mapped_field:
                    column_mapping[column] = mapped_field
            
            # Store mapping in session
            import_data['column_mapping'] = column_mapping
            request.session['import_data'] = import_data
            
            # Validate data with mapping
            try:
                validation_results = validate_data(
                    import_job=import_job,
                    column_mapping=column_mapping,
                    preview_data=import_data['preview_data']
                )
                
                import_data['validation_results'] = validation_results
                request.session['import_data'] = import_data
                
                messages.success(request, 'Column mapping completed. Data validation results available.')
                return redirect('master_data_import:preview_data')
                
            except Exception as e:
                messages.error(request, f'Error during validation: {str(e)}')
    else:
        form = ColumnMappingForm(columns=columns, template_fields=template_fields)
    
    context = {
        'form': form,
        'import_job': import_job,
        'columns': columns,
        'template_fields': template_fields
    }
    
    return render(request, 'master_data_import/column_mapping.html', context)


@login_required
@permission_required('master_data_import.add_importjob')
def preview_data(request):
    """Show preview of data before import"""
    import_data = request.session.get('import_data')
    if not import_data:
        messages.error(request, 'No import data found. Please upload a file first.')
        return redirect('master_data_import:upload_file')
    
    import_job = get_object_or_404(ImportJob, id=import_data['job_id'])
    preview_data = import_data.get('preview_data', [])
    validation_results = import_data.get('validation_results', {})
    
    if request.method == 'POST':
        form = ImportPreviewForm(request.POST)
        if form.is_valid() and form.cleaned_data['confirm_import']:
            # Start import process
            try:
                import_job.status = 'processing'
                import_job.started_at = timezone.now()
                import_job.save()
                
                # Create audit log
                create_audit_log(
                    import_job=import_job,
                    action='import',
                    message='Import process started',
                    request=request
                )
                
                # Process import in background (you might want to use Celery here)
                process_import(
                    import_job=import_job,
                    column_mapping=import_data['column_mapping'],
                    skip_errors=import_data['skip_errors']
                )
                
                # Clear session data
                del request.session['import_data']
                
                messages.success(request, 'Import process started successfully.')
                return redirect('master_data_import:job_detail', pk=import_job.id)
                
            except Exception as e:
                import_job.status = 'failed'
                import_job.save()
                messages.error(request, f'Error starting import: {str(e)}')
    else:
        form = ImportPreviewForm()
    
    context = {
        'form': form,
        'import_job': import_job,
        'preview_data': preview_data,
        'validation_results': validation_results,
        'total_rows': import_data['total_rows']
    }
    
    return render(request, 'master_data_import/preview.html', context)


class ImportJobListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """List view for import jobs with filtering and search"""
    model = ImportJob
    template_name = 'master_data_import/job_list.html'
    context_object_name = 'import_jobs'
    paginate_by = 20
    permission_required = 'master_data_import.view_importjob'
    
    def get_queryset(self):
        queryset = ImportJob.objects.select_related('template', 'created_by').all()
        
        # Apply filters
        form = ImportJobFilterForm(self.request.GET)
        if form.is_valid():
            status = form.cleaned_data.get('status')
            data_type = form.cleaned_data.get('data_type')
            date_from = form.cleaned_data.get('date_from')
            date_to = form.cleaned_data.get('date_to')
            search = form.cleaned_data.get('search')
            
            if status:
                queryset = queryset.filter(status=status)
            
            if data_type:
                queryset = queryset.filter(template__data_type=data_type)
            
            if date_from:
                queryset = queryset.filter(created_at__date__gte=date_from)
            
            if date_to:
                queryset = queryset.filter(created_at__date__lte=date_to)
            
            if search:
                queryset = queryset.filter(
                    models.Q(job_name__icontains=search) |
                    models.Q(file_name__icontains=search)
                )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = ImportJobFilterForm(self.request.GET)
        return context


class ImportJobDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Detail view for import jobs"""
    model = ImportJob
    template_name = 'master_data_import/job_detail.html'
    context_object_name = 'import_job'
    permission_required = 'master_data_import.view_importjob'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        import_job = self.get_object()
        
        # Get related data
        context['audit_logs'] = import_job.audit_logs.all()[:20]
        context['errors'] = import_job.errors.all()[:50]
        
        return context


class ImportTemplateListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """List view for import templates"""
    model = ImportTemplate
    template_name = 'master_data_import/template_list.html'
    context_object_name = 'templates'
    paginate_by = 20
    permission_required = 'master_data_import.view_importtemplate'
    
    def get_queryset(self):
        return ImportTemplate.objects.select_related('created_by').all()


class ImportTemplateDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Detail view for import templates"""
    model = ImportTemplate
    template_name = 'master_data_import/template_detail.html'
    context_object_name = 'template'
    permission_required = 'master_data_import.view_importtemplate'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        template = self.get_object()
        
        # Get related import jobs
        context['related_jobs'] = template.importjob_set.all()[:10]
        
        # Get validation rules
        context['validation_rules'] = template.template_validation_rules.all()
        
        # Get usage statistics
        context['total_jobs'] = template.importjob_set.count()
        context['completed_jobs'] = template.importjob_set.filter(status='completed').count()
        context['failed_jobs'] = template.importjob_set.filter(status='failed').count()
        
        return context


class ImportTemplateCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Create view for import templates"""
    model = ImportTemplate
    form_class = ImportTemplateForm
    template_name = 'master_data_import/template_form.html'
    permission_required = 'master_data_import.add_importtemplate'
    success_url = reverse_lazy('master_data_import:template_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class ImportTemplateUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Update view for import templates"""
    model = ImportTemplate
    form_class = ImportTemplateForm
    template_name = 'master_data_import/template_form.html'
    permission_required = 'master_data_import.change_importtemplate'
    success_url = reverse_lazy('master_data_import:template_list')


class ImportTemplateDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Delete view for import templates"""
    model = ImportTemplate
    template_name = 'master_data_import/template_confirm_delete.html'
    permission_required = 'master_data_import.delete_importtemplate'
    success_url = reverse_lazy('master_data_import:template_list')


@login_required
@permission_required('master_data_import.view_importtemplate')
def download_template(request, template_id):
    """Download import template file"""
    template = get_object_or_404(ImportTemplate, id=template_id)
    
    try:
        # Generate template file
        file_content = generate_template_file(template)
        
        # Create response
        response = HttpResponse(
            file_content,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{template.name}_template.xlsx"'
        
        return response
        
    except Exception as e:
        messages.error(request, f'Error generating template: {str(e)}')
        return redirect('master_data_import:template_list')


@login_required
@permission_required('master_data_import.view_importjob')
def job_progress(request, job_id):
    """Get job progress via AJAX"""
    import_job = get_object_or_404(ImportJob, id=job_id)
    
    return JsonResponse({
        'status': import_job.status,
        'progress_percentage': import_job.progress_percentage,
        'processed_rows': import_job.processed_rows,
        'total_rows': import_job.total_rows,
        'successful_rows': import_job.successful_rows,
        'failed_rows': import_job.failed_rows,
        'duration': str(import_job.duration) if import_job.duration else None
    })


@login_required
@permission_required('master_data_import.delete_importjob')
def cancel_job(request, job_id):
    """Cancel a running import job"""
    import_job = get_object_or_404(ImportJob, id=job_id)
    
    if import_job.status in ['pending', 'processing']:
        import_job.status = 'cancelled'
        import_job.save()
        
        # Create audit log
        create_audit_log(
            import_job=import_job,
            action='error',
            message='Import job cancelled by user',
            request=request
        )
        
        messages.success(request, 'Import job cancelled successfully.')
    else:
        messages.error(request, 'Cannot cancel job in current status.')
    
    return redirect('master_data_import:job_detail', pk=job_id)


@login_required
@permission_required('master_data_import.view_importjob')
def export_errors(request, job_id):
    """Export import errors to CSV"""
    import_job = get_object_or_404(ImportJob, id=job_id)
    errors = import_job.errors.all()
    
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="import_errors_{job_id}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Row Number', 'Column', 'Error Type', 'Error Message', 'Field Value', 'Suggested Correction'])
    
    for error in errors:
        writer.writerow([
            error.row_number,
            error.column_name,
            error.get_error_type_display(),
            error.error_message,
            error.field_value,
            error.suggested_correction
        ])
    
    return response
