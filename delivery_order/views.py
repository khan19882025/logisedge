from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.http import JsonResponse, HttpResponse
from django.forms import formset_factory
from django.utils import timezone
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import os
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from .models import DeliveryOrder, DeliveryOrderItem
from .forms import DeliveryOrderForm, DeliveryOrderItemForm, DeliveryOrderItemFormSet
from datetime import datetime

@login_required
def delivery_order_list(request):
    """Display list of delivery orders with search and filtering"""
    delivery_orders = DeliveryOrder.objects.select_related(
        'customer', 'facility', 'assigned_to', 'created_by'
    ).prefetch_related('items')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        delivery_orders = delivery_orders.filter(
            Q(do_number__icontains=search_query) |
            Q(customer__customer_name__icontains=search_query) |
            Q(customer_ref__icontains=search_query) |
            Q(delivery_contact__icontains=search_query) |
            Q(tracking_number__icontains=search_query)
        )
    
    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        delivery_orders = delivery_orders.filter(status=status_filter)
    
    # Priority filter
    priority_filter = request.GET.get('priority', '')
    if priority_filter:
        delivery_orders = delivery_orders.filter(priority=priority_filter)
    
    # Pagination
    paginator = Paginator(delivery_orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'delivery_orders': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'status_choices': DeliveryOrder.STATUS_CHOICES,
        'priority_choices': DeliveryOrder.PRIORITY_CHOICES,
    }
    
    return render(request, 'delivery_order/delivery_order_list.html', context)

@login_required
def delivery_order_create(request):
    """Create a new delivery order"""
    if request.method == 'POST':
        form = DeliveryOrderForm(request.POST)
        if form.is_valid():
            delivery_order = form.save(commit=False)
            delivery_order.created_by = request.user
            
            # Get the selected GRN from the form
            grn_id = request.POST.get('grn')
            if grn_id:
                from grn.models import GRN
                try:
                    delivery_order.grn = GRN.objects.get(id=grn_id)
                except GRN.DoesNotExist:
                    pass
            
            delivery_order.save()
            print(f"Generated DO number: {delivery_order.do_number}")
            
            # Handle selected items data
            selected_items_data = request.POST.get('selected_items_data', '')
            if selected_items_data:
                import json
                try:
                    selected_items = json.loads(selected_items_data)
                    for item_data in selected_items:
                        # Get the item from GRN item ID
                        from grn.models import GRNItem
                        grn_item = GRNItem.objects.get(id=item_data.get('id'))
                        
                        # Create delivery order item with all GRN item data
                        delivery_order_item = DeliveryOrderItem.objects.create(
                            delivery_order=delivery_order,
                            item=grn_item.item,
                            requested_qty=float(item_data.get('quantity', 0)),
                            unit_price=float(item_data.get('rate', 0)),
                            notes=item_data.get('notes', ''),
                            source_location_id=item_data.get('source_location_id'),
                        )
                        
                        # Store all GRN item details in notes for complete data preservation
                        additional_info = []
                        
                        # Store GRN number - always save it from the GRN item
                        if delivery_order.grn:
                            additional_info.append(f"GRN-No: {delivery_order.grn.grn_number}")
                        elif grn_item.grn:
                            additional_info.append(f"GRN-No: {grn_item.grn.grn_number}")
                        
                        # Store all GRN item details
                        if grn_item.hs_code:
                            additional_info.append(f"HS-Code: {grn_item.hs_code}")
                        if grn_item.coo:
                            additional_info.append(f"COO: {grn_item.coo}")
                        if grn_item.net_weight:
                            additional_info.append(f"N-weight: {grn_item.net_weight}")
                        if grn_item.gross_weight:
                            additional_info.append(f"G-weight: {grn_item.gross_weight}")
                        if grn_item.volume:
                            additional_info.append(f"Volume: {grn_item.volume}")
                        if grn_item.p_date:
                            additional_info.append(f"P-Date: {grn_item.p_date}")
                        if grn_item.expiry_date:
                            additional_info.append(f"E-Date: {grn_item.expiry_date}")
                        if grn_item.color:
                            additional_info.append(f"Color: {grn_item.color}")
                        if grn_item.size:
                            additional_info.append(f"Size: {grn_item.size}")
                        if grn_item.batch_number:
                            additional_info.append(f"Barcode: {grn_item.batch_number}")
                        if grn_item.ed:
                            additional_info.append(f"ED: {grn_item.ed}")
                        
                        # Also store any additional data from the form
                        if item_data.get('volume') and item_data.get('volume') != '-':
                            additional_info.append(f"Volume: {item_data.get('volume')}")
                        if item_data.get('p_date') and item_data.get('p_date') != '-':
                            additional_info.append(f"P-Date: {item_data.get('p_date')}")
                        if item_data.get('expiry_date') and item_data.get('expiry_date') != '-':
                            additional_info.append(f"E-Date: {item_data.get('expiry_date')}")
                        if item_data.get('color') and item_data.get('color') != '-':
                            additional_info.append(f"Color: {item_data.get('color')}")
                        if item_data.get('size') and item_data.get('size') != '-':
                            additional_info.append(f"Size: {item_data.get('size')}")
                        if item_data.get('barcode') and item_data.get('barcode') != '-':
                            additional_info.append(f"Barcode: {item_data.get('barcode')}")
                        if item_data.get('ed') and item_data.get('ed') != '-':
                            additional_info.append(f"ED: {item_data.get('ed')}")
                        
                        if additional_info:
                            delivery_order_item.notes = f"{delivery_order_item.notes}\n" + "\n".join(additional_info)
                            delivery_order_item.save()
                        
                except (json.JSONDecodeError, KeyError, GRNItem.DoesNotExist) as e:
                    messages.warning(request, f'Error processing selected items: {str(e)}')
            
            messages.success(request, f'Delivery Order {delivery_order.do_number} created successfully!')
            print(f"Redirecting to delivery order detail: {delivery_order.pk}")
            return redirect('delivery_order:delivery_order_detail', pk=delivery_order.pk)
        else:
            print("Form validation failed")
            print("Form errors:", form.errors)
            print("Form data received:", request.POST)
            print("Form field errors:")
            for field_name, errors in form.errors.items():
                print(f"  {field_name}: {errors}")
            messages.error(request, 'Please correct the errors below.')
    else:
        form = DeliveryOrderForm()
    
    context = {
        'form': form,
        'submit_text': 'Create Delivery Order',
        'page_title': 'Create New Delivery Order',
        'next_do_number': generate_next_do_number()
    }
    
    return render(request, 'delivery_order/delivery_order_form.html', context)

