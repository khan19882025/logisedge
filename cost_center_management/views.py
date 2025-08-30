from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
import json
from datetime import datetime, timedelta
from decimal import Decimal

from .models import (
    Department, CostCenter, CostCenterBudget, CostCenterTransaction,
    CostCenterReport, CostCenterAuditLog
)
from .forms import (
    DepartmentForm, CostCenterForm, CostCenterBudgetForm, CostCenterTransactionForm,
    CostCenterSearchForm, CostCenterBudgetSearchForm, CostCenterTransactionSearchForm,
    CostCenterReportForm, CostCenterBulkUploadForm
)


@login_required
def dashboard(request):
    """Dashboard view for cost center management"""
    # Get summary statistics
    total_cost_centers = CostCenter.objects.filter(is_active=True).count()
    total_departments = Department.objects.filter(is_active=True).count()
    total_budgets = CostCenterBudget.objects.filter(is_active=True).count()
    total_transactions = CostCenterTransaction.objects.filter(is_active=True).count()
    
    # Get recent cost centers
    recent_cost_centers = CostCenter.objects.filter(is_active=True).order_by('-created_at')[:5]
    
    # Get cost centers with budget variances
    cost_centers_with_variance = []
    for cost_center in CostCenter.objects.filter(is_active=True, budget_amount__gt=0):
        variance = cost_center.budget_variance
        if abs(variance) > 0:
            cost_centers_with_variance.append({
                'cost_center': cost_center,
                'variance': variance,
                'utilization_percentage': cost_center.budget_utilization_percentage
            })
    
    # Sort by variance (highest first)
    cost_centers_with_variance.sort(key=lambda x: abs(x['variance']), reverse=True)
    
    context = {
        'total_cost_centers': total_cost_centers,
        'total_departments': total_departments,
        'total_budgets': total_budgets,
        'total_transactions': total_transactions,
        'recent_cost_centers': recent_cost_centers,
        'cost_centers_with_variance': cost_centers_with_variance[:5],
    }
    
    return render(request, 'cost_center_management/dashboard.html', context)


