from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST, require_http_methods
from django.db import models
from django.urls import reverse
from .models import DispatchNote, DispatchItem
from .forms import DispatchNoteForm, DispatchItemForm, DispatchNoteSearchForm
from customer.models import Customer
from delivery_order.models import DeliveryOrder, DeliveryOrderItem

@login_required
def dispatch_list(request):
    """List all dispatch notes with search and filtering"""
    search_form = DispatchNoteSearchForm(request.GET)
    dispatch_notes = DispatchNote.objects.all().prefetch_related('dispatch_items')
    
    if search_form.is_valid():
        search = search_form.cleaned_data.get('search')
        status = search_form.cleaned_data.get('status')
        customer = search_form.cleaned_data.get('customer')
        date_from = search_form.cleaned_data.get('date_from')
        date_to = search_form.cleaned_data.get('date_to')
        
        if search:
            dispatch_notes = dispatch_notes.filter(
                Q(gdn_number__icontains=search) |
                Q(customer__customer_name__icontains=search) |
                Q(delivery_order__do_number__icontains=search)
            )
        
        if status:
            dispatch_notes = dispatch_notes.filter(status=status)
        
        if customer:
            dispatch_notes = dispatch_notes.filter(customer=customer)
        
        if date_from:
            dispatch_notes = dispatch_notes.filter(dispatch_date__gte=date_from)
        
        if date_to:
            dispatch_notes = dispatch_notes.filter(dispatch_date__lte=date_to)
    
    # Pagination
    paginator = Paginator(dispatch_notes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_dispatch_notes': dispatch_notes.count(),
    }
    
    return render(request, 'dispatchnote/dispatch_list.html', context)

@login_required
def dispatch_create(request):
    """Create a new dispatch note"""
    if request.method == 'POST':
        form = DispatchNoteForm(request.POST)
        
        if form.is_valid():
            dispatch_note = form.save(commit=False)
            dispatch_note.created_by = request.user
            dispatch_note.save()
            
            # Handle cargo items from form data
            cargo_data = request.POST.getlist('grn_no[]')
            for i, grn_no in enumerate(cargo_data):
                if grn_no:  # Only create item if GRN number is provided
                    # Get all the cargo item fields with safe indexing
                    item_code_list = request.POST.getlist('item_code[]')
                    item_name_list = request.POST.getlist('item_name[]')
                    hs_code_list = request.POST.getlist('hs_code[]')
                    unit_list = request.POST.getlist('unit[]')
                    qty_list = request.POST.getlist('qty[]')
                    coo_list = request.POST.getlist('coo[]')
                    n_weight_list = request.POST.getlist('n_weight[]')
                    g_weight_list = request.POST.getlist('g_weight[]')
                    cbm_list = request.POST.getlist('cbm[]')
                    p_date_list = request.POST.getlist('p_date[]')
                    e_date_list = request.POST.getlist('e_date[]')
                    color_list = request.POST.getlist('color[]')
                    size_list = request.POST.getlist('size[]')
                    barcode_list = request.POST.getlist('barcode[]')
                    rate_list = request.POST.getlist('rate[]')
                    amount_list = request.POST.getlist('amount[]')
                    ed_cntr_list = request.POST.getlist('ed_cntr[]')
                    ed_list = request.POST.getlist('ed[]')
                    ctnr_list = request.POST.getlist('ctnr[]')
                    
                    DispatchItem.objects.create(
                        dispatch_note=dispatch_note,
                        grn_no=grn_no,
                        item_code=item_code_list[i] if i < len(item_code_list) else '',
                        item_name=item_name_list[i] if i < len(item_name_list) else '',
                        hs_code=hs_code_list[i] if i < len(hs_code_list) else '',
                        unit=unit_list[i] if i < len(unit_list) else '',
                        quantity=qty_list[i] if i < len(qty_list) else 0,
                        coo=coo_list[i] if i < len(coo_list) else '',
                        n_weight=n_weight_list[i] if i < len(n_weight_list) else 0,
                        g_weight=g_weight_list[i] if i < len(g_weight_list) else 0,
                        cbm=cbm_list[i] if i < len(cbm_list) else 0,
                        p_date=p_date_list[i] if i < len(p_date_list) and p_date_list[i] else None,
                        e_date=e_date_list[i] if i < len(e_date_list) and e_date_list[i] else None,
                        color=color_list[i] if i < len(color_list) else '',
                        size=size_list[i] if i < len(size_list) else '',
                        barcode=barcode_list[i] if i < len(barcode_list) else '',
                        rate=rate_list[i] if i < len(rate_list) else 0,
                        amount=amount_list[i] if i < len(amount_list) else 0,
                        ed_cntr=ed_cntr_list[i] if i < len(ed_cntr_list) else '',
                        ed=ed_list[i] if i < len(ed_list) else '',
                        ctnr=ctnr_list[i] if i < len(ctnr_list) else '',
                    )
            
            messages.success(request, f'Dispatch Note {dispatch_note.gdn_number} created successfully!')
            return redirect('dispatchnote:dispatch_detail', pk=dispatch_note.pk)
    else:
        form = DispatchNoteForm()
    
    context = {
        'form': form,
        'title': 'Create Dispatch Note',
        'action': 'Create'
    }
    
    return render(request, 'dispatchnote/dispatch_form.html', context)