@login_required
def delivery_order_detail(request, pk):
    """Display delivery order details"""
    delivery_order = get_object_or_404(DeliveryOrder, pk=pk)
    
    # Get GRN items data for detailed display
    grn_items_data = []
    
    # First try to get data from related GRN
    if delivery_order.grn:
        from grn.models import GRNItem
        grn_items = GRNItem.objects.filter(grn=delivery_order.grn)
        for grn_item in grn_items:
            # Check if this GRN item is used in the delivery order
            do_items = delivery_order.items.filter(item=grn_item.item)
            if do_items.exists():
                do_item = do_items.first()
                grn_items_data.append({
                    'grn_number': delivery_order.grn.grn_number,
                    'item_code': grn_item.item_code or grn_item.item.item_code if grn_item.item else '',
                    'item_name': grn_item.item_name or grn_item.item.item_name if grn_item.item else '',
                    'hs_code': grn_item.hs_code or '',  # Use GRN item hs_code if available
                    'unit': grn_item.unit or grn_item.item.unit_of_measure if grn_item.item else '',
                    'quantity': do_item.requested_qty,
                    'coo': grn_item.coo or '',
                    'n_weight': grn_item.net_weight or 0,
                    'g_weight': grn_item.gross_weight or 0,
                    'volume': grn_item.volume or 0,
                    'p_date': grn_item.p_date,
                    'expiry_date': grn_item.expiry_date,
                    'color': grn_item.color or '',
                    'size': grn_item.size or '',
                    'barcode': grn_item.batch_number or '',
                    'rate': do_item.unit_price or 0,
                    'amount': do_item.total_price or 0,
                    'ed': grn_item.ed or '',
                })
    
    # If no GRN data found, try to extract from delivery order items notes
    if not grn_items_data and delivery_order.items.exists():
        for do_item in delivery_order.items.all():
            # Try to extract GRN number from notes or other fields
            grn_number = "N/A"
            if delivery_order.grn:
                grn_number = delivery_order.grn.grn_number
            
            # Extract additional info from notes
            notes = do_item.notes or ""
            additional_info = {}
            
            # Parse notes for additional information
            for line in notes.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    additional_info[key.strip()] = value.strip()
            
            # Extract GRN number from notes if not available from delivery order
            if grn_number == "N/A" and 'GRN-No' in additional_info:
                grn_number = additional_info['GRN-No']
            
            # Also try to get data from the original GRN item if available
            grn_item_data = {}
            if delivery_order.grn:
                try:
                    from grn.models import GRNItem
                    grn_item = GRNItem.objects.filter(grn=delivery_order.grn, item=do_item.item).first()
                    if grn_item:
                        grn_item_data = {
                            'coo': grn_item.coo or '',
                            'n_weight': grn_item.net_weight or 0,
                            'g_weight': grn_item.gross_weight or 0,
                            'volume': grn_item.volume or 0,
                            'p_date': grn_item.p_date,
                            'expiry_date': grn_item.expiry_date,
                            'color': grn_item.color or '',
                            'size': grn_item.size or '',
                            'barcode': grn_item.batch_number or '',
                            'ed': grn_item.ed or '',
                            'hs_code': grn_item.hs_code or '',
                        }
                except:
                    pass
            
            # Extract dates and convert to proper date objects
            p_date = None
            expiry_date = None
            if 'P-Date' in additional_info:
                try:
                    p_date = datetime.strptime(additional_info['P-Date'], '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    p_date = None
            if 'E-Date' in additional_info:
                try:
                    expiry_date = datetime.strptime(additional_info['E-Date'], '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    expiry_date = None
            
            grn_items_data.append({
                'grn_number': grn_number,
                'item_code': do_item.item.item_code if do_item.item else '',
                'item_name': do_item.item.item_name if do_item.item else '',
                'hs_code': grn_item_data.get('hs_code') or additional_info.get('HS-Code', ''),
                'unit': do_item.item.unit_of_measure if do_item.item else '',
                'quantity': do_item.requested_qty,
                'coo': grn_item_data.get('coo') or additional_info.get('COO', ''),
                'n_weight': grn_item_data.get('n_weight') or float(additional_info.get('N-weight', 0)) if additional_info.get('N-weight') else 0,
                'g_weight': grn_item_data.get('g_weight') or float(additional_info.get('G-weight', 0)) if additional_info.get('G-weight') else 0,
                'volume': grn_item_data.get('volume') or float(additional_info.get('Volume', 0)) if additional_info.get('Volume') else 0,
                'p_date': grn_item_data.get('p_date') or p_date,
                'expiry_date': grn_item_data.get('expiry_date') or expiry_date,
                'color': grn_item_data.get('color') or additional_info.get('Color', ''),
                'size': grn_item_data.get('size') or additional_info.get('Size', ''),
                'barcode': grn_item_data.get('barcode') or additional_info.get('Barcode', ''),
                'rate': do_item.unit_price or 0,
                'amount': do_item.total_price or 0,
                'ed': grn_item_data.get('ed') or additional_info.get('ED', ''),
            })
    
    # If still no GRN data found, try to extract from any delivery order items notes (even if GRN data was found)
    if not grn_items_data and delivery_order.items.exists():
        for do_item in delivery_order.items.all():
            # Extract data from notes as final fallback
            notes = do_item.notes or ""
            additional_info = {}
            
            # Parse notes for additional information
            for line in notes.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    additional_info[key.strip()] = value.strip()
            
            # Extract GRN number from notes
            grn_number = "N/A"
            if 'GRN-No' in additional_info:
                grn_number = additional_info['GRN-No']
            elif delivery_order.grn:
                grn_number = delivery_order.grn.grn_number
            
            # Extract dates and convert to proper date objects
            p_date = None
            expiry_date = None
            if 'P-Date' in additional_info:
                try:
                    p_date = datetime.strptime(additional_info['P-Date'], '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    p_date = None
            if 'E-Date' in additional_info:
                try:
                    expiry_date = datetime.strptime(additional_info['E-Date'], '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    expiry_date = None
            
            grn_items_data.append({
                'grn_number': grn_number,
                'item_code': do_item.item.item_code if do_item.item else '',
                'item_name': do_item.item.item_name if do_item.item else '',
                'hs_code': additional_info.get('HS-Code', ''),
                'unit': do_item.item.unit_of_measure if do_item.item else '',
                'quantity': do_item.requested_qty,
                'coo': additional_info.get('COO', ''),
                'n_weight': float(additional_info.get('N-weight', 0)) if additional_info.get('N-weight') else 0,
                'g_weight': float(additional_info.get('G-weight', 0)) if additional_info.get('G-weight') else 0,
                'volume': float(additional_info.get('Volume', 0)) if additional_info.get('Volume') else 0,
                'p_date': p_date,
                'expiry_date': expiry_date,
                'color': additional_info.get('Color', ''),
                'size': additional_info.get('Size', ''),
                'barcode': additional_info.get('Barcode', ''),
                'rate': do_item.unit_price or 0,
                'amount': do_item.total_price or 0,
                'ed': additional_info.get('ED', ''),
            })
    
    # Debug: Print the data being passed to template
    print(f"Delivery Order {delivery_order.do_number} - GRN Items Data: {len(grn_items_data)} items")
    for i, item in enumerate(grn_items_data):
        print(f"  Item {i+1}: {item}")
    
    context = {
        'delivery_order': delivery_order,
        'grn_items_data': grn_items_data,
    }
    
    return render(request, 'delivery_order/delivery_order_detail.html', context)

@login_required
def delivery_order_edit(request, pk):
    """Edit an existing delivery order"""
    delivery_order = get_object_or_404(DeliveryOrder, pk=pk)
    
    if request.method == 'POST':
        form = DeliveryOrderForm(request.POST, instance=delivery_order)
        
        if form.is_valid():
            delivery_order = form.save(commit=False)
            
            # Calculate totals from selected items
            selected_items_data = request.POST.get('selected_items_data', '')
            total_quantity = 0
            total_weight = 0
            total_volume = 0
            
            if selected_items_data:
                import json
                try:
                    selected_items = json.loads(selected_items_data)
                    for item_data in selected_items:
                        quantity = float(item_data.get('quantity', 0))
                        n_weight = float(item_data.get('n_weight', 0)) if item_data.get('n_weight') != '-' else 0
                        g_weight = float(item_data.get('g_weight', 0)) if item_data.get('g_weight') != '-' else 0
                        volume = float(item_data.get('volume', 0)) if item_data.get('volume') != '-' else 0
                        
                        total_quantity += quantity
                        total_weight += g_weight  # Use gross weight for total
                        total_volume += volume
                except (json.JSONDecodeError, ValueError) as e:
                    messages.warning(request, f'Error calculating totals: {str(e)}')
            
            # Set calculated totals
            delivery_order.total_quantity = total_quantity
            delivery_order.total_weight = total_weight
            delivery_order.total_volume = total_volume
            
            delivery_order.save()
            
            # Handle selected items data
            if selected_items_data:
                import json
                try:
                    # Clear existing items
                    delivery_order.items.all().delete()
                    
                    selected_items = json.loads(selected_items_data)
                    for item_data in selected_items:
                        # Get the item from GRN item ID
                        from grn.models import GRNItem
                        grn_item = GRNItem.objects.get(id=item_data.get('id'))
                        
                        # Create delivery order item
                        delivery_order_item = DeliveryOrderItem.objects.create(
                            delivery_order=delivery_order,
                            item=grn_item.item,
                            requested_qty=float(item_data.get('quantity', 0)),
                            unit_price=float(item_data.get('rate', 0)),
                            notes=item_data.get('notes', ''),
                            source_location_id=item_data.get('source_location_id'),
                        )
                        
                        # Store additional item details in notes if needed
                        additional_info = []
                        if item_data.get('volume') and item_data.get('volume') != '-':
                            additional_info.append(f"Volume: {item_data.get('volume')}")
                        if item_data.get('p_date') and item_data.get('p_date') != '-':
                            additional_info.append(f"P-Date: {item_data.get('p_date')}")
                        if item_data.get('expiry_date') and item_data.get('expiry_date') != '-':
                            additional_info.append(f"E-Date: {item_data.get('expiry_date')}")
                        if item_data.get('color') and item_data.get('color') != '-':
                            additional_info.append(f"Color: {item_data.get('color')}")
                        if item_data.get('size') and item_data.get('size') != '-':
                            additional_info.append(f"Size: {item_data.get('size')}")
                        if item_data.get('barcode') and item_data.get('barcode') != '-':
                            additional_info.append(f"Barcode: {item_data.get('barcode')}")
                        if item_data.get('ed') and item_data.get('ed') != '-':
                            additional_info.append(f"ED: {item_data.get('ed')}")
                        
                        if additional_info:
                            delivery_order_item.notes = f"{delivery_order_item.notes}\n" + "\n".join(additional_info)
                            delivery_order_item.save()
                        
                except (json.JSONDecodeError, KeyError, GRNItem.DoesNotExist) as e:
                    messages.warning(request, f'Error processing selected items: {str(e)}')
            
            messages.success(request, f'Delivery Order {delivery_order.do_number} updated successfully!')
            return redirect('delivery_order:delivery_order_detail', pk=delivery_order.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = DeliveryOrderForm(instance=delivery_order)
    
    context = {
        'form': form,
        'delivery_order': delivery_order,
        'submit_text': 'Update Delivery Order',
        'page_title': f'Edit Delivery Order {delivery_order.do_number}',
        'current_do_number': delivery_order.do_number
    }
    
    return render(request, 'delivery_order/delivery_order_form.html', context)

@login_required
def delivery_order_delete(request, pk):
    """Delete a delivery order"""
    delivery_order = get_object_or_404(DeliveryOrder, pk=pk)
    
    if request.method == 'POST':
        do_number = delivery_order.do_number
        delivery_order.delete()
        messages.success(request, f'Delivery Order {do_number} deleted successfully!')
        return redirect('delivery_order:delivery_order_list')
    
    context = {
        'delivery_order': delivery_order,
    }
    
    return render(request, 'delivery_order/delivery_order_confirm_delete.html', context)

@login_required
def delivery_order_status_update(request, pk):
    """Update delivery order status"""
    delivery_order = get_object_or_404(DeliveryOrder, pk=pk)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(DeliveryOrder.STATUS_CHOICES):
            delivery_order.status = new_status
            if new_status == 'delivered':
                delivery_order.actual_delivery_date = timezone.now().date()
            delivery_order.save()
            messages.success(request, f'Delivery Order status updated to {delivery_order.get_status_display()}')
        else:
            messages.error(request, 'Invalid status')
    
    return redirect('delivery_order:delivery_order_detail', pk=delivery_order.pk)

@login_required
def get_customer_info(request, customer_id):
    """AJAX endpoint to get customer information"""
    try:
        from customer.models import Customer
        customer = Customer.objects.get(id=customer_id)
        
        customer_data = {
            'customer_name': customer.customer_name,
            'customer_code': customer.customer_code,
            'billing_address': customer.billing_address,
            'shipping_address': customer.shipping_address,
            'phone': customer.phone,
            'email': customer.email,
        }
        
        return JsonResponse({
            'success': True,
            'customer': customer_data
        })
    except Customer.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Customer not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def get_grn_items(request, grn_id):
    """AJAX endpoint to get items from a specific GRN"""
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
def get_customer_items(request, customer_id):
    """AJAX endpoint to get available items for a customer from GRNs"""
    try:
        from grn.models import GRN, GRNItem
        from django.db.models import Sum, F
        
        # Get current delivery order ID if editing (from request parameters)
        current_do_id = request.GET.get('current_do_id')
        if current_do_id == 'None':
            current_do_id = None
        
        # Get all GRNs for the customer that have draft or received status
        grns = GRN.objects.filter(
            customer_id=customer_id,
            status__in=['draft', 'received']
        ).prefetch_related('items')
        
        items_data = []
        
        for grn in grns:
            # Get all items from this GRN
            grn_items = GRNItem.objects.filter(grn=grn).select_related('item')
            
            for grn_item in grn_items:
                # Calculate used quantity from existing delivery orders
                # Exclude the current delivery order if editing
                used_qty_query = DeliveryOrderItem.objects.filter(
                    item=grn_item.item,
                    delivery_order__customer_id=customer_id
                )
                
                if current_do_id:
                    # Exclude current delivery order from used quantity calculation
                    used_qty_query = used_qty_query.exclude(delivery_order_id=current_do_id)
                
                used_qty = used_qty_query.aggregate(
                    total_used=Sum('requested_qty')
                )['total_used'] or 0
                
                # Calculate available quantity
                available_qty = float(grn_item.received_qty or 0) - float(used_qty)
                
                if available_qty > 0:
                    # Calculate weights and amounts
                    n_weight = float(grn_item.net_weight or 0)
                    g_weight = float(grn_item.gross_weight or 0)
                    volume = float(grn_item.volume or 0)
                    
                    # Get rate and amount from job cargo if GRN has job reference
                    rate = 0.0
                    amount = 0.0
                    
                    if grn.job_ref:
                        from job.models import JobCargo
                        # Try to find matching job cargo item
                        job_cargo = JobCargo.objects.filter(
                            job=grn.job_ref,
                            item=grn_item.item
                        ).first()
                        
                        if job_cargo:
                            rate = float(job_cargo.rate or 0)
                            amount = float(job_cargo.amount or 0)
                        else:
                            # If no exact item match, try to find by item code
                            job_cargo = JobCargo.objects.filter(
                                job=grn.job_ref,
                                item_code=grn_item.item_code
                            ).first()
                            
                            if job_cargo:
                                rate = float(job_cargo.rate or 0)
                                amount = float(job_cargo.amount or 0)
                    
                    # Get ED number from GRNItem ed field
                    ed_number = grn_item.ed or ''
                    
                    items_data.append({
                        'id': grn_item.id,
                        'grn_id': grn.id,
                        'grn_number': grn.grn_number,
                        'item_code': grn_item.item_code or '',
                        'item_name': grn_item.item_name or grn_item.item.item_name if grn_item.item else '',
                        'hs_code': grn_item.hs_code or '',  # Use GRN item hs_code
                        'unit': grn_item.unit or '',
                        'quantity': available_qty,
                        'original_quantity': float(grn_item.received_qty or 0),
                        'used_quantity': float(used_qty),
                        'coo': grn_item.coo or '',
                        'n_weight': n_weight,
                        'g_weight': g_weight,
                        'volume': volume,
                        'p_date': grn_item.p_date.strftime('%Y-%m-%d') if grn_item.p_date else '',
                        'expiry_date': grn_item.expiry_date.strftime('%Y-%m-%d') if grn_item.expiry_date else '',
                        'color': grn_item.color or '',
                        'size': grn_item.size or '',
                        'barcode': grn_item.batch_number or '',  # Using batch_number as barcode
                        'rate': rate,
                        'amount': amount,
                        'ed': ed_number,
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
def get_customers_with_grns(request):
    """AJAX endpoint to get customers who have available GRNs"""
    try:
        from customer.models import Customer
        from grn.models import GRN, GRNItem
        from django.db.models import Sum, Q
        
        # Get current delivery order ID if editing (from request parameters)
        current_do_id = request.GET.get('current_do_id')
        if current_do_id == 'None':
            current_do_id = None
        
        # Get customers who have GRNs with draft or received status
        customers_with_grns = Customer.objects.filter(
            grn__status__in=['draft', 'received']
        ).distinct().order_by('customer_name')
        
        customers_data = []
        
        for customer in customers_with_grns:
            # Get all GRNs for this customer with draft or received status
            grns = GRN.objects.filter(
                customer=customer,
                status__in=['draft', 'received']
            )
            
            # Check if any GRN has available items
            has_available_items = False
            total_available_items = 0
            
            for grn in grns:
                grn_items = GRNItem.objects.filter(grn=grn)
                
                for grn_item in grn_items:
                    # Calculate used quantity from existing delivery orders
                    # Exclude the current delivery order if editing
                    used_qty_query = DeliveryOrderItem.objects.filter(
                        item=grn_item.item,
                        delivery_order__customer=customer
                    )
                    
                    if current_do_id:
                        # Exclude current delivery order from used quantity calculation
                        used_qty_query = used_qty_query.exclude(delivery_order_id=current_do_id)
                    
                    used_qty = used_qty_query.aggregate(
                        total_used=Sum('requested_qty')
                    )['total_used'] or 0
                    
                    # Calculate available quantity
                    available_qty = float(grn_item.received_qty or 0) - float(used_qty)
                    
                    if available_qty > 0:
                        has_available_items = True
                        total_available_items += 1
            
            # Only include customers who have available items
            if has_available_items:
                customers_data.append({
                    'id': customer.id,
                    'name': customer.customer_name,
                    'code': customer.customer_code,
                    'available_items_count': total_available_items
                })
        
        return JsonResponse({
            'success': True,
            'customers': customers_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

def generate_next_do_number():
    """Generate the next DO number in the format DO-YYYY-NNNN"""
    current_year = timezone.now().year
    # Get the last DO number for the current year
    last_do = DeliveryOrder.objects.filter(
        do_number__startswith=f"DO-{current_year}-"
    ).order_by('-do_number').first()
    
    if last_do:
        try:
            # Extract the number part from the last DO number
            last_number = int(last_do.do_number.split('-')[-1])
            new_number = last_number + 1
        except (ValueError, IndexError):
            new_number = 1
    else:
        new_number = 1
    
    return f"DO-{current_year}-{new_number:04d}"

@login_required
def send_delivery_order_email(request, pk):
    """Send delivery order via email"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        delivery_order = get_object_or_404(DeliveryOrder, pk=pk)
        
        # Get form data
        recipient_email = request.POST.get('recipient_email')
        cc_email = request.POST.get('cc_email', '')
        email_subject = request.POST.get('email_subject')
        email_message = request.POST.get('email_message', '')
        include_pdf = request.POST.get('include_pdf') == 'on'
        
        if not recipient_email or not email_subject:
            return JsonResponse({'success': False, 'error': 'Recipient email and subject are required'})
        
        # Prepare email content
        context = {
            'delivery_order': delivery_order,
            'message': email_message,
            'sender_name': request.user.get_full_name() or request.user.username,
        }
        
        # Render email template
        html_content = render_to_string('delivery_order/email_template.html', context)
        text_content = strip_tags(html_content)
        
        # Create email message
        email = EmailMessage(
            subject=email_subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email],
            cc=[cc_email] if cc_email else None,
        )
        email.content_subtype = "html"
        
        # Add PDF attachment if requested
        if include_pdf:
            try:
                # Generate PDF (you may need to implement PDF generation)
                pdf_path = generate_delivery_order_pdf(delivery_order)
                if pdf_path and os.path.exists(pdf_path):
                    with open(pdf_path, 'rb') as pdf_file:
                        email.attach(
                            f'Delivery_Order_{delivery_order.do_number}.pdf',
                            pdf_file.read(),
                            'application/pdf'
                        )
            except Exception as e:
                # Log the error but continue without PDF
                print(f"Error generating PDF: {e}")
        
        # Send email
        email.send()
        
        # Log the email action
        print(f"Email sent for Delivery Order {delivery_order.do_number} to {recipient_email}")
        
        return JsonResponse({
            'success': True,
            'message': f'Email sent successfully to {recipient_email}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to send email: {str(e)}'
        })

def generate_delivery_order_pdf(delivery_order):
    """Generate PDF for delivery order using WeasyPrint"""
    try:
        # Create context for the template
        context = {
            'delivery_order': delivery_order,
        }
        
        # Render the HTML template
        html_string = render_to_string('delivery_order/delivery_order_print.html', context)
        print(f"HTML template rendered successfully for DO {delivery_order.do_number}")
        
        # Create PDF directory if it doesn't exist
        pdf_dir = os.path.join(settings.MEDIA_ROOT, 'pdfs')
        os.makedirs(pdf_dir, exist_ok=True)
        print(f"PDF directory created/verified: {pdf_dir}")
        
        # Generate PDF filename
        pdf_filename = f'Delivery_Order_{delivery_order.do_number}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        pdf_path = os.path.join(pdf_dir, pdf_filename)
        print(f"PDF path: {pdf_path}")
        
        # Configure fonts
        font_config = FontConfiguration()
        
        # Create PDF from HTML
        HTML(string=html_string).write_pdf(
            pdf_path,
            font_config=font_config
        )
        
        print(f"PDF generated successfully: {pdf_path}")
        return pdf_path
        
    except Exception as e:
        print(f"Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        return None

@login_required
def delivery_order_print(request, pk):
    """Generate and download PDF for delivery order"""
    delivery_order = get_object_or_404(DeliveryOrder, pk=pk)
    print(f"Starting PDF generation for DO {delivery_order.do_number}")
    
    try:
        # Generate PDF
        pdf_path = generate_delivery_order_pdf(delivery_order)
        
        if pdf_path and os.path.exists(pdf_path):
            print(f"PDF file exists, serving download: {pdf_path}")
            # Read the PDF file
            with open(pdf_path, 'rb') as pdf_file:
                response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="Delivery_Order_{delivery_order.do_number}.pdf"'
                return response
        else:
            print(f"PDF generation failed or file doesn't exist: {pdf_path}")
            # Fallback to HTML view if PDF generation fails
            context = {
                'delivery_order': delivery_order,
            }
            return render(request, 'delivery_order/delivery_order_print.html', context)
            
    except Exception as e:
        print(f"Error in delivery_order_print: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to HTML view
        context = {
            'delivery_order': delivery_order,
        }
        return render(request, 'delivery_order/delivery_order_print.html', context)
