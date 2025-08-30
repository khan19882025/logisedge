from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from django.urls import reverse
import json
from datetime import datetime, date
from decimal import Decimal

from .models import ReceiptVoucher, ReceiptVoucherAttachment, ReceiptVoucherAudit
from .forms import (
    ReceiptVoucherForm, ReceiptVoucherAttachmentForm, 
    ReceiptVoucherSearchForm, ReceiptVoucherApprovalForm,
    ReceiptVoucherMarkReceivedForm
)
from customer.models import Customer, CustomerType
from salesman.models import Salesman
from chart_of_accounts.models import ChartOfAccount
from multi_currency.models import Currency


@login_required
def receipt_voucher_list(request):
    """List all receipt vouchers with search and filtering"""
    
    # Get search form
    search_form = ReceiptVoucherSearchForm(request.GET)
    
    # Get all vouchers
    vouchers = ReceiptVoucher.objects.select_related(
        'currency', 'account_to_credit', 'created_by', 'approved_by'
    ).prefetch_related('attachments')
    
    # Apply search filters
    if search_form.is_valid():
        search_field = search_form.cleaned_data.get('search_field')
        search_query = search_form.cleaned_data.get('search_query')
        status = search_form.cleaned_data.get('status')
        receipt_mode = search_form.cleaned_data.get('receipt_mode')
        payer_type = search_form.cleaned_data.get('payer_type')
        currency = search_form.cleaned_data.get('currency')
        date_from = search_form.cleaned_data.get('date_from')
        date_to = search_form.cleaned_data.get('date_to')
        amount_min = search_form.cleaned_data.get('amount_min')
        amount_max = search_form.cleaned_data.get('amount_max')
        
        # Apply search query
        if search_query:
            if search_field == 'voucher_number':
                vouchers = vouchers.filter(voucher_number__icontains=search_query)
            elif search_field == 'payer_name':
                vouchers = vouchers.filter(payer_name__icontains=search_query)
            elif search_field == 'description':
                vouchers = vouchers.filter(description__icontains=search_query)
            elif search_field == 'reference_number':
                vouchers = vouchers.filter(reference_number__icontains=search_query)
        
        # Apply filters
        if status:
            vouchers = vouchers.filter(status=status)
        if receipt_mode:
            vouchers = vouchers.filter(receipt_mode=receipt_mode)
        if payer_type:
            vouchers = vouchers.filter(payer_type=payer_type)
        if currency:
            vouchers = vouchers.filter(currency=currency)
        if date_from:
            vouchers = vouchers.filter(voucher_date__gte=date_from)
        if date_to:
            vouchers = vouchers.filter(voucher_date__lte=date_to)
        if amount_min:
            vouchers = vouchers.filter(amount__gte=amount_min)
        if amount_max:
            vouchers = vouchers.filter(amount__lte=amount_max)
    
    # Pagination
    paginator = Paginator(vouchers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Summary statistics
    total_vouchers = vouchers.count()
    total_amount = vouchers.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    draft_count = vouchers.filter(status='draft').count()
    approved_count = vouchers.filter(status='approved').count()
    received_count = vouchers.filter(status='received').count()
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_vouchers': total_vouchers,
        'total_amount': total_amount,
        'draft_count': draft_count,
        'approved_count': approved_count,
        'received_count': received_count,
    }
    
    return render(request, 'receipt_voucher/receipt_voucher_list.html', context)


@login_required
def receipt_voucher_create(request):
    """Create a new receipt voucher"""
    
    if request.method == 'POST':
        form = ReceiptVoucherForm(request.POST)
        if form.is_valid():
            voucher = form.save(commit=False)
            voucher.created_by = request.user
            voucher.save()
            
            # Create audit trail
            ReceiptVoucherAudit.objects.create(
                voucher=voucher,
                action='created',
                description=f'Receipt voucher created by {request.user.get_full_name()}',
                user=request.user
            )
            
            messages.success(request, f'Receipt voucher {voucher.voucher_number} created successfully.')
            return redirect('receipt_voucher:receipt_voucher_detail', pk=voucher.pk)
    else:
        form = ReceiptVoucherForm()
    
    context = {
        'form': form,
        'title': 'Create Receipt Voucher',
        'submit_text': 'Create Voucher',
    }
    
    return render(request, 'receipt_voucher/receipt_voucher_form.html', context)


