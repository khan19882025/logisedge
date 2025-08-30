from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models.functions import TruncMonth
import json
import os
from datetime import datetime, timedelta
from decimal import Decimal

from .models import (
    ExitType, ClearanceDepartment, ClearanceItem, ResignationRequest,
    ClearanceProcess, ClearanceItemStatus, GratuityCalculation,
    FinalSettlement, ExitDocument, ExitAuditLog, ExitConfiguration
)
from .forms import (
    ExitTypeForm, ClearanceDepartmentForm, ClearanceItemForm,
    ResignationRequestForm, ResignationApprovalForm, ClearanceItemStatusForm,
    GratuityCalculationForm, FinalSettlementForm, ExitDocumentForm,
    ExitConfigurationForm, ResignationSearchForm, ClearanceSearchForm,
    GratuitySearchForm, SettlementSearchForm, BulkClearanceForm,
    NoticePeriodCalculationForm, ExitReportForm
)
from employees.models import Employee


@login_required
@permission_required('exit_management.view_resignationrequest')
def dashboard(request):
    """Dashboard view for Exit Management"""
    # Get statistics
    total_resignations = ResignationRequest.objects.count()
    pending_resignations = ResignationRequest.objects.filter(status='pending').count()
    approved_resignations = ResignationRequest.objects.filter(status='approved').count()
    completed_exits = ResignationRequest.objects.filter(status='completed').count()
    
    # Recent resignations
    recent_resignations = ResignationRequest.objects.select_related(
        'employee', 'exit_type'
    ).order_by('-submitted_at')[:5]
    
    # Resignations by status
    resignations_by_status = ResignationRequest.objects.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    # Clearance processes
    active_clearances = ClearanceProcess.objects.filter(is_completed=False).count()
    completed_clearances = ClearanceProcess.objects.filter(is_completed=True).count()
    
    # Gratuity calculations
    total_gratuity_paid = GratuityCalculation.objects.aggregate(
        total=Sum('final_gratuity')
    )['total'] or 0
    
    # Monthly attrition trend
    monthly_attrition = ResignationRequest.objects.filter(
        submitted_at__year=timezone.now().year
    ).annotate(
        month=TruncMonth('submitted_at')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    # Exit reasons
    exit_reasons = ResignationRequest.objects.values('exit_type__name').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    context = {
        'total_resignations': total_resignations,
        'pending_resignations': pending_resignations,
        'approved_resignations': approved_resignations,
        'completed_exits': completed_exits,
        'recent_resignations': recent_resignations,
        'resignations_by_status': resignations_by_status,
        'active_clearances': active_clearances,
        'completed_clearances': completed_clearances,
        'total_gratuity_paid': total_gratuity_paid,
        'monthly_attrition': monthly_attrition,
        'exit_reasons': exit_reasons,
    }
    
    return render(request, 'exit_management/dashboard.html', context)


# Exit Type Views
class ExitTypeListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = ExitType
    template_name = 'exit_management/exit_type_list.html'
    context_object_name = 'exit_types'
    permission_required = 'exit_management.view_exittype'
    
    def get_queryset(self):
        queryset = ExitType.objects.all().order_by('name')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        return queryset


class ExitTypeCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = ExitType
    form_class = ExitTypeForm
    template_name = 'exit_management/exit_type_form.html'
    permission_required = 'exit_management.add_exittype'
    success_url = reverse_lazy('exit_management:exit_type_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Exit type created successfully.')
        return super().form_valid(form)


class ExitTypeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = ExitType
    form_class = ExitTypeForm
    template_name = 'exit_management/exit_type_form.html'
    permission_required = 'exit_management.change_exittype'
    success_url = reverse_lazy('exit_management:exit_type_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Exit type updated successfully.')
        return super().form_valid(form)


class ExitTypeDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = ExitType
    template_name = 'exit_management/exit_type_confirm_delete.html'
    permission_required = 'exit_management.delete_exittype'
    success_url = reverse_lazy('exit_management:exit_type_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Exit type deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Clearance Department Views
class ClearanceDepartmentListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = ClearanceDepartment
    template_name = 'exit_management/clearance_department_list.html'
    context_object_name = 'departments'
    permission_required = 'exit_management.view_clearancedepartment'


class ClearanceDepartmentCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = ClearanceDepartment
    form_class = ClearanceDepartmentForm
    template_name = 'exit_management/clearance_department_form.html'
    permission_required = 'exit_management.add_clearancedepartment'
    success_url = reverse_lazy('exit_management:clearance_department_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Clearance department created successfully.')
        return super().form_valid(form)


class ClearanceDepartmentUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = ClearanceDepartment
    form_class = ClearanceDepartmentForm
    template_name = 'exit_management/clearance_department_form.html'
    permission_required = 'exit_management.change_clearancedepartment'
    success_url = reverse_lazy('exit_management:clearance_department_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Clearance department updated successfully.')
        return super().form_valid(form)


class ClearanceDepartmentDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = ClearanceDepartment
    template_name = 'exit_management/clearance_department_confirm_delete.html'
    permission_required = 'exit_management.delete_clearancedepartment'
    success_url = reverse_lazy('exit_management:clearance_department_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Clearance department deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Clearance Item Views
class ClearanceItemListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = ClearanceItem
    template_name = 'exit_management/clearance_item_list.html'
    context_object_name = 'items'
    permission_required = 'exit_management.view_clearanceitem'
    
    def get_queryset(self):
        queryset = ClearanceItem.objects.select_related('department').all().order_by('department__order', 'order')
        department = self.request.GET.get('department')
        if department:
            queryset = queryset.filter(department_id=department)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = ClearanceDepartment.objects.filter(is_active=True)
        return context


class ClearanceItemCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = ClearanceItem
    form_class = ClearanceItemForm
    template_name = 'exit_management/clearance_item_form.html'
    permission_required = 'exit_management.add_clearanceitem'
    success_url = reverse_lazy('exit_management:clearance_item_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Clearance item created successfully.')
        return super().form_valid(form)


class ClearanceItemUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = ClearanceItem
    form_class = ClearanceItemForm
    template_name = 'exit_management/clearance_item_form.html'
    permission_required = 'exit_management.change_clearanceitem'
    success_url = reverse_lazy('exit_management:clearance_item_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Clearance item updated successfully.')
        return super().form_valid(form)


class ClearanceItemDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = ClearanceItem
    template_name = 'exit_management/clearance_item_confirm_delete.html'
    permission_required = 'exit_management.delete_clearanceitem'
    success_url = reverse_lazy('exit_management:clearance_item_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Clearance item deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Resignation Request Views
class ResignationRequestListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = ResignationRequest
    template_name = 'exit_management/resignation_request_list.html'
    context_object_name = 'resignations'
    permission_required = 'exit_management.view_resignationrequest'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = ResignationRequest.objects.select_related(
            'employee', 'exit_type', 'manager', 'hr_manager'
        ).all().order_by('-submitted_at')
        
        form = ResignationSearchForm(self.request.GET)
        if form.is_valid():
            search = form.cleaned_data.get('search')
            status = form.cleaned_data.get('status')
            exit_type = form.cleaned_data.get('exit_type')
            date_from = form.cleaned_data.get('date_from')
            date_to = form.cleaned_data.get('date_to')
            department = form.cleaned_data.get('department')
            
            if search:
                queryset = queryset.filter(
                    Q(reference_number__icontains=search) |
                    Q(employee__full_name__icontains=search) |
                    Q(exit_type__name__icontains=search) |
                    Q(reason__icontains=search)
                )
            if status:
                queryset = queryset.filter(status=status)
            if exit_type:
                queryset = queryset.filter(exit_type=exit_type)
            if date_from:
                queryset = queryset.filter(resignation_date__gte=date_from)
            if date_to:
                queryset = queryset.filter(resignation_date__lte=date_to)
            if department:
                queryset = queryset.filter(employee__department=department)
                
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ResignationSearchForm(self.request.GET)
        context['exit_types'] = ExitType.objects.filter(is_active=True)
        return context


class ResignationRequestDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = ResignationRequest
    template_name = 'exit_management/resignation_request_detail.html'
    context_object_name = 'resignation'
    permission_required = 'exit_management.view_resignationrequest'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['audit_logs'] = self.object.audit_logs.all()[:10]
        
        # Check if clearance process exists
        if hasattr(self.object, 'clearance_process'):
            context['clearance_process'] = self.object.clearance_process
            context['clearance_items'] = self.object.clearance_process.clearance_items.select_related('clearance_item')
        
        # Check if gratuity calculation exists
        if hasattr(self.object, 'gratuity_calculation'):
            context['gratuity_calculation'] = self.object.gratuity_calculation
        
        # Check if final settlement exists
        if hasattr(self.object, 'final_settlement'):
            context['final_settlement'] = self.object.final_settlement
        
        # Get exit documents
        context['exit_documents'] = self.object.exit_documents.all()
        
        return context


class ResignationRequestCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = ResignationRequest
    form_class = ResignationRequestForm
    template_name = 'exit_management/resignation_request_form.html'
    permission_required = 'exit_management.add_resignationrequest'
    success_url = reverse_lazy('exit_management:resignation_request_list')
    
    def form_valid(self, form):
        resignation = form.save(commit=False)
        resignation.manager = self.request.user  # Set current user as manager initially
        resignation.save()
        
        # Create audit log
        ExitAuditLog.objects.create(
            resignation=resignation,
            action='resignation_submitted',
            user=self.request.user,
            details=f'Resignation request submitted by {self.request.user.get_full_name()}'
        )
        
        messages.success(self.request, 'Resignation request submitted successfully.')
        return super().form_valid(form)


class ResignationRequestUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = ResignationRequest
    form_class = ResignationRequestForm
    template_name = 'exit_management/resignation_request_form.html'
    permission_required = 'exit_management.change_resignationrequest'
    success_url = reverse_lazy('exit_management:resignation_request_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Resignation request updated successfully.')
        return super().form_valid(form)


class ResignationRequestDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = ResignationRequest
    template_name = 'exit_management/resignation_request_confirm_delete.html'
    permission_required = 'exit_management.delete_resignationrequest'
    success_url = reverse_lazy('exit_management:resignation_request_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Resignation request deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Approval Views
@login_required
@permission_required('exit_management.change_resignationrequest')
def manager_approval(request, pk):
    """Manager approval of resignation request"""
    resignation = get_object_or_404(ResignationRequest, pk=pk)
    
    if request.method == 'POST':
        form = ResignationApprovalForm(request.POST, instance=resignation)
        if form.is_valid():
            resignation = form.save(commit=False)
            resignation.status = 'manager_review'
            resignation.manager_approval_date = timezone.now()
            resignation.save()
            
            # Create audit log
            ExitAuditLog.objects.create(
                resignation=resignation,
                action='manager_approved',
                user=request.user,
                details=f'Resignation approved by manager: {request.user.get_full_name()}'
            )
            
            messages.success(request, 'Resignation request approved by manager.')
            return redirect('exit_management:resignation_request_detail', pk=resignation.pk)
    else:
        form = ResignationApprovalForm(instance=resignation)
    
    return render(request, 'exit_management/resignation_approval.html', {
        'form': form, 'resignation': resignation, 'approval_type': 'manager'
    })


@login_required
@permission_required('exit_management.change_resignationrequest')
def hr_approval(request, pk):
    """HR approval of resignation request"""
    resignation = get_object_or_404(ResignationRequest, pk=pk)
    
    if request.method == 'POST':
        form = ResignationApprovalForm(request.POST, instance=resignation)
        if form.is_valid():
            resignation = form.save(commit=False)
            resignation.status = 'approved'
            resignation.hr_approval_date = timezone.now()
            resignation.save()
            
            # Create audit log
            ExitAuditLog.objects.create(
                resignation=resignation,
                action='hr_approved',
                user=request.user,
                details=f'Resignation approved by HR: {request.user.get_full_name()}'
            )
            
            messages.success(request, 'Resignation request approved by HR.')
            return redirect('exit_management:resignation_request_detail', pk=resignation.pk)
    else:
        form = ResignationApprovalForm(instance=resignation)
    
    return render(request, 'exit_management/resignation_approval.html', {
        'form': form, 'resignation': resignation, 'approval_type': 'hr'
    })


# Clearance Process Views
@login_required
@permission_required('exit_management.add_clearanceprocess')
def start_clearance_process(request, pk):
    """Start clearance process for a resignation request"""
    resignation = get_object_or_404(ResignationRequest, pk=pk)
    
    if hasattr(resignation, 'clearance_process'):
        messages.warning(request, 'Clearance process already exists for this resignation.')
        return redirect('exit_management:resignation_request_detail', pk=resignation.pk)
    
    # Create clearance process
    clearance_process = ClearanceProcess.objects.create(resignation=resignation)
    
    # Create clearance item statuses for all active items
    clearance_items = ClearanceItem.objects.filter(is_active=True)
    for item in clearance_items:
        ClearanceItemStatus.objects.create(
            clearance_process=clearance_process,
            clearance_item=item
        )
    
    # Create audit log
    ExitAuditLog.objects.create(
        resignation=resignation,
        action='clearance_started',
        user=request.user,
        details=f'Clearance process started by {request.user.get_full_name()}'
    )
    
    messages.success(request, 'Clearance process started successfully.')
    return redirect('exit_management:clearance_process_detail', pk=clearance_process.pk)


@login_required
@permission_required('exit_management.view_clearanceprocess')
def clearance_process_detail(request, pk):
    """Detail view for clearance process"""
    clearance_process = get_object_or_404(ClearanceProcess, pk=pk)
    
    return render(request, 'exit_management/clearance_process_detail.html', {
        'clearance_process': clearance_process
    })


@login_required
@permission_required('exit_management.change_clearanceitemstatus')
def update_clearance_item(request, pk):
    """Update clearance item status"""
    clearance_item_status = get_object_or_404(ClearanceItemStatus, pk=pk)
    
    if request.method == 'POST':
        form = ClearanceItemStatusForm(request.POST, instance=clearance_item_status)
        if form.is_valid():
            clearance_item_status = form.save(commit=False)
            if form.cleaned_data['status'] == 'cleared':
                clearance_item_status.cleared_by = request.user
                clearance_item_status.cleared_at = timezone.now()
            clearance_item_status.save()
            
            messages.success(request, 'Clearance item status updated successfully.')
            return redirect('exit_management:clearance_process_detail', pk=clearance_item_status.clearance_process.pk)
    else:
        form = ClearanceItemStatusForm(instance=clearance_item_status)
    
    return render(request, 'exit_management/clearance_item_update.html', {
        'form': form, 'clearance_item_status': clearance_item_status
    })


# Gratuity Calculation Views
@login_required
@permission_required('exit_management.add_gratuitycalculation')
def calculate_gratuity(request, pk):
    """Calculate gratuity for a resignation request"""
    resignation = get_object_or_404(ResignationRequest, pk=pk)
    
    if hasattr(resignation, 'gratuity_calculation'):
        messages.warning(request, 'Gratuity calculation already exists for this resignation.')
        return redirect('exit_management:resignation_request_detail', pk=resignation.pk)
    
    if request.method == 'POST':
        form = GratuityCalculationForm(request.POST, resignation=resignation)
        if form.is_valid():
            gratuity_calculation = form.save(commit=False)
            gratuity_calculation.resignation = resignation
            gratuity_calculation.calculated_by = request.user
            gratuity_calculation.calculate_gratuity()
            gratuity_calculation.save()
            
            # Create audit log
            ExitAuditLog.objects.create(
                resignation=resignation,
                action='gratuity_calculated',
                user=request.user,
                details=f'Gratuity calculated by {request.user.get_full_name()}: AED {gratuity_calculation.final_gratuity}'
            )
            
            messages.success(request, 'Gratuity calculated successfully.')
            return redirect('exit_management:resignation_request_detail', pk=resignation.pk)
    else:
        form = GratuityCalculationForm(resignation=resignation)
    
    return render(request, 'exit_management/gratuity_calculation_form.html', {
        'form': form, 'resignation': resignation
    })


@login_required
@permission_required('exit_management.change_gratuitycalculation')
def update_gratuity_calculation(request, pk):
    """Update gratuity calculation"""
    gratuity_calculation = get_object_or_404(GratuityCalculation, pk=pk)
    
    if request.method == 'POST':
        form = GratuityCalculationForm(request.POST, instance=gratuity_calculation)
        if form.is_valid():
            gratuity_calculation = form.save(commit=False)
            gratuity_calculation.calculate_gratuity()
            gratuity_calculation.save()
            
            messages.success(request, 'Gratuity calculation updated successfully.')
            return redirect('exit_management:resignation_request_detail', pk=gratuity_calculation.resignation.pk)
    else:
        form = GratuityCalculationForm(instance=gratuity_calculation)
    
    return render(request, 'exit_management/gratuity_calculation_form.html', {
        'form': form, 'resignation': gratuity_calculation.resignation
    })


# Final Settlement Views
@login_required
@permission_required('exit_management.add_finalsettlement')
def create_final_settlement(request, pk):
    """Create final settlement for a resignation request"""
    resignation = get_object_or_404(ResignationRequest, pk=pk)
    
    if hasattr(resignation, 'final_settlement'):
        messages.warning(request, 'Final settlement already exists for this resignation.')
        return redirect('exit_management:resignation_request_detail', pk=resignation.pk)
    
    if request.method == 'POST':
        form = FinalSettlementForm(request.POST)
        if form.is_valid():
            final_settlement = form.save(commit=False)
            final_settlement.resignation = resignation
            
            # Get gratuity amount if available
            if hasattr(resignation, 'gratuity_calculation'):
                final_settlement.gratuity_amount = resignation.gratuity_calculation.final_gratuity
            
            final_settlement.calculate_settlement()
            final_settlement.save()
            
            # Create audit log
            ExitAuditLog.objects.create(
                resignation=resignation,
                action='settlement_processed',
                user=request.user,
                details=f'Final settlement created by {request.user.get_full_name()}: AED {final_settlement.net_settlement}'
            )
            
            messages.success(request, 'Final settlement created successfully.')
            return redirect('exit_management:resignation_request_detail', pk=resignation.pk)
    else:
        form = FinalSettlementForm()
    
    return render(request, 'exit_management/final_settlement_form.html', {
        'form': form, 'resignation': resignation
    })


@login_required
@permission_required('exit_management.change_finalsettlement')
def update_final_settlement(request, pk):
    """Update final settlement"""
    final_settlement = get_object_or_404(FinalSettlement, pk=pk)
    
    if request.method == 'POST':
        form = FinalSettlementForm(request.POST, instance=final_settlement)
        if form.is_valid():
            final_settlement = form.save(commit=False)
            final_settlement.calculate_settlement()
            final_settlement.save()
            
            messages.success(request, 'Final settlement updated successfully.')
            return redirect('exit_management:resignation_request_detail', pk=final_settlement.resignation.pk)
    else:
        form = FinalSettlementForm(instance=final_settlement)
    
    return render(request, 'exit_management/final_settlement_form.html', {
        'form': form, 'resignation': final_settlement.resignation
    })


# AJAX Views
@login_required
@require_http_methods(["POST"])
def calculate_notice_period(request):
    """AJAX endpoint to calculate notice period"""
    resignation_date = request.POST.get('resignation_date')
    notice_period_days = int(request.POST.get('notice_period_days', 30))
    
    if resignation_date:
        try:
            resignation_date = datetime.strptime(resignation_date, '%Y-%m-%d').date()
            last_working_day = resignation_date + timedelta(days=notice_period_days)
            
            return JsonResponse({
                'success': True,
                'last_working_day': last_working_day.strftime('%Y-%m-%d'),
                'notice_period_days': notice_period_days
            })
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid date format'})
    
    return JsonResponse({'success': False, 'error': 'Resignation date required'})


@login_required
@require_http_methods(["GET"])
def get_employee_details(request):
    """Get employee details for resignation"""
    employee_id = request.GET.get('employee_id')
    if employee_id:
        try:
            employee = Employee.objects.get(id=employee_id)
            data = {
                'full_name': employee.full_name,
                'designation': employee.designation or 'N/A',
                'department': employee.department.name if employee.department else 'N/A',
                'employee_id': employee.employee_id or 'N/A',
                'date_of_joining': employee.date_of_joining.strftime('%Y-%m-%d') if employee.date_of_joining else 'N/A',
                'salary': employee.salary or 0,
                'years_service': round((timezone.now().date() - employee.date_of_joining).days / 365.25, 2) if employee.date_of_joining else 0,
            }
            return JsonResponse(data)
        except Employee.DoesNotExist:
            return JsonResponse({'error': 'Employee not found'}, status=404)
    return JsonResponse({'error': 'Employee ID required'}, status=400)


@login_required
@require_http_methods(["POST"])
def bulk_update_clearance(request, pk):
    """Bulk update clearance items"""
    clearance_process = get_object_or_404(ClearanceProcess, pk=pk)
    
    if request.method == 'POST':
        form = BulkClearanceForm(request.POST)
        if form.is_valid():
            clearance_items = form.cleaned_data.get('clearance_items')
            status = form.cleaned_data.get('status')
            comments = form.cleaned_data.get('comments')
            
            updated_count = 0
            for item in clearance_items:
                clearance_item_status, created = ClearanceItemStatus.objects.get_or_create(
                    clearance_process=clearance_process,
                    clearance_item=item,
                    defaults={'status': status, 'comments': comments}
                )
                if not created:
                    clearance_item_status.status = status
                    clearance_item_status.comments = comments
                    clearance_item_status.save()
                updated_count += 1
            
            return JsonResponse({
                'success': True,
                'message': f'{updated_count} clearance items updated successfully'
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})


# Report Views
@login_required
@permission_required('exit_management.view_resignationrequest')
def exit_reports(request):
    """Generate exit management reports"""
    if request.method == 'POST':
        form = ExitReportForm(request.POST)
        if form.is_valid():
            report_type = form.cleaned_data.get('report_type')
            date_from = form.cleaned_data.get('date_from')
            date_to = form.cleaned_data.get('date_to')
            department = form.cleaned_data.get('department')
            export_format = form.cleaned_data.get('export_format')
            
            # Generate report based on type
            if report_type == 'attrition':
                data = generate_attrition_report(date_from, date_to, department)
            elif report_type == 'gratuity':
                data = generate_gratuity_report(date_from, date_to, department)
            elif report_type == 'clearance':
                data = generate_clearance_report(date_from, date_to, department)
            elif report_type == 'settlement':
                data = generate_settlement_report(date_from, date_to, department)
            elif report_type == 'exit_reasons':
                data = generate_exit_reasons_report(date_from, date_to, department)
            
            # Handle export
            if export_format == 'pdf':
                return generate_pdf_report(data, report_type)
            elif export_format == 'excel':
                return generate_excel_report(data, report_type)
            elif export_format == 'csv':
                return generate_csv_report(data, report_type)
            
            return render(request, 'exit_management/report_results.html', {
                'data': data, 'report_type': report_type
            })
    else:
        form = ExitReportForm()
    
    return render(request, 'exit_management/exit_reports.html', {'form': form})


# Helper functions for reports
def generate_attrition_report(date_from, date_to, department):
    """Generate attrition report"""
    queryset = ResignationRequest.objects.filter(
        submitted_at__date__range=[date_from, date_to]
    )
    
    if department:
        queryset = queryset.filter(employee__department=department)
    
    return {
        'total_resignations': queryset.count(),
        'by_status': queryset.values('status').annotate(count=Count('id')),
        'by_month': queryset.annotate(month=TruncMonth('submitted_at')).values('month').annotate(count=Count('id')),
        'by_department': queryset.values('employee__department__name').annotate(count=Count('id')),
    }


def generate_gratuity_report(date_from, date_to, department):
    """Generate gratuity report"""
    queryset = GratuityCalculation.objects.filter(
        calculation_date__range=[date_from, date_to]
    )
    
    if department:
        queryset = queryset.filter(resignation__employee__department=department)
    
    return {
        'total_gratuity': queryset.aggregate(total=Sum('final_gratuity'))['total'] or 0,
        'average_gratuity': queryset.aggregate(avg=Avg('final_gratuity'))['avg'] or 0,
        'by_contract_type': queryset.values('contract_type').annotate(
            total=Sum('final_gratuity'), count=Count('id')
        ),
        'by_years_service': queryset.values('total_years_service').annotate(
            total=Sum('final_gratuity'), count=Count('id')
        ),
    }


def generate_clearance_report(date_from, date_to, department):
    """Generate clearance report"""
    queryset = ClearanceProcess.objects.filter(
        created_at__date__range=[date_from, date_to]
    )
    
    if department:
        queryset = queryset.filter(resignation__employee__department=department)
    
    return {
        'total_clearances': queryset.count(),
        'completed_clearances': queryset.filter(is_completed=True).count(),
        'pending_clearances': queryset.filter(is_completed=False).count(),
        'average_completion_time': queryset.filter(is_completed=True).aggregate(
            avg_time=Avg('completed_at' - 'created_at')
        )['avg_time'],
    }


def generate_settlement_report(date_from, date_to, department):
    """Generate settlement report"""
    queryset = FinalSettlement.objects.filter(
        created_at__date__range=[date_from, date_to]
    )
    
    if department:
        queryset = queryset.filter(resignation__employee__department=department)
    
    return {
        'total_settlements': queryset.count(),
        'total_amount': queryset.aggregate(total=Sum('net_settlement'))['total'] or 0,
        'average_settlement': queryset.aggregate(avg=Avg('net_settlement'))['avg'] or 0,
        'processed_settlements': queryset.filter(is_processed=True).count(),
        'pending_settlements': queryset.filter(is_processed=False).count(),
    }


def generate_exit_reasons_report(date_from, date_to, department):
    """Generate exit reasons report"""
    queryset = ResignationRequest.objects.filter(
        submitted_at__date__range=[date_from, date_to]
    )
    
    if department:
        queryset = queryset.filter(employee__department=department)
    
    return {
        'by_exit_type': queryset.values('exit_type__name').annotate(count=Count('id')),
        'by_reason': queryset.values('reason').annotate(count=Count('id')),
        'trend_by_month': queryset.annotate(month=TruncMonth('submitted_at')).values('month').annotate(count=Count('id')),
    }


# Export functions (placeholder implementations)
def generate_pdf_report(data, report_type):
    """Generate PDF report"""
    # Placeholder - implement PDF generation
    return HttpResponse("PDF report generation not implemented yet")


def generate_excel_report(data, report_type):
    """Generate Excel report"""
    # Placeholder - implement Excel generation
    return HttpResponse("Excel report generation not implemented yet")


def generate_csv_report(data, report_type):
    """Generate CSV report"""
    # Placeholder - implement CSV generation
    return HttpResponse("CSV report generation not implemented yet")
