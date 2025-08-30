from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.db.models import Q
from django.core.paginator import Paginator
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration
import tempfile
import os
from .models import SupplierPayment, SupplierPaymentInvoice, SupplierPaymentBill
from .forms import SupplierPaymentForm
from customer.models import Customer
from invoice.models import Invoice
from supplier_bills.models import SupplierBill
from decimal import Decimal
import sys
from company.company_model import Company
from multi_currency.models import CurrencySettings
from django.template import Template, Context

def update_supplier_bill_status(supplier_bill):
    """Update supplier bill status based on total allocated payments"""
    from django.db.models import Sum
    
    # Calculate total allocated amount for this bill
    total_allocated = SupplierPaymentBill.objects.filter(
        supplier_bill=supplier_bill
    ).aggregate(total=Sum('allocated_amount'))['total'] or Decimal('0.00')
    
    # Update status based on payment coverage
    if total_allocated >= supplier_bill.amount:
        supplier_bill.status = 'paid'
    elif total_allocated > 0:
        # Partial payment - keep original status unless it was already paid
        if supplier_bill.status == 'paid':
            supplier_bill.status = 'draft'  # or 'sent' based on business logic
    else:
        # No payments - revert to appropriate unpaid status
        if supplier_bill.status == 'paid':
            supplier_bill.status = 'draft'  # or 'sent' based on business logic
    
    supplier_bill.save()

@login_required
def supplier_payment_list(request):
    """Display list of supplier payments with search and filtering"""
    payments = SupplierPayment.objects.select_related('supplier').prefetch_related(
        'payment_invoices__invoice'
    ).all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        payments = payments.filter(
            Q(payment_id__icontains=search_query) |
            Q(supplier__customer_name__icontains=search_query) |
            Q(reference_number__icontains=search_query) |
            Q(notes__icontains=search_query)
        )
    
    # Filter by payment method
    payment_method = request.GET.get('payment_method', '')
    if payment_method:
        payments = payments.filter(payment_method=payment_method)
    
    # Filter by date range
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if date_from:
        payments = payments.filter(payment_date__gte=date_from)
    if date_to:
        payments = payments.filter(payment_date__lte=date_to)
    
    # Pagination
    paginator = Paginator(payments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'payment_method': payment_method,
        'date_from': date_from,
        'date_to': date_to,
        'payment_methods': SupplierPayment.PAYMENT_METHODS,
    }
    
    return render(request, 'supplier_payments/supplier_payment_list.html', context)

