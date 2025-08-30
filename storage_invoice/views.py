from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from datetime import datetime, timedelta
from decimal import Decimal
import json

from .models import StorageInvoice, StorageInvoiceItem
from .forms import (
    StorageInvoiceSearchForm, GenerateInvoiceForm,
    StorageInvoiceForm, StorageInvoiceItemForm, MonthSelectionForm,
    BulkInvoiceForm
)
from customer.models import Customer
from facility.models import FacilityLocation
from items.models import Item

@login_required
def storage_invoice_list(request):
    """Display list of storage invoices with month-wise filtering"""
    # Get month selection
    month_form = MonthSelectionForm(request.GET or None)
    search_form = StorageInvoiceSearchForm(request.GET or None)
    
    # Get selected month or default to current month
    if month_form.is_valid() and month_form.cleaned_data.get('month'):
        selected_month = month_form.cleaned_data['month']
    else:
        selected_month = timezone.now().date().replace(day=1)
    
    # Base queryset
    invoices = StorageInvoice.objects.all()
    
    # Apply month filter
    start_of_month = selected_month.replace(day=1)
    if selected_month.month == 12:
        end_of_month = selected_month.replace(year=selected_month.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        end_of_month = selected_month.replace(month=selected_month.month + 1, day=1) - timedelta(days=1)
    
    invoices = invoices.filter(
        Q(invoice_date__gte=start_of_month, invoice_date__lte=end_of_month) |
        Q(storage_period_from__gte=start_of_month, storage_period_from__lte=end_of_month) |
        Q(storage_period_to__gte=start_of_month, storage_period_to__lte=end_of_month)
    )
    
    # Apply search filters
    if search_form.is_valid():
        if search_form.cleaned_data.get('invoice_number'):
            invoices = invoices.filter(
                invoice_number__icontains=search_form.cleaned_data['invoice_number']
            )
        
        if search_form.cleaned_data.get('customer'):
            invoices = invoices.filter(customer=search_form.cleaned_data['customer'])
        
        if search_form.cleaned_data.get('status'):
            invoices = invoices.filter(status=search_form.cleaned_data['status'])
        
        if search_form.cleaned_data.get('date_from'):
            invoices = invoices.filter(invoice_date__gte=search_form.cleaned_data['date_from'])
        
        if search_form.cleaned_data.get('date_to'):
            invoices = invoices.filter(invoice_date__lte=search_form.cleaned_data['date_to'])
        
        if search_form.cleaned_data.get('amount_min'):
            invoices = invoices.filter(total_amount__gte=search_form.cleaned_data['amount_min'])
        
        if search_form.cleaned_data.get('amount_max'):
            invoices = invoices.filter(total_amount__lte=search_form.cleaned_data['amount_max'])
    
    # Order by invoice date (newest first)
    invoices = invoices.order_by('-invoice_date', '-created_at')
    
    # Pagination
    paginator = Paginator(invoices, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_invoices = invoices.count()
    total_amount = invoices.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    draft_invoices = invoices.filter(status='draft').count()
    finalized_invoices = invoices.filter(status='finalized').count()
    
    # Monthly statistics
    monthly_stats = StorageInvoice.objects.filter(
        invoice_date__year=selected_month.year,
        invoice_date__month=selected_month.month
    ).aggregate(
        total_invoices=Count('id'),
        total_amount=Sum('total_amount'),
        draft_count=Count('id', filter=Q(status='draft')),
        finalized_count=Count('id', filter=Q(status='finalized')),
    )
    
    context = {
        'page_obj': page_obj,
        'month_form': month_form,
        'search_form': search_form,
        'selected_month': selected_month,
        'total_invoices': total_invoices,
        'total_amount': total_amount,
        'draft_invoices': draft_invoices,
        'finalized_invoices': finalized_invoices,
        'monthly_stats': monthly_stats,
    }
    
    return render(request, 'storage_invoice/storage_invoice_list.html', context)

@login_required
def storage_invoice_detail(request, pk):
    """Display detailed view of a storage invoice"""
    invoice = get_object_or_404(StorageInvoice, pk=pk)
    
    # Calculate total days
    if invoice.storage_period_from and invoice.storage_period_to:
        total_days = (invoice.storage_period_to - invoice.storage_period_from).days + 1
    else:
        total_days = 0
    
    context = {
        'object': invoice,
        'total_days': total_days,
    }
    
    return render(request, 'storage_invoice/storage_invoice_detail.html', context)

@login_required
def generate_invoice(request):
    """Generate storage invoices based on storage data"""
    if request.method == 'POST':
        form = GenerateInvoiceForm(request.POST)
        if form.is_valid():
            customer_selection = form.cleaned_data['customer']
            storage_period_from = form.cleaned_data['storage_period_from']
            storage_period_to = form.cleaned_data['storage_period_to']
            invoice_date = form.cleaned_data['invoice_date']
            notes = form.cleaned_data.get('notes', '')
            
            # Determine customers to process
            if customer_selection == 'all':
                customers = Customer.objects.all()
            else:
                specific_customer = form.cleaned_data.get('specific_customer')
                if specific_customer:
                    customers = [specific_customer]
                else:
                    messages.error(request, 'Please select a specific customer.')
                    return redirect('storage_invoice:generate_invoice')
            
            generated_count = 0
            
            for customer in customers:
                # Check if invoice already exists for this customer and period
                existing_invoice = StorageInvoice.objects.filter(
                    customer=customer,
                    storage_period_from=storage_period_from,
                    storage_period_to=storage_period_to,
                    status__in=['draft', 'finalized']
                ).first()
                
                if existing_invoice:
                    messages.warning(request, f'Invoice already exists for {customer.customer_name} for this period.')
                    continue
                
                # Create invoice
                invoice = StorageInvoice.objects.create(
                    customer=customer,
                    invoice_date=invoice_date,
                    storage_period_from=storage_period_from,
                    storage_period_to=storage_period_to,
                    notes=notes,
                    generated_by=request.user,
                    status='draft'
                )
                
                # Calculate storage days
                storage_days = (storage_period_to - storage_period_from).days + 1
                
                # Create sample line items (you can modify this based on your business logic)
                # For now, we'll create a simple line item
                sample_item = Item.objects.first()
                sample_location = FacilityLocation.objects.first()
                
                if sample_item and sample_location:
                    StorageInvoiceItem.objects.create(
                        invoice=invoice,
                        item=sample_item,
                        location=sample_location,
                        quantity=Decimal('1.00'),
                        weight=Decimal('10.00'),
                        volume=Decimal('1.00'),
                        storage_days=storage_days,
                        charge_type='per_pallet_day',
                        rate=Decimal('5.00'),
                        line_total=Decimal('5.00') * storage_days
                    )
                
                # Calculate totals
                invoice.calculate_totals()
                generated_count += 1
            
            if generated_count > 0:
                messages.success(request, f'Successfully generated {generated_count} invoice(s).')
                return redirect('storage_invoice:storage_invoice_list')
            else:
                messages.error(request, 'No invoices were generated. Please check your settings.')
    else:
        form = GenerateInvoiceForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'storage_invoice/generate_invoice.html', context)

@login_required
def storage_invoice_edit(request, pk):
    """Edit a storage invoice"""
    invoice = get_object_or_404(StorageInvoice, pk=pk)
    
    if not invoice.is_editable:
        messages.error(request, 'This invoice cannot be edited.')
        return redirect('storage_invoice:storage_invoice_detail', pk=pk)
    
    if request.method == 'POST':
        form = StorageInvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            form.save()
            messages.success(request, 'Invoice updated successfully.')
            return redirect('storage_invoice:storage_invoice_detail', pk=pk)
    else:
        form = StorageInvoiceForm(instance=invoice)
    
    context = {
        'form': form,
        'object': invoice,
    }
    
    return render(request, 'storage_invoice/storage_invoice_edit.html', context)

@login_required
@require_POST
def storage_invoice_finalize(request, pk):
    """Finalize a storage invoice"""
    invoice = get_object_or_404(StorageInvoice, pk=pk)
    
    if invoice.can_be_finalized:
        invoice.finalize(request.user)
        messages.success(request, 'Invoice finalized successfully.')
    else:
        messages.error(request, 'This invoice cannot be finalized.')
    
    return redirect('storage_invoice:storage_invoice_detail', pk=pk)

@login_required
@require_POST
def storage_invoice_cancel(request, pk):
    """Cancel a storage invoice"""
    invoice = get_object_or_404(StorageInvoice, pk=pk)
    
    if invoice.can_be_cancelled:
        invoice.cancel(request.user)
        messages.success(request, 'Invoice cancelled successfully.')
    else:
        messages.error(request, 'This invoice cannot be cancelled.')
    
    return redirect('storage_invoice:storage_invoice_detail', pk=pk)
