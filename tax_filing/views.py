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

from .models import TaxFilingReport, TaxFilingTransaction, TaxFilingValidation, TaxFilingExport, TaxFilingSettings
from .forms import TaxFilingReportForm, TaxFilingFilterForm, TaxFilingExportForm, TaxFilingSearchForm, TaxFilingValidationForm, TaxFilingSettingsForm
from tax_settings.models import TaxTransaction


@login_required
def tax_filing_dashboard(request):
    """Tax Filing Dashboard"""
    # Get summary statistics
    total_reports = TaxFilingReport.objects.count()
    total_output_tax = TaxFilingReport.objects.aggregate(
        total=Coalesce(Sum('total_output_tax'), Decimal('0.00'))
    )['total']
    total_input_tax = TaxFilingReport.objects.aggregate(
        total=Coalesce(Sum('total_input_tax'), Decimal('0.00'))
    )['total']
    total_adjustments = TaxFilingReport.objects.aggregate(
        total=Coalesce(Sum('total_adjustments'), Decimal('0.00'))
    )['total']
    net_tax_payable = total_output_tax - total_input_tax + total_adjustments
    
    # Get recent reports
    recent_reports = TaxFilingReport.objects.select_related('generated_by').order_by('-generated_at')[:5]
    
    # Get recent transactions
    recent_transactions = TaxFilingTransaction.objects.select_related('report').order_by('-created_at')[:10]
    
    # Get validation issues
    validation_issues = TaxFilingValidation.objects.filter(is_resolved=False).order_by('-severity', '-created_at')[:5]
    
    # Get monthly summary for current year (database-agnostic approach)
    current_year = timezone.now().year
    monthly_summary = []
    
    # Get all reports for the current year
    yearly_reports = TaxFilingReport.objects.filter(
        generated_at__year=current_year
    )
    
    # Group by month using Python
    monthly_data = {}
    for report in yearly_reports:
        month = report.generated_at.month
        if month not in monthly_data:
            monthly_data[month] = {
                'total_output': Decimal('0.00'),
                'total_input': Decimal('0.00'),
                'total_adjustments': Decimal('0.00'),
                'report_count': 0
            }
        monthly_data[month]['total_output'] += report.total_output_tax or Decimal('0.00')
        monthly_data[month]['total_input'] += report.total_input_tax or Decimal('0.00')
        monthly_data[month]['total_adjustments'] += report.total_adjustments or Decimal('0.00')
        monthly_data[month]['report_count'] += 1
    
    # Convert to list and sort by month
    monthly_summary = [
        {
            'month': month,
            'total_output': data['total_output'],
            'total_input': data['total_input'],
            'total_adjustments': data['total_adjustments'],
            'report_count': data['report_count']
        }
        for month, data in sorted(monthly_data.items())
    ]
    
    context = {
        'total_reports': total_reports,
        'total_output_tax': total_output_tax,
        'total_input_tax': total_input_tax,
        'total_adjustments': total_adjustments,
        'net_tax_payable': net_tax_payable,
        'recent_reports': recent_reports,
        'recent_transactions': recent_transactions,
        'validation_issues': validation_issues,
        'monthly_summary': monthly_summary,
    }
    
    return render(request, 'tax_filing/dashboard.html', context)


