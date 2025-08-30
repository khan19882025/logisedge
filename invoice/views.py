from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Invoice
from .forms import InvoiceForm
from customer.models import Customer, CustomerType
from job.models import Job
from delivery_order.models import DeliveryOrder
from company.company_model import Company
from service.models import Service
import json
from decimal import Decimal
from xhtml2pdf import pisa
from io import BytesIO

@login_required
def invoice_list(request):
    """Display list of all invoices"""
    invoices = Invoice.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        invoices = invoices.filter(
            Q(invoice_number__icontains=search_query) |
            Q(customer__customer_name__icontains=search_query) |
            Q(shipper__icontains=search_query) |
            Q(consignee__icontains=search_query) |
            Q(jobs__job_code__icontains=search_query)
        ).distinct()
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        invoices = invoices.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(invoices, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': Invoice.STATUS_CHOICES,
    }
    return render(request, 'invoice/invoice_list.html', context)

@login_required
def invoice_create(request):
    """Create a new invoice"""
    if request.method == 'POST':
        
        form = InvoiceForm(request.POST)
        
        if form.is_valid():
            
            try:
                invoice = form.save(commit=False)
                invoice.created_by = request.user
                
                # Handle invoice items JSON data
                invoice_items_data = request.POST.get('invoice_items', '[]')
                try:
                    invoice.invoice_items = json.loads(invoice_items_data)
                except json.JSONDecodeError:
                    invoice.invoice_items = []
                
                invoice.save()
                
                # Handle jobs linking manually since we're using a custom field
                jobs_data = form.cleaned_data.get('jobs')
                if jobs_data:
                    # Convert comma-separated job IDs to actual Job objects
                    job_ids = [jid.strip() for jid in jobs_data if jid.strip()]
                    jobs = Job.objects.filter(id__in=job_ids)
                    invoice.jobs.set(jobs)
                
                # Save many-to-many relationships
                form.save_m2m()
                
                messages.success(request, f'Invoice {invoice.invoice_number} created successfully.')
                return redirect('invoice:invoice_detail', pk=invoice.pk)
            except Exception as e:
                messages.error(request, f'Error creating invoice: {str(e)}')
        else:
            # Print form errors for debugging
            print("Form errors:", form.errors)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = InvoiceForm()
    
    context = {
        'form': form,
        'title': 'Create New Invoice',
    }
    return render(request, 'invoice/invoice_form.html', context)

@login_required
def invoice_detail(request, pk):
    """Display invoice details"""
    invoice = get_object_or_404(Invoice, pk=pk)
    
    # Get payment history for this invoice
    from customer_payments.models import CustomerPaymentInvoice
    payment_history = CustomerPaymentInvoice.objects.filter(invoice=invoice).select_related('payment')
    
    # Calculate total paid and remaining balance
    total_paid = sum(payment.amount_received for payment in payment_history)
    total_discount = sum(payment.discount_amount for payment in payment_history)
    remaining_balance = invoice.total_sale - total_paid - total_discount
    
    context = {
        'invoice': invoice,
        'payment_history': payment_history,
        'total_paid': total_paid,
        'total_discount': total_discount,
        'remaining_balance': remaining_balance,
    }
    return render(request, 'invoice/invoice_detail.html', context)

@login_required
def invoice_edit(request, pk):
    """Edit an existing invoice"""
    invoice = get_object_or_404(Invoice, pk=pk)
    
    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            try:
                invoice = form.save(commit=False)
                invoice.updated_by = request.user
                
                # Handle invoice items JSON data
                invoice_items_data = request.POST.get('invoice_items', '[]')
                try:
                    invoice.invoice_items = json.loads(invoice_items_data)
                except json.JSONDecodeError:
                    invoice.invoice_items = []
                
                invoice.save()
                
                # Handle jobs linking manually since we're using a custom field
                jobs_data = form.cleaned_data.get('jobs')
                if jobs_data:
                    # Convert comma-separated job IDs to actual Job objects
                    job_ids = [jid.strip() for jid in jobs_data if jid.strip()]
                    jobs = Job.objects.filter(id__in=job_ids)
                    invoice.jobs.set(jobs)
                
                # Save many-to-many relationships
                form.save_m2m()
                
                messages.success(request, f'Invoice {invoice.invoice_number} updated successfully.')
                return redirect('invoice:invoice_detail', pk=invoice.pk)
            except Exception as e:
                messages.error(request, f'Error updating invoice: {str(e)}')
                print(f"Error updating invoice: {e}")
        else:
            # Print form errors for debugging
            print("Form errors:", form.errors)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = InvoiceForm(instance=invoice)
    
    context = {
        'form': form,
        'invoice': invoice,
        'title': f'Edit Invoice {invoice.invoice_number}',
    }
    return render(request, 'invoice/invoice_form.html', context)

