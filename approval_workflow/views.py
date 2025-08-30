from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.core.paginator import Paginator
from django.db import transaction
from datetime import datetime, timedelta
import json

from .models import (
    WorkflowType, WorkflowDefinition, WorkflowLevel, ApprovalRequest,
    WorkflowLevelApproval, ApprovalComment, ApprovalNotification,
    ApprovalAuditLog, WorkflowTemplate
)
from .forms import (
    WorkflowTypeForm, WorkflowDefinitionForm, WorkflowLevelForm,
    ApprovalRequestForm, ApprovalRequestFilterForm, WorkflowLevelApprovalForm,
    ApprovalCommentForm, WorkflowTemplateForm, BulkApprovalForm,
    WorkflowLevelAssignForm, ApprovalNotificationForm
)


@login_required
def approval_dashboard(request):
    """Main approval workflow dashboard"""
    user = request.user
    
    # Get pending approvals for the user
    pending_approvals = ApprovalRequest.objects.filter(
        current_approvers=user,
        status__in=['pending', 'in_progress']
    ).order_by('-created_at')[:10]
    
    # Get user's submitted requests
    my_requests = ApprovalRequest.objects.filter(
        requester=user
    ).order_by('-created_at')[:10]
    
    # Get overdue approvals
    overdue_approvals = ApprovalRequest.objects.filter(
        current_approvers=user,
        status__in=['pending', 'in_progress'],
        deadline__lt=timezone.now()
    ).order_by('deadline')[:5]
    
    # Dashboard statistics
    stats = {
        'total_pending': ApprovalRequest.objects.filter(status__in=['pending', 'in_progress']).count(),
        'my_pending': ApprovalRequest.objects.filter(requester=user, status__in=['pending', 'in_progress']).count(),
        'overdue_count': overdue_approvals.count(),
        'approved_today': ApprovalRequest.objects.filter(
            approved_at__date=timezone.now().date(),
            status='approved'
        ).count(),
    }
    
    # Recent activities
    recent_activities = ApprovalAuditLog.objects.filter(
        Q(user=user) | Q(approval_request__requester=user) | Q(approval_request__current_approvers=user)
    ).order_by('-created_at')[:15]
    
    context = {
        'pending_approvals': pending_approvals,
        'my_requests': my_requests,
        'overdue_approvals': overdue_approvals,
        'stats': stats,
        'recent_activities': recent_activities,
    }
    
    return render(request, 'approval_workflow/dashboard.html', context)


class WorkflowTypeListView(LoginRequiredMixin, ListView):
    """List view for workflow types"""
    model = WorkflowType
    template_name = 'approval_workflow/workflow_type_list.html'
    context_object_name = 'workflow_types'
    paginate_by = 20

    def get_queryset(self):
        queryset = WorkflowType.objects.all()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        return queryset


class WorkflowTypeCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create view for workflow types"""
    model = WorkflowType
    form_class = WorkflowTypeForm
    template_name = 'approval_workflow/workflow_type_form.html'
    success_url = reverse_lazy('approval_workflow:workflow_type_list')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        messages.success(self.request, 'Workflow type created successfully.')
        return super().form_valid(form)


class WorkflowTypeUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update view for workflow types"""
    model = WorkflowType
    form_class = WorkflowTypeForm
    template_name = 'approval_workflow/workflow_type_form.html'
    success_url = reverse_lazy('approval_workflow:workflow_type_list')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        messages.success(self.request, 'Workflow type updated successfully.')
        return super().form_valid(form)


class WorkflowDefinitionListView(LoginRequiredMixin, ListView):
    """List view for workflow definitions"""
    model = WorkflowDefinition
    template_name = 'approval_workflow/workflow_definition_list.html'
    context_object_name = 'workflow_definitions'
    paginate_by = 20

    def get_queryset(self):
        queryset = WorkflowDefinition.objects.select_related('workflow_type')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        return queryset


class WorkflowDefinitionCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create view for workflow definitions"""
    model = WorkflowDefinition
    form_class = WorkflowDefinitionForm
    template_name = 'approval_workflow/workflow_definition_form.html'
    success_url = reverse_lazy('approval_workflow:workflow_definition_list')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        messages.success(self.request, 'Workflow definition created successfully.')
        return super().form_valid(form)


class WorkflowDefinitionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update view for workflow definitions"""
    model = WorkflowDefinition
    form_class = WorkflowDefinitionForm
    template_name = 'approval_workflow/workflow_definition_form.html'
    success_url = reverse_lazy('approval_workflow:workflow_definition_list')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        messages.success(self.request, 'Workflow definition updated successfully.')
        return super().form_valid(form)