@login_required
def receipt_voucher_edit(request, pk):
    """Edit an existing receipt voucher"""
    
    voucher = get_object_or_404(ReceiptVoucher, pk=pk)
    
    # Check if voucher can be edited
    if voucher.status not in ['draft']:
        messages.error(request, 'Only draft vouchers can be edited.')
        return redirect('receipt_voucher:receipt_voucher_detail', pk=voucher.pk)
    
    if request.method == 'POST':
        form = ReceiptVoucherForm(request.POST, instance=voucher)
        if form.is_valid():
            voucher = form.save(commit=False)
            voucher.updated_by = request.user
            voucher.save()
            
            # Create audit trail
            ReceiptVoucherAudit.objects.create(
                voucher=voucher,
                action='updated',
                description=f'Receipt voucher updated by {request.user.get_full_name()}',
                user=request.user
            )
            
            messages.success(request, f'Receipt voucher {voucher.voucher_number} updated successfully.')
            return redirect('receipt_voucher:receipt_voucher_detail', pk=voucher.pk)
    else:
        form = ReceiptVoucherForm(instance=voucher)
    
    context = {
        'form': form,
        'voucher': voucher,
        'title': 'Edit Receipt Voucher',
        'submit_text': 'Update Voucher',
    }
    
    return render(request, 'receipt_voucher/receipt_voucher_form.html', context)


@login_required
def receipt_voucher_detail(request, pk):
    """View receipt voucher details"""
    
    voucher = get_object_or_404(
        ReceiptVoucher.objects.select_related(
            'currency', 'account_to_credit', 'created_by', 'updated_by', 'approved_by'
        ).prefetch_related('attachments', 'audit_trail'),
        pk=pk
    )
    
    # Get audit trail
    audit_trail = voucher.audit_trail.all()[:10]  # Last 10 entries
    
    # Get attachments
    attachments = voucher.attachments.all()
    
    context = {
        'voucher': voucher,
        'audit_trail': audit_trail,
        'attachments': attachments,
    }
    
    return render(request, 'receipt_voucher/receipt_voucher_detail.html', context)


@login_required
def receipt_voucher_delete(request, pk):
    """Delete a receipt voucher"""
    
    voucher = get_object_or_404(ReceiptVoucher, pk=pk)
    
    # Check if voucher can be deleted
    if voucher.status not in ['draft']:
        messages.error(request, 'Only draft vouchers can be deleted.')
        return redirect('receipt_voucher:receipt_voucher_detail', pk=voucher.pk)
    
    if request.method == 'POST':
        voucher_number = voucher.voucher_number
        voucher.delete()
        messages.success(request, f'Receipt voucher {voucher_number} deleted successfully.')
        return redirect('receipt_voucher:receipt_voucher_list')
    
    context = {
        'voucher': voucher,
    }
    
    return render(request, 'receipt_voucher/receipt_voucher_delete.html', context)