@login_required
def dispatch_update(request, pk):
    """Update an existing dispatch note"""
    dispatch_note = get_object_or_404(DispatchNote, pk=pk)
    
    if request.method == 'POST':
        form = DispatchNoteForm(request.POST, instance=dispatch_note)
        if form.is_valid():
            dispatch_note = form.save(commit=False)
            dispatch_note.updated_by = request.user
            dispatch_note.save()
            
            # Clear existing items and recreate from form data
            dispatch_note.dispatch_items.all().delete()
            
            # Handle cargo items from form data
            cargo_data = request.POST.getlist('grn_no[]')
            for i, grn_no in enumerate(cargo_data):
                if grn_no:  # Only create item if GRN number is provided
                    # Get all the cargo item fields with safe indexing
                    item_code_list = request.POST.getlist('item_code[]')
                    item_name_list = request.POST.getlist('item_name[]')
                    hs_code_list = request.POST.getlist('hs_code[]')
                    unit_list = request.POST.getlist('unit[]')
                    qty_list = request.POST.getlist('qty[]')
                    coo_list = request.POST.getlist('coo[]')
                    n_weight_list = request.POST.getlist('n_weight[]')
                    g_weight_list = request.POST.getlist('g_weight[]')
                    cbm_list = request.POST.getlist('cbm[]')
                    p_date_list = request.POST.getlist('p_date[]')
                    e_date_list = request.POST.getlist('e_date[]')
                    color_list = request.POST.getlist('color[]')
                    size_list = request.POST.getlist('size[]')
                    barcode_list = request.POST.getlist('barcode[]')
                    rate_list = request.POST.getlist('rate[]')
                    amount_list = request.POST.getlist('amount[]')
                    ed_cntr_list = request.POST.getlist('ed_cntr[]')
                    ed_list = request.POST.getlist('ed[]')
                    ctnr_list = request.POST.getlist('ctnr[]')
                    
                    DispatchItem.objects.create(
                        dispatch_note=dispatch_note,
                        grn_no=grn_no,
                        item_code=item_code_list[i] if i < len(item_code_list) else '',
                        item_name=item_name_list[i] if i < len(item_name_list) else '',
                        hs_code=hs_code_list[i] if i < len(hs_code_list) else '',
                        unit=unit_list[i] if i < len(unit_list) else '',
                        quantity=qty_list[i] if i < len(qty_list) else 0,
                        coo=coo_list[i] if i < len(coo_list) else '',
                        n_weight=n_weight_list[i] if i < len(n_weight_list) else 0,
                        g_weight=g_weight_list[i] if i < len(g_weight_list) else 0,
                        cbm=cbm_list[i] if i < len(cbm_list) else 0,
                        p_date=p_date_list[i] if i < len(p_date_list) and p_date_list[i] else None,
                        e_date=e_date_list[i] if i < len(e_date_list) and e_date_list[i] else None,
                        color=color_list[i] if i < len(color_list) else '',
                        size=size_list[i] if i < len(size_list) else '',
                        barcode=barcode_list[i] if i < len(barcode_list) else '',
                        rate=rate_list[i] if i < len(rate_list) else 0,
                        amount=amount_list[i] if i < len(amount_list) else 0,
                        ed_cntr=ed_cntr_list[i] if i < len(ed_cntr_list) else '',
                        ed=ed_list[i] if i < len(ed_list) else '',
                        ctnr=ctnr_list[i] if i < len(ctnr_list) else '',
                    )
            
            messages.success(request, f'Dispatch Note {dispatch_note.gdn_number} updated successfully!')
            return redirect('dispatchnote:dispatch_detail', pk=dispatch_note.pk)
    else:
        form = DispatchNoteForm(instance=dispatch_note)
    
    context = {
        'form': form,
        'dispatch_note': dispatch_note,
        'title': 'Edit Dispatch Note',
        'action': 'Update'
    }
    
    return render(request, 'dispatchnote/dispatch_form.html', context)

