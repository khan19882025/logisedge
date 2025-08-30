from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime, timedelta

from .models import (
    Grievance, GrievanceCategory, GrievanceAttachment, GrievanceNote,
    DisciplinaryCase, DisciplinaryAction, DisciplinaryActionType,
    DisciplinaryActionDocument, Appeal, EscalationMatrix, CaseAuditLog
)
from .forms import (
    GrievanceForm, GrievanceCategoryForm, GrievanceAttachmentForm, GrievanceNoteForm,
    DisciplinaryCaseForm, DisciplinaryActionForm, DisciplinaryActionTypeForm,
    DisciplinaryActionDocumentForm, AppealForm, AppealReviewForm,
    EscalationMatrixForm, GrievanceSearchForm, DisciplinaryCaseSearchForm,
    GrievanceStatusUpdateForm, DisciplinaryCaseStatusUpdateForm
)


# Dashboard Views
@login_required
def dashboard(request):
    """Main dashboard for disciplinary and grievance management"""
    context = {
        'total_grievances': Grievance.objects.count(),
        'open_grievances': Grievance.objects.filter(status__in=['new', 'under_review', 'investigating']).count(),
        'resolved_grievances': Grievance.objects.filter(status='resolved').count(),
        'total_disciplinary_cases': DisciplinaryCase.objects.count(),
        'open_disciplinary_cases': DisciplinaryCase.objects.filter(status__in=['open', 'investigating', 'hearing_scheduled']).count(),
        'pending_appeals': Appeal.objects.filter(status='pending').count(),
        'recent_grievances': Grievance.objects.order_by('-created_at')[:5],
        'recent_disciplinary_cases': DisciplinaryCase.objects.order_by('-created_at')[:5],
        'urgent_grievances': Grievance.objects.filter(priority='urgent', status__in=['new', 'under_review'])[:3],
        'my_assigned_cases': Grievance.objects.filter(assigned_to=request.user, status__in=['new', 'under_review', 'investigating'])[:3],
    }
    return render(request, 'disciplinary_grievance/dashboard.html', context)


# Grievance Views
@login_required
def grievance_list(request):
    """List all grievances with search and filtering"""
    grievances = Grievance.objects.select_related('employee', 'category', 'assigned_to', 'created_by').all()
    
    # Search and filtering
    search_form = GrievanceSearchForm(request.GET)
    if search_form.is_valid():
        if search_form.cleaned_data.get('ticket_number'):
            grievances = grievances.filter(ticket_number__icontains=search_form.cleaned_data['ticket_number'])
        if search_form.cleaned_data.get('title'):
            grievances = grievances.filter(title__icontains=search_form.cleaned_data['title'])
        if search_form.cleaned_data.get('employee'):
            grievances = grievances.filter(employee=search_form.cleaned_data['employee'])
        if search_form.cleaned_data.get('category'):
            grievances = grievances.filter(category=search_form.cleaned_data['category'])
        if search_form.cleaned_data.get('status'):
            grievances = grievances.filter(status=search_form.cleaned_data['status'])
        if search_form.cleaned_data.get('priority'):
            grievances = grievances.filter(priority=search_form.cleaned_data['priority'])
        if search_form.cleaned_data.get('date_from'):
            grievances = grievances.filter(created_at__date__gte=search_form.cleaned_data['date_from'])
        if search_form.cleaned_data.get('date_to'):
            grievances = grievances.filter(created_at__date__lte=search_form.cleaned_data['date_to'])
    
    # Pagination
    paginator = Paginator(grievances, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_count': grievances.count(),
    }
    return render(request, 'disciplinary_grievance/grievance_list.html', context)