@login_required
def receipt_voucher_approve(request, pk):
    """Approve a receipt voucher"""
    
    voucher = get_object_or_404(ReceiptVoucher, pk=pk)
    
    # Check if voucher can be approved
    if not voucher.can_approve:
        messages.error(request, 'Only draft vouchers can be approved.')
        return redirect('receipt_voucher:receipt_voucher_detail', pk=voucher.pk)
    
    if request.method == 'POST':
        form = ReceiptVoucherApprovalForm(request.POST, voucher=voucher)
        if form.is_valid():
            voucher.status = 'approved'
            voucher.approved_by = request.user
            voucher.approved_at = timezone.now()
            voucher.save()
            
            # Create audit trail
            approval_notes = form.cleaned_data.get('approval_notes', '')
            description = f'Receipt voucher approved by {request.user.get_full_name()}'
            if approval_notes:
                description += f' - Notes: {approval_notes}'
            
            ReceiptVoucherAudit.objects.create(
                voucher=voucher,
                action='approved',
                description=description,
                user=request.user
            )
            
            messages.success(request, f'Receipt voucher {voucher.voucher_number} approved successfully.')
            return redirect('receipt_voucher:receipt_voucher_detail', pk=voucher.pk)
    else:
        form = ReceiptVoucherApprovalForm(voucher=voucher)
    
    context = {
        'voucher': voucher,
        'form': form,
    }
    
    return render(request, 'receipt_voucher/receipt_voucher_approve.html', context)


@login_required
def receipt_voucher_mark_received(request, pk):
    """Mark a receipt voucher as received"""
    
    voucher = get_object_or_404(ReceiptVoucher, pk=pk)
    
    # Check if voucher can be marked as received
    if not voucher.can_mark_received:
        messages.error(request, 'Only approved vouchers can be marked as received.')
        return redirect('receipt_voucher:receipt_voucher_detail', pk=voucher.pk)
    
    if request.method == 'POST':
        form = ReceiptVoucherMarkReceivedForm(request.POST, voucher=voucher)
        if form.is_valid():
            voucher.status = 'received'
            voucher.received_at = timezone.now()
            voucher.save()
            
            # Create audit trail
            received_notes = form.cleaned_data.get('received_notes', '')
            description = f'Receipt voucher marked as received by {request.user.get_full_name()}'
            if received_notes:
                description += f' - Notes: {received_notes}'
            
            ReceiptVoucherAudit.objects.create(
                voucher=voucher,
                action='marked_received',
                description=description,
                user=request.user
            )
            
            messages.success(request, f'Receipt voucher {voucher.voucher_number} marked as received successfully.')
            return redirect('receipt_voucher:receipt_voucher_detail', pk=voucher.pk)
    else:
        form = ReceiptVoucherMarkReceivedForm(voucher=voucher)
    
    context = {
        'voucher': voucher,
        'form': form,
    }
    
    return render(request, 'receipt_voucher/receipt_voucher_mark_received.html', context)


@login_required
def receipt_voucher_cancel(request, pk):
    """Cancel a receipt voucher"""
    
    voucher = get_object_or_404(ReceiptVoucher, pk=pk)
    
    # Check if voucher can be cancelled
    if voucher.status in ['received']:
        messages.error(request, 'Received vouchers cannot be cancelled.')
        return redirect('receipt_voucher:receipt_voucher_detail', pk=voucher.pk)
    
    if request.method == 'POST':
        voucher.status = 'cancelled'
        voucher.save()
        
        # Create audit trail
        ReceiptVoucherAudit.objects.create(
            voucher=voucher,
            action='cancelled',
            description=f'Receipt voucher cancelled by {request.user.get_full_name()}',
            user=request.user
        )
        
        messages.success(request, f'Receipt voucher {voucher.voucher_number} cancelled successfully.')
        return redirect('receipt_voucher:receipt_voucher_detail', pk=voucher.pk)
    
    context = {
        'voucher': voucher,
    }
    
    return render(request, 'receipt_voucher/receipt_voucher_cancel.html', context)


@login_required
def receipt_voucher_attachment_upload(request, pk):
    """Upload attachment for receipt voucher"""
    
    voucher = get_object_or_404(ReceiptVoucher, pk=pk)
    
    if request.method == 'POST':
        form = ReceiptVoucherAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.voucher = voucher
            attachment.uploaded_by = request.user
            attachment.save()
            
            # Create audit trail
            ReceiptVoucherAudit.objects.create(
                voucher=voucher,
                action='attachment_added',
                description=f'Attachment "{attachment.filename}" added by {request.user.get_full_name()}',
                user=request.user
            )
            
            messages.success(request, 'Attachment uploaded successfully.')
            return redirect('receipt_voucher:receipt_voucher_detail', pk=voucher.pk)
    else:
        form = ReceiptVoucherAttachmentForm()
    
    context = {
        'voucher': voucher,
        'form': form,
    }
    
    return render(request, 'receipt_voucher/receipt_voucher_attachment_upload.html', context)