@login_required
def dispatch_detail(request, pk):
    """View dispatch note details"""
    dispatch_note = get_object_or_404(DispatchNote, pk=pk)
    
    context = {
        'dispatch_note': dispatch_note,
    }
    
    return render(request, 'dispatchnote/dispatch_detail.html', context)

@login_required
def dispatch_delete(request, pk):
    """Delete a dispatch note"""
    dispatch_note = get_object_or_404(DispatchNote, pk=pk)
    
    if request.method == 'POST':
        gdn_number = dispatch_note.gdn_number
        dispatch_note.delete()
        
        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Dispatch Note {gdn_number} deleted successfully!'
            })
        
        messages.success(request, f'Dispatch Note {gdn_number} deleted successfully!')
        return redirect('dispatchnote:dispatch_list')
    
    context = {
        'dispatch_note': dispatch_note,
    }
    
    return render(request, 'dispatchnote/dispatch_confirm_delete.html', context)

@login_required
def dispatch_item_add(request, dispatch_pk):
    """Add an item to a dispatch note"""
    dispatch_note = get_object_or_404(DispatchNote, pk=dispatch_pk)
    
    if request.method == 'POST':
        form = DispatchItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.dispatch_note = dispatch_note
            item.save()
            
            messages.success(request, f'Item "{item.item.item_name}" added successfully.')
            return redirect('dispatchnote:dispatch_detail', pk=dispatch_pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = DispatchItemForm()
    
    context = {
        'form': form,
        'dispatch_note': dispatch_note,
        'title': 'Add Item to Dispatch Note',
    }
    return render(request, 'dispatchnote/dispatch_item_form.html', context)

@login_required
def dispatch_item_update(request, dispatch_pk, item_pk):
    """Update an item in a dispatch note"""
    dispatch_note = get_object_or_404(DispatchNote, pk=dispatch_pk)
    item = get_object_or_404(DispatchItem, pk=item_pk, dispatch_note=dispatch_note)
    
    if request.method == 'POST':
        form = DispatchItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f'Item "{item.item.item_name}" updated successfully.')
            return redirect('dispatchnote:dispatch_detail', pk=dispatch_pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = DispatchItemForm(instance=item)
    
    context = {
        'form': form,
        'dispatch_note': dispatch_note,
        'item': item,
        'title': 'Update Item in Dispatch Note',
    }
    return render(request, 'dispatchnote/dispatch_item_form.html', context)

@login_required
def dispatch_item_delete(request, dispatch_pk, item_pk):
    """Delete an item from a dispatch note"""
    dispatch_note = get_object_or_404(DispatchNote, pk=dispatch_pk)
    item = get_object_or_404(DispatchItem, pk=item_pk, dispatch_note=dispatch_note)
    
    if request.method == 'POST':
        item_name = item.item.item_name
        item.delete()
        messages.success(request, f'Item "{item_name}" removed successfully.')
        return redirect('dispatchnote:dispatch_detail', pk=dispatch_pk)
    
    context = {
        'dispatch_note': dispatch_note,
        'item': item,
    }
    return render(request, 'dispatchnote/dispatch_item_confirm_delete.html', context)

@login_required
@require_POST
def update_dispatch_status(request, pk):
    """Update dispatch note status via AJAX"""
    dispatch_note = get_object_or_404(DispatchNote, pk=pk)
    new_status = request.POST.get('status')
    
    if new_status in dict(DispatchNote.STATUS_CHOICES):
        dispatch_note.status = new_status
        dispatch_note.updated_by = request.user
        dispatch_note.save()
        
        return JsonResponse({
            'success': True,
            'status': new_status,
            'status_display': dispatch_note.get_status_display(),
            'message': f'Status updated to {dispatch_note.get_status_display()}'
        })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid status'
    })

