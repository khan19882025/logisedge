from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from datetime import datetime, date
from decimal import Decimal
import json

from .models import HBL, HBLItem, HBLCharge, HBLHistory
from .forms import HBLForm, HBLItemForm, HBLChargeForm, HBLSearchForm, HBLReportForm
from .forms import HBLItemFormSet, HBLChargeFormSet


@login_required
def dashboard(request):
    """Dashboard view for HBL management"""
    
    # Get counts for dashboard
    draft_hbl_count = HBL.objects.filter(status='Draft').count()
    confirmed_hbl_count = HBL.objects.filter(status__in=['Original', 'SEAWAY BILL']).count()
    total_hbl_count = HBL.objects.count()
    
    # Get recent HBLs
    recent_hbls = HBL.objects.select_related('shipper', 'consignee').order_by('-created_at')[:10]
    
    # Get unpaid invoices (placeholder - you may need to adjust based on your invoice model)
    unpaid_invoices = []
    
    context = {
        'draft_hbl_count': draft_hbl_count,
        'confirmed_hbl_count': confirmed_hbl_count,
        'total_hbl_count': total_hbl_count,
        'recent_hbls': recent_hbls,
        'unpaid_invoices': unpaid_invoices,
    }
    
    return render(request, 'bill_of_lading/dashboard.html', context)


