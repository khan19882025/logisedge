from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

from .models import StockTransfer, StockTransferItem, StockLedger
from .forms import (
    StockTransferForm, StockTransferItemForm, StockTransferSearchForm,
    StockLedgerSearchForm, StockTransferApprovalForm, StockTransferProcessingForm,
    StockTransferItemFormSet
)
from facility.models import Facility
from items.models import Item


@login_required
def stock_transfer_list(request):
    """List all stock transfers with search and filtering"""
    
    # Get search parameters
    search_form = StockTransferSearchForm(request.GET)
    transfers = StockTransfer.objects.all()
    
    if search_form.is_valid():
        transfer_number = search_form.cleaned_data.get('transfer_number')
        transfer_date_from = search_form.cleaned_data.get('transfer_date_from')
        transfer_date_to = search_form.cleaned_data.get('transfer_date_to')
        transfer_type = search_form.cleaned_data.get('transfer_type')
        status = search_form.cleaned_data.get('status')
        source_facility = search_form.cleaned_data.get('source_facility')
        destination_facility = search_form.cleaned_data.get('destination_facility')
        created_by = search_form.cleaned_data.get('created_by')
        
        # Apply filters
        if transfer_number:
            transfers = transfers.filter(transfer_number__icontains=transfer_number)
        
        if transfer_date_from:
            transfers = transfers.filter(transfer_date__gte=transfer_date_from)
        
        if transfer_date_to:
            transfers = transfers.filter(transfer_date__lte=transfer_date_to)
        
        if transfer_type:
            transfers = transfers.filter(transfer_type=transfer_type)
        
        if status:
            transfers = transfers.filter(status=status)
        
        if source_facility:
            transfers = transfers.filter(source_facility=source_facility)
        
        if destination_facility:
            transfers = transfers.filter(destination_facility=destination_facility)
        
        if created_by:
            transfers = transfers.filter(created_by__username__icontains=created_by)
    
    # Pagination
    paginator = Paginator(transfers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_transfers = transfers.count()
    pending_transfers = transfers.filter(status='pending').count()
    approved_transfers = transfers.filter(status='approved').count()
    completed_transfers = transfers.filter(status='completed').count()
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_transfers': total_transfers,
        'pending_transfers': pending_transfers,
        'approved_transfers': approved_transfers,
        'completed_transfers': completed_transfers,
    }
    
    return render(request, 'stock_transfer/stock_transfer_list.html', context)


@login_required
def stock_transfer_create(request):
    """Create a new stock transfer"""
    
    if request.method == 'POST':
        form = StockTransferForm(request.POST)
        formset = StockTransferItemFormSet(request.POST, instance=StockTransfer())
        
        if form.is_valid() and formset.is_valid():
            transfer = form.save(commit=False)
            transfer.created_by = request.user
            transfer.save()
            
            # Save formset
            formset.instance = transfer
            formset.save()
            
            messages.success(request, f'Stock transfer {transfer.transfer_number} created successfully.')
            return redirect('stock_transfer:stock_transfer_detail', pk=transfer.pk)
    else:
        form = StockTransferForm()
        formset = StockTransferItemFormSet(instance=StockTransfer())
    
    context = {
        'form': form,
        'formset': formset,
        'title': 'Create Stock Transfer',
        'submit_text': 'Create Transfer',
    }
    
    return render(request, 'stock_transfer/stock_transfer_form.html', context)


@login_required
def stock_transfer_detail(request, pk):
    """View stock transfer details"""
    
    transfer = get_object_or_404(StockTransfer, pk=pk)
    items = transfer.items.all()
    
    context = {
        'transfer': transfer,
        'items': items,
    }
    
    return render(request, 'stock_transfer/stock_transfer_detail.html', context)


@login_required
def stock_transfer_edit(request, pk):
    """Edit an existing stock transfer"""
    
    transfer = get_object_or_404(StockTransfer, pk=pk)
    
    # Only allow editing if transfer is in draft or pending status
    if transfer.status not in ['draft', 'pending']:
        messages.error(request, 'Cannot edit transfer that is not in draft or pending status.')
        return redirect('stock_transfer:stock_transfer_detail', pk=transfer.pk)
    
    if request.method == 'POST':
        form = StockTransferForm(request.POST, instance=transfer)
        formset = StockTransferItemFormSet(request.POST, instance=transfer)
        
        if form.is_valid() and formset.is_valid():
            transfer = form.save(commit=False)
            transfer.updated_by = request.user
            transfer.save()
            
            formset.save()
            
            messages.success(request, f'Stock transfer {transfer.transfer_number} updated successfully.')
            return redirect('stock_transfer:stock_transfer_detail', pk=transfer.pk)
    else:
        form = StockTransferForm(instance=transfer)
        formset = StockTransferItemFormSet(instance=transfer)
    
    context = {
        'form': form,
        'formset': formset,
        'transfer': transfer,
        'title': 'Edit Stock Transfer',
        'submit_text': 'Update Transfer',
    }
    
    return render(request, 'stock_transfer/stock_transfer_form.html', context)