@login_required
def invoice_delete(request, pk):
    """Delete an invoice"""
    invoice = get_object_or_404(Invoice, pk=pk)
    
    if request.method == 'POST':
        invoice_number = invoice.invoice_number
        invoice.delete()
        messages.success(request, f'Invoice {invoice_number} deleted successfully.')
        return redirect('invoice:invoice_list')
    
    context = {
        'invoice': invoice,
    }
    return render(request, 'invoice/invoice_confirm_delete.html', context)

@login_required
def invoice_print(request, pk):
    """Print invoice as PDF"""
    invoice = get_object_or_404(
        Invoice.objects.select_related('customer', 'payment_source')
        .prefetch_related(
            'jobs',
            'jobs__cargo_items',
            'jobs__cargo_items__item'
        ), 
        pk=pk
    )
    
    # Get company details (assuming first active company)
    try:
        company = Company.objects.filter(is_active=True).first()
    except:
        company = None
    
    # Generate PDF
    html_string = render_to_string('invoice/print/invoice.html', {
        'invoice': invoice,
        'company': company
    })
    
    # Create PDF
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_string.encode("UTF-8")), result)
    
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'
        return response
    
    return HttpResponse('Error generating PDF', status=500)

@login_required
def invoice_cost_sale_print(request, pk):
    """Print invoice cost & sale breakdown as PDF"""
    invoice = get_object_or_404(
        Invoice.objects.select_related('customer', 'payment_source')
        .prefetch_related(
            'jobs',
            'jobs__cargo_items',
            'jobs__cargo_items__item'
        ), 
        pk=pk
    )
    
    # Get company details (assuming first active company)
    try:
        company = Company.objects.filter(is_active=True).first()
    except:
        company = None
    
    # Generate PDF
    html_string = render_to_string('invoice/print/cost_sale.html', {
        'invoice': invoice,
        'company': company
    })
    
    # Create PDF
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_string.encode("UTF-8")), result)
    
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_cost_sale_{invoice.invoice_number}.pdf"'
        return response
    
    return HttpResponse('Error generating PDF', status=500)

@login_required
def invoice_pdf(request, pk):
    """Generate PDF invoice"""
    invoice = get_object_or_404(Invoice, pk=pk)
    
    # Generate PDF using a library like reportlab or weasyprint
    # For now, just return the print template
    context = {
        'invoice': invoice,
    }
    return render(request, 'invoice/print/invoice.html', context)

@login_required
def get_customer_details(request):
    """Get customer details via AJAX"""
    customer_id = request.GET.get('customer_id')
    if customer_id:
        try:
            customer = Customer.objects.get(id=customer_id)
            data = {
                'customer_name': customer.customer_name,
                'address': customer.billing_address,
                'phone': customer.phone,
                'email': customer.email,
            }
            return JsonResponse(data)
        except Customer.DoesNotExist:
            return JsonResponse({'error': 'Customer not found'}, status=404)
    return JsonResponse({'error': 'Customer ID required'}, status=400)

@login_required
def get_customer_jobs(request):
    """Get jobs for a specific customer via AJAX that don't have invoices yet"""
    customer_id = request.GET.get('customer_id')
    if customer_id:
        try:
            customer = Customer.objects.get(id=customer_id)
            
            # Get all job IDs that already have invoices (correct relationship)
            jobs_with_invoices = Invoice.objects.values_list('jobs', flat=True).distinct()
            
            # Get jobs for this customer that don't have invoices yet
            available_jobs = Job.objects.filter(
                customer_name=customer,
                status__is_active=True  # Only active status jobs
            ).exclude(id__in=jobs_with_invoices).order_by('-created_at')
            
            jobs_data = [{
                'id': job.id, 
                'job_code': job.job_code, 
                'description': job.description or job.title or 'No description'
            } for job in available_jobs]
            
            return JsonResponse({'jobs': jobs_data})
        except Customer.DoesNotExist:
            return JsonResponse({'error': 'Customer not found'}, status=404)
    return JsonResponse({'error': 'Customer ID required'}, status=400)