class WorkflowDefinitionDetailView(LoginRequiredMixin, DetailView):
    """Detail view for workflow definitions"""
    model = WorkflowDefinition
    template_name = 'approval_workflow/workflow_definition_detail.html'
    context_object_name = 'workflow_definition'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['levels'] = self.object.levels.all()
        context['recent_requests'] = self.object.requests.all()[:10]
        return context


@login_required
def workflow_level_list(request, workflow_definition_id):
    """List view for workflow levels"""
    workflow_definition = get_object_or_404(WorkflowDefinition, id=workflow_definition_id)
    levels = workflow_definition.levels.all()
    
    context = {
        'workflow_definition': workflow_definition,
        'levels': levels,
    }
    return render(request, 'approval_workflow/workflow_level_list.html', context)


class WorkflowLevelCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create view for workflow levels"""
    model = WorkflowLevel
    form_class = WorkflowLevelForm
    template_name = 'approval_workflow/workflow_level_form.html'

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        workflow_definition_id = self.kwargs.get('workflow_definition_id')
        context['workflow_definition'] = get_object_or_404(WorkflowDefinition, id=workflow_definition_id)
        return context

    def form_valid(self, form):
        workflow_definition_id = self.kwargs.get('workflow_definition_id')
        workflow_definition = get_object_or_404(WorkflowDefinition, id=workflow_definition_id)
        form.instance.workflow_definition = workflow_definition
        messages.success(self.request, 'Workflow level created successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('approval_workflow:workflow_level_list', 
                      kwargs={'workflow_definition_id': self.kwargs.get('workflow_definition_id')})


class ApprovalRequestListView(LoginRequiredMixin, ListView):
    """List view for approval requests"""
    model = ApprovalRequest
    template_name = 'approval_workflow/approval_request_list.html'
    context_object_name = 'approval_requests'
    paginate_by = 20

    def get_queryset(self):
        queryset = ApprovalRequest.objects.select_related(
            'workflow_definition', 'requester', 'current_level'
        ).prefetch_related('current_approvers')
        
        # Apply filters
        form = ApprovalRequestFilterForm(self.request.GET)
        if form.is_valid():
            if form.cleaned_data.get('status'):
                queryset = queryset.filter(status=form.cleaned_data['status'])
            if form.cleaned_data.get('priority'):
                queryset = queryset.filter(priority=form.cleaned_data['priority'])
            if form.cleaned_data.get('workflow_definition'):
                queryset = queryset.filter(workflow_definition=form.cleaned_data['workflow_definition'])
            if form.cleaned_data.get('requester'):
                queryset = queryset.filter(requester=form.cleaned_data['requester'])
            if form.cleaned_data.get('search'):
                search = form.cleaned_data['search']
                queryset = queryset.filter(
                    Q(title__icontains=search) | 
                    Q(description__icontains=search) |
                    Q(request_id__icontains=search)
                )
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = ApprovalRequestFilterForm(self.request.GET)
        return context


class ApprovalRequestCreateView(LoginRequiredMixin, CreateView):
    """Create view for approval requests"""
    model = ApprovalRequest
    form_class = ApprovalRequestForm
    template_name = 'approval_workflow/approval_request_form.html'
    success_url = reverse_lazy('approval_workflow:approval_request_list')

    def form_valid(self, form):
        form.instance.requester = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Approval request created successfully.')
        return response


class ApprovalRequestDetailView(LoginRequiredMixin, DetailView):
    """Detail view for approval requests"""
    model = ApprovalRequest
    template_name = 'approval_workflow/approval_request_detail.html'
    context_object_name = 'approval_request'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comments.all()
        context['audit_logs'] = self.object.audit_logs.all()[:10]
        context['level_approvals'] = self.object.workflow_level_approvals.select_related('approver', 'workflow_level').all()
        
        # Check if user can approve
        context['can_approve'] = self.request.user in self.object.current_approvers.all()
        context['approval_form'] = WorkflowLevelApprovalForm(
            approval_request=self.object,
            user=self.request.user
        )
        context['comment_form'] = ApprovalCommentForm()
        
        return context


@login_required
def approve_request(request, pk):
    """Approve, reject, or return an approval request"""
    approval_request = get_object_or_404(ApprovalRequest, pk=pk)
    
    if request.method == 'POST':
        form = WorkflowLevelApprovalForm(request.POST, approval_request=approval_request, user=request.user)
        if form.is_valid():
            action = form.cleaned_data['action']
            comments = form.cleaned_data['comments']
            
            with transaction.atomic():
                # Create approval record
                approval = WorkflowLevelApproval.objects.create(
                    approval_request=approval_request,
                    workflow_level=approval_request.current_level,
                    approver=request.user,
                    status=action,
                    comments=comments
                )
                
                # Update approval request status
                if action == 'approve':
                    approval_request.status = 'approved'
                    approval_request.approved_by = request.user
                    approval_request.approved_at = timezone.now()
                elif action == 'reject':
                    approval_request.status = 'rejected'
                    approval_request.rejected_by = request.user
                    approval_request.rejected_at = timezone.now()
                elif action == 'return':
                    approval_request.status = 'pending'
                
                approval_request.save()
                
                # Create audit log
                ApprovalAuditLog.objects.create(
                    approval_request=approval_request,
                    user=request.user,
                    action=action,
                    description=f"Request {action} by {request.user.username}",
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                # Send notifications
                # TODO: Implement notification system
                
                messages.success(request, f'Request {action} successfully.')
                return redirect('approval_workflow:approval_request_detail', pk=pk)
    else:
        form = WorkflowLevelApprovalForm(approval_request=approval_request, user=request.user)
    
    return render(request, 'approval_workflow/approve_request.html', {
        'approval_request': approval_request,
        'form': form
    })


@login_required
def add_comment(request, pk):
    """Add comment to approval request"""
    approval_request = get_object_or_404(ApprovalRequest, pk=pk)
    
    if request.method == 'POST':
        form = ApprovalCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.approval_request = approval_request
            comment.user = request.user
            comment.save()
            
            messages.success(request, 'Comment added successfully.')
            return redirect('approval_workflow:approval_request_detail', pk=pk)
    else:
        form = ApprovalCommentForm()
    
    return render(request, 'approval_workflow/add_comment.html', {
        'approval_request': approval_request,
        'form': form
    })


@login_required
def my_approvals(request):
    """View for user's pending approvals"""
    user = request.user
    pending_approvals = ApprovalRequest.objects.filter(
        current_approvers=user,
        status__in=['pending', 'in_progress']
    ).order_by('-created_at')
    
    context = {
        'pending_approvals': pending_approvals,
    }
    return render(request, 'approval_workflow/my_approvals.html', context)