@login_required
def stock_transfer_approve(request, pk):
    """Approve a stock transfer"""
    
    transfer = get_object_or_404(StockTransfer, pk=pk)
    
    if transfer.status != 'pending':
        messages.error(request, 'Only pending transfers can be approved.')
        return redirect('stock_transfer:stock_transfer_detail', pk=transfer.pk)
    
    if request.method == 'POST':
        form = StockTransferApprovalForm(request.POST, instance=transfer)
        if form.is_valid():
            transfer.approve(request.user)
            messages.success(request, f'Stock transfer {transfer.transfer_number} approved successfully.')
            return redirect('stock_transfer:stock_transfer_detail', pk=transfer.pk)
    else:
        form = StockTransferApprovalForm(instance=transfer)
    
    context = {
        'form': form,
        'transfer': transfer,
        'title': 'Approve Stock Transfer',
        'submit_text': 'Approve Transfer',
    }
    
    return render(request, 'stock_transfer/stock_transfer_approve.html', context)


@login_required
def stock_transfer_process(request, pk):
    """Process a stock transfer (mark as completed)"""
    
    transfer = get_object_or_404(StockTransfer, pk=pk)
    
    if not transfer.can_be_processed:
        messages.error(request, 'Only approved transfers can be processed.')
        return redirect('stock_transfer:stock_transfer_detail', pk=transfer.pk)
    
    if request.method == 'POST':
        form = StockTransferProcessingForm(request.POST, instance=transfer)
        if form.is_valid():
            # Process the transfer
            transfer.process(request.user)
            
            # Create stock ledger entries
            create_stock_ledger_entries(transfer, request.user)
            
            messages.success(request, f'Stock transfer {transfer.transfer_number} processed successfully.')
            return redirect('stock_transfer:stock_transfer_detail', pk=transfer.pk)
    else:
        form = StockTransferProcessingForm(instance=transfer)
    
    context = {
        'form': form,
        'transfer': transfer,
        'title': 'Process Stock Transfer',
        'submit_text': 'Process Transfer',
    }
    
    return render(request, 'stock_transfer/stock_transfer_process.html', context)


@login_required
def stock_transfer_cancel(request, pk):
    """Cancel a stock transfer"""
    
    transfer = get_object_or_404(StockTransfer, pk=pk)
    
    if transfer.status in ['completed', 'cancelled']:
        messages.error(request, 'Cannot cancel a completed or already cancelled transfer.')
        return redirect('stock_transfer:stock_transfer_detail', pk=transfer.pk)
    
    if request.method == 'POST':
        transfer.status = 'cancelled'
        transfer.updated_by = request.user
        transfer.save()
        
        messages.success(request, f'Stock transfer {transfer.transfer_number} cancelled successfully.')
        return redirect('stock_transfer:stock_transfer_list')
    
    context = {
        'transfer': transfer,
        'title': 'Cancel Stock Transfer',
    }
    
    return render(request, 'stock_transfer/stock_transfer_cancel.html', context)


@login_required
def stock_ledger_list(request):
    """List stock ledger entries with search and filtering"""
    
    # Get search parameters
    search_form = StockLedgerSearchForm(request.GET)
    entries = StockLedger.objects.all()
    
    if search_form.is_valid():
        item = search_form.cleaned_data.get('item')
        facility = search_form.cleaned_data.get('facility')
        movement_type = search_form.cleaned_data.get('movement_type')
        movement_date_from = search_form.cleaned_data.get('movement_date_from')
        movement_date_to = search_form.cleaned_data.get('movement_date_to')
        reference_number = search_form.cleaned_data.get('reference_number')
        
        # Apply filters
        if item:
            entries = entries.filter(item=item)
        
        if facility:
            entries = entries.filter(facility=facility)
        
        if movement_type:
            entries = entries.filter(movement_type=movement_type)
        
        if movement_date_from:
            entries = entries.filter(movement_date__gte=movement_date_from)
        
        if movement_date_to:
            entries = entries.filter(movement_date__lte=movement_date_to)
        
        if reference_number:
            entries = entries.filter(reference_number__icontains=reference_number)
    
    # Pagination
    paginator = Paginator(entries, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
    }
    
    return render(request, 'stock_transfer/stock_ledger_list.html', context)


