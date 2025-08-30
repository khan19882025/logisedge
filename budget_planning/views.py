from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q, DecimalField
from django.db.models.functions import Coalesce
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from decimal import Decimal
import json
from datetime import datetime, timedelta

from .models import (
    BudgetPlan, BudgetItem, BudgetTemplate, BudgetTemplateItem,
    BudgetApproval, BudgetImport, BudgetAuditLog, BudgetVarianceAlert,
    BudgetVarianceNotification, BudgetVsActualReport
)
from .forms import (
    BudgetPlanForm, BudgetItemForm, BudgetItemBulkForm,
    BudgetApprovalForm, BudgetTemplateForm, BudgetTemplateItemForm,
    BudgetSearchForm, BudgetImportForm, BudgetVarianceReportForm,
    BudgetVarianceAlertForm, BudgetVsActualReportForm, BudgetVarianceNotificationForm
)
from cost_center_management.models import CostCenter, Department
from chart_of_accounts.models import ChartOfAccount


@login_required
def dashboard(request):
    """Dashboard view for budget planning"""
    # Get statistics
    total_budgets = BudgetPlan.objects.count()
    total_approved_budgets = BudgetPlan.objects.filter(status='approved').count()
    total_draft_budgets = BudgetPlan.objects.filter(status='draft').count()
    total_pending_budgets = BudgetPlan.objects.filter(status='submitted').count()
    
    # Get recent budgets
    recent_budgets = BudgetPlan.objects.order_by('-created_at')[:5]
    
    # Get budget statistics by status
    budget_status_stats = BudgetPlan.objects.values('status').annotate(
        count=Count('id'),
        total_amount=Sum('total_budget_amount')
    ).order_by('status')
    
    # Calculate percentages for budget status stats
    for stat in budget_status_stats:
        if total_budgets > 0:
            stat['percentage'] = (stat['count'] / total_budgets) * 100
        else:
            stat['percentage'] = 0
    
    # Get top cost centers by budget amount
    cost_center_stats = CostCenter.objects.filter(is_active=True).annotate(
        budget_count=Count('budget_items'),
        total_budget_amount=Coalesce(Sum('budget_items__budget_amount'), Decimal('0.00')),
        total_actual_amount=Coalesce(Sum('budget_items__actual_amount'), Decimal('0.00'))
    ).filter(budget_count__gt=0).order_by('-total_budget_amount')[:10]
    
    # Calculate percentages for cost centers
    total_budget_amount = sum(stat.total_budget_amount for stat in cost_center_stats)
    for stat in cost_center_stats:
        if total_budget_amount > 0:
            stat.percentage = (stat.total_budget_amount / total_budget_amount) * 100
        else:
            stat.percentage = 0
        
        # Calculate variance (budget - actual)
        stat.variance = stat.total_budget_amount - stat.total_actual_amount
    
    context = {
        'total_budgets': total_budgets,
        'total_approved_budgets': total_approved_budgets,
        'total_draft_budgets': total_draft_budgets,
        'total_pending_budgets': total_pending_budgets,
        'recent_budgets': recent_budgets,
        'budget_status_stats': budget_status_stats,
        'cost_center_stats': cost_center_stats,
    }
    
    return render(request, 'budget_planning/dashboard.html', context)


@login_required
def budget_list(request):
    """List view for budget plans"""
    budgets = BudgetPlan.objects.all()
    
    # Apply search filters
    search_form = BudgetSearchForm(request.GET)
    if search_form.is_valid():
        if search_form.cleaned_data.get('budget_code'):
            budgets = budgets.filter(budget_code__icontains=search_form.cleaned_data['budget_code'])
        if search_form.cleaned_data.get('budget_name'):
            budgets = budgets.filter(budget_name__icontains=search_form.cleaned_data['budget_name'])
        if search_form.cleaned_data.get('fiscal_year'):
            budgets = budgets.filter(fiscal_year=search_form.cleaned_data['fiscal_year'])
        if search_form.cleaned_data.get('budget_period'):
            budgets = budgets.filter(budget_period=search_form.cleaned_data['budget_period'])
        if search_form.cleaned_data.get('status'):
            budgets = budgets.filter(status=search_form.cleaned_data['status'])
    
    # Pagination
    paginator = Paginator(budgets, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
    }
    
    return render(request, 'budget_planning/budget_list.html', context)


@login_required
def budget_create(request):
    """Create a new budget plan"""
    if request.method == 'POST':
        form = BudgetPlanForm(request.POST)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.created_by = request.user
            budget.save()
            messages.success(request, 'Budget plan created successfully.')
            return redirect('budget_planning:budget_detail', pk=budget.pk)
    else:
        form = BudgetPlanForm()
    
    context = {
        'form': form,
        'title': 'Create Budget Plan'
    }
    
    return render(request, 'budget_planning/budget_form.html', context)