@login_required
def receipt_voucher_attachment_delete(request, pk, attachment_pk):
    """Delete attachment from receipt voucher"""
    
    voucher = get_object_or_404(ReceiptVoucher, pk=pk)
    attachment = get_object_or_404(ReceiptVoucherAttachment, pk=attachment_pk, voucher=voucher)
    
    if request.method == 'POST':
        file_name = attachment.filename
        attachment.delete()
        
        # Create audit trail
        ReceiptVoucherAudit.objects.create(
            voucher=voucher,
            action='attachment_removed',
            description=f'Attachment "{file_name}" removed by {request.user.get_full_name()}',
            user=request.user
        )
        
        messages.success(request, 'Attachment deleted successfully.')
        return redirect('receipt_voucher:receipt_voucher_detail', pk=voucher.pk)
    
    context = {
        'voucher': voucher,
        'attachment': attachment,
    }
    
    return render(request, 'receipt_voucher/receipt_voucher_attachment_delete.html', context)


# AJAX Views for autocomplete and dynamic functionality

@login_required
@require_http_methods(["GET"])
def ajax_payer_search(request):
    """AJAX endpoint for payer search autocomplete"""
    
    payer_type = request.GET.get('payer_type')
    search_query = request.GET.get('q', '')
    
    if not search_query or len(search_query) < 2:
        return JsonResponse({'results': []})
    
    results = []
    
    if payer_type == 'customer':
        # Search in customers
        customers = Customer.objects.filter(
            customer_name__icontains=search_query,
            is_active=True
        )[:10]
        
        for customer in customers:
            results.append({
                'id': customer.id,
                'text': f"{customer.customer_name} ({customer.customer_code})",
                'name': customer.customer_name,
                'code': customer.customer_code,
                'contact': customer.contact_number or '',
                'email': customer.email or '',
                'type': 'customer'
            })
    
    elif payer_type == 'employee':
        # Search in salesmen
        employees = Salesman.objects.filter(
            Q(first_name__icontains=search_query) | 
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query),
            status='active'
        )[:10]
        
        for employee in employees:
            results.append({
                'id': employee.id,
                'text': f"{employee.first_name} {employee.last_name} ({employee.salesman_code})",
                'name': f"{employee.first_name} {employee.last_name}",
                'code': employee.salesman_code,
                'contact': employee.phone or '',
                'email': employee.email or '',
                'type': 'employee'
            })
    
    elif payer_type == 'vendor':
        # Search in customers with vendor type
        vendors = Customer.objects.filter(
            customer_name__icontains=search_query,
            customer_types__name__icontains='vendor',
            is_active=True
        )[:10]
        
        for vendor in vendors:
            results.append({
                'id': vendor.id,
                'text': f"{vendor.customer_name} ({vendor.customer_code})",
                'name': vendor.customer_name,
                'code': vendor.customer_code,
                'contact': vendor.contact_number or '',
                'email': vendor.email or '',
                'type': 'vendor'
            })
    
    elif payer_type == 'other':
        # Search in all customers
        customers = Customer.objects.filter(
            customer_name__icontains=search_query,
            is_active=True
        )[:10]
        
        for customer in customers:
            results.append({
                'id': customer.id,
                'text': f"{customer.customer_name} ({customer.customer_code})",
                'name': customer.customer_name,
                'code': customer.customer_code,
                'contact': customer.contact_number or '',
                'email': customer.email or '',
                'type': 'customer'
            })
    
    return JsonResponse({'results': results})