@login_required
def dispatch_status_update(request, pk):
    """Update dispatch note status via AJAX"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        dispatch_note = get_object_or_404(DispatchNote, pk=pk)
        new_status = request.POST.get('status')
        
        if new_status in dict(DispatchNote.STATUS_CHOICES):
            dispatch_note.status = new_status
            dispatch_note.updated_by = request.user
            dispatch_note.save()
            
            return JsonResponse({
                'success': True,
                'status': new_status,
                'status_display': dict(DispatchNote.STATUS_CHOICES)[new_status]
            })
        
        return JsonResponse({'success': False, 'error': 'Invalid status'})
    
    return HttpResponseForbidden()

# API Views for AJAX requests
@login_required
def api_delivery_orders_by_customer(request, customer_id):
    """API endpoint to get delivery orders for a specific customer"""
    try:
        customer = get_object_or_404(Customer, pk=customer_id)
        delivery_orders = DeliveryOrder.objects.filter(
            customer=customer,
            status__in=['draft', 'pending', 'in_progress', 'shipped']
        ).values('id', 'do_number', 'status')
        
        return JsonResponse({
            'success': True,
            'delivery_orders': list(delivery_orders)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def api_delivery_order_items(request, delivery_order_id):
    """API endpoint to get delivery order items for auto-population"""
    try:
        delivery_order = get_object_or_404(DeliveryOrder, pk=delivery_order_id)
        items = []
        
        # Access delivery order items through the related name
        for do_item in delivery_order.items.all():
            item_obj = do_item.item if do_item.item else None
            item_data = {
                'grn_no': delivery_order.grn.grn_number if delivery_order.grn else '',
                'item_code': item_obj.item_code if item_obj else '',
                'item_name': item_obj.item_name if item_obj else '',
                'hs_code': item_obj.hs_code if item_obj and item_obj.hs_code else '',
                'unit': item_obj.unit_of_measure if item_obj else '',
                'quantity': float(do_item.requested_qty) if do_item.requested_qty else 0.00,
                'coo': item_obj.country_of_origin if item_obj and item_obj.country_of_origin else '',
                'n_weight': float(item_obj.net_weight) if item_obj and item_obj.net_weight else 0.00,
                'g_weight': float(item_obj.gross_weight) if item_obj and item_obj.gross_weight else 0.00,
                'cbm': float(item_obj.cbm) if item_obj and item_obj.cbm else 0.00,
                'p_date': do_item.production_date.isoformat() if do_item.production_date else '',
                'e_date': do_item.expiry_date.isoformat() if do_item.expiry_date else '',
                'color': item_obj.color if item_obj else '',
                'size': item_obj.size if item_obj else '',
                'barcode': item_obj.barcode if item_obj else '',
                'rate': float(do_item.unit_price) if do_item.unit_price else 0.00,
                'amount': float(do_item.total_price) if do_item.total_price else 0.00,
                'ed_cntr': '',  # ED Container
                'ed': '',  # ED (Export Declaration)
                'ctnr': '',  # CTNR (Container)
            }
            items.append(item_data)
        
        delivery_order_data = {
            'delivery_contact': delivery_order.delivery_contact or '',
            'delivery_address': delivery_order.delivery_address or '',
            'facility': delivery_order.facility.id if delivery_order.facility else '',
        }
        
        print(f"Debug - Delivery Order {delivery_order.do_number} facility info:")
        print(f"  - Facility object: {delivery_order.facility}")
        print(f"  - Facility name: {delivery_order.facility.facility_name if delivery_order.facility else 'None'}")
        print(f"  - Facility data being sent: {delivery_order_data['facility']}")
        
        return JsonResponse({
            'success': True,
            'items': items,
            'delivery_order': delivery_order_data
        })
    except Exception as e:
        print(f"Error in api_delivery_order_items: {str(e)}")  # Debug logging
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def dispatch_print(request, pk):
    """Print dispatch note as PDF"""
    dispatch_note = get_object_or_404(DispatchNote, pk=pk)
    
    # Get company data (assuming there's one active company)
    try:
        from company.company_model import Company
        company = Company.objects.filter(is_active=True).first()
    except:
        company = None
    
    context = {
        'dispatch_note': dispatch_note,
        'company': company,
    }
    
    return render(request, 'dispatchnote/print_dispatch.html', context)
