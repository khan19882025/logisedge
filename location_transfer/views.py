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

from .models import Pallet, PalletItem, LocationTransfer, LocationTransferHistory
from .forms import (
    PalletSearchForm, LocationTransferForm, LocationTransferApprovalForm,
    LocationTransferProcessingForm, LocationTransferSearchForm, QuickTransferForm
)
from facility.models import FacilityLocation
from items.models import Item

@login_required
def location_transfer_list(request):
    """List all location transfers with search and filtering"""
    
    # Get search form
    search_form = LocationTransferSearchForm(request.GET)
    
    # Build queryset
    transfers = LocationTransfer.objects.select_related(
        'pallet', 'source_location', 'destination_location', 
        'created_by', 'approved_by', 'processed_by'
    ).all()
    
    # Apply filters
    if search_form.is_valid():
        if search_form.cleaned_data.get('transfer_number'):
            transfers = transfers.filter(
                transfer_number__icontains=search_form.cleaned_data['transfer_number']
            )
        
        if search_form.cleaned_data.get('pallet_id'):
            transfers = transfers.filter(
                pallet__pallet_id__icontains=search_form.cleaned_data['pallet_id']
            )
        
        if search_form.cleaned_data.get('status'):
            transfers = transfers.filter(status=search_form.cleaned_data['status'])
        
        if search_form.cleaned_data.get('transfer_type'):
            transfers = transfers.filter(transfer_type=search_form.cleaned_data['transfer_type'])
        
        if search_form.cleaned_data.get('priority'):
            transfers = transfers.filter(priority=search_form.cleaned_data['priority'])
        
        if search_form.cleaned_data.get('source_location'):
            transfers = transfers.filter(source_location=search_form.cleaned_data['source_location'])
        
        if search_form.cleaned_data.get('destination_location'):
            transfers = transfers.filter(destination_location=search_form.cleaned_data['destination_location'])
        
        if search_form.cleaned_data.get('created_by'):
            transfers = transfers.filter(created_by=search_form.cleaned_data['created_by'])
        
        if search_form.cleaned_data.get('date_from'):
            transfers = transfers.filter(created_at__date__gte=search_form.cleaned_data['date_from'])
        
        if search_form.cleaned_data.get('date_to'):
            transfers = transfers.filter(created_at__date__lte=search_form.cleaned_data['date_to'])
    
    # Get statistics
    total_transfers = LocationTransfer.objects.count()
    pending_transfers = LocationTransfer.objects.filter(status='pending').count()
    completed_transfers = LocationTransfer.objects.filter(status='completed').count()
    in_progress_transfers = LocationTransfer.objects.filter(status='in_progress').count()
    
    # Pagination
    paginator = Paginator(transfers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_transfers': total_transfers,
        'pending_transfers': pending_transfers,
        'completed_transfers': completed_transfers,
        'in_progress_transfers': in_progress_transfers,
    }
    
    return render(request, 'location_transfer/location_transfer_list.html', context)

@login_required
def location_transfer_create(request):
    """Create a new location transfer"""
    
    if request.method == 'POST':
        form = LocationTransferForm(request.POST)
        if form.is_valid():
            transfer = form.save(commit=False)
            transfer.created_by = request.user
            transfer.source_location = transfer.pallet.current_location
            transfer.save()
            
            # Create history entry
            LocationTransferHistory.objects.create(
                transfer=transfer,
                action='created',
                description=f'Transfer created by {request.user.get_full_name() or request.user.username}',
                performed_by=request.user
            )
            
            messages.success(request, f'Location transfer {transfer.transfer_number} created successfully.')
            return redirect('location_transfer:location_transfer_detail', pk=transfer.pk)
    else:
        form = LocationTransferForm()
    
    context = {
        'form': form,
        'title': 'Create Location Transfer',
        'submit_text': 'Create Transfer'
    }
    
    return render(request, 'location_transfer/location_transfer_form.html', context)

@login_required
def location_transfer_detail(request, pk):
    """View details of a location transfer"""
    
    transfer = get_object_or_404(LocationTransfer.objects.select_related(
        'pallet', 'source_location', 'destination_location', 
        'created_by', 'approved_by', 'processed_by'
    ), pk=pk)
    
    # Get pallet items
    pallet_items = transfer.pallet.pallet_items.select_related('item').all()
    
    # Get transfer history
    history = transfer.history.select_related('performed_by').all()
    
    context = {
        'transfer': transfer,
        'pallet_items': pallet_items,
        'history': history,
    }
    
    return render(request, 'location_transfer/location_transfer_detail.html', context)