@login_required
def budget_detail(request, pk):
    """Detail view for budget plan"""
    budget = get_object_or_404(BudgetPlan, pk=pk)
    budget_items = budget.budget_items.all()
    
    context = {
        'budget': budget,
        'budget_items': budget_items,
    }
    
    return render(request, 'budget_planning/budget_detail.html', context)


@login_required
def budget_edit(request, pk):
    """Edit a budget plan"""
    budget = get_object_or_404(BudgetPlan, pk=pk)
    
    if request.method == 'POST':
        form = BudgetPlanForm(request.POST, instance=budget)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.updated_by = request.user
            budget.save()
            messages.success(request, 'Budget plan updated successfully.')
            return redirect('budget_planning:budget_detail', pk=budget.pk)
    else:
        form = BudgetPlanForm(instance=budget)
    
    context = {
        'form': form,
        'budget': budget,
        'title': 'Edit Budget Plan'
    }
    
    return render(request, 'budget_planning/budget_form.html', context)


@login_required
def budget_delete(request, pk):
    """Delete a budget plan"""
    budget = get_object_or_404(BudgetPlan, pk=pk)
    
    if request.method == 'POST':
        budget.delete()
        messages.success(request, 'Budget plan deleted successfully.')
        return redirect('budget_planning:budget_list')
    
    context = {
        'budget': budget,
    }
    
    return render(request, 'budget_planning/budget_confirm_delete.html', context)


@login_required
def budget_item_create(request, budget_pk):
    """Create a new budget item"""
    budget = get_object_or_404(BudgetPlan, pk=budget_pk)
    
    if request.method == 'POST':
        form = BudgetItemForm(request.POST)
        if form.is_valid():
            budget_item = form.save(commit=False)
            budget_item.budget_plan = budget
            budget_item.created_by = request.user
            budget_item.save()
            messages.success(request, 'Budget item created successfully.')
            return redirect('budget_planning:budget_detail', pk=budget.pk)
    else:
        form = BudgetItemForm()
    
    context = {
        'form': form,
        'budget': budget,
        'title': 'Create Budget Item'
    }
    
    return render(request, 'budget_planning/budget_item_form.html', context)


@login_required
def budget_item_edit(request, pk):
    """Edit a budget item"""
    budget_item = get_object_or_404(BudgetItem, pk=pk)
    
    if request.method == 'POST':
        form = BudgetItemForm(request.POST, instance=budget_item)
        if form.is_valid():
            budget_item = form.save(commit=False)
            budget_item.updated_by = request.user
            budget_item.save()
            messages.success(request, 'Budget item updated successfully.')
            return redirect('budget_planning:budget_detail', pk=budget_item.budget_plan.pk)
    else:
        form = BudgetItemForm(instance=budget_item)
    
    context = {
        'form': form,
        'budget_item': budget_item,
        'title': 'Edit Budget Item'
    }
    
    return render(request, 'budget_planning/budget_item_form.html', context)


@login_required
def budget_item_delete(request, pk):
    """Delete a budget item"""
    budget_item = get_object_or_404(BudgetItem, pk=pk)
    
    if request.method == 'POST':
        budget_plan_pk = budget_item.budget_plan.pk
        budget_item.delete()
        messages.success(request, 'Budget item deleted successfully.')
        return redirect('budget_planning:budget_detail', pk=budget_plan_pk)
    
    context = {
        'budget_item': budget_item,
    }
    
    return render(request, 'budget_planning/budget_item_confirm_delete.html', context)


@login_required
@permission_required('budget_planning.can_approve_budget', raise_exception=True)
def budget_approve(request, pk):
    """Approve or reject a budget plan"""
    budget = get_object_or_404(BudgetPlan, pk=pk)
    
    if request.method == 'POST':
        form = BudgetApprovalForm(request.POST)
        if form.is_valid():
            approval = form.save(commit=False)
            approval.budget_plan = budget
            approval.approved_by = request.user
            approval.save()
            
            # Update budget status
            if approval.approval_type == 'approve':
                budget.status = 'approved'
                budget.approved_by = request.user
                budget.approved_at = timezone.now()
                budget.save()
                messages.success(request, 'Budget plan approved successfully.')
            elif approval.approval_type == 'reject':
                budget.status = 'rejected'
                budget.save()
                messages.success(request, 'Budget plan rejected successfully.')
            elif approval.approval_type == 'return':
                budget.status = 'draft'
                budget.save()
                messages.success(request, 'Budget plan returned for revision.')
            
            return redirect('budget_planning:budget_detail', pk=budget.pk)
    else:
        form = BudgetApprovalForm()
    
    context = {
        'form': form,
        'budget': budget,
    }
    
    return render(request, 'budget_planning/budget_approve.html', context)