@login_required
def pending_bills_list(request):
    """Display list of pending supplier bills and invoices for payment selection"""
    # Get all vendor and supplier customers
    vendor_suppliers = Customer.objects.filter(
        Q(customer_types__name__icontains='supplier') | Q(customer_types__name__icontains='vendor')
    )
    
    # Find vendors that actually have cost entries in invoices
    vendors_with_costs = set()
    unpaid_invoices = Invoice.objects.filter(status__in=['draft', 'sent', 'overdue', 'paid'])
    
    for invoice in unpaid_invoices:
        if invoice.invoice_items:
            for item in invoice.invoice_items:
                vendor_field = item.get('vendor', '')
                if vendor_field:
                    # Extract vendor code from format "VEN0001 - Waseem Transport (Vendor)"
                    if ' - ' in vendor_field:
                        vendor_code = vendor_field.split(' - ')[0].strip()
                        try:
                            vendor = vendor_suppliers.get(
                                customer_code=vendor_code,
                                is_active=True
                            )
                            vendors_with_costs.add(vendor.customer_name)
                        except Customer.DoesNotExist:
                            pass
    
    # Only get supplier bills for vendors that have actual cost transactions
    bills = SupplierBill.objects.filter(
        status__in=['draft', 'sent', 'overdue', 'paid'],
        supplier__in=vendors_with_costs
    ).order_by('-bill_date')
    
    # Get invoices that have vendor items
    from .models import SupplierPaymentInvoice
    paid_invoice_ids = SupplierPaymentInvoice.objects.values_list('invoice_id', flat=True)
    
    invoices = Invoice.objects.filter(
        status__in=['draft', 'sent', 'overdue', 'paid']
    ).exclude(id__in=paid_invoice_ids).order_by('-invoice_date')
    
    # Filter invoices to only include those with vendor items from vendors with cost transactions
    invoice_items = []
    vendors_with_costs_objects = vendor_suppliers.filter(customer_name__in=vendors_with_costs)
    
    for invoice in invoices:
        for vendor_supplier in vendors_with_costs_objects:
            supplier_code = vendor_supplier.customer_code
            supplier_name = vendor_supplier.customer_name
            
            # Find items for this supplier
            items = []
            cost_total = Decimal('0.00')
            for item in invoice.invoice_items:
                vendor_field = item.get('vendor', '')
                # Match by code or name (e.g., 'VEN0001 - Waseem Transport')
                if supplier_code in vendor_field or supplier_name in vendor_field:
                    items.append(item)
                    try:
                        cost_total += Decimal(str(item.get('cost_total', 0)))
                    except Exception:
                        pass
            
            if items and cost_total > 0:
                # Create a pseudo-bill object for invoices
                invoice_item = type('InvoiceItem', (), {
                    'id': f'inv_{invoice.id}',
                    'number': invoice.invoice_number,
                    'supplier': supplier_name,
                    'bill_date': invoice.invoice_date,
                    'due_date': invoice.invoice_date,  # Use invoice date as due date
                    'amount': cost_total,
                    'status': invoice.status,
                    'type': 'invoice',
                    'invoice_obj': invoice,
                    'customer_name': invoice.customer.customer_name,
                    'total_paid': Decimal('0.00'),
                    'payment_status': 'unpaid'
                })()
                invoice_items.append(invoice_item)
                break  # Only add once per invoice
    
    # Combine bills and invoice items
    all_items = list(bills) + invoice_items
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        filtered_items = []
        for item in all_items:
            item_number = getattr(item, 'invoice_number', None) or getattr(item, 'number', '')
            item_supplier = ''
            if hasattr(item, 'supplier') and item.supplier:
                if hasattr(item.supplier, 'customer_name'):
                    item_supplier = item.supplier.customer_name
                else:
                    item_supplier = str(item.supplier)
            
            if (search_query.lower() in item_number.lower() or 
                search_query.lower() in item_supplier.lower()):
                filtered_items.append(item)
        all_items = filtered_items
    
    # Filter by supplier
    supplier_name_filter = request.GET.get('supplier', '')
    if supplier_name_filter:
        filtered_items = []
        for item in all_items:
            item_supplier = ''
            if hasattr(item, 'supplier') and item.supplier:
                # For SupplierBill objects
                if hasattr(item.supplier, 'customer_name'):
                    item_supplier = item.supplier.customer_name
                else:
                    item_supplier = str(item.supplier)
            elif hasattr(item, 'vendor') and item.vendor:
                # For Invoice objects with vendor property
                if hasattr(item.vendor, 'customer_name'):
                    item_supplier = item.vendor.customer_name
                else:
                    item_supplier = str(item.vendor)
            
            if supplier_name_filter.lower() in item_supplier.lower():
                filtered_items.append(item)
        all_items = filtered_items
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        filtered_items = []
        for item in all_items:
            if item.status == status_filter:
                filtered_items.append(item)
        all_items = filtered_items
    
    # Filter by date range
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if date_from or date_to:
        from datetime import datetime
        filtered_items = []
        for item in all_items:
            item_date = item.bill_date
            include_item = True
            
            if date_from:
                try:
                    from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
                    if item_date < from_date:
                        include_item = False
                except ValueError:
                    pass
            
            if date_to and include_item:
                try:
                    to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
                    if item_date > to_date:
                        include_item = False
                except ValueError:
                    pass
            
            if include_item:
                filtered_items.append(item)
        all_items = filtered_items
    
    # Add payment information for supplier bills
    for item in all_items:
        if hasattr(item, 'type') and item.type == 'invoice':
            # Invoice items already have payment info set
            continue
        else:
            # This is a supplier bill
            payments = SupplierPaymentBill.objects.filter(supplier_bill=item)
            total_paid = sum(payment.allocated_amount for payment in payments)
            
            # Add payment status and total paid to the bill object
            item.total_paid = total_paid
            if total_paid >= item.amount:
                item.payment_status = 'fully_paid'
            elif total_paid > 0:
                item.payment_status = 'partially_paid'
            else:
                item.payment_status = 'unpaid'
    
    # Sort all items by date (newest first)
    all_items.sort(key=lambda x: x.bill_date, reverse=True)
    
    # Pagination
    paginator = Paginator(all_items, 25)  # Show 25 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all vendors and suppliers for filter dropdown
    suppliers = Customer.objects.filter(
        Q(customer_types__name__icontains='supplier') | Q(customer_types__name__icontains='vendor')
    ).order_by('customer_name')
    
    # Get default currency
    currency_settings = CurrencySettings.objects.first()
    default_currency = currency_settings.default_currency if currency_settings else None
    
    context = {
        'bills': page_obj,
        'suppliers': suppliers,
        'search_query': search_query,
        'selected_supplier': supplier_name_filter,
        'selected_status': status_filter,
        'date_from': date_from,
        'date_to': date_to,
        'total_bills': len(all_items),
        'total_amount': sum(item.amount for item in all_items),
        'default_currency': default_currency,
    }
    
    return render(request, 'supplier_payments/pending_bills_list.html', context)

