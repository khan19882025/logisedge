from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings
import json
import weasyprint
from io import BytesIO

from .models import CrossStuffing, CrossStuffingCargo, CrossStuffingSummary
from .forms import CrossStuffingForm
from job.models import Job, JobCargo
from customer.models import Customer
from company.company_model import Company


@login_required
def crossstuffing_list(request):
    """Display list of cross stuffing operations with search and filtering"""
    crossstuffings = CrossStuffing.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        crossstuffings = crossstuffings.filter(
            Q(cs_number__icontains=search_query) |
            Q(title__icontains=search_query) |
            Q(customer__customer_name__icontains=search_query) |
            Q(container_number__icontains=search_query) |
            Q(job__job_code__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        crossstuffings = crossstuffings.filter(status=status_filter)
    
    # Filter by priority
    priority_filter = request.GET.get('priority', '')
    if priority_filter:
        crossstuffings = crossstuffings.filter(priority=priority_filter)
    
    # Filter by facility
    facility_filter = request.GET.get('facility', '')
    if facility_filter:
        crossstuffings = crossstuffings.filter(facility_id=facility_filter)
    
    # Sort by
    sort_by = request.GET.get('sort', '-created_at')
    crossstuffings = crossstuffings.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(crossstuffings, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'facility_filter': facility_filter,
        'sort_by': sort_by,
        'status_choices': CrossStuffing.CROSS_STUFFING_STATUS,
        'priority_choices': CrossStuffing._meta.get_field('priority').choices,
    }
    
    return render(request, 'crossstuffing/crossstuffing_list.html', context)


def save_cargo_items(crossstuffing, cargo_data):
    """Helper function to save cargo items for a crossstuffing operation"""
    if not cargo_data:
        return
    
    try:
        # Clear existing cargo items
        crossstuffing.cargo_items.all().delete()
        
        # Parse cargo data
        cargo_items = json.loads(cargo_data)
        
        # Create new cargo items
        for cargo_item in cargo_items:
            job_cargo_id = cargo_item.get('job_cargo_id')
            if job_cargo_id:
                try:
                    job_cargo = JobCargo.objects.get(id=job_cargo_id)
                    CrossStuffingCargo.objects.create(
                        crossstuffing=crossstuffing,
                        job_cargo=job_cargo,
                        quantity=cargo_item.get('quantity'),
                        rate=cargo_item.get('rate'),
                        amount=cargo_item.get('amount'),
                        net_weight=cargo_item.get('net_weight'),
                        gross_weight=cargo_item.get('gross_weight'),
                        ed_number=cargo_item.get('ed'),
                        remark=cargo_item.get('remark', '')
                    )
                except JobCargo.DoesNotExist:
                    continue
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error saving cargo items: {e}")


def save_cs_summary(crossstuffing, summary_data):
    """Helper function to save CS Summary data for a crossstuffing operation"""
    if not summary_data:
        return
    
    try:
        # Clear existing summary items
        crossstuffing.summary_items.all().delete()
        
        # Parse summary data
        summary_items = json.loads(summary_data)
        
        # Create new summary items
        for summary_item in summary_items:
            CrossStuffingSummary.objects.create(
                crossstuffing=crossstuffing,
                job_no=summary_item.get('job_no', ''),
                items=summary_item.get('items', ''),
                qty=summary_item.get('qty'),
                imp_cntr=summary_item.get('imp_cntr', ''),
                size=summary_item.get('size', ''),
                seal=summary_item.get('seal', ''),
                exp_cntr=summary_item.get('exp_cntr', ''),
                exp_size=summary_item.get('exp_size', ''),
                exp_seal=summary_item.get('exp_seal', ''),
                remarks=summary_item.get('remarks', '')
            )
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error saving CS summary: {e}")


@login_required
def crossstuffing_create(request):
    """Create a new cross stuffing operation"""
    if request.method == 'POST':
        form = CrossStuffingForm(request.POST)
        
        if form.is_valid():
            crossstuffing = form.save(commit=False)
            crossstuffing.created_by = request.user
            crossstuffing.save()
            
            # Save cargo items
            cargo_data = request.POST.get('selected_cargo_items')
            save_cargo_items(crossstuffing, cargo_data)
            
            # Save CS Summary data
            summary_data = request.POST.get('cs_summary_data')
            save_cs_summary(crossstuffing, summary_data)
            
            messages.success(request, f'Cross stuffing {crossstuffing.cs_number} created successfully.')
            return redirect('crossstuffing:crossstuffing_detail', pk=crossstuffing.pk)
    else:
        form = CrossStuffingForm()
    
    context = {
        'form': form,
        'title': 'Create New Cross Stuffing',
        'submit_text': 'Create Cross Stuffing',
        'existing_summary_items': [],  # Empty list for new records
    }
    
    return render(request, 'crossstuffing/crossstuffing_form.html', context)


@login_required
def crossstuffing_update(request, pk):
    """Update an existing cross stuffing operation"""
    crossstuffing = get_object_or_404(CrossStuffing, pk=pk)
    
    if request.method == 'POST':
        form = CrossStuffingForm(request.POST, instance=crossstuffing)
        
        if form.is_valid():
            form.save()
            
            # Save cargo items
            cargo_data = request.POST.get('selected_cargo_items')
            save_cargo_items(crossstuffing, cargo_data)
            
            # Save CS Summary data
            summary_data = request.POST.get('cs_summary_data')
            save_cs_summary(crossstuffing, summary_data)
            
            messages.success(request, f'Cross stuffing {crossstuffing.cs_number} updated successfully.')
            return redirect('crossstuffing:crossstuffing_detail', pk=crossstuffing.pk)
    else:
        form = CrossStuffingForm(instance=crossstuffing)
    
    # Get existing cargo items for this crossstuffing
    existing_cargo_items = []
    for cargo_item in crossstuffing.cargo_items.all():
        existing_cargo_items.append({
            "job_cargo_id": cargo_item.job_cargo.id,
            "job_code": cargo_item.job_cargo.job.job_code,
            "item_code": cargo_item.job_cargo.item.item_code if cargo_item.job_cargo.item else cargo_item.job_cargo.item_code,
            "item_name": cargo_item.job_cargo.item.item_name if cargo_item.job_cargo.item else "",
            "hs_code": cargo_item.job_cargo.hs_code,
            "unit": cargo_item.job_cargo.unit,
            "quantity": str(cargo_item.quantity) if cargo_item.quantity else "",
            "coo": cargo_item.job_cargo.coo,
            "net_weight": str(cargo_item.net_weight) if cargo_item.net_weight else "",
            "gross_weight": str(cargo_item.gross_weight) if cargo_item.gross_weight else "",
            "rate": str(cargo_item.rate) if cargo_item.rate else "",
            "amount": str(cargo_item.amount) if cargo_item.amount else "",
            "ed": cargo_item.ed_number if cargo_item.ed_number else "",
            "remark": cargo_item.remark if cargo_item.remark else "",
        })
    
    # Get existing CS Summary items for this crossstuffing
    existing_summary_items = []
    for summary_item in crossstuffing.summary_items.all():
        existing_summary_items.append({
            "job_no": summary_item.job_no,
            "items": summary_item.items,
            "qty": str(summary_item.qty) if summary_item.qty else "",
            "imp_cntr": summary_item.imp_cntr,
            "size": summary_item.size,
            "seal": summary_item.seal,
            "exp_cntr": summary_item.exp_cntr,
            "exp_size": summary_item.exp_size,
            "exp_seal": summary_item.exp_seal,
            "remarks": summary_item.remarks,
        })
    
    context = {
        'form': form,
        'crossstuffing': crossstuffing,
        'existing_cargo_items': existing_cargo_items,
        'existing_summary_items': existing_summary_items,
        'title': f'Edit Cross Stuffing {crossstuffing.cs_number}',
        'submit_text': 'Update Cross Stuffing',
    }
    
    return render(request, 'crossstuffing/crossstuffing_form.html', context)


@login_required
def crossstuffing_detail(request, pk):
    """Display cross stuffing details"""
    crossstuffing = get_object_or_404(CrossStuffing, pk=pk)
    
    context = {
        'crossstuffing': crossstuffing,
    }
    
    return render(request, 'crossstuffing/crossstuffing_detail.html', context)


@login_required
def crossstuffing_delete(request, pk):
    """Delete a cross stuffing operation"""
    crossstuffing = get_object_or_404(CrossStuffing, pk=pk)
    
    if request.method == 'POST':
        cs_number = crossstuffing.cs_number
        crossstuffing.delete()
        messages.success(request, f'Cross stuffing {cs_number} deleted successfully.')
        return redirect('crossstuffing:crossstuffing_list')
    
    context = {
        'crossstuffing': crossstuffing,
    }
    
    return render(request, 'crossstuffing/crossstuffing_confirm_delete.html', context)


@login_required
def crossstuffing_status_update(request, pk):
    """Update cross stuffing status via AJAX"""
    if request.method == 'POST' and request.is_ajax():
        crossstuffing = get_object_or_404(CrossStuffing, pk=pk)
        new_status = request.POST.get('status')
        
        if new_status in dict(CrossStuffing.CROSS_STUFFING_STATUS):
            crossstuffing.status = new_status
            if new_status == 'completed':
                crossstuffing.complete()
            else:
                crossstuffing.save()
            return JsonResponse({'success': True, 'status': new_status})
    
    return JsonResponse({'success': False})


@login_required
def crossstuffing_quick_view(request, pk):
    """Quick view of cross stuffing details"""
    crossstuffing = get_object_or_404(CrossStuffing, pk=pk)
    
    context = {
        'crossstuffing': crossstuffing,
    }
    
    return render(request, 'crossstuffing/crossstuffing_quick_view.html', context)


@login_required
def crossstuffing_duplicate(request, pk):
    """Duplicate an existing cross stuffing operation"""
    original_cs = get_object_or_404(CrossStuffing, pk=pk)
    
    # Create new cross stuffing with same data
    crossstuffing = CrossStuffing.objects.create(
        title=f"Copy of {original_cs.title}",
        description=original_cs.description,
        job=original_cs.job,
        customer=original_cs.customer,
        facility=original_cs.facility,
        scheduled_date=original_cs.scheduled_date,
        priority=original_cs.priority,
        status='pending',
        container_number=original_cs.container_number,
        container_size=original_cs.container_size,
        container_type=original_cs.container_type,
        cargo_description=original_cs.cargo_description,
        total_packages=original_cs.total_packages,
        total_weight=original_cs.total_weight,
        total_volume=original_cs.total_volume,
        charges=original_cs.charges,
        currency=original_cs.currency,
        notes=original_cs.notes,
        special_instructions=original_cs.special_instructions,
        created_by=request.user,
    )
    
    messages.success(request, f'Cross stuffing {crossstuffing.cs_number} duplicated successfully.')
    return redirect('crossstuffing:crossstuffing_detail', pk=crossstuffing.pk)


@login_required
def get_customer_cargo_items(request, customer_id):
    print(f"DEBUG: get_customer_cargo_items called with customer_id: {customer_id}")
    print(f"DEBUG: Request method: {request.method}")
    print(f"DEBUG: Request user: {request.user}")
    print(f"DEBUG: Request headers: {dict(request.headers)}")
    
    try:
        # Get jobs for this customer with Cross Stuffing type
        jobs = Job.objects.filter(customer_name_id=customer_id, job_type="Cross Stuffing")
        print(f"DEBUG: Found {jobs.count()} jobs for customer {customer_id}")
        
        # Get cargo items for these jobs
        cargo_items = JobCargo.objects.filter(job__in=jobs)
        print(f"DEBUG: Found {cargo_items.count()} cargo items")
        
        # Debug: Print job details
        for job in jobs:
            print(f"DEBUG: Job {job.job_code} - Type: {job.job_type} - Customer: {job.customer_name}")
        
        # Debug: Print cargo details
        for cargo in cargo_items:
            print(f"DEBUG: Cargo for job {cargo.job.job_code} - Item: {cargo.item_code}")
            # Check containers for this job
            containers = cargo.job.containers.all()
            print(f"DEBUG: Job {cargo.job.job_code} has {containers.count()} containers")
            for container in containers:
                print(f"DEBUG: Container ED: '{container.ed_number}'")
        
        data = []
        for cargo in cargo_items:
            # Calculate how much of this cargo has already been used in crossstuffing
            used_quantity = CrossStuffingCargo.objects.filter(
                job_cargo=cargo
            ).aggregate(
                total_used=Sum('quantity')
            )['total_used'] or 0
            
            # Calculate remaining balance
            original_quantity = cargo.quantity or 0
            remaining_quantity = original_quantity - used_quantity
            
            # Only include cargo items that have remaining quantity
            if remaining_quantity > 0:
                # Calculate proportional weights and amounts for remaining quantity
                remaining_ratio = remaining_quantity / original_quantity if original_quantity > 0 else 0
                
                remaining_net_weight = None
                remaining_gross_weight = None
                remaining_amount = None
                
                if cargo.net_weight:
                    remaining_net_weight = cargo.net_weight * remaining_ratio
                if cargo.gross_weight:
                    remaining_gross_weight = cargo.gross_weight * remaining_ratio
                if cargo.amount:
                    remaining_amount = cargo.amount * remaining_ratio
                
                data.append({
                    "job_cargo_id": cargo.id,
                    "job_code": cargo.job.job_code,
                    "item_code": cargo.item.item_code if cargo.item else cargo.item_code,
                    "item_name": cargo.item.item_name if cargo.item else "",
                    "hs_code": cargo.hs_code,
                    "unit": cargo.unit,
                    "quantity": str(remaining_quantity),  # Show remaining quantity instead of original
                    "original_quantity": str(original_quantity),  # Keep original for reference
                    "used_quantity": str(used_quantity),  # How much already used
                    "coo": cargo.coo,
                    "net_weight": str(remaining_net_weight) if remaining_net_weight else "",
                    "gross_weight": str(remaining_gross_weight) if remaining_gross_weight else "",
                    "rate": str(cargo.rate) if cargo.rate else "",
                    "amount": str(remaining_amount) if remaining_amount else "",
                    "ed": cargo.job.containers.first().ed_number if cargo.job.containers.exists() else "",
                    "remark": cargo.remark,
                })
        
        # Debug: Print ED data
        for item in data:
            print(f"DEBUG: Job {item['job_code']} - ED: '{item['ed']}' - Available Qty: {item['quantity']} (Original: {item['original_quantity']}, Used: {item['used_quantity']})")
        
        print(f"DEBUG: Returning {len(data)} items")
        print(f"DEBUG: Data: {data}")
        return JsonResponse({"items": data})
        
    except Exception as e:
        print(f"DEBUG: Error in get_customer_cargo_items: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({"items": [], "error": str(e)})


@login_required
def test_crossstuffing_jobs(request):
    """Test view to check cross stuffing jobs"""
    jobs = Job.objects.filter(job_type="Cross Stuffing")
    return JsonResponse({
        'jobs': list(jobs.values('id', 'job_code', 'customer_name__customer_name'))
    })


# Print Views
@login_required
def crossstuffing_print_invoice(request, pk):
    """Print invoice as PDF"""
    try:
        crossstuffing = get_object_or_404(CrossStuffing, pk=pk)
        company = Company.objects.filter(is_active=True).first()
        
        html = render_to_string('crossstuffing/print/invoice.html', {
            'crossstuffing': crossstuffing,
            'company': company,
            'cargo_items': crossstuffing.cargo_items.all(),
            'summary_items': crossstuffing.summary_items.all()
        })
        
        # Generate PDF
        pdf = weasyprint.HTML(string=html).write_pdf()
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Invoice_{crossstuffing.cs_number}.pdf"'
        return response
    except Exception as e:
        messages.error(request, f'Error generating PDF: {str(e)}')
        return redirect('crossstuffing:crossstuffing_detail', pk=pk)


@login_required
def crossstuffing_print_packing_list(request, pk):
    """Print packing list as PDF"""
    try:
        crossstuffing = get_object_or_404(CrossStuffing, pk=pk)
        company = Company.objects.filter(is_active=True).first()
        
        html = render_to_string('crossstuffing/print/packing_list.html', {
            'crossstuffing': crossstuffing,
            'company': company,
            'cargo_items': crossstuffing.cargo_items.all(),
            'summary_items': crossstuffing.summary_items.all()
        })
        
        # Generate PDF
        pdf = weasyprint.HTML(string=html).write_pdf()
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="PackingList_{crossstuffing.cs_number}.pdf"'
        return response
    except Exception as e:
        messages.error(request, f'Error generating PDF: {str(e)}')
        return redirect('crossstuffing:crossstuffing_detail', pk=pk)


@login_required
def crossstuffing_print_da(request, pk):
    """Print DA (Delivery Authorization) as PDF"""
    try:
        crossstuffing = get_object_or_404(CrossStuffing, pk=pk)
        company = Company.objects.filter(is_active=True).first()
        
        html = render_to_string('crossstuffing/print/da.html', {
            'crossstuffing': crossstuffing,
            'company': company,
            'cargo_items': crossstuffing.cargo_items.all(),
            'summary_items': crossstuffing.summary_items.all()
        })
        
        # Generate PDF
        pdf = weasyprint.HTML(string=html).write_pdf()
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="DA_{crossstuffing.cs_number}.pdf"'
        return response
    except Exception as e:
        messages.error(request, f'Error generating PDF: {str(e)}')
        return redirect('crossstuffing:crossstuffing_detail', pk=pk)


@login_required
def crossstuffing_print_cs_summary(request, pk):
    """Print CS Summary as PDF"""
    try:
        crossstuffing = get_object_or_404(CrossStuffing, pk=pk)
        company = Company.objects.filter(is_active=True).first()
        
        html = render_to_string('crossstuffing/print/cs_summary.html', {
            'crossstuffing': crossstuffing,
            'company': company,
            'cargo_items': crossstuffing.cargo_items.all(),
            'summary_items': crossstuffing.summary_items.all()
        })
        
        # Generate PDF
        pdf = weasyprint.HTML(string=html).write_pdf()
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="CS_Summary_{crossstuffing.cs_number}.pdf"'
        return response
    except Exception as e:
        messages.error(request, f'Error generating PDF: {str(e)}')
        return redirect('crossstuffing:crossstuffing_detail', pk=pk)


# Email Views
@login_required
def crossstuffing_email_invoice(request, pk):
    """Email invoice as PDF attachment"""
    try:
        crossstuffing = get_object_or_404(CrossStuffing, pk=pk)
        company = Company.objects.filter(is_active=True).first()
        
        # Generate PDF
        html = render_to_string('crossstuffing/print/invoice.html', {
            'crossstuffing': crossstuffing,
            'company': company,
            'cargo_items': crossstuffing.cargo_items.all(),
            'summary_items': crossstuffing.summary_items.all()
        })
        pdf = weasyprint.HTML(string=html).write_pdf()
        
        # Create email
        subject = f'Invoice - {crossstuffing.cs_number}'
        message = f'Please find attached the invoice for cross stuffing {crossstuffing.cs_number}.'
        
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[crossstuffing.customer.email] if crossstuffing.customer and crossstuffing.customer.email else [settings.DEFAULT_FROM_EMAIL]
        )
        
        email.attach(f'Invoice_{crossstuffing.cs_number}.pdf', pdf, 'application/pdf')
        email.send()
        
        messages.success(request, f'Invoice for {crossstuffing.cs_number} has been sent via email.')
        return redirect('crossstuffing:crossstuffing_detail', pk=pk)
    except Exception as e:
        messages.error(request, f'Error sending email: {str(e)}')
        return redirect('crossstuffing:crossstuffing_detail', pk=pk)


@login_required
def crossstuffing_email_packing_list(request, pk):
    """Email packing list as PDF attachment"""
    try:
        crossstuffing = get_object_or_404(CrossStuffing, pk=pk)
        company = Company.objects.filter(is_active=True).first()
        
        # Generate PDF
        html = render_to_string('crossstuffing/print/packing_list.html', {
            'crossstuffing': crossstuffing,
            'company': company,
            'cargo_items': crossstuffing.cargo_items.all(),
            'summary_items': crossstuffing.summary_items.all()
        })
        pdf = weasyprint.HTML(string=html).write_pdf()
        
        # Create email
        subject = f'Packing List - {crossstuffing.cs_number}'
        message = f'Please find attached the packing list for cross stuffing {crossstuffing.cs_number}.'
        
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[crossstuffing.customer.email] if crossstuffing.customer and crossstuffing.customer.email else [settings.DEFAULT_FROM_EMAIL]
        )
        
        email.attach(f'PackingList_{crossstuffing.cs_number}.pdf', pdf, 'application/pdf')
        email.send()
        
        messages.success(request, f'Packing list for {crossstuffing.cs_number} has been sent via email.')
        return redirect('crossstuffing:crossstuffing_detail', pk=pk)
    except Exception as e:
        messages.error(request, f'Error sending email: {str(e)}')
        return redirect('crossstuffing:crossstuffing_detail', pk=pk)


@login_required
def crossstuffing_email_da(request, pk):
    """Email DA (Delivery Authorization) as PDF attachment"""
    try:
        crossstuffing = get_object_or_404(CrossStuffing, pk=pk)
        company = Company.objects.filter(is_active=True).first()
        
        # Generate PDF
        html = render_to_string('crossstuffing/print/da.html', {
            'crossstuffing': crossstuffing,
            'company': company,
            'cargo_items': crossstuffing.cargo_items.all(),
            'summary_items': crossstuffing.summary_items.all()
        })
        pdf = weasyprint.HTML(string=html).write_pdf()
        
        # Create email
        subject = f'Delivery Authorization - {crossstuffing.cs_number}'
        message = f'Please find attached the delivery authorization for cross stuffing {crossstuffing.cs_number}.'
        
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[crossstuffing.customer.email] if crossstuffing.customer and crossstuffing.customer.email else [settings.DEFAULT_FROM_EMAIL]
        )
        
        email.attach(f'DA_{crossstuffing.cs_number}.pdf', pdf, 'application/pdf')
        email.send()
        
        messages.success(request, f'Delivery Authorization for {crossstuffing.cs_number} has been sent via email.')
        return redirect('crossstuffing:crossstuffing_detail', pk=pk)
    except Exception as e:
        messages.error(request, f'Error sending email: {str(e)}')
        return redirect('crossstuffing:crossstuffing_detail', pk=pk)


