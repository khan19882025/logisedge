from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from datetime import date
import json
from .models import LGP, LGPItem, LGPDispatch, LGPDispatchItem, PackageType
from django.db.models import Sum
from .forms import LGPForm, LGPItemFormSet, LGPDispatchForm, LGPSearchForm
from customer.models import Customer


@login_required
def lgp_list(request):
    """List available LGPs (excluding dispatched) with search and filtering"""
    from multi_currency.models import CurrencySettings
    
    form = LGPSearchForm(request.GET or None)
    # Filter out dispatched LGPs - only show available ones
    lgps = LGP.objects.select_related('customer', 'warehouse', 'created_by').exclude(status='dispatched').order_by('-created_at')
    
    # Apply filters
    if form.is_valid():
        search = form.cleaned_data.get('search')
        status = form.cleaned_data.get('status')
        customer = form.cleaned_data.get('customer')
        warehouse = form.cleaned_data.get('warehouse')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        
        if search:
            lgps = lgps.filter(
                Q(lgp_number__icontains=search) |
                Q(customer__customer_name__icontains=search) |
                Q(dpw_ref_no__icontains=search) |
                Q(items__good_description__icontains=search)
            ).distinct()
        
        if status:
            lgps = lgps.filter(status=status)
        
        if customer:
            lgps = lgps.filter(customer=customer)
        
        if warehouse:
            lgps = lgps.filter(warehouse=warehouse)
        
        if date_from:
            lgps = lgps.filter(document_date__gte=date_from)
        
        if date_to:
            lgps = lgps.filter(document_date__lte=date_to)
    
    # Calculate remaining quantities for each LGP item
    lgps_with_remaining = []
    for lgp in lgps:
        lgp_items_with_remaining = []
        for item in lgp.items.all().order_by('line_number'):
            # Calculate dispatched quantity for this item
            dispatched_qty = (
                LGPDispatchItem.objects.filter(lgp_item=item)
                .aggregate(total=Sum('quantity'))['total'] or 0
            )
            
            # Calculate remaining quantity
            remaining_qty = float(item.quantity) - float(dispatched_qty)
            
            # Only include items with remaining quantity > 0
            if remaining_qty > 0:
                # Add remaining quantity as an attribute to the item
                item.remaining_quantity = remaining_qty
                item.dispatched_quantity = dispatched_qty
                lgp_items_with_remaining.append(item)
        
        # Only include LGPs that have items with remaining quantities
        if lgp_items_with_remaining:
            lgp.items_with_remaining = lgp_items_with_remaining
            lgps_with_remaining.append(lgp)
    
    # Pagination
    paginator = Paginator(lgps_with_remaining, 25)  # Show 25 LGPs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get default currency
    currency_settings = CurrencySettings.objects.first()
    default_currency = currency_settings.default_currency if currency_settings else None
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'total_count': len(lgps_with_remaining),
        'default_currency': default_currency,
    }
    
    return render(request, 'lgp/lgp_list.html', context)


@login_required
def lgp_detail(request, pk):
    """View LGP details"""
    from multi_currency.models import CurrencySettings
    
    lgp = get_object_or_404(LGP.objects.select_related('customer', 'warehouse', 'created_by'), pk=pk)
    items = lgp.items.all().order_by('line_number')
    
    # Get default currency
    currency_settings = CurrencySettings.objects.first()
    default_currency = currency_settings.default_currency if currency_settings else None
    
    context = {
        'lgp': lgp,
        'items': items,
        'default_currency': default_currency,
    }
    
    return render(request, 'lgp/lgp_detail.html', context)