@login_required
def supplier_payment_create(request):
    """Create a new supplier payment"""
    if request.method == 'POST':
        form = SupplierPaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            # Set company and user fields
            payment.company = request.user.company if hasattr(request.user, 'company') else None
            payment.created_by = request.user
            payment.updated_by = request.user
            payment.save()
            
            # Handle selected invoices
            selected_invoices = request.POST.getlist('selected_invoices')
            invoice_amounts = request.POST.getlist('invoice_amounts')
            
            # Debug: Print what we received
            print(f"DEBUG: POST data keys: {list(request.POST.keys())}")
            print(f"DEBUG: Selected invoices: {selected_invoices}")
            print(f"DEBUG: Invoice amounts: {invoice_amounts}")
            print(f"DEBUG: Full POST data: {dict(request.POST)}")
            
            for i, invoice_number in enumerate(selected_invoices):
                try:
                    invoice = Invoice.objects.get(invoice_number=invoice_number)
                    allocated_amount = Decimal(invoice_amounts[i]) if i < len(invoice_amounts) else Decimal('0.00')
                    
                    if allocated_amount > 0:
                        SupplierPaymentInvoice.objects.create(
                            supplier_payment=payment,
                            invoice=invoice,
                            allocated_amount=allocated_amount
                        )
                except (Invoice.DoesNotExist, ValueError, IndexError):
                    continue
            
            # Handle selected bills
            from supplier_bills.models import SupplierBill
            from .models import SupplierPaymentBill
            
            selected_bills = request.POST.getlist('selected_bills')
            bill_amounts = request.POST.getlist('bill_amounts')
            
            for i, bill_number in enumerate(selected_bills):
                try:
                    bill = SupplierBill.objects.get(number=bill_number)
                    allocated_amount = Decimal(bill_amounts[i]) if i < len(bill_amounts) else Decimal('0.00')
                    
                    if allocated_amount > 0:
                        SupplierPaymentBill.objects.create(
                            supplier_payment=payment,
                            supplier_bill=bill,
                            allocated_amount=allocated_amount
                        )
                        
                        # Update bill status based on total allocated payments
                        update_supplier_bill_status(bill)
                except (SupplierBill.DoesNotExist, ValueError, IndexError):
                    continue
            
            messages.success(request, f'Supplier payment {payment.payment_id} created successfully!')
            return redirect('supplier_payments:supplier_payment_detail', pk=payment.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SupplierPaymentForm()
        
        # Check if there are any suppliers with unpaid invoices or pending bills
        from customer.models import CustomerType
        
        vendor_supplier_types = CustomerType.objects.filter(
            name__icontains='vendor'
        ) | CustomerType.objects.filter(
            name__icontains='supplier'
        )
        
        unpaid_statuses = ['draft', 'sent', 'overdue']
        
        # Check for suppliers with unpaid invoices
        suppliers_with_unpaid_invoices = Customer.objects.filter(
            is_active=True,
            customer_types__in=vendor_supplier_types,
            invoice__status__in=unpaid_statuses
        ).distinct()
        
        # Check for suppliers with pending bills
        from supplier_bills.models import SupplierBill
        
        vendor_supplier_names = Customer.objects.filter(
            is_active=True,
            customer_types__in=vendor_supplier_types
        ).values_list('customer_name', flat=True)
        
        pending_bills = SupplierBill.objects.filter(
            status__in=unpaid_statuses,
            supplier__in=vendor_supplier_names
        )
        
        suppliers_with_pending_bills = set()
        for bill in pending_bills:
            try:
                supplier = Customer.objects.get(
                    customer_name=bill.supplier,
                    is_active=True,
                    customer_types__in=vendor_supplier_types
                )
                suppliers_with_pending_bills.add(supplier.id)
            except Customer.DoesNotExist:
                continue
        
        # Check if there are any suppliers with either unpaid invoices or pending bills
        has_suppliers_with_invoices = suppliers_with_unpaid_invoices.exists()
        has_suppliers_with_bills = len(suppliers_with_pending_bills) > 0
        
        # Check if there are any unpaid invoices or pending bills in the system at all
        has_any_unpaid_invoices = Invoice.objects.filter(status__in=unpaid_statuses).exists()
        has_any_pending_bills = SupplierBill.objects.filter(status__in=unpaid_statuses).exists()
        
        if not has_suppliers_with_invoices and not has_suppliers_with_bills:
            messages.warning(request, 'No suppliers with unpaid invoices or pending bills found. You can only create payments for suppliers who have outstanding invoices or bills.')
    
    # Get default currency
    currency_settings = CurrencySettings.objects.first()
    default_currency = currency_settings.default_currency if currency_settings else None
    
    context = {
        'form': form,
        'title': 'Create Supplier Payment',
        'button_text': 'Save Payment',
        'default_currency': default_currency,
        'has_any_unpaid_invoices': has_any_unpaid_invoices,
        'has_any_pending_bills': has_any_pending_bills,
    }
    
    return render(request, 'supplier_payments/supplier_payment_form.html', context)

@login_required
def supplier_payment_detail(request, pk):
    """Display supplier payment details"""
    payment = get_object_or_404(
        SupplierPayment.objects.select_related('supplier', 'ledger_account', 'company'),
        pk=pk
    )
    
    context = {
        'payment': payment,
    }
    
    return render(request, 'supplier_payments/supplier_payment_detail.html', context)

@login_required
def supplier_payment_update(request, pk):
    """Update an existing supplier payment"""
    payment = get_object_or_404(
        SupplierPayment.objects.select_related('supplier', 'ledger_account', 'company'),
        pk=pk
    )
    
    if request.method == 'POST':
        from invoice.models import Invoice
        form = SupplierPaymentForm(request.POST, instance=payment)
        if form.is_valid():
            payment = form.save()
            
            # Clear existing invoice relationships
            SupplierPaymentInvoice.objects.filter(supplier_payment=payment).delete()
            
            # Handle selected invoices
            selected_invoices = request.POST.getlist('selected_invoices')
            invoice_amounts = request.POST.getlist('invoice_amounts')
            
            for i, invoice_number in enumerate(selected_invoices):
                try:
                    invoice = Invoice.objects.get(invoice_number=invoice_number)
                    allocated_amount = Decimal(invoice_amounts[i]) if i < len(invoice_amounts) else Decimal('0.00')
                    
                    if allocated_amount > 0:
                        SupplierPaymentInvoice.objects.create(
                            supplier_payment=payment,
                            invoice=invoice,
                            allocated_amount=allocated_amount
                        )
                except (Invoice.DoesNotExist, ValueError, IndexError):
                    continue
            
            # Clear existing bill relationships and update bill statuses
            from .models import SupplierPaymentBill
            existing_bills = SupplierPaymentBill.objects.filter(supplier_payment=payment)
            affected_bills = [pb.supplier_bill for pb in existing_bills]
            existing_bills.delete()
            
            # Update status of previously linked bills
            for bill in affected_bills:
                update_supplier_bill_status(bill)
            
            # Handle selected bills
            from supplier_bills.models import SupplierBill
            
            selected_bills = request.POST.getlist('selected_bills')
            bill_amounts = request.POST.getlist('bill_amounts')
            
            for i, bill_number in enumerate(selected_bills):
                try:
                    bill = SupplierBill.objects.get(number=bill_number)
                    allocated_amount = Decimal(bill_amounts[i]) if i < len(bill_amounts) else Decimal('0.00')
                    
                    if allocated_amount > 0:
                        SupplierPaymentBill.objects.create(
                            supplier_payment=payment,
                            supplier_bill=bill,
                            allocated_amount=allocated_amount
                        )
                        
                        # Update bill status based on total allocated payments
                        update_supplier_bill_status(bill)
                except (SupplierBill.DoesNotExist, ValueError, IndexError):
                    continue
            
            messages.success(request, f'Supplier payment {payment.payment_id} updated successfully!')
            return redirect('supplier_payments:supplier_payment_detail', pk=payment.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SupplierPaymentForm(instance=payment)
        
        # Check if there are any suppliers with unpaid invoices (for new payments)
        from customer.models import CustomerType
        from invoice.models import Invoice
        from supplier_bills.models import SupplierBill
        
        vendor_supplier_types = CustomerType.objects.filter(
            name__icontains='vendor'
        ) | CustomerType.objects.filter(
            name__icontains='supplier'
        )
        
        unpaid_statuses = ['draft', 'sent', 'overdue']
        suppliers_with_unpaid = Customer.objects.filter(
            is_active=True,
            customer_types__in=vendor_supplier_types,
            invoice__status__in=unpaid_statuses
        ).distinct()
        
        # Check if there are any unpaid invoices or pending bills in the system at all
        has_any_unpaid_invoices = Invoice.objects.filter(status__in=unpaid_statuses).exists()
        has_any_pending_bills = SupplierBill.objects.filter(status__in=unpaid_statuses).exists()
        
        if not suppliers_with_unpaid.exists():
            messages.warning(request, 'No suppliers with unpaid invoices or pending bills found. You can only create payments for suppliers who have outstanding invoices or bills.')
    
    context = {
        'form': form,
        'payment': payment,
        'title': 'Update Supplier Payment',
        'button_text': 'Update Payment',
        'has_any_unpaid_invoices': has_any_unpaid_invoices,
        'has_any_pending_bills': has_any_pending_bills,
    }
    
    return render(request, 'supplier_payments/supplier_payment_form.html', context)

@login_required
def supplier_payment_delete(request, pk):
    """Delete a supplier payment"""
    payment = get_object_or_404(SupplierPayment, pk=pk)
    
    if request.method == 'POST':
        payment_id = payment.payment_id
        
        # Get all affected bills before deleting the payment
        affected_bills = [pb.supplier_bill for pb in payment.payment_bills.all()]
        
        # Delete the payment (this will cascade delete SupplierPaymentBill records)
        payment.delete()
        
        # Update status of affected bills
        for bill in affected_bills:
            update_supplier_bill_status(bill)
        
        messages.success(request, f'Supplier payment {payment_id} deleted successfully!')
        return redirect('supplier_payments:supplier_payment_list')
    
    context = {
        'payment': payment,
    }
    
    return render(request, 'supplier_payments/supplier_payment_confirm_delete.html', context)

@login_required
def supplier_payment_print(request, pk):
    """Generate PDF receipt for supplier payment"""
    payment = get_object_or_404(SupplierPayment, pk=pk)
    
    # Get company details for the receipt
    company = Company.objects.first()
    
    context = {
        'payment': payment,
        'company': company,
    }
    
    # Render the HTML template
    html_string = render_to_string('supplier_payments/print_payment.html', context)
    
    # Configure fonts
    font_config = FontConfiguration()
    
    # Generate PDF
    html_doc = HTML(string=html_string)
    pdf = html_doc.write_pdf(font_config=font_config)
    
    # Create response
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="supplier_payment_{payment.payment_id}.pdf"'
    
    return response

@login_required
def supplier_payment_email(request, pk):
    """Send supplier payment receipt via email"""
    payment = get_object_or_404(SupplierPayment, pk=pk)
    
    # This would typically send an email with the payment receipt
    # For now, just return a success message
    messages.success(request, f'Payment receipt for {payment.payment_id} sent successfully!')
    
    return redirect('supplier_payments:supplier_payment_detail', pk=payment.pk)

@login_required
def get_pending_invoices(request, supplier_id):
    """AJAX view to get pending invoices and supplier bills for a supplier"""
    print(f"[DEBUG] get_pending_invoices called with supplier_id: {supplier_id}", file=sys.stderr)
    try:
        supplier = get_object_or_404(Customer, pk=supplier_id)
        supplier_code = supplier.customer_code
        supplier_name = supplier.customer_name

        print(f"[DEBUG] Supplier: {supplier_code} - {supplier_name}", file=sys.stderr)

        # Find invoices with status draft, sent, overdue, or paid
        # Exclude invoices that have already been paid for this supplier
        paid_invoice_ids = SupplierPaymentInvoice.objects.filter(
            supplier_payment__supplier=supplier
        ).values_list('invoice_id', flat=True)
        
        invoices = Invoice.objects.filter(
            status__in=['draft', 'sent', 'overdue', 'paid']
        ).exclude(id__in=paid_invoice_ids).order_by('-invoice_date')

        invoices_data = []
        for invoice in invoices:
            print(f"[DEBUG] Checking invoice: {invoice.invoice_number}", file=sys.stderr)
            # Find items for this supplier
            items = []
            cost_total = Decimal('0.00')
            for item in invoice.invoice_items:
                vendor_field = item.get('vendor', '')
                print(f"[DEBUG]   Item vendor: '{vendor_field}'", file=sys.stderr)
                # Match by code or name (e.g., 'VEN0001 - Waseem Transport')
                if supplier_code in vendor_field or supplier_name in vendor_field:
                    print(f"[DEBUG]   MATCHED vendor for {supplier_code} or {supplier_name}", file=sys.stderr)
                    items.append(item)
                    try:
                        cost_total += Decimal(str(item.get('cost_total', 0)))
                    except Exception as e:
                        print(f"[DEBUG]   Error adding cost_total: {e}", file=sys.stderr)
            print(f"[DEBUG]   Items matched: {len(items)}, cost_total: {cost_total}", file=sys.stderr)
            if items and cost_total > 0:
                invoices_data.append({
                    'type': 'invoice',
                    'invoice_number': invoice.invoice_number,
                    'invoice_date': invoice.invoice_date.strftime('%b %d, %Y'),
                    'bl_number': invoice.bl_number,
                    'ed_number': invoice.ed_number,
                    'container_number': invoice.container_number,
                    'job_number': invoice.jobs.first().job_code if invoice.jobs.exists() else '-',
                    'customer_name': invoice.customer.customer_name,
                    'items_count': len(items),
                    'cost_total': str(cost_total),
                    'status': invoice.get_status_display(),
                })

        # Find supplier bills with status draft, sent, or overdue
        # Exclude bills that have already been paid for this supplier
        from supplier_bills.models import SupplierBill
        from .models import SupplierPaymentBill
        
        paid_bill_ids = SupplierPaymentBill.objects.filter(
            supplier_payment__supplier=supplier
        ).values_list('supplier_bill_id', flat=True)
        
        # Match supplier bills by supplier name (since it's a CharField)
        supplier_bills = SupplierBill.objects.filter(
            status__in=['draft', 'sent', 'overdue', 'paid'],
            supplier__icontains=supplier_name
        ).exclude(id__in=paid_bill_ids).order_by('-bill_date')
        
        bills_data = []
        for bill in supplier_bills:
            print(f"[DEBUG] Found supplier bill: {bill.number}", file=sys.stderr)
            bills_data.append({
                'type': 'bill',
                'bill_number': bill.number,
                'bill_date': bill.bill_date.strftime('%b %d, %Y'),
                'due_date': bill.due_date.strftime('%b %d, %Y'),
                'supplier': bill.supplier,
                'amount': str(bill.amount),
                'status': bill.get_status_display(),
                'reference_number': bill.reference_number or '-',
                'description': bill.description or '-',
            })

        # Combine invoices and bills
        all_items = invoices_data + bills_data
        
        print(f"[DEBUG] Returning {len(invoices_data)} invoices and {len(bills_data)} bills", file=sys.stderr)
        return JsonResponse({
            'success': True,
            'invoices': invoices_data,
            'bills': bills_data,
            'all_items': all_items
        })
    except Exception as e:
        print(f"[DEBUG] Exception: {e}", file=sys.stderr)
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def ajax_filter_ledger_accounts(request):
    """AJAX endpoint to filter ledger accounts based on payment method"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            payment_method = data.get('payment_method', '')
            
            from chart_of_accounts.models import ChartOfAccount
            
            # Filter accounts based on payment method using parent-child relationships
            if payment_method == 'cash':
                # For cash payments, show only cash-related ledger accounts (not parent accounts)
                accounts = ChartOfAccount.objects.filter(
                    Q(name__icontains='cash') | Q(name__icontains='petty'),
                    is_group=False,  # Only ledger accounts, not parent groups
                    is_active=True,
                    account_type__category='ASSET'
                ).order_by('account_code')
                
                # If no cash accounts found, fallback to accounts with cash-related codes
                if not accounts.exists():
                    accounts = ChartOfAccount.objects.filter(
                        account_code__in=['1000', '1006'],  # Specific cash account codes
                        is_active=True,
                        is_group=False
                    ).order_by('account_code')
                    
            elif payment_method in ['bank_transfer', 'bank', 'cheque']:
                # For bank payments, find all Bank-related parent accounts and show their child ledger accounts
                bank_parents = ChartOfAccount.objects.filter(
                    Q(name__icontains='bank') & Q(name__icontains='account'),
                    is_group=True,
                    is_active=True
                )
                
                if bank_parents.exists():
                    # Get all child ledger accounts under Bank parents
                    accounts = ChartOfAccount.objects.filter(
                        parent_account__in=bank_parents,
                        is_active=True,
                        is_group=False
                    ).order_by('account_code')
                else:
                    # Fallback to name-based filtering if parent not found
                    accounts = ChartOfAccount.objects.filter(
                        is_active=True,
                        is_group=False,
                        account_type__category='ASSET'
                    ).filter(
                        Q(name__icontains='bank') |
                        Q(account_code__startswith='110')
                    ).order_by('account_code')
                    
            elif payment_method == 'credit_card':
                # For credit cards, show credit card and related accounts
                accounts = ChartOfAccount.objects.filter(
                    is_active=True,
                    is_group=False,
                    account_type__category__in=['ASSET', 'LIABILITY']
                ).filter(
                    Q(name__icontains='credit') | 
                    Q(name__icontains='card') |
                    Q(name__icontains='visa') |
                    Q(name__icontains='mastercard') |
                    Q(name__icontains='amex') |
                    Q(account_code__startswith='12') |
                    Q(account_code__startswith='21')
                ).order_by('account_code')
            else:
                # For other payment methods, show all asset accounts
                accounts = ChartOfAccount.objects.filter(
                    is_active=True,
                    is_group=False,
                    account_type__category='ASSET'
                ).order_by('account_code')
            
            accounts_data = []
            for account in accounts:
                accounts_data.append({
                    'id': account.id,
                    'account_code': account.account_code,
                    'name': account.name,
                    'account_type': str(account.account_type) if account.account_type else ''
                })
            
            return JsonResponse({
                'success': True,
                'accounts': accounts_data
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })


@login_required
def ajax_all_ledger_accounts(request):
    """AJAX endpoint to get all available ledger accounts"""
    try:
        from chart_of_accounts.models import ChartOfAccount
        
        accounts = ChartOfAccount.objects.filter(
            is_active=True,
            is_group=False
        ).order_by('account_code')
        
        accounts_data = []
        for account in accounts:
            accounts_data.append({
                'id': account.id,
                'account_code': account.account_code,
                'name': account.name,
                'account_type': account.account_type
            })
        
        return JsonResponse({
            'success': True,
            'accounts': accounts_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