@login_required
def get_job_details(request):
    """Get job details for auto-populating fields via AJAX"""
    job_id = request.GET.get('job_id')
    if job_id:
        try:
            job = Job.objects.get(id=job_id)
            data = {
                'bl_number': job.bl_number or '',
                'shipper': job.bl_shipper or (job.shipper.customer_name if job.shipper else ''),
                'consignee': job.bl_consignee or '',
                'description': job.description or '',
                'job_code': job.job_code,
                'origin': job.port_loading or '',
                'destination': job.port_discharge or '',
            }
            
            # Get container details
            containers = job.containers.all()
            if containers.exists():
                container = containers.first()
                data['ed_number'] = container.ed_number or ''
                data['container_number'] = container.container_number or ''
            
            # Get cargo items names and calculate total quantity
            cargo_items = job.cargo_items.all()
            item_names = []
            total_qty = 0
            
            for cargo in cargo_items:
                if cargo.item and cargo.item.item_name:
                    item_names.append(cargo.item.item_name)
                elif cargo.item_code:
                    item_names.append(cargo.item_code)
                
                # Add quantity to total
                if cargo.quantity:
                    total_qty += float(cargo.quantity)
            
            data['items'] = ', '.join(item_names) if item_names else ''
            data['items_count'] = cargo_items.count()
            data['total_qty'] = total_qty
            
            return JsonResponse(data)
        except Job.DoesNotExist:
            return JsonResponse({'error': 'Job not found'}, status=404)
    return JsonResponse({'error': 'Job ID required'}, status=400)