@login_required
def grievance_detail(request, pk):
    """Detail view for a grievance"""
    grievance = get_object_or_404(Grievance, pk=pk)
    attachments = grievance.attachments.all()
    notes = grievance.notes.all()
    
    # Check if user can view this grievance
    if grievance.is_confidential and not request.user.has_perm('disciplinary_grievance.view_confidential_grievance'):
        if request.user != grievance.assigned_to and request.user != grievance.created_by:
            messages.error(request, "You don't have permission to view this confidential grievance.")
            return redirect('disciplinary_grievance:grievance_list')
    
    context = {
        'grievance': grievance,
        'attachments': attachments,
        'notes': notes,
    }
    return render(request, 'disciplinary_grievance/grievance_detail.html', context)


@login_required
@permission_required('disciplinary_grievance.add_grievance', raise_exception=True)
def grievance_create(request):
    """Create a new grievance"""
    if request.method == 'POST':
        form = GrievanceForm(request.POST)
        if form.is_valid():
            grievance = form.save(commit=False)
            grievance.created_by = request.user
            grievance.save()
            
            # Create audit log
            CaseAuditLog.objects.create(
                content_type='grievance',
                object_id=grievance.id,
                action='created',
                description=f'Grievance {grievance.ticket_number} created',
                user=request.user
            )
            
            messages.success(request, f'Grievance {grievance.ticket_number} created successfully.')
            return redirect('disciplinary_grievance:grievance_detail', pk=grievance.pk)
    else:
        form = GrievanceForm()
    
    context = {'form': form}
    return render(request, 'disciplinary_grievance/grievance_form.html', context)


@login_required
@permission_required('disciplinary_grievance.change_grievance', raise_exception=True)
def grievance_update(request, pk):
    """Update an existing grievance"""
    grievance = get_object_or_404(Grievance, pk=pk)
    
    if request.method == 'POST':
        form = GrievanceForm(request.POST, instance=grievance)
        if form.is_valid():
            old_status = grievance.status
            grievance = form.save()
            
            # Create audit log for status change
            if old_status != grievance.status:
                CaseAuditLog.objects.create(
                    content_type='grievance',
                    object_id=grievance.id,
                    action='status_changed',
                    description=f'Status changed from {old_status} to {grievance.status}',
                    user=request.user,
                    old_values={'status': old_status},
                    new_values={'status': grievance.status}
                )
            
            messages.success(request, f'Grievance {grievance.ticket_number} updated successfully.')
            return redirect('disciplinary_grievance:grievance_detail', pk=grievance.pk)
    else:
        form = GrievanceForm(instance=grievance)
    
    context = {'form': form, 'grievance': grievance}
    return render(request, 'disciplinary_grievance/grievance_form.html', context)


@login_required
@permission_required('disciplinary_grievance.delete_grievance', raise_exception=True)
def grievance_delete(request, pk):
    """Delete a grievance"""
    grievance = get_object_or_404(Grievance, pk=pk)
    
    if request.method == 'POST':
        ticket_number = grievance.ticket_number
        grievance.delete()
        messages.success(request, f'Grievance {ticket_number} deleted successfully.')
        return redirect('disciplinary_grievance:grievance_list')
    
    context = {'grievance': grievance}
    return render(request, 'disciplinary_grievance/grievance_confirm_delete.html', context)


@login_required
def grievance_status_update(request, pk):
    """Update grievance status"""
    grievance = get_object_or_404(Grievance, pk=pk)
    
    if request.method == 'POST':
        form = GrievanceStatusUpdateForm(request.POST, instance=grievance)
        if form.is_valid():
            old_status = grievance.status
            grievance = form.save(commit=False)
            
            # Set resolved date if status is resolved
            if grievance.status == 'resolved' and not grievance.resolved_at:
                grievance.resolved_at = timezone.now()
                grievance.resolved_by = request.user
            
            grievance.save()
            
            # Create audit log
            CaseAuditLog.objects.create(
                content_type='grievance',
                object_id=grievance.id,
                action='status_changed',
                description=f'Status updated to {grievance.status}',
                user=request.user,
                old_values={'status': old_status},
                new_values={'status': grievance.status}
            )
            
            messages.success(request, f'Grievance status updated to {grievance.get_status_display()}.')
            return redirect('disciplinary_grievance:grievance_detail', pk=grievance.pk)
    else:
        form = GrievanceStatusUpdateForm(instance=grievance)
    
    context = {'form': form, 'grievance': grievance}
    return render(request, 'disciplinary_grievance/grievance_status_update.html', context)