class TaxFilingReportListView(LoginRequiredMixin, ListView):
    model = TaxFilingReport
    template_name = 'tax_filing/report_list.html'
    context_object_name = 'reports'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = TaxFilingReport.objects.select_related('generated_by').all()
        
        # Apply search filters
        search = self.request.GET.get('search')
        filing_period = self.request.GET.get('filing_period')
        status = self.request.GET.get('status')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if search:
            queryset = queryset.filter(
                Q(report_name__icontains=search) |
                Q(generated_by__username__icontains=search) |
                Q(filing_reference__icontains=search)
            )
        
        if filing_period:
            queryset = queryset.filter(filing_period=filing_period)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if date_from:
            queryset = queryset.filter(generated_at__date__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(generated_at__date__lte=date_to)
        
        return queryset.order_by('-generated_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = TaxFilingSearchForm(self.request.GET)
        return context


class TaxFilingReportCreateView(LoginRequiredMixin, CreateView):
    model = TaxFilingReport
    form_class = TaxFilingReportForm
    template_name = 'tax_filing/report_form.html'
    success_url = reverse_lazy('tax_filing:report_list')
    
    def form_valid(self, form):
        form.instance.generated_by = self.request.user
        form.instance.status = 'draft'
        messages.success(self.request, 'Tax filing report created successfully.')
        return super().form_valid(form)


class TaxFilingReportDetailView(LoginRequiredMixin, DetailView):
    model = TaxFilingReport
    template_name = 'tax_filing/report_detail.html'
    context_object_name = 'report'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get transactions for this report
        transactions = self.object.transactions.all().order_by('transaction_date', 'invoice_number')
        
        # Get summary by transaction type
        output_transactions = transactions.filter(transaction_type='output')
        input_transactions = transactions.filter(transaction_type='input')
        adjustment_transactions = transactions.filter(transaction_type='adjustment')
        
        context['transactions'] = transactions
        context['output_transactions'] = output_transactions
        context['input_transactions'] = input_transactions
        context['adjustment_transactions'] = adjustment_transactions
        context['output_summary'] = output_transactions.aggregate(
            total_amount=Sum('taxable_amount'),
            total_vat=Sum('vat_amount')
        )
        context['input_summary'] = input_transactions.aggregate(
            total_amount=Sum('taxable_amount'),
            total_vat=Sum('vat_amount')
        )
        context['adjustment_summary'] = adjustment_transactions.aggregate(
            total_amount=Sum('taxable_amount'),
            total_vat=Sum('vat_amount')
        )
        
        # Get validation issues
        context['validation_issues'] = self.object.validations.filter(is_resolved=False)
        
        return context


class TaxFilingReportUpdateView(LoginRequiredMixin, UpdateView):
    model = TaxFilingReport
    form_class = TaxFilingReportForm
    template_name = 'tax_filing/report_form.html'
    success_url = reverse_lazy('tax_filing:report_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Tax filing report updated successfully.')
        return super().form_valid(form)


class TaxFilingReportDeleteView(LoginRequiredMixin, DeleteView):
    model = TaxFilingReport
    template_name = 'tax_filing/report_confirm_delete.html'
    success_url = reverse_lazy('tax_filing:report_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Tax filing report deleted successfully.')
        return super().delete(request, *args, **kwargs)


@login_required
def generate_tax_filing(request, pk):
    """Generate tax filing report from existing transactions"""
    report = get_object_or_404(TaxFilingReport, pk=pk)
    
    if request.method == 'POST':
        # Get transactions from tax_settings app
        transactions = TaxTransaction.objects.filter(
            document_date__gte=report.start_date,
            document_date__lte=report.end_date,
            currency=report.currency
        )
        
        # Clear existing transactions for this report
        report.transactions.all().delete()
        report.validations.all().delete()
        
        # Process transactions
        output_tax_total = Decimal('0.00')
        input_tax_total = Decimal('0.00')
        adjustment_tax_total = Decimal('0.00')
        output_count = 0
        input_count = 0
        adjustment_count = 0
        
        validation_issues = []
        
        for transaction in transactions:
            # Determine transaction type
            if transaction.transaction_type == 'sale':
                transaction_type = 'output'
                output_tax_total += transaction.tax_amount or Decimal('0.00')
                output_count += 1
            elif transaction.transaction_type == 'purchase':
                transaction_type = 'input'
                input_tax_total += transaction.tax_amount or Decimal('0.00')
                input_count += 1
            elif transaction.transaction_type in ['refund', 'adjustment']:
                transaction_type = 'adjustment'
                adjustment_tax_total += transaction.tax_amount or Decimal('0.00')
                adjustment_count += 1
            else:
                continue
            
            # Get party name
            if transaction.customer:
                party_name = transaction.customer.name if hasattr(transaction.customer, 'name') else str(transaction.customer)
            else:
                party_name = transaction.supplier_name or 'Unknown'
            
            # Check for validation issues
            has_vat_number = bool(transaction.customer and hasattr(transaction.customer, 'tax_registration_number') and transaction.customer.tax_registration_number)
            vat_rate_matches = True  # TODO: Implement VAT rate validation
            
            # Create tax filing transaction
            filing_transaction = TaxFilingTransaction.objects.create(
                report=report,
                transaction_date=transaction.document_date,
                invoice_number=transaction.document_number,
                party_name=party_name,
                vat_number='',  # TODO: Add VAT number from customer/supplier profile
                transaction_type=transaction_type,
                adjustment_type='' if transaction_type != 'adjustment' else 'correction',
                taxable_amount=transaction.taxable_amount or Decimal('0.00'),
                vat_percentage=transaction.tax_rate.rate_percentage if transaction.tax_rate else Decimal('0.00'),
                vat_amount=transaction.tax_amount or Decimal('0.00'),
                total_amount=transaction.total_amount or Decimal('0.00'),
                currency=transaction.currency,
                original_transaction_id=str(transaction.id),
                original_transaction_type=transaction.transaction_type,
                has_vat_number=has_vat_number,
                vat_rate_matches=vat_rate_matches
            )
            
            # Create validation issues if needed
            if not has_vat_number:
                TaxFilingValidation.objects.create(
                    report=report,
                    transaction=filing_transaction,
                    validation_type='missing_vat_number',
                    severity='medium',
                    description=f'Missing VAT number for {party_name}',
                    field_name='vat_number'
                )
                validation_issues.append('missing_vat_number')
            
            if not vat_rate_matches:
                TaxFilingValidation.objects.create(
                    report=report,
                    transaction=filing_transaction,
                    validation_type='mismatched_rate',
                    severity='high',
                    description=f'VAT rate mismatch for {party_name}',
                    field_name='vat_percentage'
                )
                validation_issues.append('mismatched_rate')
        
        # Update report totals
        report.total_output_tax = output_tax_total
        report.total_input_tax = input_tax_total
        report.total_adjustments = adjustment_tax_total
        report.net_tax_payable = output_tax_total - input_tax_total + adjustment_tax_total
        report.output_transactions_count = output_count
        report.input_transactions_count = input_count
        report.adjustment_transactions_count = adjustment_count
        report.has_missing_vat_numbers = 'missing_vat_number' in validation_issues
        report.has_mismatched_rates = 'mismatched_rate' in validation_issues
        report.status = 'generated'
        report.save()
        
        messages.success(request, f'Tax filing report "{report.report_name}" generated successfully.')
        return redirect('tax_filing:report_detail', pk=report.pk)
    
    return render(request, 'tax_filing/generate_report.html', {'report': report})


@login_required
def tax_filing_transactions(request, pk):
    """View transactions for a specific tax filing report"""
    report = get_object_or_404(TaxFilingReport, pk=pk)
    transactions = report.transactions.all().order_by('transaction_date', 'invoice_number')
    
    # Apply filters
    filter_form = TaxFilingFilterForm(request.GET)
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
        
        if filters.get('adjustment_type'):
            transactions = transactions.filter(adjustment_type=filters['adjustment_type'])
        
        if filters.get('vat_percentage'):
            transactions = transactions.filter(vat_percentage=filters['vat_percentage'])
        
        if filters.get('currency'):
            transactions = transactions.filter(currency=filters['currency'])
        
        if filters.get('min_amount'):
            transactions = transactions.filter(taxable_amount__gte=filters['min_amount'])
        
        if filters.get('max_amount'):
            transactions = transactions.filter(taxable_amount__lte=filters['max_amount'])
        
        if filters.get('has_validation_issues'):
            transactions = transactions.filter(
                Q(has_vat_number=False) | Q(vat_rate_matches=False)
            )
    
    # Calculate summary
    summary = {
        'output_tax': transactions.filter(transaction_type='output').aggregate(
            total=Coalesce(Sum('vat_amount'), Decimal('0.00'))
        )['total'],
        'input_tax': transactions.filter(transaction_type='input').aggregate(
            total=Coalesce(Sum('vat_amount'), Decimal('0.00'))
        )['total'],
        'adjustments': transactions.filter(transaction_type='adjustment').aggregate(
            total=Coalesce(Sum('vat_amount'), Decimal('0.00'))
        )['total'],
    }
    summary['net_tax'] = summary['output_tax'] - summary['input_tax'] + summary['adjustments']
    
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
    
    return render(request, 'tax_filing/transactions.html', context)


@login_required
def export_tax_filing(request, pk):
    """Export tax filing report"""
    report = get_object_or_404(TaxFilingReport, pk=pk)
    
    if request.method == 'POST':
        form = TaxFilingExportForm(request.POST)
        if form.is_valid():
            export_format = form.cleaned_data['export_format']
            
            # TODO: Implement actual export functionality
            # For now, just create an export record
            export = TaxFilingExport.objects.create(
                report=report,
                export_format=export_format,
                exported_by=request.user
            )
            
            messages.success(request, f'Tax filing report exported as {export_format.upper()}.')
            return redirect('tax_filing:report_detail', pk=report.pk)
    else:
        form = TaxFilingExportForm()
    
    return render(request, 'tax_filing/export_report.html', {
        'report': report,
        'form': form
    })


@login_required
def tax_filing_validations(request, pk):
    """View validation issues for a specific tax filing report"""
    report = get_object_or_404(TaxFilingReport, pk=pk)
    validations = report.validations.all().order_by('-severity', '-created_at')
    
    # Pagination
    paginator = Paginator(validations, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'report': report,
        'validations': page_obj,
    }
    
    return render(request, 'tax_filing/validations.html', context)


@login_required
@csrf_exempt
def tax_filing_api(request):
    """API endpoint for tax filing data"""
    if request.method == 'GET':
        # Get summary statistics
        total_reports = TaxFilingReport.objects.count()
        total_output_tax = TaxFilingReport.objects.aggregate(
            total=Coalesce(Sum('total_output_tax'), Decimal('0.00'))
        )['total']
        total_input_tax = TaxFilingReport.objects.aggregate(
            total=Coalesce(Sum('total_input_tax'), Decimal('0.00'))
        )['total']
        total_adjustments = TaxFilingReport.objects.aggregate(
            total=Coalesce(Sum('total_adjustments'), Decimal('0.00'))
        )['total']
        
        return JsonResponse({
            'total_reports': total_reports,
            'total_output_tax': float(total_output_tax),
            'total_input_tax': float(total_input_tax),
            'total_adjustments': float(total_adjustments),
            'net_tax_payable': float(total_output_tax - total_input_tax + total_adjustments),
        })
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)