@login_required
def my_requests(request):
    """View for user's submitted requests"""
    user = request.user
    my_requests = ApprovalRequest.objects.filter(
        requester=user
    ).order_by('-created_at')
    
    context = {
        'my_requests': my_requests,
    }
    return render(request, 'approval_workflow/my_requests.html', context)


@login_required
def workflow_templates(request):
    """View for workflow templates"""
    templates = WorkflowTemplate.objects.filter(is_active=True)
    
    context = {
        'templates': templates,
    }
    return render(request, 'approval_workflow/workflow_templates.html', context)


@login_required
@csrf_exempt
def api_approval_stats(request):
    """API endpoint for approval statistics"""
    if request.method == 'GET':
        user = request.user
        
        # Get statistics
        stats = {
            'total_pending': ApprovalRequest.objects.filter(status__in=['pending', 'in_progress']).count(),
            'my_pending': ApprovalRequest.objects.filter(requester=user, status__in=['pending', 'in_progress']).count(),
            'overdue_count': ApprovalRequest.objects.filter(
                current_approvers=user,
                status__in=['pending', 'in_progress'],
                deadline__lt=timezone.now()
            ).count(),
            'approved_today': ApprovalRequest.objects.filter(
                approved_at__date=timezone.now().date(),
                status='approved'
            ).count(),
        }
        
        return JsonResponse(stats)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def bulk_approve(request):
    """Bulk approval action"""
    if request.method == 'POST':
        form = BulkApprovalForm(request.POST)
        if form.is_valid():
            approval_ids = form.cleaned_data['approval_ids']
            action = form.cleaned_data['action']
            comments = form.cleaned_data['comments']
            
            approvals = ApprovalRequest.objects.filter(
                id__in=approval_ids,
                current_approvers=request.user,
                status__in=['pending', 'in_progress']
            )
            
            with transaction.atomic():
                for approval in approvals:
                    # Create approval record
                    WorkflowLevelApproval.objects.create(
                        approval_request=approval,
                        workflow_level=approval.current_level,
                        approver=request.user,
                        status=action,
                        comments=comments
                    )
                    
                    # Update approval request status
                    if action == 'approve':
                        approval.status = 'approved'
                        approval.approved_by = request.user
                        approval.approved_at = timezone.now()
                    elif action == 'reject':
                        approval.status = 'rejected'
                        approval.rejected_by = request.user
                        approval.rejected_at = timezone.now()
                    
                    approval.save()
                    
                    # Create audit log
                    ApprovalAuditLog.objects.create(
                        approval_request=approval,
                        user=request.user,
                        action=action,
                        description=f"Bulk {action} by {request.user.username}",
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
            
            messages.success(request, f'{approvals.count()} requests {action} successfully.')
            return redirect('approval_workflow:my_approvals')
    else:
        form = BulkApprovalForm()
    
    return render(request, 'approval_workflow/bulk_approve.html', {'form': form})
