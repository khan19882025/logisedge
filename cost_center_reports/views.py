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
    CostCenterFinancialReport, CostCenterReportFilter, 
    CostCenterReportExport, CostCenterReportSchedule
)
from .forms import (
    CostCenterFinancialReportForm, CostCenterReportSearchForm,
    CostCenterReportExportForm, CostCenterReportScheduleForm
)
from cost_center_management.models import CostCenter, Department
from cost_center_transaction_tagging.models import TransactionTagging


@login_required
def dashboard(request):
    """Dashboard view for cost center reports"""
    # Get statistics
    total_reports = CostCenterFinancialReport.objects.count()
    total_cost_centers = CostCenter.objects.filter(is_active=True).count()
    total_departments = Department.objects.filter(is_active=True).count()
    
    # Get recent reports
    recent_reports = CostCenterFinancialReport.objects.order_by('-generated_at')[:5]
    
    # Get cost center statistics
    cost_center_stats = CostCenter.objects.filter(is_active=True).annotate(
        transaction_count=Count('tagged_transactions'),
        total_amount=Coalesce(Sum('tagged_transactions__amount'), Decimal('0.00'))
    ).order_by('-total_amount')[:10]
    
    # Calculate percentages for cost centers
    total_amount = sum(stat.total_amount for stat in cost_center_stats)
    for stat in cost_center_stats:
        if total_amount > 0:
            stat.percentage = (stat.total_amount / total_amount) * 100
        else:
            stat.percentage = 0
    
    # Get report type distribution
    report_type_stats = CostCenterFinancialReport.objects.values('report_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Calculate percentages for report types
    for stat in report_type_stats:
        if total_reports > 0:
            stat['percentage'] = (stat['count'] / total_reports) * 100
        else:
            stat['percentage'] = 0
    
    context = {
        'total_reports': total_reports,
        'total_cost_centers': total_cost_centers,
        'total_departments': total_departments,
        'recent_reports': recent_reports,
        'cost_center_stats': cost_center_stats,
        'report_type_stats': report_type_stats,
    }
    
    return render(request, 'cost_center_reports/dashboard.html', context)


@login_required
def report_list(request):
    """List view for cost center reports"""
    reports = CostCenterFinancialReport.objects.all()
    
    # Apply search filters
    search_form = CostCenterReportSearchForm(request.GET)
    if search_form.is_valid():
        if search_form.cleaned_data.get('report_type'):
            reports = reports.filter(report_type=search_form.cleaned_data['report_type'])
        if search_form.cleaned_data.get('cost_center'):
            reports = reports.filter(cost_center=search_form.cleaned_data['cost_center'])
        if search_form.cleaned_data.get('department'):
            reports = reports.filter(department=search_form.cleaned_data['department'])
        if search_form.cleaned_data.get('start_date'):
            reports = reports.filter(start_date__gte=search_form.cleaned_data['start_date'])
        if search_form.cleaned_data.get('end_date'):
            reports = reports.filter(end_date__lte=search_form.cleaned_data['end_date'])
        if search_form.cleaned_data.get('status'):
            reports = reports.filter(status=search_form.cleaned_data['status'])
    
    # Pagination
    paginator = Paginator(reports, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
    }
    
    return render(request, 'cost_center_reports/report_list.html', context)


@login_required
def report_create(request):
    """Create a new cost center report"""
    if request.method == 'POST':
        form = CostCenterFinancialReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.generated_by = request.user
            report.save()
            messages.success(request, 'Report created successfully.')
            return redirect('cost_center_reports:report_detail', pk=report.pk)
    else:
        form = CostCenterFinancialReportForm()
    
    context = {
        'form': form,
        'title': 'Create New Report'
    }
    
    return render(request, 'cost_center_reports/report_form.html', context)


@login_required
def report_detail(request, pk):
    """Detail view for a cost center report"""
    report = get_object_or_404(CostCenterFinancialReport, pk=pk)
    
    # Get report data based on type
    if report.report_type == 'summary':
        report_data = get_summary_report_data(report)
    elif report.report_type == 'detailed':
        report_data = get_detailed_report_data(report)
    elif report.report_type == 'budget_variance':
        report_data = get_budget_variance_report_data(report)
    elif report.report_type == 'profit_loss':
        report_data = get_profit_loss_report_data(report)
    else:
        report_data = get_expense_analysis_report_data(report)
    
    context = {
        'report': report,
        'report_data': report_data,
    }
    
    return render(request, 'cost_center_reports/report_detail.html', context)


@login_required
def report_edit(request, pk):
    """Edit a cost center report"""
    report = get_object_or_404(CostCenterFinancialReport, pk=pk)
    
    if request.method == 'POST':
        form = CostCenterFinancialReportForm(request.POST, instance=report)
        if form.is_valid():
            form.save()
            messages.success(request, 'Report updated successfully.')
            return redirect('cost_center_reports:report_detail', pk=report.pk)
    else:
        form = CostCenterFinancialReportForm(instance=report)
    
    context = {
        'form': form,
        'report': report,
        'title': 'Edit Report'
    }
    
    return render(request, 'cost_center_reports/report_form.html', context)


@login_required
def report_delete(request, pk):
    """Delete a cost center report"""
    report = get_object_or_404(CostCenterFinancialReport, pk=pk)
    
    if request.method == 'POST':
        report.delete()
        messages.success(request, 'Report deleted successfully.')
        return redirect('cost_center_reports:report_list')
    
    context = {
        'report': report,
    }
    
    return render(request, 'cost_center_reports/report_confirm_delete.html', context)


@login_required
def report_export(request, pk):
    """Export a cost center report"""
    report = get_object_or_404(CostCenterFinancialReport, pk=pk)
    
    if request.method == 'POST':
        form = CostCenterReportExportForm(request.POST)
        if form.is_valid():
            export_type = form.cleaned_data['export_type']
            
            # Create export record
            export = CostCenterReportExport.objects.create(
                report=report,
                export_type=export_type,
                generated_by=request.user
            )
            
            # Generate export file (placeholder for now)
            if export_type == 'pdf':
                return generate_pdf_export(report)
            elif export_type == 'excel':
                return generate_excel_export(report)
            elif export_type == 'csv':
                return generate_csv_export(report)
    else:
        form = CostCenterReportExportForm()
    
    context = {
        'form': form,
        'report': report,
    }
    
    return render(request, 'cost_center_reports/report_export.html', context)


@login_required
def report_schedule_list(request):
    """List view for report schedules"""
    schedules = CostCenterReportSchedule.objects.all()
    
    context = {
        'schedules': schedules,
    }
    
    return render(request, 'cost_center_reports/schedule_list.html', context)


@login_required
def report_schedule_create(request):
    """Create a new report schedule"""
    if request.method == 'POST':
        form = CostCenterReportScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.created_by = request.user
            schedule.save()
            messages.success(request, 'Schedule created successfully.')
            return redirect('cost_center_reports:schedule_list')
    else:
        form = CostCenterReportScheduleForm()
    
    context = {
        'form': form,
        'title': 'Create New Schedule'
    }
    
    return render(request, 'cost_center_reports/schedule_form.html', context)


# Helper functions for report data generation
def get_summary_report_data(report):
    """Generate summary report data"""
    queryset = CostCenter.objects.all()
    
    if not report.include_inactive:
        queryset = queryset.filter(is_active=True)
    
    if report.cost_center:
        queryset = queryset.filter(id=report.cost_center.id)
    elif report.department:
        queryset = queryset.filter(department=report.department)
    
    summary_data = []
    for cost_center in queryset:
        # Get transactions for the period
        transactions = TransactionTagging.objects.filter(
            cost_center=cost_center,
            transaction_date__range=[report.start_date, report.end_date],
            is_active=True
        )
        
        actual_amount = transactions.aggregate(
            total=Coalesce(Sum('amount'), Decimal('0.00'))
        )['total']
        
        budget_amount = cost_center.budget_amount or Decimal('0.00')
        variance = budget_amount - actual_amount
        variance_percentage = (variance / budget_amount * 100) if budget_amount > 0 else 0
        
        summary_data.append({
            'cost_center': cost_center,
            'budget': budget_amount,
            'actual': actual_amount,
            'variance': variance,
            'variance_percentage': variance_percentage,
            'transaction_count': transactions.count(),
        })
    
    return summary_data


def get_detailed_report_data(report):
    """Generate detailed report data"""
    queryset = TransactionTagging.objects.filter(
        transaction_date__range=[report.start_date, report.end_date],
        is_active=True
    )
    
    if report.cost_center:
        queryset = queryset.filter(cost_center=report.cost_center)
    elif report.department:
        queryset = queryset.filter(cost_center__department=report.department)
    
    if not report.include_inactive:
        queryset = queryset.filter(cost_center__is_active=True)
    
    return queryset.order_by('transaction_date', 'cost_center__code')


def get_budget_variance_report_data(report):
    """Generate budget variance report data"""
    return get_summary_report_data(report)  # Same as summary for now


def get_profit_loss_report_data(report):
    """Generate profit & loss report data"""
    # This would include revenue and expense analysis
    return get_summary_report_data(report)  # Placeholder


def get_expense_analysis_report_data(report):
    """Generate expense analysis report data"""
    return get_detailed_report_data(report)  # Same as detailed for now


# Export functions (placeholders)
def generate_pdf_export(report):
    """Generate PDF export"""
    # Placeholder for PDF generation
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{report.report_name}.pdf"'
    return response


def generate_excel_export(report):
    """Generate Excel export"""
    # Placeholder for Excel generation
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = f'attachment; filename="{report.report_name}.xlsx"'
    return response


def generate_csv_export(report):
    """Generate CSV export"""
    # Placeholder for CSV generation
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{report.report_name}.csv"'
    return response