@login_required
def location_transfer_edit(request, pk):
    """Edit a location transfer"""
    
    transfer = get_object_or_404(LocationTransfer, pk=pk)
    
    # Only allow editing if transfer is not completed
    if transfer.status == 'completed':
        messages.error(request, 'Cannot edit a completed transfer.')
        return redirect('location_transfer:location_transfer_detail', pk=pk)
    
    if request.method == 'POST':
        form = LocationTransferForm(request.POST, instance=transfer)
        if form.is_valid():
            transfer = form.save(commit=False)
            transfer.updated_by = request.user
            transfer.save()
            
            # Create history entry
            LocationTransferHistory.objects.create(
                transfer=transfer,
                action='notes_updated',
                description=f'Transfer updated by {request.user.get_full_name() or request.user.username}',
                performed_by=request.user
            )
            
            messages.success(request, f'Location transfer {transfer.transfer_number} updated successfully.')
            return redirect('location_transfer:location_transfer_detail', pk=pk)
    else:
        form = LocationTransferForm(instance=transfer)
    
    context = {
        'form': form,
        'transfer': transfer,
        'title': 'Edit Location Transfer',
        'submit_text': 'Update Transfer'
    }
    
    return render(request, 'location_transfer/location_transfer_form.html', context)

@login_required
def location_transfer_approve(request, pk):
    """Approve a location transfer"""
    
    transfer = get_object_or_404(LocationTransfer, pk=pk)
    
    if transfer.is_approved:
        messages.warning(request, 'This transfer is already approved.')
        return redirect('location_transfer:location_transfer_detail', pk=pk)
    
    if request.method == 'POST':
        form = LocationTransferApprovalForm(request.POST, instance=transfer)
        if form.is_valid():
            transfer.approve(request.user)
            transfer.save()
            
            # Create history entry
            LocationTransferHistory.objects.create(
                transfer=transfer,
                action='approved',
                description=f'Transfer approved by {request.user.get_full_name() or request.user.username}',
                performed_by=request.user,
                additional_data={'notes': form.cleaned_data.get('notes', '')}
            )
            
            messages.success(request, f'Location transfer {transfer.transfer_number} approved successfully.')
            return redirect('location_transfer:location_transfer_detail', pk=pk)
    else:
        form = LocationTransferApprovalForm(instance=transfer)
    
    context = {
        'form': form,
        'transfer': transfer,
        'title': 'Approve Location Transfer',
        'submit_text': 'Approve Transfer'
    }
    
    return render(request, 'location_transfer/location_transfer_approve.html', context)

@login_required
def location_transfer_process(request, pk):
    """Process a location transfer"""
    
    transfer = get_object_or_404(LocationTransfer, pk=pk)
    
    if not transfer.can_be_processed:
        messages.error(request, 'This transfer cannot be processed.')
        return redirect('location_transfer:location_transfer_detail', pk=pk)
    
    if request.method == 'POST':
        form = LocationTransferProcessingForm(request.POST, instance=transfer)
        if form.is_valid():
            try:
                transfer.process(request.user)
                
                # Create history entry
                LocationTransferHistory.objects.create(
                    transfer=transfer,
                    action='completed',
                    description=f'Transfer processed by {request.user.get_full_name() or request.user.username}',
                    performed_by=request.user,
                    additional_data={'notes': form.cleaned_data.get('notes', '')}
                )
                
                messages.success(request, f'Location transfer {transfer.transfer_number} processed successfully.')
                return redirect('location_transfer:location_transfer_detail', pk=pk)
            except ValueError as e:
                messages.error(request, str(e))
    else:
        form = LocationTransferProcessingForm(instance=transfer)
    
    context = {
        'form': form,
        'transfer': transfer,
        'title': 'Process Location Transfer',
        'submit_text': 'Process Transfer'
    }
    
    return render(request, 'location_transfer/location_transfer_process.html', context)