@login_required
def stock_balance_report(request):
    """Generate stock balance report"""
    
    # Get current stock balances
    balances = StockLedger.objects.values(
        'item__item_name', 'item__item_code', 'facility__facility_name'
    ).annotate(
        current_balance=Sum('quantity_in') - Sum('quantity_out')
    ).filter(
        current_balance__gt=0
    ).order_by('item__item_name', 'facility__facility_name')
    
    context = {
        'balances': balances,
    }
    
    return render(request, 'stock_transfer/stock_balance_report.html', context)


# AJAX views for dynamic functionality

@login_required
@csrf_exempt
def get_item_details(request):
    """Get item details for AJAX requests"""
    
    if request.method == 'POST':
        data = json.loads(request.body)
        item_id = data.get('item_id')
        source_facility_id = data.get('source_facility_id')
        
        try:
            item = Item.objects.get(pk=item_id)
            
            # Get available quantity (this would need to be implemented based on your stock tracking)
            available_quantity = get_available_quantity(item, source_facility_id)
            
            response_data = {
                'success': True,
                'item': {
                    'id': item.id,
                    'name': item.item_name,
                    'code': item.item_code,
                    'unit_of_measure': item.unit_of_measure,
                    'unit_cost': float(item.cost_price) if item.cost_price else None,
                    'unit_weight': float(item.weight) if item.weight else None,
                    'unit_volume': float(item.cbm) if item.cbm else None,
                    'available_quantity': float(available_quantity),
                }
            }
        except Item.DoesNotExist:
            response_data = {
                'success': False,
                'error': 'Item not found'
            }
        except Exception as e:
            response_data = {
                'success': False,
                'error': str(e)
            }
        
        return JsonResponse(response_data)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@csrf_exempt
def search_items(request):
    """Search items for autocomplete"""
    
    if request.method == 'GET':
        query = request.GET.get('q', '')
        
        if len(query) >= 2:
            items = Item.objects.filter(
                Q(item_name__icontains=query) | Q(item_code__icontains=query),
                status='active'
            )[:10]
            
            results = []
            for item in items:
                results.append({
                    'id': item.id,
                    'text': f"{item.item_code} - {item.item_name}",
                    'name': item.item_name,
                    'code': item.item_code,
                })
            
            return JsonResponse({'results': results})
    
    return JsonResponse({'results': []})


# Helper functions

def get_available_quantity(item, facility_id):
    """Get available quantity for an item at a specific facility"""
    # This is a placeholder implementation
    # You would need to implement this based on your stock tracking system
    
    try:
        # Get the latest stock balance for this item and facility
        latest_entry = StockLedger.objects.filter(
            item=item,
            facility_id=facility_id
        ).order_by('-movement_date', '-created_at').first()
        
        if latest_entry:
            return latest_entry.running_balance
        else:
            return 0
    except:
        return 0


def create_stock_ledger_entries(transfer, user):
    """Create stock ledger entries for a completed transfer"""
    
    for item in transfer.items.all():
        # Create transfer out entry for source facility
        StockLedger.objects.create(
            movement_date=transfer.transfer_date,
            movement_type='transfer_out',
            reference_number=transfer.transfer_number,
            item=item.item,
            facility=transfer.source_facility,
            location=item.source_location,
            quantity_out=item.quantity,
            unit_cost=item.unit_cost,
            batch_number=item.batch_number,
            serial_number=item.serial_number,
            stock_transfer=transfer,
            notes=f"Transfer to {transfer.destination_facility.facility_name}",
            created_by=user
        )
        
        # Create transfer in entry for destination facility
        StockLedger.objects.create(
            movement_date=transfer.transfer_date,
            movement_type='transfer_in',
            reference_number=transfer.transfer_number,
            item=item.item,
            facility=transfer.destination_facility,
            location=item.destination_location,
            quantity_in=item.quantity,
            unit_cost=item.unit_cost,
            batch_number=item.batch_number,
            serial_number=item.serial_number,
            stock_transfer=transfer,
            notes=f"Transfer from {transfer.source_facility.facility_name}",
            created_by=user
        )
