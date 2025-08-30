from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Sum, Count, DecimalField
from django.core.paginator import Paginator
from django.utils import timezone
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models.functions import Coalesce
import json
from decimal import Decimal
from datetime import datetime, timedelta

from .models import TaxSummaryReport, TaxSummaryTransaction, TaxSummaryFilter, TaxSummaryExport
from .forms import TaxSummaryReportForm, TaxSummaryFilterForm, TaxSummaryExportForm, TaxSummarySearchForm
from tax_settings.models import TaxTransaction


@login_required
def tax_summary_dashboard(request):
    """Tax Summary Dashboard"""
    # Get summary statistics
    total_reports = TaxSummaryReport.objects.count()
    total_input_tax = TaxSummaryReport.objects.aggregate(
        total=Coalesce(Sum('total_input_tax'), Decimal('0.00'))
    )['total']
    total_output_tax = TaxSummaryReport.objects.aggregate(
        total=Coalesce(Sum('total_output_tax'), Decimal('0.00'))
    )['total']
    net_vat_payable = total_output_tax - total_input_tax
    
    # Get recent reports
    recent_reports = TaxSummaryReport.objects.select_related('generated_by').order_by('-generated_at')[:5]
    
    # Get recent transactions
    recent_transactions = TaxSummaryTransaction.objects.select_related('report').order_by('-created_at')[:10]
    
    # Get monthly summary for current year (database-agnostic approach)
    current_year = timezone.now().year
    monthly_summary = []
    
    # Get all reports for the current year
    yearly_reports = TaxSummaryReport.objects.filter(
        generated_at__year=current_year
    )
    
    # Group by month using Python
    monthly_data = {}
    for report in yearly_reports:
        month = report.generated_at.month
        if month not in monthly_data:
            monthly_data[month] = {
                'total_input': Decimal('0.00'),
                'total_output': Decimal('0.00'),
                'report_count': 0
            }
        monthly_data[month]['total_input'] += report.total_input_tax or Decimal('0.00')
        monthly_data[month]['total_output'] += report.total_output_tax or Decimal('0.00')
        monthly_data[month]['report_count'] += 1
    
    # Convert to list and sort by month
    monthly_summary = [
        {
            'month': month,
            'total_input': data['total_input'],
            'total_output': data['total_output'],
            'report_count': data['report_count']
        }
        for month, data in sorted(monthly_data.items())
    ]
    
    context = {
        'total_reports': total_reports,
        'total_input_tax': total_input_tax,
        'total_output_tax': total_output_tax,
        'net_vat_payable': net_vat_payable,
        'recent_reports': recent_reports,
        'recent_transactions': recent_transactions,
        'monthly_summary': monthly_summary,
    }
    
    return render(request, 'tax_summary/dashboard.html', context)