@login_required
def location_transfer_cancel(request, pk):
    """Cancel a location transfer"""
    
    transfer = get_object_or_404(LocationTransfer, pk=pk)
    
    if transfer.status in ['completed', 'cancelled']:
        messages.error(request, 'Cannot cancel a completed or already cancelled transfer.')
        return redirect('location_transfer:location_transfer_detail', pk=pk)
    
    if request.method == 'POST':
        transfer.status = 'cancelled'
        transfer.updated_by = request.user
        transfer.save()
        
        # Create history entry
        LocationTransferHistory.objects.create(
            transfer=transfer,
            action='cancelled',
            description=f'Transfer cancelled by {request.user.get_full_name() or request.user.username}',
            performed_by=request.user
        )
        
        messages.success(request, f'Location transfer {transfer.transfer_number} cancelled successfully.')
        return redirect('location_transfer:location_transfer_detail', pk=pk)
    
    context = {
        'transfer': transfer,
        'title': 'Cancel Location Transfer'
    }
    
    return render(request, 'location_transfer/location_transfer_cancel.html', context)

@login_required
def pallet_list(request):
    """List all pallets with search and filtering"""
    
    # Get search form
    search_form = PalletSearchForm(request.GET)
    
    # Build queryset
    pallets = Pallet.objects.select_related('current_location', 'created_by').all()
    
    # Apply filters
    if search_form.is_valid():
        if search_form.cleaned_data.get('pallet_id'):
            pallets = pallets.filter(pallet_id__icontains=search_form.cleaned_data['pallet_id'])
        
        if search_form.cleaned_data.get('location'):
            pallets = pallets.filter(current_location=search_form.cleaned_data['location'])
        
        if search_form.cleaned_data.get('status'):
            pallets = pallets.filter(status=search_form.cleaned_data['status'])
    
    # Get statistics
    total_pallets = Pallet.objects.count()
    active_pallets = Pallet.objects.filter(status='active').count()
    pallets_with_location = Pallet.objects.filter(current_location__isnull=False).count()
    pallets_without_location = Pallet.objects.filter(current_location__isnull=True).count()
    
    # Pagination
    paginator = Paginator(pallets, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_pallets': total_pallets,
        'active_pallets': active_pallets,
        'pallets_with_location': pallets_with_location,
        'pallets_without_location': pallets_without_location,
    }
    
    return render(request, 'location_transfer/pallet_list.html', context)

@login_required
def pallet_detail(request, pk):
    """View details of a pallet"""
    
    pallet = get_object_or_404(Pallet.objects.select_related('current_location', 'created_by'), pk=pk)
    pallet_items = pallet.pallet_items.select_related('item').all()
    
    # Get transfer history for this pallet
    transfers = LocationTransfer.objects.filter(pallet=pallet).select_related(
        'source_location', 'destination_location', 'created_by'
    ).order_by('-created_at')
    
    context = {
        'pallet': pallet,
        'pallet_items': pallet_items,
        'transfers': transfers,
    }
    
    return render(request, 'location_transfer/pallet_detail.html', context)

@login_required
def quick_transfer(request):
    """Quick transfer form for immediate pallet transfer"""
    
    if request.method == 'POST':
        form = QuickTransferForm(request.POST)
        if form.is_valid():
            pallet_id = form.cleaned_data['pallet_id']
            destination_location = form.cleaned_data['destination_location']
            notes = form.cleaned_data.get('notes', '')
            
            try:
                pallet = Pallet.objects.get(pallet_id=pallet_id, status='active')
                
                # Create transfer
                transfer = LocationTransfer.objects.create(
                    pallet=pallet,
                    transfer_type='internal',
                    source_location=pallet.current_location,
                    destination_location=destination_location,
                    priority='normal',
                    notes=notes,
                    created_by=request.user
                )
                
                # Auto-approve and process
                transfer.approve(request.user)
                transfer.process(request.user)
                
                messages.success(request, f'Pallet {pallet_id} transferred to {destination_location.display_name} successfully.')
                return redirect('location_transfer:location_transfer_detail', pk=transfer.pk)
                
            except Pallet.DoesNotExist:
                messages.error(request, f'Pallet {pallet_id} not found.')
            except Exception as e:
                messages.error(request, f'Error processing transfer: {str(e)}')
    else:
        form = QuickTransferForm()
    
    context = {
        'form': form,
        'title': 'Quick Transfer',
        'submit_text': 'Transfer Pallet'
    }
    
    return render(request, 'location_transfer/quick_transfer.html', context)

