from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.template.loader import render_to_string
from django.conf import settings
import weasyprint

from .models import Quotation, QuotationItem
from .forms import QuotationForm, QuotationItemFormSet
from company.company_model import Company


@login_required
def quotation_list(request):
    """Display list of quotations with search and filtering"""
    quotations = Quotation.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        quotations = quotations.filter(
            Q(quotation_number__icontains=search_query) |
            Q(customer__name__icontains=search_query) |
            Q(subject__icontains=search_query) |
            Q(salesman__name__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        quotations = quotations.filter(status=status_filter)
    
    # Sort by
    sort_by = request.GET.get('sort', '-created_at')
    quotations = quotations.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(quotations, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'sort_by': sort_by,
        'status_choices': Quotation.QUOTATION_STATUS,
    }
    
    return render(request, 'quotation/quotation_list.html', context)


@login_required
def quotation_create(request):
    """Create a new quotation"""
    if request.method == 'POST':
        form = QuotationForm(request.POST)
        formset = QuotationItemFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            quotation = form.save(commit=False)
            quotation.created_by = request.user
            quotation.save()
            
            # Save formset with the saved quotation instance
            formset.instance = quotation
            instances = formset.save(commit=False)
            
            # Debug: Print all POST data related to VAT
            print("=== VAT Debug Info ===")
            for key, value in request.POST.items():
                if 'vat_enabled' in key:
                    print(f"{key}: {value}")
            print("=====================")
            
            # Process VAT checkbox data
            for i, instance in enumerate(instances):
                # Check if VAT checkbox is checked (checkbox sends 'true' if checked, nothing if unchecked)
                vat_field_name = f'quotation_items-{i}-vat_enabled'
                vat_enabled = vat_field_name in request.POST and request.POST.get(vat_field_name) == 'true'
                print(f"Item {i}: VAT field '{vat_field_name}' present: {vat_field_name in request.POST}, value: {request.POST.get(vat_field_name)}, enabled: {vat_enabled}")
                instance.vat_applied = vat_enabled
                instance.save()
            
            # Calculate totals after all items are saved
            quotation.calculate_totals()
            quotation.save(update_fields=['subtotal', 'vat_amount', 'additional_tax_amount', 'total_amount', 'tax_amount'])
            
            messages.success(request, f'Quotation {quotation.quotation_number} created successfully.')
            return redirect('quotation:quotation_detail', pk=quotation.pk)
    else:
        form = QuotationForm()
        formset = QuotationItemFormSet()
    
    context = {
        'form': form,
        'formset': formset,
        'title': 'Create New Quotation',
        'submit_text': 'Create Quotation',
    }
    
    return render(request, 'quotation/quotation_form.html', context)


@login_required
def quotation_update(request, pk):
    """Update an existing quotation"""
    quotation = get_object_or_404(Quotation, pk=pk)
    
    if request.method == 'POST':
        form = QuotationForm(request.POST, instance=quotation)
        formset = QuotationItemFormSet(request.POST, instance=quotation)
        
        if form.is_valid() and formset.is_valid():
            form.save()
            instances = formset.save(commit=False)
            
            # Process VAT checkbox data
            for i, instance in enumerate(instances):
                # Check if VAT checkbox is checked (checkbox sends 'true' if checked, nothing if unchecked)
                vat_field_name = f'quotation_items-{i}-vat_enabled'
                vat_enabled = vat_field_name in request.POST and request.POST.get(vat_field_name) == 'true'
                print(f"Item {i}: VAT field '{vat_field_name}' present: {vat_field_name in request.POST}, value: {request.POST.get(vat_field_name)}, enabled: {vat_enabled}")
                instance.vat_applied = vat_enabled
                instance.save()
            
            # Calculate totals after all items are saved
            quotation.calculate_totals()
            quotation.save(update_fields=['subtotal', 'vat_amount', 'additional_tax_amount', 'total_amount', 'tax_amount'])
            
            messages.success(request, f'Quotation {quotation.quotation_number} updated successfully.')
            return redirect('quotation:quotation_detail', pk=quotation.pk)
    else:
        form = QuotationForm(instance=quotation)
        formset = QuotationItemFormSet(instance=quotation)
    
    context = {
        'form': form,
        'formset': formset,
        'quotation': quotation,
        'title': f'Edit Quotation {quotation.quotation_number}',
        'submit_text': 'Update Quotation',
    }
    
    return render(request, 'quotation/quotation_form.html', context)


@login_required
def quotation_detail(request, pk):
    """Display quotation details"""
    quotation = get_object_or_404(Quotation, pk=pk)
    
    context = {
        'quotation': quotation,
        'items': quotation.quotation_items.all(),
    }
    
    return render(request, 'quotation/quotation_detail.html', context)


@login_required
def quotation_delete(request, pk):
    """Delete a quotation"""
    quotation = get_object_or_404(Quotation, pk=pk)
    
    if request.method == 'POST':
        quotation_number = quotation.quotation_number
        quotation.delete()
        messages.success(request, f'Quotation {quotation_number} deleted successfully.')
        return redirect('quotation:quotation_list')
    
    context = {
        'quotation': quotation,
    }
    
    return render(request, 'quotation/quotation_confirm_delete.html', context)


@login_required
def quotation_status_update(request, pk):
    """Update quotation status via AJAX"""
    if request.method == 'POST' and request.is_ajax():
        quotation = get_object_or_404(Quotation, pk=pk)
        new_status = request.POST.get('status')
        
        if new_status in dict(Quotation.QUOTATION_STATUS):
            quotation.status = new_status
            quotation.save()
            return JsonResponse({'success': True, 'status': new_status})
    
    return JsonResponse({'success': False})


@login_required
def quotation_duplicate(request, pk):
    """Duplicate an existing quotation"""
    original_quotation = get_object_or_404(Quotation, pk=pk)
    
    # Create new quotation with same data
    quotation = Quotation.objects.create(
        customer=original_quotation.customer,
        facility=original_quotation.facility,
        salesman=original_quotation.salesman,
        subject=f"Copy of {original_quotation.subject}",
        description=original_quotation.description,
        valid_until=original_quotation.valid_until,
        tax_amount=original_quotation.tax_amount,
        discount_amount=original_quotation.discount_amount,
        currency=original_quotation.currency,
        terms_conditions=original_quotation.terms_conditions,
        notes=original_quotation.notes,
        status='draft',
        created_by=request.user,
    )
    
    # Copy quotation items
    for item in original_quotation.quotation_items.all():
        QuotationItem.objects.create(
            quotation=quotation,
            service=item.service,
            description=item.description,
            quantity=item.quantity,
            unit_price=item.unit_price,
            notes=item.notes,
        )
    
    messages.success(request, f'Quotation {quotation.quotation_number} created as a copy.')
    return redirect('quotation:quotation_detail', pk=quotation.pk)


@login_required
def print_quotation(request, pk):
    """Generate and return a PDF for a quotation"""
    quotation = get_object_or_404(Quotation, pk=pk)
    
    # Get company information
    company = Company.objects.filter(is_active=True).first()
    
    # Generate HTML content for the PDF
    html_content = render_to_string('quotation/quotation_pdf.html', {
        'quotation': quotation,
        'company': company
    })
    
    # Generate PDF from HTML content
    pdf_content = weasyprint.HTML(string=html_content).write_pdf()
    
    # Return PDF as HttpResponse
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="quotation_{quotation.quotation_number}.pdf"'
    return response