@login_required
def crossstuffing_email_cs_summary(request, pk):
    """Email CS Summary as PDF attachment"""
    try:
        crossstuffing = get_object_or_404(CrossStuffing, pk=pk)
        company = Company.objects.filter(is_active=True).first()
        
        # Generate PDF
        html = render_to_string('crossstuffing/print/cs_summary.html', {
            'crossstuffing': crossstuffing,
            'company': company,
            'cargo_items': crossstuffing.cargo_items.all(),
            'summary_items': crossstuffing.summary_items.all()
        })
        pdf = weasyprint.HTML(string=html).write_pdf()
        
        # Create email
        subject = f'CS Summary - {crossstuffing.cs_number}'
        message = f'Please find attached the CS Summary for cross stuffing {crossstuffing.cs_number}.'
        
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[crossstuffing.customer.email] if crossstuffing.customer and crossstuffing.customer.email else [settings.DEFAULT_FROM_EMAIL]
        )
        
        email.attach(f'CS_Summary_{crossstuffing.cs_number}.pdf', pdf, 'application/pdf')
        email.send()
        
        messages.success(request, f'CS Summary for {crossstuffing.cs_number} has been sent via email.')
        return redirect('crossstuffing:crossstuffing_detail', pk=pk)
    except Exception as e:
        messages.error(request, f'Error sending email: {str(e)}')
        return redirect('crossstuffing:crossstuffing_detail', pk=pk) 