@login_required
def grievance_attachment_upload(request, grievance_pk):
    """Upload attachment for a grievance"""
    grievance = get_object_or_404(Grievance, pk=grievance_pk)
    
    if request.method == 'POST':
        form = GrievanceAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.grievance = grievance
            attachment.uploaded_by = request.user
            attachment.filename = attachment.file.name
            attachment.save()
            
            # Create audit log
            CaseAuditLog.objects.create(
                content_type='grievance',
                object_id=grievance.id,
                action='document_uploaded',
                description=f'Attachment uploaded: {attachment.filename}',
                user=request.user
            )
            
            messages.success(request, 'Attachment uploaded successfully.')
            return redirect('disciplinary_grievance:grievance_detail', pk=grievance.pk)
    else:
        form = GrievanceAttachmentForm()
    
    context = {'form': form, 'grievance': grievance}
    return render(request, 'disciplinary_grievance/grievance_attachment_form.html', context)


@login_required
def grievance_note_add(request, grievance_pk):
    """Add a note to a grievance"""
    grievance = get_object_or_404(Grievance, pk=grievance_pk)
    
    if request.method == 'POST':
        form = GrievanceNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.grievance = grievance
            note.created_by = request.user
            note.save()
            
            # Create audit log
            CaseAuditLog.objects.create(
                content_type='grievance',
                object_id=grievance.id,
                action='note_added',
                description=f'Note added: {note.note[:50]}...',
                user=request.user
            )
            
            messages.success(request, 'Note added successfully.')
            return redirect('disciplinary_grievance:grievance_detail', pk=grievance.pk)
    else:
        form = GrievanceNoteForm()
    
    context = {'form': form, 'grievance': grievance}
    return render(request, 'disciplinary_grievance/grievance_note_form.html', context)


# Disciplinary Case Views
@login_required
def disciplinary_case_list(request):
    """List all disciplinary cases with search and filtering"""
    cases = DisciplinaryCase.objects.select_related('employee', 'reported_by', 'assigned_investigator').all()
    
    # Search and filtering
    search_form = DisciplinaryCaseSearchForm(request.GET)
    if search_form.is_valid():
        if search_form.cleaned_data.get('case_number'):
            cases = cases.filter(case_number__icontains=search_form.cleaned_data['case_number'])
        if search_form.cleaned_data.get('title'):
            cases = cases.filter(title__icontains=search_form.cleaned_data['title'])
        if search_form.cleaned_data.get('employee'):
            cases = cases.filter(employee=search_form.cleaned_data['employee'])
        if search_form.cleaned_data.get('severity'):
            cases = cases.filter(severity=search_form.cleaned_data['severity'])
        if search_form.cleaned_data.get('status'):
            cases = cases.filter(status=search_form.cleaned_data['status'])
        if search_form.cleaned_data.get('assigned_investigator'):
            cases = cases.filter(assigned_investigator=search_form.cleaned_data['assigned_investigator'])
        if search_form.cleaned_data.get('date_from'):
            cases = cases.filter(created_at__date__gte=search_form.cleaned_data['date_from'])
        if search_form.cleaned_data.get('date_to'):
            cases = cases.filter(created_at__date__lte=search_form.cleaned_data['date_to'])
    
    # Pagination
    paginator = Paginator(cases, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_count': cases.count(),
    }
    return render(request, 'disciplinary_grievance/disciplinary_case_list.html', context)


@login_required
def disciplinary_case_detail(request, pk):
    """Detail view for a disciplinary case"""
    case = get_object_or_404(DisciplinaryCase, pk=pk)
    actions = case.actions.all()
    documents = DisciplinaryActionDocument.objects.filter(action__case=case)
    
    # Check if user can view this case
    if case.is_confidential and not request.user.has_perm('disciplinary_grievance.view_confidential_disciplinarycase'):
        if request.user != case.assigned_investigator and request.user != case.reported_by:
            messages.error(request, "You don't have permission to view this confidential case.")
            return redirect('disciplinary_grievance:disciplinary_case_list')
    
    context = {
        'case': case,
        'actions': actions,
        'documents': documents,
    }
    return render(request, 'disciplinary_grievance/disciplinary_case_detail.html', context)