# AJAX endpoints
@login_required
@csrf_exempt
def get_pallet_details(request):
    """Get pallet details via AJAX"""
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            pallet_id = data.get('pallet_id')
            
            if not pallet_id:
                return JsonResponse({'error': 'Pallet ID is required'}, status=400)
            
            try:
                pallet = Pallet.objects.select_related('current_location').get(
                    pallet_id=pallet_id, 
                    status='active'
                )
                
                # Get pallet items
                items = pallet.pallet_items.select_related('item').all()
                items_data = []
                
                for item in items:
                    items_data.append({
                        'item_name': item.item.item_name,
                        'item_code': item.item.item_code,
                        'quantity': str(item.quantity),
                        'unit_of_measure': item.unit_of_measure,
                        'batch_number': item.batch_number,
                        'serial_number': item.serial_number,
                        'expiry_date': item.expiry_date.strftime('%Y-%m-%d') if item.expiry_date else None,
                        'total_value': str(item.total_value) if item.total_value else None,
                    })
                
                response_data = {
                    'pallet_id': pallet.pallet_id,
                    'description': pallet.description,
                    'status': pallet.status,
                    'current_location': {
                        'id': pallet.current_location.id,
                        'name': pallet.current_location.display_name,
                        'code': pallet.current_location.location_code,
                    } if pallet.current_location else None,
                    'weight': str(pallet.weight) if pallet.weight else None,
                    'volume': str(pallet.volume) if pallet.volume else None,
                    'dimensions': pallet.dimensions,
                    'items': items_data,
                    'total_items': len(items_data),
                    'total_quantity': sum(float(item['quantity']) for item in items_data),
                }
                
                return JsonResponse(response_data)
                
            except Pallet.DoesNotExist:
                return JsonResponse({'error': f'Pallet {pallet_id} not found'}, status=404)
                
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
@csrf_exempt
def search_pallets(request):
    """Search pallets via AJAX"""
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            query = data.get('query', '').strip()
            
            if len(query) < 2:
                return JsonResponse({'pallets': []})
            
            pallets = Pallet.objects.filter(
                Q(pallet_id__icontains=query) | Q(description__icontains=query),
                status='active'
            ).select_related('current_location')[:10]
            
            pallets_data = []
            for pallet in pallets:
                pallets_data.append({
                    'id': pallet.id,
                    'pallet_id': pallet.pallet_id,
                    'description': pallet.description,
                    'current_location': pallet.current_location.display_name if pallet.current_location else 'No Location',
                })
            
            return JsonResponse({'pallets': pallets_data})
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
@csrf_exempt
def get_available_locations(request):
    """Get available locations for transfer via AJAX"""
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            source_location_id = data.get('source_location_id')
            
            # Get all active locations except the source
            locations = FacilityLocation.objects.filter(status='active')
            if source_location_id:
                locations = locations.exclude(id=source_location_id)
            
            locations_data = []
            for location in locations:
                locations_data.append({
                    'id': location.id,
                    'name': location.display_name,
                    'code': location.location_code,
                    'type': location.location_type,
                    'utilization': float(location.current_utilization),
                    'capacity': str(location.capacity) if location.capacity else None,
                    'is_available': location.is_available,
                })
            
            return JsonResponse({'locations': locations_data})
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
def location_transfer_dashboard(request):
    """Dashboard view for location transfers"""
    
    # Get recent transfers
    recent_transfers = LocationTransfer.objects.select_related(
        'pallet', 'source_location', 'destination_location'
    ).order_by('-created_at')[:10]
    
    # Get statistics
    total_transfers = LocationTransfer.objects.count()
    pending_transfers = LocationTransfer.objects.filter(status='pending').count()
    completed_transfers = LocationTransfer.objects.filter(status='completed').count()
    in_progress_transfers = LocationTransfer.objects.filter(status='in_progress').count()
    
    # Get transfers by status
    transfers_by_status = LocationTransfer.objects.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    # Get transfers by type
    transfers_by_type = LocationTransfer.objects.values('transfer_type').annotate(
        count=Count('id')
    ).order_by('transfer_type')
    
    # Get top source locations
    top_source_locations = LocationTransfer.objects.values(
        'source_location__location_name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    # Get top destination locations
    top_destination_locations = LocationTransfer.objects.values(
        'destination_location__location_name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    context = {
        'recent_transfers': recent_transfers,
        'total_transfers': total_transfers,
        'pending_transfers': pending_transfers,
        'completed_transfers': completed_transfers,
        'in_progress_transfers': in_progress_transfers,
        'transfers_by_status': transfers_by_status,
        'transfers_by_type': transfers_by_type,
        'top_source_locations': top_source_locations,
        'top_destination_locations': top_destination_locations,
    }
    
    return render(request, 'location_transfer/location_transfer_dashboard.html', context)
