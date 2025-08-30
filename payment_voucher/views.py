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

from .models import PaymentVoucher, PaymentVoucherAttachment, PaymentVoucherAudit
from .forms import (
    PaymentVoucherForm, PaymentVoucherAttachmentForm, 
    PaymentVoucherSearchForm, PaymentVoucherApprovalForm
)
from customer.models import Customer, CustomerType
from salesman.models import Salesman
from chart_of_accounts.models import ChartOfAccount
from multi_currency.models import Currency


@login_required
def payment_voucher_list(request):
    """List all payment vouchers with search and filtering"""
    
    # Get search form
    search_form = PaymentVoucherSearchForm(request.GET)
    
    # Get all vouchers
    vouchers = PaymentVoucher.objects.select_related(
        'currency', 'account_to_debit', 'created_by', 'approved_by'
    ).prefetch_related('attachments')
    
    # Apply search filters
    if search_form.is_valid():
        search_field = search_form.cleaned_data.get('search_field')
        search_query = search_form.cleaned_data.get('search_query')
        status = search_form.cleaned_data.get('status')
        payment_mode = search_form.cleaned_data.get('payment_mode')
        payee_type = search_form.cleaned_data.get('payee_type')
        currency = search_form.cleaned_data.get('currency')
        date_from = search_form.cleaned_data.get('date_from')
        date_to = search_form.cleaned_data.get('date_to')
        amount_min = search_form.cleaned_data.get('amount_min')
        amount_max = search_form.cleaned_data.get('amount_max')
        
        # Apply search query
        if search_query:
            if search_field == 'voucher_number':
                vouchers = vouchers.filter(voucher_number__icontains=search_query)
            elif search_field == 'payee_name':
                vouchers = vouchers.filter(payee_name__icontains=search_query)
            elif search_field == 'description':
                vouchers = vouchers.filter(description__icontains=search_query)
            elif search_field == 'reference_number':
                vouchers = vouchers.filter(reference_number__icontains=search_query)
        
        # Apply filters
        if status:
            vouchers = vouchers.filter(status=status)
        if payment_mode:
            vouchers = vouchers.filter(payment_mode=payment_mode)
        if payee_type:
            vouchers = vouchers.filter(payee_type=payee_type)
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
    paid_count = vouchers.filter(status='paid').count()
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_vouchers': total_vouchers,
        'total_amount': total_amount,
        'draft_count': draft_count,
        'approved_count': approved_count,
        'paid_count': paid_count,
    }
    
    return render(request, 'payment_voucher/payment_voucher_list.html', context)


@login_required
def payment_voucher_create(request):
    """Create a new payment voucher"""
    
    if request.method == 'POST':
        form = PaymentVoucherForm(request.POST)
        if form.is_valid():
            voucher = form.save(commit=False)
            voucher.created_by = request.user
            voucher.save()
            
            # Create audit trail
            PaymentVoucherAudit.objects.create(
                voucher=voucher,
                action='created',
                description=f'Payment voucher created by {request.user.get_full_name()}',
                user=request.user
            )
            
            messages.success(request, f'Payment voucher {voucher.voucher_number} created successfully.')
            return redirect('payment_voucher:payment_voucher_detail', pk=voucher.pk)
    else:
        form = PaymentVoucherForm()
    
    context = {
        'form': form,
        'title': 'Create Payment Voucher',
        'submit_text': 'Create Voucher',
    }
    
    return render(request, 'payment_voucher/payment_voucher_form.html', context)


@login_required
def payment_voucher_edit(request, pk):
    """Edit an existing payment voucher"""
    
    voucher = get_object_or_404(PaymentVoucher, pk=pk)
    
    # Check if voucher can be edited
    if voucher.status not in ['draft']:
        messages.error(request, 'Only draft vouchers can be edited.')
        return redirect('payment_voucher:payment_voucher_detail', pk=voucher.pk)
    
    if request.method == 'POST':
        form = PaymentVoucherForm(request.POST, instance=voucher)
        if form.is_valid():
            voucher = form.save(commit=False)
            voucher.updated_by = request.user
            voucher.save()
            
            # Create audit trail
            PaymentVoucherAudit.objects.create(
                voucher=voucher,
                action='updated',
                description=f'Payment voucher updated by {request.user.get_full_name()}',
                user=request.user
            )
            
            messages.success(request, f'Payment voucher {voucher.voucher_number} updated successfully.')
            return redirect('payment_voucher:payment_voucher_detail', pk=voucher.pk)
    else:
        form = PaymentVoucherForm(instance=voucher)
    
    context = {
        'form': form,
        'voucher': voucher,
        'title': 'Edit Payment Voucher',
        'submit_text': 'Update Voucher',
    }
    
    return render(request, 'payment_voucher/payment_voucher_form.html', context)