@login_required
@permission_required('disciplinary_grievance.add_disciplinarycase', raise_exception=True)
def disciplinary_case_create(request):
    """Create a new disciplinary case"""
    if request.method == 'POST':
        form = DisciplinaryCaseForm(request.POST)
        if form.is_valid():
            case = form.save(commit=False)
            case.reported_by = request.user
            case.save()
            form.save_m2m()  # Save many-to-many relationships
            
            # Create audit log
            CaseAuditLog.objects.create(
                content_type='disciplinary',
                object_id=case.id,
                action='created',
                description=f'Disciplinary case {case.case_number} created',
                user=request.user
            )
            
            messages.success(request, f'Disciplinary case {case.case_number} created successfully.')
            return redirect('disciplinary_grievance:disciplinary_case_detail', pk=case.pk)
    else:
        form = DisciplinaryCaseForm()
    
    context = {'form': form}
    return render(request, 'disciplinary_grievance/disciplinary_case_form.html', context)


@login_required
@permission_required('disciplinary_grievance.change_disciplinarycase', raise_exception=True)
def disciplinary_case_update(request, pk):
    """Update an existing disciplinary case"""
    case = get_object_or_404(DisciplinaryCase, pk=pk)
    
    if request.method == 'POST':
        form = DisciplinaryCaseForm(request.POST, instance=case)
        if form.is_valid():
            old_status = case.status
            case = form.save(commit=False)
            case.save()
            form.save_m2m()
            
            # Create audit log for status change
            if old_status != case.status:
                CaseAuditLog.objects.create(
                    content_type='disciplinary',
                    object_id=case.id,
                    action='status_changed',
                    description=f'Status changed from {old_status} to {case.status}',
                    user=request.user,
                    old_values={'status': old_status},
                    new_values={'status': case.status}
                )
            
            messages.success(request, f'Disciplinary case {case.case_number} updated successfully.')
            return redirect('disciplinary_grievance:disciplinary_case_detail', pk=case.pk)
    else:
        form = DisciplinaryCaseForm(instance=case)
    
    context = {'form': form, 'case': case}
    return render(request, 'disciplinary_grievance/disciplinary_case_form.html', context)


@login_required
def disciplinary_case_status_update(request, pk):
    """Update disciplinary case status"""
    case = get_object_or_404(DisciplinaryCase, pk=pk)
    
    if request.method == 'POST':
        form = DisciplinaryCaseStatusUpdateForm(request.POST, instance=case)
        if form.is_valid():
            old_status = case.status
            case = form.save(commit=False)
            
            # Set closed date if status is closed
            if case.status == 'closed' and not case.closed_at:
                case.closed_at = timezone.now()
            
            case.save()
            
            # Create audit log
            CaseAuditLog.objects.create(
                content_type='disciplinary',
                object_id=case.id,
                action='status_changed',
                description=f'Status updated to {case.status}',
                user=request.user,
                old_values={'status': old_status},
                new_values={'status': case.status}
            )
            
            messages.success(request, f'Case status updated to {case.get_status_display()}.')
            return redirect('disciplinary_grievance:disciplinary_case_detail', pk=case.pk)
    else:
        form = DisciplinaryCaseStatusUpdateForm(instance=case)
    
    context = {'form': form, 'case': case}
    return render(request, 'disciplinary_grievance/disciplinary_case_status_update.html', context)