class TaxSummaryReportListView(LoginRequiredMixin, ListView):
    model = TaxSummaryReport
    template_name = 'tax_summary/report_list.html'
    context_object_name = 'reports'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = TaxSummaryReport.objects.select_related('generated_by').all()
        
        # Apply search filters
        search = self.request.GET.get('search')
        report_type = self.request.GET.get('report_type')
        status = self.request.GET.get('status')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if search:
            queryset = queryset.filter(
                Q(report_name__icontains=search) |
                Q(generated_by__username__icontains=search)
            )
        
        if report_type:
            queryset = queryset.filter(report_type=report_type)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if date_from:
            queryset = queryset.filter(generated_at__date__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(generated_at__date__lte=date_to)
        
        return queryset.order_by('-generated_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = TaxSummarySearchForm(self.request.GET)
        return context


class TaxSummaryReportCreateView(LoginRequiredMixin, CreateView):
    model = TaxSummaryReport
    form_class = TaxSummaryReportForm
    template_name = 'tax_summary/report_form.html'
    success_url = reverse_lazy('tax_summary:report_list')
    
    def form_valid(self, form):
        form.instance.generated_by = self.request.user
        form.instance.status = 'draft'
        messages.success(self.request, 'Tax summary report created successfully.')
        return super().form_valid(form)


class TaxSummaryReportDetailView(LoginRequiredMixin, DetailView):
    model = TaxSummaryReport
    template_name = 'tax_summary/report_detail.html'
    context_object_name = 'report'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get transactions for this report
        transactions = self.object.transactions.all().order_by('transaction_date', 'invoice_number')
        
        # Get summary by transaction type
        input_transactions = transactions.filter(transaction_type='input')
        output_transactions = transactions.filter(transaction_type='output')
        
        context['transactions'] = transactions
        context['input_transactions'] = input_transactions
        context['output_transactions'] = output_transactions
        context['input_summary'] = input_transactions.aggregate(
            total_amount=Sum('taxable_amount'),
            total_vat=Sum('vat_amount')
        )
        context['output_summary'] = output_transactions.aggregate(
            total_amount=Sum('taxable_amount'),
            total_vat=Sum('vat_amount')
        )
        return context


class TaxSummaryReportUpdateView(LoginRequiredMixin, UpdateView):
    model = TaxSummaryReport
    form_class = TaxSummaryReportForm
    template_name = 'tax_summary/report_form.html'
    success_url = reverse_lazy('tax_summary:report_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Tax summary report updated successfully.')
        return super().form_valid(form)


class TaxSummaryReportDeleteView(LoginRequiredMixin, DeleteView):
    model = TaxSummaryReport
    template_name = 'tax_summary/report_confirm_delete.html'
    success_url = reverse_lazy('tax_summary:report_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Tax summary report deleted successfully.')
        return super().delete(request, *args, **kwargs)


@login_required
def generate_tax_summary(request, pk):
    """Generate tax summary report from existing transactions"""
    report = get_object_or_404(TaxSummaryReport, pk=pk)
    
    if request.method == 'POST':
        # Get transactions from tax_settings app
        transactions = TaxTransaction.objects.filter(
            document_date__gte=report.start_date,
            document_date__lte=report.end_date,
            currency=report.currency
        )
        
        # Clear existing transactions for this report
        report.transactions.all().delete()
        
        # Process transactions
        input_tax_total = Decimal('0.00')
        output_tax_total = Decimal('0.00')
        input_count = 0
        output_count = 0
        
        for transaction in transactions:
            # Determine transaction type
            if transaction.transaction_type == 'purchase':
                transaction_type = 'input'
                input_tax_total += transaction.tax_amount or Decimal('0.00')
                input_count += 1
            elif transaction.transaction_type == 'sale':
                transaction_type = 'output'
                output_tax_total += transaction.tax_amount or Decimal('0.00')
                output_count += 1
            else:
                continue
            
            # Get party name
            if transaction.customer:
                party_name = transaction.customer.name if hasattr(transaction.customer, 'name') else str(transaction.customer)
            else:
                party_name = transaction.supplier_name or 'Unknown'
            
            # Create tax summary transaction
            TaxSummaryTransaction.objects.create(
                report=report,
                transaction_date=transaction.document_date,
                invoice_number=transaction.document_number,
                party_name=party_name,
                vat_number='',  # TODO: Add VAT number from customer/supplier profile
                transaction_type=transaction_type,
                taxable_amount=transaction.taxable_amount or Decimal('0.00'),
                vat_percentage=transaction.tax_rate.rate_percentage if transaction.tax_rate else Decimal('0.00'),
                vat_amount=transaction.tax_amount or Decimal('0.00'),
                total_amount=transaction.total_amount or Decimal('0.00'),
                currency=transaction.currency,
                original_transaction_id=str(transaction.id),
                original_transaction_type=transaction.transaction_type
            )
        
        # Update report totals
        report.total_input_tax = input_tax_total
        report.total_output_tax = output_tax_total
        report.net_vat_payable = output_tax_total - input_tax_total
        report.input_transactions_count = input_count
        report.output_transactions_count = output_count
        report.status = 'generated'
        report.save()
        
        messages.success(request, f'Tax summary report "{report.report_name}" generated successfully.')
        return redirect('tax_summary:report_detail', pk=report.pk)
    
    return render(request, 'tax_summary/generate_report.html', {'report': report})


@login_required
def tax_summary_transactions(request, pk):
    """View transactions for a specific tax summary report"""
    report = get_object_or_404(TaxSummaryReport, pk=pk)
    transactions = report.transactions.all().order_by('transaction_date', 'invoice_number')
    
    # Apply filters
    filter_form = TaxSummaryFilterForm(request.GET)
    if filter_form.is_valid():
        filters = filter_form.cleaned_data
        
        if filters.get('start_date'):
            transactions = transactions.filter(transaction_date__gte=filters['start_date'])
        
        if filters.get('end_date'):
            transactions = transactions.filter(transaction_date__lte=filters['end_date'])
        
        if filters.get('party_name'):
            transactions = transactions.filter(party_name__icontains=filters['party_name'])
        
        if filters.get('vat_number'):
            transactions = transactions.filter(vat_number__icontains=filters['vat_number'])
        
        if filters.get('transaction_type'):
            transactions = transactions.filter(transaction_type=filters['transaction_type'])
        
        if filters.get('vat_percentage'):
            transactions = transactions.filter(vat_percentage=filters['vat_percentage'])
        
        if filters.get('currency'):
            transactions = transactions.filter(currency=filters['currency'])
        
        if filters.get('min_amount'):
            transactions = transactions.filter(taxable_amount__gte=filters['min_amount'])
        
        if filters.get('max_amount'):
            transactions = transactions.filter(taxable_amount__lte=filters['max_amount'])
    
    # Calculate summary
    summary = {
        'input_tax': transactions.filter(transaction_type='input').aggregate(
            total=Coalesce(Sum('vat_amount'), Decimal('0.00'))
        )['total'],
        'output_tax': transactions.filter(transaction_type='output').aggregate(
            total=Coalesce(Sum('vat_amount'), Decimal('0.00'))
        )['total'],
    }
    summary['net_vat'] = summary['output_tax'] - summary['input_tax']
    
    # Pagination
    paginator = Paginator(transactions, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'report': report,
        'transactions': page_obj,
        'filter_form': filter_form,
        'summary': summary,
    }
    
    return render(request, 'tax_summary/transactions.html', context)


@login_required
def export_tax_summary(request, pk):
    """Export tax summary report"""
    report = get_object_or_404(TaxSummaryReport, pk=pk)
    
    if request.method == 'POST':
        form = TaxSummaryExportForm(request.POST)
        if form.is_valid():
            export_format = form.cleaned_data['export_format']
            
            # TODO: Implement actual export functionality
            # For now, just create an export record
            export = TaxSummaryExport.objects.create(
                report=report,
                export_format=export_format,
                exported_by=request.user
            )
            
            messages.success(request, f'Tax summary report exported as {export_format.upper()}.')
            return redirect('tax_summary:report_detail', pk=report.pk)
    else:
        form = TaxSummaryExportForm()
    
    return render(request, 'tax_summary/export_report.html', {
        'report': report,
        'form': form
    })


@login_required
@csrf_exempt
def tax_summary_api(request):
    """API endpoint for tax summary data"""
    if request.method == 'GET':
        # Get summary statistics
        total_reports = TaxSummaryReport.objects.count()
        total_input_tax = TaxSummaryReport.objects.aggregate(
            total=Coalesce(Sum('total_input_tax'), Decimal('0.00'))
        )['total']
        total_output_tax = TaxSummaryReport.objects.aggregate(
            total=Coalesce(Sum('total_output_tax'), Decimal('0.00'))
        )['total']
        
        return JsonResponse({
            'total_reports': total_reports,
            'total_input_tax': float(total_input_tax),
            'total_output_tax': float(total_output_tax),
            'net_vat_payable': float(total_output_tax - total_input_tax),
        })
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)