@login_required
@require_http_methods(["GET"])
def ajax_account_search(request):
    """AJAX endpoint for account search autocomplete"""
    
    search_query = request.GET.get('q', '')
    
    if not search_query or len(search_query) < 2:
        return JsonResponse({'results': []})
    
    # Search in chart of accounts (only asset and income accounts)
    accounts = ChartOfAccount.objects.filter(
        Q(account_code__icontains=search_query) | 
        Q(name__icontains=search_query),
        is_active=True,
        account_type__category__in=['ASSET', 'INCOME']
    )[:10]
    
    results = []
    for account in accounts:
        results.append({
            'id': account.id,
            'text': f"{account.account_code} - {account.name}",
            'code': account.account_code,
            'name': account.name,
            'category': account.account_type.category
        })
    
    return JsonResponse({'results': results})


@login_required
@require_http_methods(["GET"])
def ajax_voucher_summary(request):
    """AJAX endpoint for voucher summary statistics"""
    
    # Get date range from request
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    vouchers = ReceiptVoucher.objects.all()
    
    if date_from:
        vouchers = vouchers.filter(voucher_date__gte=date_from)
    if date_to:
        vouchers = vouchers.filter(voucher_date__lte=date_to)
    
    # Calculate statistics
    total_vouchers = vouchers.count()
    total_amount = vouchers.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    status_counts = {}
    for status, label in ReceiptVoucher.STATUS_CHOICES:
        status_counts[status] = vouchers.filter(status=status).count()
    
    receipt_mode_counts = {}
    for mode, label in ReceiptVoucher.RECEIPT_MODES:
        receipt_mode_counts[mode] = vouchers.filter(receipt_mode=mode).count()
    
    return JsonResponse({
        'total_vouchers': total_vouchers,
        'total_amount': float(total_amount),
        'status_counts': status_counts,
        'receipt_mode_counts': receipt_mode_counts,
    })


@login_required
def receipt_voucher_dashboard(request):
    """Dashboard view for receipt vouchers"""
    
    # Get recent vouchers
    recent_vouchers = ReceiptVoucher.objects.select_related(
        'currency', 'created_by'
    ).order_by('-created_at')[:10]
    
    # Get statistics
    total_vouchers = ReceiptVoucher.objects.count()
    total_amount = ReceiptVoucher.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Status breakdown
    status_breakdown = {}
    for status, label in ReceiptVoucher.STATUS_CHOICES:
        status_breakdown[status] = ReceiptVoucher.objects.filter(status=status).count()
    
    # Receipt mode breakdown
    receipt_mode_breakdown = {}
    for mode, label in ReceiptVoucher.RECEIPT_MODES:
        receipt_mode_breakdown[mode] = ReceiptVoucher.objects.filter(receipt_mode=mode).count()
    
    # Monthly totals for current year
    current_year = datetime.now().year
    monthly_totals = []
    for month in range(1, 13):
        month_total = ReceiptVoucher.objects.filter(
            voucher_date__year=current_year,
            voucher_date__month=month
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        monthly_totals.append(float(month_total))
    
    context = {
        'recent_vouchers': recent_vouchers,
        'total_vouchers': total_vouchers,
        'total_amount': total_amount,
        'status_breakdown': status_breakdown,
        'receipt_mode_breakdown': receipt_mode_breakdown,
        'monthly_totals': monthly_totals,
        'current_year': current_year,
    }
    
    return render(request, 'receipt_voucher/receipt_voucher_dashboard.html', context)


@login_required
def receipt_voucher_print(request, pk):
    """Print receipt voucher"""
    
    voucher = get_object_or_404(
        ReceiptVoucher.objects.select_related(
            'currency', 'account_to_credit', 'created_by', 'updated_by', 'approved_by'
        ).prefetch_related('attachments'),
        pk=pk
    )
    
    # Get attachments
    attachments = voucher.attachments.all()
    
    context = {
        'voucher': voucher,
        'attachments': attachments,
        'print_mode': True,
    }
    
    return render(request, 'receipt_voucher/receipt_voucher_print.html', context)