# Disciplinary Action Views
@login_required
@permission_required('disciplinary_grievance.add_disciplinaryaction', raise_exception=True)
def disciplinary_action_create(request, case_pk):
    """Create a new disciplinary action"""
    case = get_object_or_404(DisciplinaryCase, pk=case_pk)
    
    if request.method == 'POST':
        form = DisciplinaryActionForm(request.POST)
        if form.is_valid():
            action = form.save(commit=False)
            action.case = case
            action.save()
            
            # Create audit log
            CaseAuditLog.objects.create(
                content_type='disciplinary',
                object_id=case.id,
                action='action_taken',
                description=f'Disciplinary action {action.action_type.name} created',
                user=request.user
            )
            
            messages.success(request, f'Disciplinary action created successfully.')
            return redirect('disciplinary_grievance:disciplinary_case_detail', pk=case.pk)
    else:
        form = DisciplinaryActionForm()
    
    context = {'form': form, 'case': case}
    return render(request, 'disciplinary_grievance/disciplinary_action_form.html', context)


@login_required
def disciplinary_action_detail(request, pk):
    """Detail view for a disciplinary action"""
    action = get_object_or_404(DisciplinaryAction, pk=pk)
    documents = action.documents.all()
    appeals = action.appeals.all()
    
    context = {
        'action': action,
        'documents': documents,
        'appeals': appeals,
    }
    return render(request, 'disciplinary_grievance/disciplinary_action_detail.html', context)


# Appeal Views
@login_required
def appeal_create(request, action_pk):
    """Create a new appeal"""
    action = get_object_or_404(DisciplinaryAction, pk=action_pk)
    
    if request.method == 'POST':
        form = AppealForm(request.POST)
        if form.is_valid():
            appeal = form.save(commit=False)
            appeal.action = action
            appeal.employee = action.case.employee
            appeal.save()
            
            # Create audit log
            CaseAuditLog.objects.create(
                content_type='disciplinary',
                object_id=action.case.id,
                action='appeal_filed',
                description=f'Appeal filed against action {action.action_type.name}',
                user=request.user
            )
            
            messages.success(request, 'Appeal filed successfully.')
            return redirect('disciplinary_grievance:disciplinary_action_detail', pk=action.pk)
    else:
        form = AppealForm()
    
    context = {'form': form, 'action': action}
    return render(request, 'disciplinary_grievance/appeal_form.html', context)


@login_required
@permission_required('disciplinary_grievance.change_appeal', raise_exception=True)
def appeal_review(request, pk):
    """Review an appeal"""
    appeal = get_object_or_404(Appeal, pk=pk)
    
    if request.method == 'POST':
        form = AppealReviewForm(request.POST, instance=appeal)
        if form.is_valid():
            appeal = form.save(commit=False)
            appeal.reviewed_by = request.user
            appeal.reviewed_at = timezone.now()
            
            if appeal.status in ['approved', 'rejected']:
                appeal.outcome_date = timezone.now()
            
            appeal.save()
            
            messages.success(request, f'Appeal {appeal.get_status_display()} successfully.')
            return redirect('disciplinary_grievance:disciplinary_action_detail', pk=appeal.action.pk)
    else:
        form = AppealReviewForm(instance=appeal)
    
    context = {'form': form, 'appeal': appeal}
    return render(request, 'disciplinary_grievance/appeal_review_form.html', context)


# Configuration Views
@login_required
@permission_required('disciplinary_grievance.view_grievancecategory', raise_exception=True)
def grievance_category_list(request):
    """List grievance categories"""
    categories = GrievanceCategory.objects.all()
    context = {'categories': categories}
    return render(request, 'disciplinary_grievance/grievance_category_list.html', context)


@login_required
@permission_required('disciplinary_grievance.add_grievancecategory', raise_exception=True)
def grievance_category_create(request):
    """Create a new grievance category"""
    if request.method == 'POST':
        form = GrievanceCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Grievance category created successfully.')
            return redirect('disciplinary_grievance:grievance_category_list')
    else:
        form = GrievanceCategoryForm()
    
    context = {'form': form}
    return render(request, 'disciplinary_grievance/grievance_category_form.html', context)