@login_required
def budget_import(request):
    """Import budgets from Excel file"""
    if request.method == 'POST':
        form = BudgetImportForm(request.POST, request.FILES)
        if form.is_valid():
            # Handle file import logic here
            messages.success(request, 'Budget import completed successfully.')
            return redirect('budget_planning:budget_list')
    else:
        form = BudgetImportForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'budget_planning/budget_import.html', context)


@login_required
def budget_variance_report(request):
    """Generate budget variance report"""
    if request.method == 'POST':
        form = BudgetVarianceReportForm(request.POST)
        if form.is_valid():
            # Generate report based on form data
            # This is a placeholder - actual implementation would generate the report
            messages.success(request, 'Report generated successfully.')
            return redirect('budget_planning:budget_list')
    else:
        form = BudgetVarianceReportForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'budget_planning/budget_variance_report.html', context)


@login_required
def budget_template_list(request):
    """List view for budget templates"""
    templates = BudgetTemplate.objects.all()
    
    context = {
        'templates': templates,
    }
    
    return render(request, 'budget_planning/budget_template_list.html', context)


@login_required
def budget_template_create(request):
    """Create a new budget template"""
    if request.method == 'POST':
        form = BudgetTemplateForm(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            template.created_by = request.user
            template.save()
            messages.success(request, 'Budget template created successfully.')
            return redirect('budget_planning:budget_template_list')
    else:
        form = BudgetTemplateForm()
    
    context = {
        'form': form,
        'title': 'Create Budget Template'
    }
    
    return render(request, 'budget_planning/budget_template_form.html', context)


@login_required
def budget_template_detail(request, pk):
    """Detail view for budget template"""
    template = get_object_or_404(BudgetTemplate, pk=pk)
    template_items = template.template_items.all()
    
    context = {
        'template': template,
        'template_items': template_items,
    }
    
    return render(request, 'budget_planning/budget_template_detail.html', context)


# API endpoints for AJAX requests
@login_required
def get_cost_centers_by_department(request):
    """Get cost centers for a specific department"""
    department_id = request.GET.get('department_id')
    if department_id:
        cost_centers = CostCenter.objects.filter(
            department_id=department_id,
            is_active=True
        ).values('id', 'code', 'name')
        return JsonResponse({'cost_centers': list(cost_centers)})
    return JsonResponse({'cost_centers': []})


@login_required
def get_accounts_by_type(request):
    """Get accounts by account type"""
    account_type = request.GET.get('account_type')
    if account_type:
        accounts = ChartOfAccount.objects.filter(
            account_type__category=account_type,
            is_active=True
        ).values('id', 'account_code', 'name')
        return JsonResponse({'accounts': list(accounts)})
    return JsonResponse({'accounts': []})


@login_required
def budget_summary_data(request):
    """Get budget summary data for charts"""
    # Get budget summary statistics
    total_budgets = BudgetPlan.objects.count()
    total_approved_budgets = BudgetPlan.objects.filter(status='approved').count()
    total_draft_budgets = BudgetPlan.objects.filter(status='draft').count()
    total_pending_budgets = BudgetPlan.objects.filter(status='submitted').count()
    
    # Get budget amounts by status
    budget_amounts = BudgetPlan.objects.values('status').annotate(
        total_amount=Sum('total_budget_amount')
    )
    
    data = {
        'total_budgets': total_budgets,
        'total_approved_budgets': total_approved_budgets,
        'total_draft_budgets': total_draft_budgets,
        'total_pending_budgets': total_pending_budgets,
        'budget_amounts': list(budget_amounts),
    }
    
    return JsonResponse(data)


# New views for Budget vs Actual Comparison
@login_required
def budget_vs_actual_dashboard(request):
    """Dashboard for Budget vs Actual Comparison"""
    # Get overall statistics
    total_budget_amount = BudgetItem.objects.aggregate(
        total=Sum('budget_amount')
    )['total'] or Decimal('0.00')
    
    total_actual_amount = BudgetItem.objects.aggregate(
        total=Sum('actual_amount')
    )['total'] or Decimal('0.00')
    
    total_variance = total_budget_amount - total_actual_amount
    variance_percentage = (total_variance / total_budget_amount * 100) if total_budget_amount > 0 else 0
    
    # Get top variances by cost center
    cost_center_variances = CostCenter.objects.filter(is_active=True).annotate(
        total_budget_amount=Coalesce(Sum('budget_items__budget_amount'), Decimal('0.00')),
        total_actual_amount=Coalesce(Sum('budget_items__actual_amount'), Decimal('0.00'))
    ).filter(total_budget_amount__gt=0).order_by('-total_budget_amount')[:10]
    
    for cost_center in cost_center_variances:
        cost_center.variance = cost_center.total_budget_amount - cost_center.total_actual_amount
        cost_center.variance_percentage = (cost_center.variance / cost_center.total_budget_amount * 100) if cost_center.total_budget_amount > 0 else 0
    
    # Get recent budget vs actual reports
    recent_reports = BudgetVsActualReport.objects.order_by('-generated_at')[:5]
    
    # Get active variance alerts
    active_alerts = BudgetVarianceAlert.objects.filter(is_active=True)[:5]
    
    context = {
        'total_budget_amount': total_budget_amount,
        'total_actual_amount': total_actual_amount,
        'total_variance': total_variance,
        'variance_percentage': variance_percentage,
        'cost_center_variances': cost_center_variances,
        'recent_reports': recent_reports,
        'active_alerts': active_alerts,
    }
    
    return render(request, 'budget_planning/budget_vs_actual_dashboard.html', context)


@login_required
def budget_vs_actual_report(request):
    """Generate Budget vs Actual report"""
    if request.method == 'POST':
        form = BudgetVsActualReportForm(request.POST)
        if form.is_valid():
            # Generate report based on form data
            report_data = generate_budget_vs_actual_data(form.cleaned_data)
            
            # Save report
            report = BudgetVsActualReport.objects.create(
                report_name=form.cleaned_data['report_name'],
                report_type=form.cleaned_data['report_type'],
                fiscal_year=form.cleaned_data['fiscal_year'],
                start_date=form.cleaned_data.get('start_date') or timezone.now().date(),
                end_date=form.cleaned_data.get('end_date') or timezone.now().date(),
                cost_center=form.cleaned_data.get('cost_center'),
                department=form.cleaned_data.get('department'),
                report_data=report_data,
                total_budget=report_data.get('total_budget', 0),
                total_actual=report_data.get('total_actual', 0),
                total_variance=report_data.get('total_variance', 0),
                variance_percentage=report_data.get('variance_percentage', 0),
                generated_by=request.user
            )
            
            messages.success(request, 'Budget vs Actual report generated successfully.')
            return redirect('budget_planning:budget_vs_actual_report_detail', pk=report.pk)
    else:
        form = BudgetVsActualReportForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'budget_planning/budget_vs_actual_report.html', context)


