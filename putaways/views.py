from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Putaway
from .forms import PutawayForm
from items.models import Item
from grn.models import GRN, GRNPallet

@login_required
def putaway_list(request):
    """Display list of all putaways"""
    putaways = Putaway.objects.all().order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        putaways = putaways.filter(
            Q(putaway_number__icontains=search_query) |
            Q(grn__grn_number__icontains=search_query) |
            Q(item__item_name__icontains=search_query) |
            Q(pallet_id__icontains=search_query) |
            Q(location__location_name__icontains=search_query)
        )
    
    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        putaways = putaways.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(putaways, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'putaways': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': Putaway.STATUS_CHOICES,
    }
    
    return render(request, 'putaways/putaway_list.html', context)

@login_required
def putaway_create(request):
    """Create a new putaway"""
    if request.method == 'POST':
        form = PutawayForm(request.POST)
        if form.is_valid():
            putaway = form.save(commit=False)
            putaway.created_by = request.user
            putaway.save()
            messages.success(request, f'Putaway {putaway.putaway_number} created successfully!')
            return redirect('putaways:putaway_detail', pk=putaway.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PutawayForm()
    
    context = {
        'form': form,
        'submit_text': 'Create Putaway',
        'page_title': 'Create New Putaway'
    }
    
    return render(request, 'putaways/putaway_form.html', context)

@login_required
def putaway_detail(request, pk):
    """Display putaway details"""
    putaway = get_object_or_404(Putaway, pk=pk)
    
    context = {
        'putaway': putaway,
    }
    
    return render(request, 'putaways/putaway_detail.html', context)

@login_required
def putaway_edit(request, pk):
    """Edit an existing putaway"""
    putaway = get_object_or_404(Putaway, pk=pk)
    
    if request.method == 'POST':
        form = PutawayForm(request.POST, instance=putaway)
        if form.is_valid():
            putaway = form.save()
            messages.success(request, f'Putaway {putaway.putaway_number} updated successfully!')
            return redirect('putaways:putaway_detail', pk=putaway.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PutawayForm(instance=putaway)
    
    context = {
        'form': form,
        'putaway': putaway,
        'submit_text': 'Update Putaway',
        'page_title': f'Edit Putaway {putaway.putaway_number}'
    }
    
    return render(request, 'putaways/putaway_form.html', context)

@login_required
def putaway_delete(request, pk):
    """Delete a putaway"""
    putaway = get_object_or_404(Putaway, pk=pk)
    
    if request.method == 'POST':
        putaway_number = putaway.putaway_number
        putaway.delete()
        messages.success(request, f'Putaway {putaway_number} deleted successfully!')
        return redirect('putaways:putaway_list')
    
    context = {
        'putaway': putaway,
    }
    
    return render(request, 'putaways/putaway_confirm_delete.html', context)

@login_required
def get_grn_pallets(request, grn_id):
    """AJAX endpoint to get pallets for a specific GRN"""
    try:
        pallets = GRNPallet.objects.filter(grn_id=grn_id).select_related('item')
        
        pallets_data = []
        for pallet in pallets:
            pallets_data.append({
                'id': pallet.pallet_no,
                'name': pallet.pallet_no,  # Show only pallet ID
                'pallet_no': pallet.pallet_no,
                'description': pallet.description,
            })
        
        return JsonResponse({
            'success': True,
            'pallets': pallets_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def get_pallet_details(request, grn_id, pallet_id):
    """AJAX endpoint to get details for a specific pallet"""
    try:
        pallet = GRNPallet.objects.get(grn_id=grn_id, pallet_no=pallet_id)
        
        pallet_data = {
            'item_id': pallet.item.id if pallet.item else None,
            'item_name': pallet.item.item_name if pallet.item else pallet.description,
            'item_code': pallet.item.item_code if pallet.item else '',
            'quantity': float(pallet.quantity),
            'weight': float(pallet.weight) if pallet.weight else 0,
            'volume': float(pallet.volume) if pallet.volume else 0,
            'description': pallet.description,
        }
        
        return JsonResponse({
            'success': True,
            'pallet': pallet_data
        })
    except GRNPallet.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Pallet not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def get_grn_items(request, grn_id):
    """AJAX endpoint to get items for a specific GRN"""
    try:
        from grn.models import GRNItem
        grn_items = GRNItem.objects.filter(grn_id=grn_id).select_related('item')
        
        items_data = []
        for grn_item in grn_items:
            items_data.append({
                'id': grn_item.item.id,
                'name': grn_item.item.item_name,
                'code': grn_item.item.item_code,
                'available_qty': float(grn_item.received_qty or 0),
            })
        
        return JsonResponse({
            'success': True,
            'items': items_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def putaway_status_update(request, pk):
    """Update putaway status"""
    putaway = get_object_or_404(Putaway, pk=pk)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Putaway.STATUS_CHOICES):
            putaway.status = new_status
            if new_status == 'completed':
                from django.utils import timezone
                putaway.completed_date = timezone.now()
            putaway.save()
            messages.success(request, f'Putaway status updated to {putaway.get_status_display()}')
        else:
            messages.error(request, 'Invalid status')
    
    return redirect('putaways:putaway_detail', pk=putaway.pk) 