@login_required
def calculate_totals(request):
    """Calculate invoice totals via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            items = data.get('items', [])
            
            subtotal = Decimal('0.00')
            vat_amount = Decimal('0.00')
            
            for item in items:
                quantity = Decimal(str(item.get('quantity', 0)))
                unit_price = Decimal(str(item.get('unit_price', 0)))
                vat_rate = Decimal(str(item.get('vat_rate', 5)))
                
                amount = quantity * unit_price
                item_vat = amount * (vat_rate / Decimal('100'))
                
                subtotal += amount
                vat_amount += item_vat
            
            total_amount = subtotal + vat_amount
            
            return JsonResponse({
                'subtotal': float(subtotal),
                'vat_amount': float(vat_amount),
                'total_amount': float(total_amount),
            })
        except (json.JSONDecodeError, ValueError) as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'POST method required'}, status=405)

@login_required
def get_services_for_description(request):
    """Get all active services for description dropdown via AJAX"""
    try:
        services = Service.objects.filter(status='active').order_by('service_name')
        services_data = [{
            'id': service.id, 
            'service_name': service.service_name, 
            'service_code': service.service_code,
            'base_price': float(service.base_price),
            'sale_price': float(service.sale_price),
            'cost_price': float(service.cost_price),
            'currency': service.currency,
            'has_vat': service.has_vat
        } for service in services]
        return JsonResponse({'services': services_data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_vendors(request):
    """Get vendors (customers with vendor type) and payment sources for the vendor dropdown in invoice items"""
    try:
        # Get vendors (customers with vendor type)
        vendor_type = CustomerType.objects.get(code='VEN')
        vendors = Customer.objects.filter(customer_types=vendor_type, is_active=True).order_by('customer_name')
        vendors_data = [{
            'id': f'vendor_{vendor.id}', 
            'name': vendor.customer_name, 
            'code': vendor.customer_code,
            'type': 'vendor',
            'display_name': f"{vendor.customer_code} - {vendor.customer_name} (Vendor)"
        } for vendor in vendors]
        
        # Try to get payment sources if available
        payment_sources = []
        try:
            from payment_source.models import PaymentSource
            print("Payment source models imported successfully")
            
            # Get active payment sources
            active_payment_sources = PaymentSource.objects.filter(active=True).order_by('name')
            
            print(f"Found {active_payment_sources.count()} payment sources")
            
            # Add payment sources
            for source in active_payment_sources:
                payment_sources.append({
                    'id': f'payment_source_{source.id}',
                    'name': source.name,
                    'code': source.code or '',
                    'type': 'payment_source',
                    'category': source.category,
                    'display_name': f"{source.name}" + (f" - {source.description}" if source.description else "")
                })
                
        except ImportError as e:
            # Payment source not available, continue with vendors only
            print(f"Payment source not available: {e}")
            pass
        except Exception as e:
            # Log the error but continue with vendors only
            print(f"Error loading payment sources: {e}")
        
        # Combine vendors and payment sources
        all_options = vendors_data + payment_sources
        
        print(f"Returning {len(vendors_data)} vendors and {len(payment_sources)} payment sources")
        print(f"Total options: {len(all_options)}")
        if all_options:
            print(f"First option structure: {all_options[0]}")
        
        # If no options found, return a helpful message
        if not all_options:
            return JsonResponse({
                'vendors': [],
                'vendor_count': 0,
                'payment_source_count': 0,
                'total_count': 0,
                'message': 'No vendors or payment sources found. Please check your data setup.'
            })
        
        return JsonResponse({
            'vendors': all_options,
            'vendor_count': len(vendors_data),
            'payment_source_count': len(payment_sources),
            'total_count': len(all_options)
        })
    except CustomerType.DoesNotExist:
        return JsonResponse({'error': 'Vendor customer type not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def post_invoice_to_ledger(request, invoice_id):
    """Post invoice to ledger with payment source tracking"""
    try:
        invoice = get_object_or_404(Invoice, pk=invoice_id)
        
        # Check if invoice is already posted
        if hasattr(invoice, 'is_posted') and invoice.is_posted:
            return JsonResponse({'error': 'Invoice is already posted to ledger'}, status=400)
        
        # Import required models
        from ledger.models import Ledger
        from chart_of_accounts.models import ChartOfAccount
        from company.company_model import Company
        from fiscal_year.models import FiscalYear
        from payment_source.models import PaymentSource
        
        # Get current company and fiscal year
        company = Company.objects.filter(is_active=True).first()
        if not company:
            return JsonResponse({'error': 'No active company found'}, status=400)
        
        fiscal_year = FiscalYear.objects.filter(is_current=True).first()
        if not fiscal_year:
            return JsonResponse({'error': 'No active fiscal year found'}, status=400)
        
        # Get required accounts
        try:
            # Accounts Receivable account
            ar_account = ChartOfAccount.objects.filter(
                name__icontains='receivable',
                is_active=True,
                company=company
            ).first()
            
            # Revenue account (or default to first revenue account)
            revenue_account = ChartOfAccount.objects.filter(
                account_type__category='REVENUE',
                is_active=True,
                company=company
            ).first()
            
            if not ar_account or not revenue_account:
                return JsonResponse({'error': 'Required chart of accounts not found'}, status=400)
                
        except Exception as e:
            return JsonResponse({'error': f'Error accessing chart of accounts: {str(e)}'}, status=400)
        
        # Create ledger entries
        try:
            # 1. Debit Accounts Receivable
            ar_entry = Ledger.objects.create(
                entry_date=invoice.invoice_date,
                reference=invoice.invoice_number,
                description=f"Invoice {invoice.invoice_number} - {invoice.customer.customer_name}",
                account=ar_account,
                entry_type='DR',
                amount=invoice.total_sale,
                voucher_number=invoice.invoice_number,
                company=company,
                fiscal_year=fiscal_year,
                created_by=request.user,
                updated_by=request.user,
                payment_source=invoice.payment_source,  # Copy payment source from invoice
                status='POSTED'
            )
            
            # 2. Credit Revenue
            revenue_entry = Ledger.objects.create(
                entry_date=invoice.invoice_date,
                reference=invoice.invoice_number,
                description=f"Invoice {invoice.invoice_number} - {invoice.customer.customer_name}",
                account=revenue_account,
                entry_type='CR',
                amount=invoice.total_sale,
                voucher_number=invoice.invoice_number,
                company=company,
                fiscal_year=fiscal_year,
                created_by=request.user,
                updated_by=request.user,
                payment_source=invoice.payment_source,  # Copy payment source from invoice
                status='POSTED'
            )
            
            # 3. Create payment source entries for each invoice item that has a payment source
            from payment_source.models import PaymentSource
            
            if invoice.invoice_items:
                for item in invoice.invoice_items:
                    payment_source_id = item.get('payment_source_id')
                    if payment_source_id:
                        try:
                            payment_source = PaymentSource.objects.get(id=payment_source_id)
                            if payment_source.linked_ledger:
                                item_amount = Decimal(str(item.get('cost_total', 0)))
                                
                                if payment_source.payment_type == 'prepaid' and item_amount > 0:
                                    # Credit the linked account (asset account)
                                    payment_source_entry = Ledger.objects.create(
                                        entry_date=invoice.invoice_date,
                                        reference=invoice.invoice_number,
                                        description=f"Invoice {invoice.invoice_number} - {item.get('description', 'Item')} - {payment_source.name}",
                                        account=payment_source.linked_ledger,
                                        entry_type='CR',
                                        amount=item_amount,
                                        voucher_number=invoice.invoice_number,
                                        company=company,
                                        fiscal_year=fiscal_year,
                                        created_by=request.user,
                                        updated_by=request.user,
                                        payment_source=payment_source,
                                        status='POSTED'
                                    )
                                elif payment_source.payment_type == 'postpaid' and item_amount > 0:
                                    # Debit the linked account (liability account) - we owe the payment source
                                    payment_source_entry = Ledger.objects.create(
                                        entry_date=invoice.invoice_date,
                                        reference=invoice.invoice_number,
                                        description=f"Invoice {invoice.invoice_number} - {item.get('description', 'Item')} - {payment_source.name}",
                                        account=payment_source.linked_ledger,
                                        entry_type='DR',
                                        amount=item_amount,
                                        voucher_number=invoice.invoice_number,
                                        company=company,
                                        fiscal_year=fiscal_year,
                                        created_by=request.user,
                                        updated_by=request.user,
                                        payment_source=payment_source,
                                        status='POSTED'
                                    )
                                    # Credit Accounts Receivable to reduce customer balance
                                    Ledger.objects.create(
                                        entry_date=invoice.invoice_date,
                                        reference=invoice.invoice_number,
                                        description=f"Invoice {invoice.invoice_number} - Payment via {payment_source.name}",
                                        account=ar_account,
                                        entry_type='CR',
                                        amount=item_amount,
                                        voucher_number=invoice.invoice_number,
                                        company=company,
                                        fiscal_year=fiscal_year,
                                        created_by=request.user,
                                        updated_by=request.user,
                                        payment_source=payment_source,
                                        status='POSTED'
                                    )
                                elif payment_source.payment_type == 'cash_bank' and item_amount > 0:
                                    # Debit the linked account (asset account) - cash/bank received
                                    payment_source_entry = Ledger.objects.create(
                                        entry_date=invoice.invoice_date,
                                        reference=invoice.invoice_number,
                                        description=f"Invoice {invoice.invoice_number} - {item.get('description', 'Item')} - {payment_source.name}",
                                        account=payment_source.linked_ledger,
                                        entry_type='DR',
                                        amount=item_amount,
                                        voucher_number=invoice.invoice_number,
                                        company=company,
                                        fiscal_year=fiscal_year,
                                        created_by=request.user,
                                        updated_by=request.user,
                                        payment_source=payment_source,
                                        status='POSTED'
                                    )
                                    # Credit Accounts Receivable to reduce customer balance
                                    Ledger.objects.create(
                                        entry_date=invoice.invoice_date,
                                        reference=invoice.invoice_number,
                                        description=f"Invoice {invoice.invoice_number} - Payment via {payment_source.name}",
                                        account=ar_account,
                                        entry_type='CR',
                                        amount=item_amount,
                                        voucher_number=invoice.invoice_number,
                                        company=company,
                                        fiscal_year=fiscal_year,
                                        created_by=request.user,
                                        updated_by=request.user,
                                        payment_source=payment_source,
                                        status='POSTED'
                                    )
                        except PaymentSource.DoesNotExist:
                            continue  # Skip if payment source not found
                        except Exception as e:
                            continue  # Skip if error creating payment source entry
            
            # Mark invoice as posted
            invoice.is_posted = True
            invoice.save(update_fields=['is_posted'])
            
            # Prepare response data
            ledger_entries = [
                {
                    'id': ar_entry.id,
                    'ledger_number': ar_entry.ledger_number,
                    'entry_type': ar_entry.entry_type,
                    'amount': float(ar_entry.amount),
                    'payment_source': ar_entry.payment_source.name if ar_entry.payment_source else None
                },
                {
                    'id': revenue_entry.id,
                    'ledger_number': revenue_entry.ledger_number,
                    'entry_type': revenue_entry.entry_type,
                    'amount': float(revenue_entry.amount),
                    'payment_source': revenue_entry.payment_source.name if revenue_entry.payment_source else None
                }
            ]
            
            # Add payment source entry if created
            if 'payment_source_entry' in locals() and payment_source_entry:
                ledger_entries.append({
                    'id': payment_source_entry.id,
                    'ledger_number': payment_source_entry.ledger_number,
                    'entry_type': payment_source_entry.entry_type,
                    'amount': float(payment_source_entry.amount),
                    'payment_source': payment_source_entry.payment_source.name if payment_source_entry.payment_source else None
                })
            
            return JsonResponse({
                'success': True,
                'message': f'Invoice {invoice.invoice_number} posted to ledger successfully',
                'ledger_entries': ledger_entries
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Error creating ledger entries: {str(e)}'}, status=500)
            
    except Invoice.DoesNotExist:
        return JsonResponse({'error': 'Invoice not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Error posting invoice: {str(e)}'}, status=500)