@login_required
def budget_vs_actual_report_detail(request, pk):
    """Detail view for Budget vs Actual report"""
    report = get_object_or_404(BudgetVsActualReport, pk=pk)
    
    context = {
        'report': report,
    }
    
    return render(request, 'budget_planning/budget_vs_actual_report_detail.html', context)


@login_required
def budget_variance_alerts(request):
    """List view for budget variance alerts"""
    alerts = BudgetVarianceAlert.objects.all()
    
    context = {
        'alerts': alerts,
    }
    
    return render(request, 'budget_planning/budget_variance_alerts.html', context)


@login_required
def budget_variance_alert_create(request):
    """Create a new budget variance alert"""
    if request.method == 'POST':
        form = BudgetVarianceAlertForm(request.POST)
        if form.is_valid():
            alert = form.save(commit=False)
            alert.created_by = request.user
            alert.save()
            form.save_m2m()  # Save many-to-many relationships
            messages.success(request, 'Variance alert created successfully.')
            return redirect('budget_planning:budget_variance_alerts')
    else:
        form = BudgetVarianceAlertForm()
    
    context = {
        'form': form,
        'title': 'Create Variance Alert'
    }
    
    return render(request, 'budget_planning/budget_variance_alert_form.html', context)


@login_required
def budget_variance_alert_edit(request, pk):
    """Edit a budget variance alert"""
    alert = get_object_or_404(BudgetVarianceAlert, pk=pk)
    
    if request.method == 'POST':
        form = BudgetVarianceAlertForm(request.POST, instance=alert)
        if form.is_valid():
            alert = form.save(commit=False)
            alert.save()
            form.save_m2m()  # Save many-to-many relationships
            messages.success(request, 'Variance alert updated successfully.')
            return redirect('budget_planning:budget_variance_alerts')
    else:
        form = BudgetVarianceAlertForm(instance=alert)
    
    context = {
        'form': form,
        'alert': alert,
        'title': 'Edit Variance Alert'
    }
    
    return render(request, 'budget_planning/budget_variance_alert_form.html', context)


@login_required
def budget_variance_notifications(request):
    """List view for budget variance notifications"""
    notifications = BudgetVarianceNotification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')
    
    context = {
        'notifications': notifications,
    }
    
    return render(request, 'budget_planning/budget_variance_notifications.html', context)


def generate_budget_vs_actual_data(form_data):
    """Generate budget vs actual data based on form parameters"""
    # This is a placeholder implementation
    # In a real application, this would query the database based on the form parameters
    
    data = {
        'total_budget': 0.00,
        'total_actual': 0.00,
        'total_variance': 0.00,
        'variance_percentage': 0.00,
        'items': [],
        'summary': {}
    }
    
    return data