# Department Views
@login_required
@permission_required('cost_center_management.add_department')
def department_list(request):
    """List all departments"""
    departments = Department.objects.all().order_by('name')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        departments = departments.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(departments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    
    return render(request, 'cost_center_management/department_list.html', context)


@login_required
@permission_required('cost_center_management.add_department')
def department_create(request):
    """Create a new department"""
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            department = form.save(commit=False)
            department.created_by = request.user
            department.save()
            messages.success(request, f'Department "{department.name}" created successfully.')
            return redirect('cost_center_management:department_list')
    else:
        form = DepartmentForm()
    
    context = {
        'form': form,
        'title': 'Create Department',
    }
    
    return render(request, 'cost_center_management/department_form.html', context)


@login_required
@permission_required('cost_center_management.change_department')
def department_update(request, pk):
    """Update a department"""
    department = get_object_or_404(Department, pk=pk)
    
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            department = form.save(commit=False)
            department.updated_by = request.user
            department.save()
            messages.success(request, f'Department "{department.name}" updated successfully.')
            return redirect('cost_center_management:department_list')
    else:
        form = DepartmentForm(instance=department)
    
    context = {
        'form': form,
        'department': department,
        'title': 'Update Department',
    }
    
    return render(request, 'cost_center_management/department_form.html', context)


@login_required
@permission_required('cost_center_management.delete_department')
def department_delete(request, pk):
    """Delete a department"""
    department = get_object_or_404(Department, pk=pk)
    
    if request.method == 'POST':
        # Check if department has cost centers
        if department.cost_centers.exists():
            messages.error(request, f'Cannot delete department "{department.name}" because it has associated cost centers.')
        else:
            department.delete()
            messages.success(request, f'Department "{department.name}" deleted successfully.')
        return redirect('cost_center_management:department_list')
    
    context = {
        'department': department,
    }
    
    return render(request, 'cost_center_management/department_confirm_delete.html', context)


# Cost Center Views
@login_required
def cost_center_list(request):
    """List all cost centers"""
    cost_centers = CostCenter.objects.select_related('department', 'manager', 'parent_cost_center').all()
    
    # Search and filter functionality
    form = CostCenterSearchForm(request.GET)
    if form.is_valid():
        search = form.cleaned_data.get('search')
        department = form.cleaned_data.get('department')
        status = form.cleaned_data.get('status')
        manager = form.cleaned_data.get('manager')
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')
        
        if search:
            cost_centers = cost_centers.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        if department:
            cost_centers = cost_centers.filter(department=department)
        
        if status:
            cost_centers = cost_centers.filter(status=status)
        
        if manager:
            cost_centers = cost_centers.filter(manager=manager)
        
        if start_date:
            cost_centers = cost_centers.filter(created_at__date__gte=start_date)
        
        if end_date:
            cost_centers = cost_centers.filter(created_at__date__lte=end_date)
    
    # Pagination
    paginator = Paginator(cost_centers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'form': form,
    }
    
    return render(request, 'cost_center_management/cost_center_list.html', context)


@login_required
@permission_required('cost_center_management.add_costcenter')
def cost_center_create(request):
    """Create a new cost center"""
    if request.method == 'POST':
        form = CostCenterForm(request.POST)
        if form.is_valid():
            cost_center = form.save(commit=False)
            cost_center.created_by = request.user
            cost_center.save()
            messages.success(request, f'Cost Center "{cost_center.name}" created successfully.')
            return redirect('cost_center_management:cost_center_list')
    else:
        form = CostCenterForm()
    
    context = {
        'form': form,
        'title': 'Create Cost Center',
    }
    
    return render(request, 'cost_center_management/cost_center_form.html', context)


@login_required
@permission_required('cost_center_management.change_costcenter')
def cost_center_update(request, pk):
    """Update a cost center"""
    cost_center = get_object_or_404(CostCenter, pk=pk)
    
    if request.method == 'POST':
        form = CostCenterForm(request.POST, instance=cost_center)
        if form.is_valid():
            cost_center = form.save(commit=False)
            cost_center.updated_by = request.user
            cost_center.save()
            messages.success(request, f'Cost Center "{cost_center.name}" updated successfully.')
            return redirect('cost_center_management:cost_center_list')
    else:
        form = CostCenterForm(instance=cost_center)
    
    context = {
        'form': form,
        'cost_center': cost_center,
        'title': 'Update Cost Center',
    }
    
    return render(request, 'cost_center_management/cost_center_form.html', context)


@login_required
@permission_required('cost_center_management.delete_costcenter')
def cost_center_delete(request, pk):
    """Delete a cost center"""
    cost_center = get_object_or_404(CostCenter, pk=pk)
    
    if request.method == 'POST':
        # Check if cost center has transactions
        if cost_center.cost_center_transactions.exists():
            messages.error(request, f'Cannot delete cost center "{cost_center.name}" because it has associated transactions.')
        else:
            cost_center.delete()
            messages.success(request, f'Cost Center "{cost_center.name}" deleted successfully.')
        return redirect('cost_center_management:cost_center_list')
    
    context = {
        'cost_center': cost_center,
    }
    
    return render(request, 'cost_center_management/cost_center_confirm_delete.html', context)


@login_required
def cost_center_detail(request, pk):
    """Detail view for a cost center"""
    cost_center = get_object_or_404(CostCenter.objects.select_related('department', 'manager', 'parent_cost_center'), pk=pk)
    
    # Get recent transactions
    recent_transactions = cost_center.cost_center_transactions.order_by('-transaction_date')[:10]
    
    # Get budget information
    budgets = cost_center.budgets.filter(is_active=True).order_by('-start_date')
    
    # Get child cost centers
    child_cost_centers = cost_center.child_cost_centers.filter(is_active=True)
    
    context = {
        'cost_center': cost_center,
        'recent_transactions': recent_transactions,
        'budgets': budgets,
        'child_cost_centers': child_cost_centers,
    }
    
    return render(request, 'cost_center_management/cost_center_detail.html', context)


# Cost Center Budget Views
@login_required
def cost_center_budget_list(request):
    """List all cost center budgets"""
    budgets = CostCenterBudget.objects.select_related('cost_center').all()
    
    # Search and filter functionality
    form = CostCenterBudgetSearchForm(request.GET)
    if form.is_valid():
        cost_center = form.cleaned_data.get('cost_center')
        budget_period = form.cleaned_data.get('budget_period')
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')
        
        if cost_center:
            budgets = budgets.filter(cost_center=cost_center)
        
        if budget_period:
            budgets = budgets.filter(budget_period=budget_period)
        
        if start_date:
            budgets = budgets.filter(start_date__gte=start_date)
        
        if end_date:
            budgets = budgets.filter(end_date__lte=end_date)
    
    # Pagination
    paginator = Paginator(budgets, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'form': form,
    }
    
    return render(request, 'cost_center_management/cost_center_budget_list.html', context)


@login_required
@permission_required('cost_center_management.add_costcenterbudget')
def cost_center_budget_create(request):
    """Create a new cost center budget"""
    if request.method == 'POST':
        form = CostCenterBudgetForm(request.POST)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.created_by = request.user
            budget.save()
            messages.success(request, f'Budget for "{budget.cost_center.name}" created successfully.')
            return redirect('cost_center_management:cost_center_budget_list')
    else:
        form = CostCenterBudgetForm()
    
    context = {
        'form': form,
        'title': 'Create Cost Center Budget',
    }
    
    return render(request, 'cost_center_management/cost_center_budget_form.html', context)


@login_required
@permission_required('cost_center_management.change_costcenterbudget')
def cost_center_budget_update(request, pk):
    """Update a cost center budget"""
    budget = get_object_or_404(CostCenterBudget, pk=pk)
    
    if request.method == 'POST':
        form = CostCenterBudgetForm(request.POST, instance=budget)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.updated_by = request.user
            budget.save()
            messages.success(request, f'Budget for "{budget.cost_center.name}" updated successfully.')
            return redirect('cost_center_management:cost_center_budget_list')
    else:
        form = CostCenterBudgetForm(instance=budget)
    
    context = {
        'form': form,
        'budget': budget,
        'title': 'Update Cost Center Budget',
    }
    
    return render(request, 'cost_center_management/cost_center_budget_form.html', context)


# Cost Center Transaction Views
@login_required
def cost_center_transaction_list(request):
    """List all cost center transactions"""
    transactions = CostCenterTransaction.objects.select_related('cost_center').all()
    
    # Search and filter functionality
    form = CostCenterTransactionSearchForm(request.GET)
    if form.is_valid():
        cost_center = form.cleaned_data.get('cost_center')
        transaction_type = form.cleaned_data.get('transaction_type')
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')
        min_amount = form.cleaned_data.get('min_amount')
        max_amount = form.cleaned_data.get('max_amount')
        
        if cost_center:
            transactions = transactions.filter(cost_center=cost_center)
        
        if transaction_type:
            transactions = transactions.filter(transaction_type=transaction_type)
        
        if start_date:
            transactions = transactions.filter(transaction_date__gte=start_date)
        
        if end_date:
            transactions = transactions.filter(transaction_date__lte=end_date)
        
        if min_amount:
            transactions = transactions.filter(amount__gte=min_amount)
        
        if max_amount:
            transactions = transactions.filter(amount__lte=max_amount)
    
    # Pagination
    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'form': form,
    }
    
    return render(request, 'cost_center_management/cost_center_transaction_list.html', context)