@login_required
def payment_voucher_detail(request, pk):
    """View payment voucher details"""
    
    voucher = get_object_or_404(
        PaymentVoucher.objects.select_related(
            'currency', 'account_to_debit', 'created_by', 'updated_by', 'approved_by'
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
    
    return render(request, 'payment_voucher/payment_voucher_detail.html', context)


@login_required
def payment_voucher_delete(request, pk):
    """Delete a payment voucher"""
    
    voucher = get_object_or_404(PaymentVoucher, pk=pk)
    
    # Check if voucher can be deleted
    if voucher.status not in ['draft']:
        messages.error(request, 'Only draft vouchers can be deleted.')
        return redirect('payment_voucher:payment_voucher_detail', pk=voucher.pk)
    
    if request.method == 'POST':
        voucher_number = voucher.voucher_number
        voucher.delete()
        messages.success(request, f'Payment voucher {voucher_number} deleted successfully.')
        return redirect('payment_voucher:payment_voucher_list')
    
    context = {
        'voucher': voucher,
    }
    
    return render(request, 'payment_voucher/payment_voucher_confirm_delete.html', context)


@login_required
def payment_voucher_approve(request, pk):
    """Approve a payment voucher"""
    
    voucher = get_object_or_404(PaymentVoucher, pk=pk)
    
    # Check if voucher can be approved
    if not voucher.can_approve:
        messages.error(request, 'This voucher cannot be approved.')
        return redirect('payment_voucher:payment_voucher_detail', pk=voucher.pk)
    
    if request.method == 'POST':
        form = PaymentVoucherApprovalForm(voucher, request.POST)
        if form.is_valid():
            voucher.status = 'approved'
            voucher.approved_by = request.user
            voucher.approved_at = timezone.now()
            voucher.updated_by = request.user
            voucher.save()
            
            # Create audit trail
            approval_notes = form.cleaned_data.get('approval_notes', '')
            PaymentVoucherAudit.objects.create(
                voucher=voucher,
                action='approved',
                description=f'Payment voucher approved by {request.user.get_full_name()}. {approval_notes}',
                user=request.user
            )
            
            messages.success(request, f'Payment voucher {voucher.voucher_number} approved successfully.')
            return redirect('payment_voucher:payment_voucher_detail', pk=voucher.pk)
    else:
        form = PaymentVoucherApprovalForm(voucher)
    
    context = {
        'form': form,
        'voucher': voucher,
    }
    
    return render(request, 'payment_voucher/payment_voucher_approve.html', context)


@login_required
def payment_voucher_mark_paid(request, pk):
    """Mark a payment voucher as paid"""
    
    voucher = get_object_or_404(PaymentVoucher, pk=pk)
    
    # Check if voucher can be marked as paid
    if not voucher.can_pay:
        messages.error(request, 'This voucher cannot be marked as paid.')
        return redirect('payment_voucher:payment_voucher_detail', pk=voucher.pk)
    
    if request.method == 'POST':
        voucher.status = 'paid'
        voucher.updated_by = request.user
        voucher.save()
        
        # Create audit trail
        PaymentVoucherAudit.objects.create(
            voucher=voucher,
            action='paid',
            description=f'Payment voucher marked as paid by {request.user.get_full_name()}',
            user=request.user
        )
        
        messages.success(request, f'Payment voucher {voucher.voucher_number} marked as paid successfully.')
        return redirect('payment_voucher:payment_voucher_detail', pk=voucher.pk)
    
    context = {
        'voucher': voucher,
    }
    
    return render(request, 'payment_voucher/payment_voucher_mark_paid.html', context)


@login_required
def payment_voucher_cancel(request, pk):
    """Cancel a payment voucher"""
    
    voucher = get_object_or_404(PaymentVoucher, pk=pk)
    
    # Check if voucher can be cancelled
    if voucher.status not in ['draft', 'approved']:
        messages.error(request, 'This voucher cannot be cancelled.')
        return redirect('payment_voucher:payment_voucher_detail', pk=voucher.pk)
    
    if request.method == 'POST':
        voucher.status = 'cancelled'
        voucher.updated_by = request.user
        voucher.save()
        
        # Create audit trail
        PaymentVoucherAudit.objects.create(
            voucher=voucher,
            action='cancelled',
            description=f'Payment voucher cancelled by {request.user.get_full_name()}',
            user=request.user
        )
        
        messages.success(request, f'Payment voucher {voucher.voucher_number} cancelled successfully.')
        return redirect('payment_voucher:payment_voucher_detail', pk=voucher.pk)
    
    context = {
        'voucher': voucher,
    }
    
    return render(request, 'payment_voucher/payment_voucher_cancel.html', context)


@login_required
def payment_voucher_attachment_upload(request, pk):
    """Upload attachment for payment voucher"""
    
    voucher = get_object_or_404(PaymentVoucher, pk=pk)
    
    if request.method == 'POST':
        form = PaymentVoucherAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.voucher = voucher
            attachment.uploaded_by = request.user
            attachment.file_name = request.FILES['file'].name
            attachment.save()
            
            # Create audit trail
            PaymentVoucherAudit.objects.create(
                voucher=voucher,
                action='attachment_added',
                description=f'Attachment "{attachment.file_name}" added by {request.user.get_full_name()}',
                user=request.user
            )
            
            messages.success(request, 'Attachment uploaded successfully.')
            return redirect('payment_voucher:payment_voucher_detail', pk=voucher.pk)
    else:
        form = PaymentVoucherAttachmentForm()
    
    context = {
        'form': form,
        'voucher': voucher,
    }
    
    return render(request, 'payment_voucher/payment_voucher_attachment_upload.html', context)


@login_required
def payment_voucher_attachment_delete(request, pk, attachment_pk):
    """Delete attachment from payment voucher"""
    
    voucher = get_object_or_404(PaymentVoucher, pk=pk)
    attachment = get_object_or_404(PaymentVoucherAttachment, pk=attachment_pk, voucher=voucher)
    
    if request.method == 'POST':
        file_name = attachment.file_name
        attachment.delete()
        
        # Create audit trail
        PaymentVoucherAudit.objects.create(
            voucher=voucher,
            action='attachment_removed',
            description=f'Attachment "{file_name}" removed by {request.user.get_full_name()}',
            user=request.user
        )
        
        messages.success(request, 'Attachment deleted successfully.')
        return redirect('payment_voucher:payment_voucher_detail', pk=voucher.pk)
    
    context = {
        'voucher': voucher,
        'attachment': attachment,
    }
    
    return render(request, 'payment_voucher/payment_voucher_attachment_delete.html', context)


# AJAX Views for autocomplete and dynamic functionality

@login_required
@require_http_methods(["GET"])
def ajax_payee_search(request):
    """AJAX endpoint for payee search autocomplete"""
    
    payee_type = request.GET.get('payee_type')
    search_query = request.GET.get('q', '')
    
    if not search_query or len(search_query) < 2:
        return JsonResponse({'results': []})
    
    results = []
    
    if payee_type == 'vendor':
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
                'type': 'vendor'
            })
    
    elif payee_type == 'employee':
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
                'type': 'employee'
            })
    
    elif payee_type == 'other':
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
                'type': 'customer'
            })
    
    return JsonResponse({'results': results})