@login_required
def lgp_create(request):
    """Create new LGP"""
    from multi_currency.models import CurrencySettings
    
    print(f"=== LGP CREATE VIEW ACCESSED ===")
    print(f"Request method: {request.method}")
    print(f"User: {request.user}")
    print(f"User authenticated: {request.user.is_authenticated}")
    
    if request.method == 'POST':
        print(f"POST data received: {dict(request.POST)}")
        form = LGPForm(request.POST)
        formset = LGPItemFormSet(request.POST)
        
        print(f"Form is valid: {form.is_valid()}")
        print(f"Formset is valid: {formset.is_valid()}")
        
        if not form.is_valid():
            print(f"Form errors: {form.errors}")
        if not formset.is_valid():
            print(f"Formset errors: {formset.errors}")
            print(f"Formset non-form errors: {formset.non_form_errors()}")
            print(f"Formset total forms: {formset.total_form_count()}")
            print(f"Formset initial forms: {formset.initial_form_count()}")
            print(f"Formset management form data: {formset.management_form.cleaned_data if formset.management_form.is_valid() else 'Invalid management form'}")
            for i, form in enumerate(formset):
                print(f"Form {i}: valid={form.is_valid()}, errors={form.errors}, data={form.data if hasattr(form, 'data') else 'No data'}")
                if hasattr(form, 'cleaned_data'):
                    print(f"Form {i} cleaned_data: {form.cleaned_data}")
        
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    lgp = form.save(commit=False)
                    # Handle case where user might not be authenticated during testing
                    if request.user.is_authenticated:
                        lgp.created_by = request.user
                    else:
                        # For testing purposes, use a default user or handle appropriately
                        from django.contrib.auth.models import User
                        lgp.created_by = User.objects.filter(is_superuser=True).first()
                    lgp.save()
                    print(f"LGP saved successfully: {lgp.lgp_number}")
                    
                    formset.instance = lgp
                    formset.save()
                    print(f"Formset saved successfully")
                    
                    messages.success(request, f'LGP {lgp.lgp_number} created successfully!')
                    return redirect('lgp:lgp_list')
            except Exception as e:
                print(f"Exception during save: {str(e)}")
                messages.error(request, f'Error creating LGP: {str(e)}')
        else:
            print("Form validation failed")
            messages.error(request, 'Please correct the errors below.')
    else:
        print("GET request - displaying form")
        form = LGPForm()
        formset = LGPItemFormSet()
    
    # Get default currency
    currency_settings = CurrencySettings.objects.first()
    default_currency = currency_settings.default_currency if currency_settings else None
    
    context = {
        'form': form,
        'formset': formset,
        'title': 'Create LGP',
        'package_types': PackageType.objects.all(),
        'default_currency': default_currency,
    }
    
    print(f"Rendering template with context")
    return render(request, 'lgp/lgp_form.html', context)