@login_required
def hbl_list(request):
    """List view for HBL documents"""
    
    # Get filter parameters
    search_term = request.GET.get('search_term', '')
    search_field = request.GET.get('search_field', '')
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    terms = request.GET.get('terms', '')
    
    # Start with all HBLs
    hbls = HBL.objects.select_related('shipper', 'consignee', 'notify_party').prefetch_related('cargo_items')
    
    # Apply filters
    if search_term:
        if search_field == 'hbl_number':
            hbls = hbls.filter(hbl_number__icontains=search_term)
        elif search_field == 'mbl_number':
            hbls = hbls.filter(mbl_number__icontains=search_term)
        elif search_field == 'shipper':
            hbls = hbls.filter(shipper__name__icontains=search_term)
        elif search_field == 'consignee':
            hbls = hbls.filter(consignee__name__icontains=search_term)
        elif search_field == 'notify_party':
            hbls = hbls.filter(notify_party__name__icontains=search_term)
        elif search_field == 'ocean_vessel':
            hbls = hbls.filter(ocean_vessel__icontains=search_term)
        elif search_field == 'container_no':
            hbls = hbls.filter(cargo_items__container_no__icontains=search_term).distinct()
        else:
            # Default search across multiple fields
            hbls = hbls.filter(
                Q(hbl_number__icontains=search_term) |
                Q(mbl_number__icontains=search_term) |
                Q(shipper__name__icontains=search_term) |
                Q(consignee__name__icontains=search_term) |
                Q(ocean_vessel__icontains=search_term)
            )
    
    if status:
        hbls = hbls.filter(status=status)
    
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            hbls = hbls.filter(created_at__date__gte=date_from)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            hbls = hbls.filter(created_at__date__lte=date_to)
        except ValueError:
            pass
    
    if terms:
        hbls = hbls.filter(terms=terms)
    
    # Pagination
    paginator = Paginator(hbls, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Search form
    search_form = HBLSearchForm(request.GET)
    
    context = {
        'hbls': page_obj,
        'search_form': search_form,
        'mode': 'list',
    }
    
    return render(request, 'bill_of_lading/hbl.html', context)


@login_required
def hbl_detail(request, hbl_id=None):
    """Detail view for creating/editing HBL"""
    
    hbl = None
    cargo_items = []
    mode = 'create'
    
    if hbl_id and hbl_id != 'new':
        hbl = get_object_or_404(HBL, id=hbl_id)
        cargo_items = hbl.cargo_items.all()
        mode = 'edit'
    
    if request.method == 'POST':
        # Copy POST so we can safely mutate defaults and computed fields
        post_data = request.POST.copy()

        # Parse cargo rows from custom table inputs instead of a Django formset
        cargo_container_nos = post_data.getlist('cargo_container_no[]')
        cargo_container_sizes = post_data.getlist('cargo_container_size[]')
        cargo_seal_nos = post_data.getlist('cargo_seal_no[]')
        cargo_num_packages_list = post_data.getlist('cargo_number_of_packages[]')
        cargo_package_types = post_data.getlist('cargo_package_type[]')
        cargo_custom_package_types = post_data.getlist('cargo_custom_package_type[]')
        cargo_descriptions = post_data.getlist('cargo_description[]')
        cargo_gross_weights = post_data.getlist('cargo_gross_weight[]')
        cargo_net_weights = post_data.getlist('cargo_net_weight[]')
        cargo_measurements = post_data.getlist('cargo_measurement[]')

        cargo_row_count = max(
            len(cargo_container_nos), len(cargo_container_sizes), len(cargo_seal_nos),
            len(cargo_num_packages_list), len(cargo_package_types), len(cargo_custom_package_types),
            len(cargo_descriptions), len(cargo_gross_weights), len(cargo_net_weights),
            len(cargo_measurements)
        )

        cargo_rows_valid = True
        cargo_errors = []
        computed_total_packages = 0
        computed_total_gross_weight = 0
        computed_total_measurement = 0

        if cargo_row_count == 0:
            cargo_rows_valid = False
            cargo_errors.append('At least one cargo item is required.')
        else:
            for index in range(cargo_row_count):
                try:
                    num_packages = int(cargo_num_packages_list[index])
                    gross_weight = float(cargo_gross_weights[index])
                    measurement = float(cargo_measurements[index])
                except (ValueError, IndexError):
                    cargo_rows_valid = False
                    cargo_errors.append(f'Row {index + 1}: Invalid numeric values.')
                    continue

                # Basic presence checks
                try:
                    desc_present = bool(cargo_descriptions[index].strip())
                except IndexError:
                    desc_present = False
                if num_packages < 1 or not desc_present:
                    cargo_rows_valid = False
                    cargo_errors.append(f'Row {index + 1}: Number of packages must be >= 1 and description is required.')

                computed_total_packages += num_packages
                computed_total_gross_weight += gross_weight
                computed_total_measurement += measurement

        # Ensure defaults for required-but-hidden fields when not present in POST
        if not post_data.get('currency'):
            post_data['currency'] = 'USD'
        # Use status from header radios if present; otherwise Draft
        if not post_data.get('status'):
            post_data['status'] = 'Draft'

        # Inject computed totals into POST so HBLForm validates
        if cargo_rows_valid:
            post_data['number_of_packages'] = str(computed_total_packages)
            post_data['gross_weight'] = str(computed_total_gross_weight)
            post_data['measurement'] = str(computed_total_measurement)

        # Now validate main form
        form = HBLForm(post_data, instance=hbl)
        print(f"Form is valid: {form.is_valid()}")
        if not form.is_valid():
            print(f"Form errors: {form.errors}")
            messages.error(request, f'Form validation failed: {form.errors}')

        if not cargo_rows_valid:
            print(f"Item rows invalid: {cargo_errors}")
            messages.error(request, f'Item rows validation failed: {cargo_errors}')

        # Save if both main form and cargo rows are valid
        if form.is_valid() and cargo_rows_valid:
            hbl = form.save(commit=False)
            if not hbl.created_by:
                hbl.created_by = request.user
            hbl.updated_by = request.user

            # Ensure totals on HBL reflect cargo totals
            hbl.number_of_packages = computed_total_packages
            hbl.gross_weight = Decimal(str(computed_total_gross_weight))
            hbl.measurement = Decimal(str(computed_total_measurement))
            if not hbl.currency:
                hbl.currency = 'USD'

            hbl.save()

            # Replace existing cargo items with submitted ones
            HBLItem.objects.filter(hbl=hbl).delete()
            for index in range(cargo_row_count):
                try:
                    HBLItem.objects.create(
                        hbl=hbl,
                        container_no=cargo_container_nos[index] if index < len(cargo_container_nos) else '',
                        container_size=cargo_container_sizes[index] if index < len(cargo_container_sizes) else '',
                        seal_no=cargo_seal_nos[index] if index < len(cargo_seal_nos) else '',
                        number_of_packages=int(cargo_num_packages_list[index]),
                        package_type=cargo_package_types[index] if index < len(cargo_package_types) else '',
                        custom_package_type=cargo_custom_package_types[index] if index < len(cargo_custom_package_types) else '',
                        description=cargo_descriptions[index],
                        gross_weight=cargo_gross_weights[index],
                        net_weight=cargo_net_weights[index],
                        measurement=cargo_measurements[index],
                    )
                except Exception as e:
                    # Log and continue; surface a message but do not crash
                    print(f"Error creating cargo item at row {index + 1}: {e}")

            messages.success(request, f'HBL {hbl.hbl_number} saved successfully.')
            return redirect('bill_of_lading:hbl_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = HBLForm(instance=hbl)
    
    # Get customers for dropdowns
    from customer.models import Customer, CustomerType
    customers = Customer.objects.all()
    
    # Get filtered customers for each type
    shipper_customers = []
    consignee_customers = []
    notify_customers = []
    vendor_customers = []
    
    for customer in customers:
        customer_types = customer.customer_types.all()
        for customer_type in customer_types:
            if 'Shipper' in customer_type.name and customer not in shipper_customers:
                shipper_customers.append(customer)
            if 'Consignee' in customer_type.name and customer not in consignee_customers:
                consignee_customers.append(customer)
            if 'Notify Party' in customer_type.name and customer not in notify_customers:
                notify_customers.append(customer)
            if 'Vendor' in customer_type.name and customer not in vendor_customers:
                vendor_customers.append(customer)
    
    context = {
        'hbl': hbl,
        'form': form,
        'cargo_items': cargo_items,
        'customers': customers,
        'shipper_customers': shipper_customers,
        'consignee_customers': consignee_customers,
        'notify_customers': notify_customers,
        'vendor_customers': vendor_customers,
        'mode': mode,
        'today': date.today(),
    }
    
    return render(request, 'bill_of_lading/hbl.html', context)


@login_required
def hbl_delete(request, hbl_id):
    """Delete HBL"""
    hbl = get_object_or_404(HBL, id=hbl_id)
    
    if request.method == 'POST':
        hbl_number = hbl.hbl_number
        hbl.delete()
        messages.success(request, f'HBL {hbl_number} deleted successfully.')
        return redirect('bill_of_lading:hbl_list')
    
    context = {
        'hbl': hbl,
    }
    
    return render(request, 'bill_of_lading/hbl_confirm_delete.html', context)


@login_required
def print_hbl(request, hbl_id):
    """Print HBL view"""
    hbl = get_object_or_404(HBL.objects.select_related('shipper', 'consignee', 'notify_party'), id=hbl_id)
    cargo_items = hbl.cargo_items.all()
    cargo_list = list(cargo_items)

    # Totals and first package type summary
    total_packages = sum((item.number_of_packages or 0) for item in cargo_list)
    first_type_label = ''
    first_type_qty = 0
    if cargo_list:
        first_item = cargo_list[0]
        if first_item.package_type == 'OTHER':
            first_type_label = (first_item.custom_package_type or 'OTHER').upper()
            match = lambda it: (it.package_type == 'OTHER' and (it.custom_package_type or '') == (first_item.custom_package_type or ''))
        else:
            first_type_label = (first_item.package_type or '').upper()
            match = lambda it: it.package_type == first_item.package_type
        first_type_qty = sum((it.number_of_packages or 0) for it in cargo_list if match(it))
    # Load company logo if available
    encoded_logo = None
    logo_mime = None
    try:
        from company.company_model import Company
        from django.core.files.storage import default_storage
        import base64, mimetypes
        company = Company.objects.filter(is_active=True).first()
        if company and hasattr(company, 'logo') and company.logo:
            logo_path = company.logo.name
            guessed_mime, _ = mimetypes.guess_type(logo_path)
            logo_mime = guessed_mime or 'image/png'
            with default_storage.open(logo_path, 'rb') as f:
                encoded_logo = base64.b64encode(f.read()).decode('utf-8')
    except Exception:
        encoded_logo = None
        logo_mime = None
    
    context = {
        'hbl': hbl,
        'cargo_items': cargo_items,
        'encoded_logo': encoded_logo,
        'logo_mime': logo_mime,
        'total_packages': total_packages,
        'first_type_label': first_type_label,
        'first_type_qty': first_type_qty,
    }
    
    return render(request, 'bill_of_lading/print_hbl.html', context)


@login_required
def hbl_report(request):
    """HBL Report view"""
    
    if request.method == 'POST':
        form = HBLReportForm(request.POST)
        if form.is_valid():
            # Generate report based on form data
            filters = form.cleaned_data
            hbls = HBL.objects.all()
            
            # Apply filters
            if filters.get('date_from'):
                hbls = hbls.filter(created_at__date__gte=filters['date_from'])
            if filters.get('date_to'):
                hbls = hbls.filter(created_at__date__lte=filters['date_to'])
            if filters.get('mbl_number'):
                hbls = hbls.filter(mbl_number__icontains=filters['mbl_number'])
            if filters.get('hbl_number'):
                hbls = hbls.filter(hbl_number__icontains=filters['hbl_number'])
            if filters.get('container_no'):
                hbls = hbls.filter(cargo_items__container_no__icontains=filters['container_no']).distinct()
            if filters.get('customer'):
                hbls = hbls.filter(
                    Q(shipper__name__icontains=filters['customer']) |
                    Q(consignee__name__icontains=filters['customer']) |
                    Q(notify_party__name__icontains=filters['customer'])
                )
            if filters.get('shipper'):
                hbls = hbls.filter(shipper__name__icontains=filters['shipper'])
            if filters.get('consignee'):
                hbls = hbls.filter(consignee__name__icontains=filters['consignee'])
            if filters.get('description'):
                hbls = hbls.filter(description_of_goods__icontains=filters['description'])
            if filters.get('port_loading'):
                hbls = hbls.filter(port_of_loading__icontains=filters['port_loading'])
            if filters.get('port_discharge'):
                hbls = hbls.filter(port_of_discharge__icontains=filters['port_discharge'])
            
            context = {
                'hbls': hbls,
                'filters': filters,
                'report_generated': True,
            }
            return render(request, 'bill_of_lading/hbl_report.html', context)
    else:
        form = HBLReportForm()
    
    # Get filter options
    mbl_numbers = HBL.objects.values_list('mbl_number', flat=True).distinct()
    hbl_numbers = HBL.objects.values_list('hbl_number', flat=True).distinct()
    container_numbers = HBLItem.objects.values_list('container_no', flat=True).distinct()
    customers = []
    shippers = []
    consignees = []
    descriptions = []
    ports_loading = HBL.objects.values_list('port_of_loading', flat=True).distinct()
    ports_discharge = HBL.objects.values_list('port_of_discharge', flat=True).distinct()
    
    context = {
        'form': form,
        'mbl_numbers': mbl_numbers,
        'hbl_numbers': hbl_numbers,
        'container_numbers': container_numbers,
        'customers': customers,
        'shippers': shippers,
        'consignees': consignees,
        'descriptions': descriptions,
        'ports_loading': ports_loading,
        'ports_discharge': ports_discharge,
    }
    
    return render(request, 'bill_of_lading/hbl_report.html', context)


@login_required
@require_POST
def change_status(request, hbl_id):
    """Change HBL status via AJAX. Accepts form-encoded or JSON payloads."""
    try:
        hbl = get_object_or_404(HBL, id=hbl_id)

        new_status = request.POST.get('status')
        if not new_status:
            # Try JSON body
            try:
                payload = json.loads(request.body.decode('utf-8'))
                new_status = payload.get('status')
            except Exception:
                new_status = None

        if new_status in dict(HBL.STATUS_CHOICES):
            old_status = hbl.status
            hbl.status = new_status
            hbl.save()
            
            # Create history entry
            HBLHistory.objects.create(
                hbl=hbl,
                action='status_changed',
                description=f'Status changed from {old_status} to {new_status}',
                user=request.user,
                old_values={'status': old_status},
                new_values={'status': new_status}
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Status changed to {new_status} successfully.'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Invalid status.'
            }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@csrf_exempt
def add_customer(request):
    """Add new customer via AJAX"""
    if request.method == 'POST':
        try:
            from customer.models import Customer, CustomerType
            
            customer_name = request.POST.get('name')
            address = request.POST.get('address', '')
            customer_type_name = request.POST.get('customer_type', '')
            
            # Create the customer
            customer = Customer.objects.create(
                customer_name=customer_name,
                billing_address=address,
                created_by=request.user
            )
            
            # Add customer type if specified
            if customer_type_name:
                customer_type, created = CustomerType.objects.get_or_create(
                    name=customer_type_name,
                    defaults={
                        'code': customer_type_name[:3].upper(),
                        'description': f'Auto-generated type for {customer_type_name}'
                    }
                )
                customer.customer_types.add(customer_type)
            
            # Generate customer code if not already set
            if not customer.customer_code:
                try:
                    customer.customer_code = customer.generate_customer_code()
                    customer.save()
                except Exception as e:
                    # If code generation fails, create a simple one
                    import datetime
                    customer.customer_code = f"CUS{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
                    customer.save()
            
            return JsonResponse({
                'success': True,
                'customer': {
                    'id': customer.id,
                    'name': customer.customer_name,
                    'address': customer.billing_address,
                }
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


@login_required
def hbl_charges(request, hbl_id):
    """Manage HBL charges"""
    hbl = get_object_or_404(HBL, id=hbl_id)
    
    if request.method == 'POST':
        formset = HBLChargeFormSet(request.POST, instance=hbl)
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Charges updated successfully.')
            return redirect('bill_of_lading:hbl_detail', hbl_id=hbl.id)
    else:
        formset = HBLChargeFormSet(instance=hbl)
    
    context = {
        'hbl': hbl,
        'formset': formset,
    }
    
    return render(request, 'bill_of_lading/hbl_charges.html', context)


@login_required
def export_hbl_excel(request):
    """Export HBL data to Excel"""
    # Implementation for Excel export
    pass


@login_required
def export_hbl_pdf(request):
    """Export HBL data to PDF"""
    # Implementation for PDF export
    pass