@login_required
@permission_required('disciplinary_grievance.view_disciplinaryactiontype', raise_exception=True)
def disciplinary_action_type_list(request):
    """List disciplinary action types"""
    action_types = DisciplinaryActionType.objects.all()
    context = {'action_types': action_types}
    return render(request, 'disciplinary_grievance/disciplinary_action_type_list.html', context)


@login_required
@permission_required('disciplinary_grievance.add_disciplinaryactiontype', raise_exception=True)
def disciplinary_action_type_create(request):
    """Create a new disciplinary action type"""
    if request.method == 'POST':
        form = DisciplinaryActionTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Disciplinary action type created successfully.')
            return redirect('disciplinary_grievance:disciplinary_action_type_list')
    else:
        form = DisciplinaryActionTypeForm()
    
    context = {'form': form}
    return render(request, 'disciplinary_grievance/disciplinary_action_type_form.html', context)


# Report Views
@login_required
@permission_required('disciplinary_grievance.view_grievance', raise_exception=True)
def grievance_report(request):
    """Generate grievance reports"""
    # Get date range from request
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    grievances = Grievance.objects.all()
    
    if date_from:
        grievances = grievances.filter(created_at__date__gte=date_from)
    if date_to:
        grievances = grievances.filter(created_at__date__lte=date_to)
    
    # Statistics
    stats = {
        'total': grievances.count(),
        'by_status': dict(grievances.values_list('status').annotate(count=Count('id'))),
        'by_priority': dict(grievances.values_list('priority').annotate(count=Count('id'))),
        'by_category': dict(grievances.values('category__name').annotate(count=Count('id'))),
        'resolution_time': grievances.filter(status='resolved').aggregate(
            avg_time=Avg('resolved_at' - 'created_at')
        ),
    }
    
    context = {
        'grievances': grievances,
        'stats': stats,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'disciplinary_grievance/grievance_report.html', context)


@login_required
@permission_required('disciplinary_grievance.view_disciplinarycase', raise_exception=True)
def disciplinary_case_report(request):
    """Generate disciplinary case reports"""
    # Get date range from request
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    cases = DisciplinaryCase.objects.all()
    
    if date_from:
        cases = cases.filter(created_at__date__gte=date_from)
    if date_to:
        cases = cases.filter(created_at__date__lte=date_to)
    
    # Statistics
    stats = {
        'total': cases.count(),
        'by_status': dict(cases.values_list('status').annotate(count=Count('id'))),
        'by_severity': dict(cases.values_list('severity').annotate(count=Count('id'))),
        'by_employee': dict(cases.values('employee__name').annotate(count=Count('id'))),
    }
    
    context = {
        'cases': cases,
        'stats': stats,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'disciplinary_grievance/disciplinary_case_report.html', context)


# API Views for AJAX
@login_required
@csrf_exempt
def get_employee_grievances(request, employee_id):
    """Get grievances for a specific employee (AJAX)"""
    grievances = Grievance.objects.filter(employee_id=employee_id).values(
        'id', 'ticket_number', 'title', 'status', 'created_at'
    )
    return JsonResponse({'grievances': list(grievances)})


@login_required
@csrf_exempt
def get_employee_disciplinary_cases(request, employee_id):
    """Get disciplinary cases for a specific employee (AJAX)"""
    cases = DisciplinaryCase.objects.filter(employee_id=employee_id).values(
        'id', 'case_number', 'title', 'status', 'severity', 'created_at'
    )
    return JsonResponse({'cases': list(cases)})


@login_required
@csrf_exempt
def update_grievance_status_ajax(request, pk):
    """Update grievance status via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            grievance = get_object_or_404(Grievance, pk=pk)
            old_status = grievance.status
            grievance.status = data.get('status')
            grievance.save()
            
            # Create audit log
            CaseAuditLog.objects.create(
                content_type='grievance',
                object_id=grievance.id,
                action='status_changed',
                description=f'Status changed from {old_status} to {grievance.status}',
                user=request.user
            )
            
            return JsonResponse({'success': True, 'status': grievance.get_status_display()})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})