@login_required
def lgp_update(request, pk):
    """Update existing LGP"""
    from multi_currency.models import CurrencySettings
    
    lgp = get_object_or_404(LGP, pk=pk)
    
    # Check if LGP can be edited
    if lgp.status in ['dispatched', 'cancelled']:
        messages.error(request, 'Cannot edit LGP that has been dispatched or cancelled.')
        return redirect('lgp:lgp_detail', pk=lgp.pk)
    
    if request.method == 'POST':
        form = LGPForm(request.POST, instance=lgp)
        formset = LGPItemFormSet(request.POST, instance=lgp)
        
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    lgp = form.save(commit=False)
                    lgp.updated_at = timezone.now()
                    lgp.save()
                    
                    formset.save()
                    
                    messages.success(request, f'LGP {lgp.lgp_number} updated successfully!')
                    return redirect('lgp:lgp_detail', pk=lgp.pk)
            except Exception as e:
                messages.error(request, f'Error updating LGP: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = LGPForm(instance=lgp)
        formset = LGPItemFormSet(instance=lgp)
    
    # Get default currency
    currency_settings = CurrencySettings.objects.first()
    default_currency = currency_settings.default_currency if currency_settings else None
    
    context = {
        'form': form,
        'formset': formset,
        'lgp': lgp,
        'title': f'Edit LGP {lgp.lgp_number}',
        'package_types': PackageType.objects.all(),
        'default_currency': default_currency,
    }
    
    return render(request, 'lgp/lgp_form.html', context)


@login_required
def lgp_dispatch(request, pk):
    """Dispatch LGP"""
    from multi_currency.models import CurrencySettings
    
    lgp = get_object_or_404(LGP, pk=pk)
    
    # Check if LGP can be dispatched
    if lgp.status != 'draft':
        messages.error(request, 'Only draft LGPs can be dispatched.')
        return redirect('lgp:lgp_detail', pk=lgp.pk)
    
    if not lgp.items.exists():
        messages.error(request, 'Cannot dispatch LGP without items.')
        return redirect('lgp:lgp_detail', pk=lgp.pk)
    
    if request.method == 'POST':
        form = LGPDispatchForm(request.POST, instance=lgp)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    lgp = form.save(commit=False)
                    lgp.status = 'dispatched'
                    lgp.dispatched_at = timezone.now()
                    lgp.dispatched_by = request.user
                    lgp.save()
                    
                    messages.success(request, f'LGP {lgp.lgp_number} dispatched successfully!')
                    return redirect('lgp:lgp_detail', pk=lgp.pk)
            except Exception as e:
                messages.error(request, f'Error dispatching LGP: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = LGPDispatchForm(instance=lgp)
    
    # Get default currency
    currency_settings = CurrencySettings.objects.first()
    default_currency = currency_settings.default_currency if currency_settings else None
    
    context = {
        'form': form,
        'lgp': lgp,
        'title': f'Dispatch LGP {lgp.lgp_number}',
        'today': date.today(),
        'default_currency': default_currency,
    }
    
    return render(request, 'lgp/lgp_dispatch.html', context)


@login_required
def lgp_dispatch_blank(request):
    """Open dispatch page without a preselected LGP."""
    form = LGPDispatchForm()
    selected_customer_id = request.GET.get('customer')
    # Include customers with at least one draft LGP; per-item availability is computed below
    customers = Customer.objects.filter(
        is_active=True,
        lgps__status='draft'
    ).order_by('customer_name').distinct()
    available_lgps = []
    if selected_customer_id:
        try:
            base_lgps = (
                LGP.objects.select_related('customer', 'warehouse')
                .filter(customer_id=selected_customer_id, status='draft')
                .order_by('-created_at')
                .distinct()
            )
            available_lgps = list(base_lgps)
        except Exception:
            available_lgps = []

    # Build per-item availability with remaining quantities
    available_items = []
    if selected_customer_id and available_lgps:
        for lgp in available_lgps:
            for item in lgp.items.all().order_by('line_number'):
                dispatched_qty = (
                    LGPDispatchItem.objects.filter(lgp_item=item)
                    .aggregate(total=Sum('quantity'))['total'] or 0
                )
                try:
                    remaining_qty = float(item.quantity) - float(dispatched_qty)
                except Exception:
                    remaining_qty = 0
                if remaining_qty > 0:
                    # Compute per-unit weight/value to scale with quantity edits
                    base_qty = float(item.quantity) if float(item.quantity) != 0 else 1.0
                    weight_per_unit = float(item.weight) / base_qty
                    value_per_unit = float(item.value) / base_qty
                    default_weight = remaining_qty * weight_per_unit
                    default_value = remaining_qty * value_per_unit
                    available_items.append({
                        'lgp_id': lgp.id,
                        'lgp_number': lgp.lgp_number,
                        'dpw_ref_no': lgp.dpw_ref_no,
                        'item_id': item.id,
                        'line_number': item.line_number,
                        'hs_code': item.hs_code,
                        'good_description': item.good_description,
                        'package_type': item.get_package_type_display,
                        'remaining_qty': remaining_qty,
                        'default_weight': default_weight,
                        'default_value': default_value,
                    })

    # Get default currency
    currency_settings = CurrencySettings.objects.first()
    default_currency = currency_settings.default_currency if currency_settings else None
    
    context = {
        'form': form,
        'lgp': None,
        'title': 'Dispatch LGP',
        'customers': customers,
        'selected_customer_id': int(selected_customer_id) if selected_customer_id else None,
        'available_lgps': available_lgps,
        'today': date.today(),
        'available_items': available_items,
        'default_currency': default_currency,
    }
    return render(request, 'lgp/lgp_dispatch.html', context)


@login_required
def lgp_dispatch_save(request):
    """Save a new dispatch composed of selected LGP items (expects JSON)."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
        customer_id = data.get('customer')
        dispatch_date = data.get('dispatch_date')
        note = data.get('note', '')
        driver_name = data.get('driver_name', '')
        vehicle_no = data.get('vehicle_no', '')
        mobile_no = data.get('mobile_no', '')
        items = data.get('items', [])

        # Fallbacks: infer customer/date from server if omitted
        if (not customer_id) and items:
            first_item_lgp_id = (items[0] or {}).get('lgp_id')
            if first_item_lgp_id:
                try:
                    customer_id = LGP.objects.values_list('customer_id', flat=True).get(pk=first_item_lgp_id)
                except Exception:
                    customer_id = None
        if not dispatch_date:
            dispatch_date = date.today().isoformat()
        if not items:
            return JsonResponse({'success': False, 'error': 'Required fields missing: items'}, status=400)
        if not customer_id:
            return JsonResponse({'success': False, 'error': 'Required fields missing: customer'}, status=400)

        customer = get_object_or_404(Customer, pk=customer_id)
        dispatch = LGPDispatch.objects.create(
            customer=customer,
            dispatch_date=dispatch_date,
            note=note,
            driver_name=driver_name,
            vehicle_no=vehicle_no,
            mobile_no=mobile_no,
            created_by=request.user,
        )

        # Create items and track affected LGPs
        affected_lgps = set()
        for idx, it in enumerate(items, start=1):
            lgp_id = it.get('lgp_id')
            lgp = get_object_or_404(LGP, pk=lgp_id) if lgp_id else None
            lgp_item = LGPItem.objects.filter(pk=it.get('item_id')).first()
            LGPDispatchItem.objects.create(
                dispatch=dispatch,
                lgp=lgp or (lgp_item.lgp if lgp_item else None),
                lgp_item=lgp_item,
                line_number=it.get('line') or (lgp_item.line_number if lgp_item else idx),
                hs_code=it.get('hs') or (lgp_item.hs_code if lgp_item else ''),
                good_description=it.get('description') or (lgp_item.good_description if lgp_item else ''),
                package_type=it.get('pkg') or (lgp_item.get_package_type_display() if lgp_item else ''),
                quantity=it.get('qty') or (lgp_item.quantity if lgp_item else 0),
                weight=it.get('weight') or (lgp_item.weight if lgp_item else 0),
                value=it.get('value') or (lgp_item.value if lgp_item else 0),
            )
            if lgp:
                affected_lgps.add(lgp)
        
        # Update LGP status to 'dispatched' for fully dispatched LGPs
        dispatched_lgp_ids = []
        for lgp in affected_lgps:
            # Check if all items in this LGP are fully dispatched
            all_items_dispatched = True
            for item in lgp.items.all():
                dispatched_qty = (
                    LGPDispatchItem.objects.filter(lgp_item=item)
                    .aggregate(total=Sum('quantity'))['total'] or 0
                )
                if float(dispatched_qty) < float(item.quantity):
                    all_items_dispatched = False
                    break
            
            if all_items_dispatched:
                lgp.status = 'dispatched'
                lgp.dispatch_date = timezone.now()
                lgp.dispatched_by = request.user
                lgp.save()
                dispatched_lgp_ids.append(lgp.id)

        return JsonResponse({
            'success': True, 
            'redirect': True, 
            'url': request.build_absolute_uri(f"/lgp/dispatch/{dispatch.pk}/"),
            'dispatched_lgp_ids': dispatched_lgp_ids
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def lgp_dispatch_list(request):
    """List saved dispatches."""
    dispatches = LGPDispatch.objects.select_related('customer', 'created_by').all()
    return render(request, 'lgp/lgp_dispatch_list.html', {'dispatches': dispatches})


@login_required
def lgp_dispatch_detail(request, pk):
    """View a saved dispatch with its items."""
    from multi_currency.models import CurrencySettings
    
    dispatch = get_object_or_404(LGPDispatch.objects.select_related('customer', 'created_by'), pk=pk)
    items = dispatch.items.all()
    
    # Get default currency
    currency_settings = CurrencySettings.objects.first()
    default_currency = currency_settings.default_currency if currency_settings else None
    
    return render(request, 'lgp/lgp_dispatch_detail.html', {
        'dispatch': dispatch, 
        'items': items,
        'default_currency': default_currency,
    })


@login_required
def lgp_dispatch_delete(request, pk):
    if request.method != 'POST':
        return redirect('lgp:lgp_dispatch_list')
    dispatch = get_object_or_404(LGPDispatch, pk=pk)
    dispatch.delete()
    messages.success(request, f'Dispatch {pk} deleted successfully.')
    return redirect('lgp:lgp_dispatch_list')


@login_required
def lgp_cancel(request, pk):
    """Cancel LGP"""
    lgp = get_object_or_404(LGP, pk=pk)
    
    # Check if LGP can be cancelled
    if lgp.status == 'dispatched':
        messages.error(request, 'Cannot cancel dispatched LGP.')
        return redirect('lgp:lgp_detail', pk=lgp.pk)
    
    if request.method == 'POST':
        try:
            lgp.status = 'cancelled'
            lgp.updated_at = timezone.now()
            lgp.save()
            
            messages.success(request, f'LGP {lgp.lgp_number} cancelled successfully!')
            return redirect('lgp:lgp_detail', pk=lgp.pk)
        except Exception as e:
            messages.error(request, f'Error cancelling LGP: {str(e)}')
    
    return redirect('lgp:lgp_detail', pk=lgp.pk)


@login_required
def lgp_print(request, pk):
    """Print LGP"""
    from multi_currency.models import CurrencySettings
    
    lgp = get_object_or_404(LGP.objects.select_related('customer', 'warehouse', 'created_by'), pk=pk)
    items = lgp.items.all().order_by('line_number')
    
    # Get default currency
    currency_settings = CurrencySettings.objects.first()
    default_currency = currency_settings.default_currency if currency_settings else None
    
    context = {
        'lgp': lgp,
        'items': items,
        'default_currency': default_currency,
    }
    
    return render(request, 'lgp/lgp_print.html', context)


@login_required
def lgp_ajax_search(request):
    """AJAX search for LGPs"""
    query = request.GET.get('q', '')
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    lgps = LGP.objects.filter(
        Q(lgp_number__icontains=query) |
        Q(customer__customer_name__icontains=query) |
        Q(dpw_ref_no__icontains=query)
    ).select_related('customer')[:10]
    
    results = []
    for lgp in lgps:
        results.append({
            'id': lgp.id,
            'text': f'{lgp.lgp_number} - {lgp.customer.customer_name}',
            'lgp_number': lgp.lgp_number,
            'customer': lgp.customer.customer_name,
            'status': lgp.get_status_display()
        })
    
    return JsonResponse({'results': results})


@login_required
def lgp_details(request, pk):
    """Return LGP summary details for the dispatch modal (JSON)."""
    lgp = get_object_or_404(LGP.objects.select_related('customer', 'warehouse'), pk=pk)
    items = lgp.items.all()

    data = {
        'id': lgp.id,
        'lgp_number': lgp.lgp_number,
        'customer': lgp.customer.customer_name,
        'dpw_ref_no': lgp.dpw_ref_no,
        'warehouse': str(lgp.warehouse),
        'total_items': items.count(),
        'total_weight': str(sum((item.weight or 0) for item in items)),
        'total_value': str(sum((item.value or 0) for item in items)),
        'status': lgp.get_status_display(),
    }

    return JsonResponse(data)