@login_required
@permission_required('cost_center_management.add_costcentertransaction')
def cost_center_transaction_create(request):
    """Create a new cost center transaction"""
    if request.method == 'POST':
        form = CostCenterTransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.created_by = request.user
            transaction.save()
            messages.success(request, f'Transaction for "{transaction.cost_center.name}" created successfully.')
            return redirect('cost_center_management:cost_center_transaction_list')
    else:
        form = CostCenterTransactionForm()
    
    context = {
        'form': form,
        'title': 'Create Cost Center Transaction',
    }
    
    return render(request, 'cost_center_management/cost_center_transaction_form.html', context)


# Report Views
@login_required
def cost_center_report_list(request):
    """List all cost center reports"""
    reports = CostCenterReport.objects.select_related('cost_center', 'generated_by').all()
    
    # Pagination
    paginator = Paginator(reports, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    
    return render(request, 'cost_center_management/cost_center_report_list.html', context)


@login_required
def cost_center_report_create(request):
    """Create a new cost center report"""
    if request.method == 'POST':
        form = CostCenterReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.generated_by = request.user
            
            # Generate report data based on type
            report_data = generate_report_data(report)
            report.report_data = report_data
            report.save()
            
            messages.success(request, f'Report "{report.report_name}" generated successfully.')
            return redirect('cost_center_management:cost_center_report_detail', pk=report.pk)
    else:
        form = CostCenterReportForm()
    
    context = {
        'form': form,
        'title': 'Generate Cost Center Report',
    }
    
    return render(request, 'cost_center_management/cost_center_report_form.html', context)


@login_required
def cost_center_report_detail(request, pk):
    """Detail view for a cost center report"""
    report = get_object_or_404(CostCenterReport, pk=pk)
    
    context = {
        'report': report,
    }
    
    return render(request, 'cost_center_management/cost_center_report_detail.html', context)


def generate_report_data(report):
    """Generate report data based on report type"""
    data = {}
    
    if report.report_type == 'expense_summary':
        # Generate expense summary report
        transactions = CostCenterTransaction.objects.filter(
            transaction_date__gte=report.start_date,
            transaction_date__lte=report.end_date
        )
        
        if report.cost_center:
            transactions = transactions.filter(cost_center=report.cost_center)
        
        data = {
            'total_expenses': transactions.aggregate(total=Sum('amount'))['total'] or 0,
            'transaction_count': transactions.count(),
            'transactions_by_type': list(transactions.values('transaction_type').annotate(
                total=Sum('amount'), count=Count('id')
            )),
            'transactions_by_cost_center': list(transactions.values('cost_center__name').annotate(
                total=Sum('amount'), count=Count('id')
            )),
        }
    
    elif report.report_type == 'budget_variance':
        # Generate budget variance report
        cost_centers = CostCenter.objects.filter(is_active=True)
        if report.cost_center:
            cost_centers = cost_centers.filter(id=report.cost_center.id)
        
        data = {
            'cost_centers': []
        }
        
        for cost_center in cost_centers:
            budget_amount = cost_center.budget_amount
            total_expenses = cost_center.cost_center_transactions.filter(
                transaction_date__gte=report.start_date,
                transaction_date__lte=report.end_date
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            variance = budget_amount - total_expenses
            utilization_percentage = (total_expenses / budget_amount * 100) if budget_amount > 0 else 0
            
            data['cost_centers'].append({
                'name': cost_center.name,
                'code': cost_center.code,
                'budget_amount': budget_amount,
                'total_expenses': total_expenses,
                'variance': variance,
                'utilization_percentage': utilization_percentage,
            })
    
    return data


# API Views for AJAX
@login_required
@csrf_exempt
def api_cost_center_data(request):
    """API endpoint for cost center data"""
    if request.method == 'GET':
        cost_centers = CostCenter.objects.filter(is_active=True).values('id', 'code', 'name', 'department__name')
        return JsonResponse({'cost_centers': list(cost_centers)})
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)


@login_required
@csrf_exempt
def api_cost_center_stats(request, pk):
    """API endpoint for cost center statistics"""
    cost_center = get_object_or_404(CostCenter, pk=pk)
    
    # Calculate statistics
    total_expenses = cost_center.total_expenses
    budget_variance = cost_center.budget_variance
    utilization_percentage = cost_center.budget_utilization_percentage
    
    data = {
        'total_expenses': float(total_expenses),
        'budget_variance': float(budget_variance),
        'utilization_percentage': float(utilization_percentage),
        'budget_amount': float(cost_center.budget_amount),
    }
    
    return JsonResponse(data)
