from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from django.views.decorators.http import require_POST
from datetime import datetime, timedelta
from decimal import Decimal
import json

from .models import Charge
from .forms import ChargeSearchForm, ChargeForm, BulkChargeForm
from customer.models import Customer
from items.models import Item

@login_required
def charge_list(request):
    """Display list of charges with search and filtering"""
    search_form = ChargeSearchForm(request.GET or None)
    
    # Base queryset
    charges = Charge.objects.select_related('customer', 'item').all()
    
    # Apply search filters
    if search_form.is_valid():
        if search_form.cleaned_data.get('customer'):
            charges = charges.filter(customer=search_form.cleaned_data['customer'])
        
        if search_form.cleaned_data.get('item'):
            charges = charges.filter(item=search_form.cleaned_data['item'])
        
        if search_form.cleaned_data.get('charge_type'):
            charges = charges.filter(charge_type=search_form.cleaned_data['charge_type'])
        
        if search_form.cleaned_data.get('status'):
            charges = charges.filter(status=search_form.cleaned_data['status'])
        
        if search_form.cleaned_data.get('date_from'):
            charges = charges.filter(effective_date__gte=search_form.cleaned_data['date_from'])
        
        if search_form.cleaned_data.get('date_to'):
            charges = charges.filter(effective_date__lte=search_form.cleaned_data['date_to'])
        
        if search_form.cleaned_data.get('rate_min'):
            charges = charges.filter(rate__gte=search_form.cleaned_data['rate_min'])
        
        if search_form.cleaned_data.get('rate_max'):
            charges = charges.filter(rate__lte=search_form.cleaned_data['rate_max'])
    
    # Order by effective date (newest first)
    charges = charges.order_by('-effective_date', 'customer__customer_name', 'item__item_name')
    
    # Pagination
    paginator = Paginator(charges, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_charges = charges.count()
    active_charges = charges.filter(status='active').count()
    total_amount = charges.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    avg_rate = charges.aggregate(avg=Avg('rate'))['avg'] or Decimal('0.00')
    
    # Export functionality
    export_format = request.GET.get('export')
    if export_format in ['csv', 'excel']:
        return export_charges(charges, export_format)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_charges': total_charges,
        'active_charges': active_charges,
        'total_amount': total_amount,
        'avg_rate': avg_rate,
    }
    
    return render(request, 'charges/charge_list.html', context)

@login_required
def charge_create(request):
    """Create a new charge"""
    if request.method == 'POST':
        form = ChargeForm(request.POST)
        if form.is_valid():
            charge = form.save(commit=False)
            charge.created_by = request.user
            charge.save()
            messages.success(request, 'Charge created successfully.')
            return redirect('charges:charge_list')
    else:
        form = ChargeForm()
    
    context = {
        'form': form,
        'title': 'Create New Charge',
    }
    
    return render(request, 'charges/charge_form.html', context)

@login_required
def charge_edit(request, pk):
    """Edit an existing charge"""
    charge = get_object_or_404(Charge, pk=pk)
    
    if request.method == 'POST':
        form = ChargeForm(request.POST, instance=charge)
        if form.is_valid():
            charge = form.save(commit=False)
            charge.updated_by = request.user
            charge.save()
            messages.success(request, 'Charge updated successfully.')
            return redirect('charges:charge_list')
    else:
        form = ChargeForm(instance=charge)
    
    context = {
        'form': form,
        'charge': charge,
        'title': 'Edit Charge',
    }
    
    return render(request, 'charges/charge_form.html', context)

@login_required
def charge_detail(request, pk):
    """Display detailed view of a charge"""
    charge = get_object_or_404(Charge, pk=pk)
    
    context = {
        'charge': charge,
    }
    
    return render(request, 'charges/charge_detail.html', context)

@login_required
@require_POST
def charge_delete(request, pk):
    """Delete a charge"""
    charge = get_object_or_404(Charge, pk=pk)
    
    try:
        charge.delete()
        messages.success(request, 'Charge deleted successfully.')
    except Exception as e:
        messages.error(request, f'Error deleting charge: {str(e)}')
    
    return redirect('charges:charge_list')

@login_required
@require_POST
def charge_toggle_status(request, pk):
    """Toggle charge status between active and inactive"""
    charge = get_object_or_404(Charge, pk=pk)
    
    if charge.status == 'active':
        charge.status = 'inactive'
        message = 'Charge deactivated successfully.'
    else:
        charge.status = 'active'
        message = 'Charge activated successfully.'
    
    charge.updated_by = request.user
    charge.save()
    messages.success(request, message)
    
    return redirect('charges:charge_list')

@login_required
@require_POST
def bulk_action(request):
    """Perform bulk actions on charges"""
    form = BulkChargeForm(request.POST)
    
    if form.is_valid():
        action = form.cleaned_data['action']
        charge_ids = form.cleaned_data['charge_ids']
        
        if charge_ids:
            charge_ids = [int(id.strip()) for id in charge_ids.split(',') if id.strip().isdigit()]
            charges = Charge.objects.filter(id__in=charge_ids)
            
            if action == 'activate':
                count = charges.update(status='active', updated_by=request.user)
                messages.success(request, f'{count} charge(s) activated successfully.')
            elif action == 'deactivate':
                count = charges.update(status='inactive', updated_by=request.user)
                messages.success(request, f'{count} charge(s) deactivated successfully.')
            elif action == 'delete':
                count = charges.count()
                charges.delete()
                messages.success(request, f'{count} charge(s) deleted successfully.')
        else:
            messages.warning(request, 'No charges selected for bulk action.')
    else:
        messages.error(request, 'Invalid bulk action request.')
    
    return redirect('charges:charge_list')

def export_charges(charges, format_type):
    """Export charges to CSV or Excel"""
    import csv
    from io import StringIO
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="charges_export_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Customer', 'Item Code', 'Item Description', 'Charge Type', 
        'Rate', 'Amount', 'Effective Date', 'Status', 'Remarks', 'Created By', 'Created At'
    ])
    
    for charge in charges:
        writer.writerow([
            charge.customer.customer_name,
            charge.item.item_code,
            charge.item.item_name,
            charge.get_charge_type_display(),
            charge.rate,
            charge.amount,
            charge.effective_date,
            charge.get_status_display(),
            charge.remarks,
            charge.created_by.get_full_name() if charge.created_by else 'System',
            charge.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return response

@login_required
def ajax_get_charges(request):
    """AJAX endpoint to get charges for a customer and item"""
    customer_id = request.GET.get('customer_id')
    item_id = request.GET.get('item_id')
    
    if customer_id and item_id:
        charges = Charge.objects.filter(
            customer_id=customer_id,
            item_id=item_id,
            status='active'
        ).values('id', 'charge_type', 'rate', 'effective_date')
        
        return JsonResponse({'charges': list(charges)})
    
    return JsonResponse({'charges': []})