@login_required
@require_http_methods(["GET"])
def ajax_account_search(request):
    """AJAX endpoint for account search autocomplete"""
    
    search_query = request.GET.get('q', '')
    payment_mode = request.GET.get('payment_mode', '')
    
    if not search_query or len(search_query) < 2:
        return JsonResponse({'results': []})
    
    # Base query for chart of accounts
    base_query = Q(account_code__icontains=search_query) | Q(name__icontains=search_query)
    
    # Filter accounts based on payment mode
    if payment_mode == 'cash':
        # For cash payments, show cash-related accounts
        accounts = ChartOfAccount.objects.filter(
            base_query,
            Q(name__icontains='cash') | Q(name__icontains='petty') | Q(account_code__in=['1000', '1001', '1006']),
            is_active=True,
            account_type__category='ASSET'
        )[:10]
    elif payment_mode in ['bank_transfer', 'cheque']:
        # For bank payments, show bank-related accounts
        accounts = ChartOfAccount.objects.filter(
            base_query,
            Q(name__icontains='bank') | Q(name__icontains='checking') | Q(name__icontains='savings') | Q(account_code__in=['1100', '1101', '1102']),
            is_active=True,
            account_type__category='ASSET'
        )[:10]
    elif payment_mode == 'credit_card':
        # For credit card payments, show credit card accounts
        accounts = ChartOfAccount.objects.filter(
            base_query,
            Q(name__icontains='credit') | Q(name__icontains='card') | Q(account_code__in=['2100', '2101']),
            is_active=True,
            account_type__category__in=['ASSET', 'LIABILITY']
        )[:10]
    else:
        # Default: show all asset accounts (for backward compatibility)
        accounts = ChartOfAccount.objects.filter(
            base_query,
            is_active=True,
            account_type__category__in=['ASSET', 'EXPENSE']
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
    
    vouchers = PaymentVoucher.objects.all()
    
    if date_from:
        vouchers = vouchers.filter(voucher_date__gte=date_from)
    if date_to:
        vouchers = vouchers.filter(voucher_date__lte=date_to)
    
    # Calculate statistics
    total_vouchers = vouchers.count()
    total_amount = vouchers.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    status_counts = {}
    for status, label in PaymentVoucher.STATUS_CHOICES:
        status_counts[status] = vouchers.filter(status=status).count()
    
    payment_mode_counts = {}
    for mode, label in PaymentVoucher.PAYMENT_MODES:
        payment_mode_counts[mode] = vouchers.filter(payment_mode=mode).count()
    
    return JsonResponse({
        'total_vouchers': total_vouchers,
        'total_amount': float(total_amount),
        'status_counts': status_counts,
        'payment_mode_counts': payment_mode_counts,
    })


@login_required
def payment_voucher_dashboard(request):
    """Dashboard view for payment vouchers"""
    
    # Get recent vouchers
    recent_vouchers = PaymentVoucher.objects.select_related(
        'currency', 'created_by'
    ).order_by('-created_at')[:10]
    
    # Get statistics
    total_vouchers = PaymentVoucher.objects.count()
    total_amount = PaymentVoucher.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Status breakdown
    status_breakdown = {}
    for status, label in PaymentVoucher.STATUS_CHOICES:
        status_breakdown[status] = PaymentVoucher.objects.filter(status=status).count()
    
    # Payment mode breakdown
    payment_mode_breakdown = {}
    for mode, label in PaymentVoucher.PAYMENT_MODES:
        payment_mode_breakdown[mode] = PaymentVoucher.objects.filter(payment_mode=mode).count()
    
    # Monthly totals for current year
    current_year = datetime.now().year
    monthly_totals = []
    for month in range(1, 13):
        month_total = PaymentVoucher.objects.filter(
            voucher_date__year=current_year,
            voucher_date__month=month
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        monthly_totals.append(float(month_total))
    
    context = {
        'recent_vouchers': recent_vouchers,
        'total_vouchers': total_vouchers,
        'total_amount': total_amount,
        'status_breakdown': status_breakdown,
        'payment_mode_breakdown': payment_mode_breakdown,
        'monthly_totals': monthly_totals,
        'current_year': current_year,
    }
    
    return render(request, 'payment_voucher/payment_voucher_dashboard.html', context)


@login_required
def payment_voucher_print(request, pk):
    """Print payment voucher"""
    
    voucher = get_object_or_404(
        PaymentVoucher.objects.select_related(
            'currency', 'account_to_debit', 'created_by', 'updated_by', 'approved_by'
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
    
    return render(request, 'payment_voucher/payment_voucher_print.html', context)
