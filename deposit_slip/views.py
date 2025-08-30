from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET
from django.template.loader import render_to_string
from .models import DepositSlip, DepositSlipItem, DepositSlipAudit
from .forms import DepositSlipForm, ReceiptVoucherSelectionForm, DepositSlipFilterForm
from receipt_voucher.models import ReceiptVoucher
from chart_of_accounts.models import ChartOfAccount
import json


@login_required
def deposit_slip_list(request):
    """List all deposit slips with filtering and pagination"""
    
    # Get filter parameters
    form = DepositSlipFilterForm(request.GET)
    deposit_slips = DepositSlip.objects.all()
    
    # Apply filters
    if form.is_valid():
        if form.cleaned_data.get('date_from'):
            deposit_slips = deposit_slips.filter(deposit_date__gte=form.cleaned_data['date_from'])
        if form.cleaned_data.get('date_to'):
            deposit_slips = deposit_slips.filter(deposit_date__lte=form.cleaned_data['date_to'])
        if form.cleaned_data.get('status'):
            deposit_slips = deposit_slips.filter(status=form.cleaned_data['status'])
        if form.cleaned_data.get('deposit_to'):
            deposit_slips = deposit_slips.filter(deposit_to=form.cleaned_data['deposit_to'])
        if form.cleaned_data.get('search'):
            search_term = form.cleaned_data['search']
            deposit_slips = deposit_slips.filter(
                Q(slip_number__icontains=search_term) |
                Q(reference_number__icontains=search_term)
            )
    
    # Pagination
    paginator = Paginator(deposit_slips, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filter_form': form,
        'total_count': deposit_slips.count(),
        'total_amount': deposit_slips.aggregate(total=Sum('total_amount'))['total'] or 0,
    }
    
    return render(request, 'deposit_slip/list.html', context)


@login_required
def deposit_slip_create(request):
    """Create a new deposit slip"""
    
    if request.method == 'POST':
        deposit_form = DepositSlipForm(request.POST)
        voucher_form = ReceiptVoucherSelectionForm(request.POST)
        
        if deposit_form.is_valid() and voucher_form.is_valid():
            # Create deposit slip
            deposit_slip = deposit_form.save(commit=False)
            deposit_slip.created_by = request.user
            deposit_slip.save()
            
            # Add selected receipt vouchers
            selected_vouchers = voucher_form.cleaned_data.get('selected_vouchers', [])
            for voucher_id in selected_vouchers:
                try:
                    voucher = ReceiptVoucher.objects.get(id=voucher_id)
                    DepositSlipItem.objects.create(
                        deposit_slip=deposit_slip,
                        receipt_voucher=voucher,
                        amount=voucher.amount,
                        created_by=request.user
                    )
                except ReceiptVoucher.DoesNotExist:
                    continue
            
            # Create audit trail
            DepositSlipAudit.objects.create(
                deposit_slip=deposit_slip,
                action='created',
                description=f'Deposit slip created with {len(selected_vouchers)} receipt vouchers',
                user=request.user
            )
            
            messages.success(request, f'Deposit slip {deposit_slip.slip_number} created successfully.')
            return redirect('deposit_slip_detail', pk=deposit_slip.pk)
    else:
        deposit_form = DepositSlipForm()
        voucher_form = ReceiptVoucherSelectionForm()
    
    # Get available receipt vouchers for display
    available_vouchers = ReceiptVoucher.objects.filter(
        status='received',
        deposit_slip_items__isnull=True
    ).order_by('-voucher_date', '-created_at')
    
    context = {
        'deposit_form': deposit_form,
        'voucher_form': voucher_form,
        'available_vouchers': available_vouchers,
        'total_available_amount': available_vouchers.aggregate(total=Sum('amount'))['total'] or 0,
    }
    
    return render(request, 'deposit_slip/create.html', context)


@login_required
def deposit_slip_edit(request, pk):
    """Edit an existing deposit slip"""
    
    deposit_slip = get_object_or_404(DepositSlip, pk=pk)
    
    if not deposit_slip.can_edit:
        messages.error(request, 'This deposit slip cannot be edited.')
        return redirect('deposit_slip_detail', pk=pk)
    
    if request.method == 'POST':
        deposit_form = DepositSlipForm(request.POST, instance=deposit_slip)
        voucher_form = ReceiptVoucherSelectionForm(request.POST)
        
        if deposit_form.is_valid() and voucher_form.is_valid():
            # Update deposit slip
            deposit_slip = deposit_form.save(commit=False)
            deposit_slip.updated_by = request.user
            deposit_slip.save()
            
            # Handle voucher selection
            selected_vouchers = voucher_form.cleaned_data.get('selected_vouchers', [])
            current_vouchers = set(deposit_slip.items.values_list('receipt_voucher_id', flat=True))
            new_vouchers = set(int(vid) for vid in selected_vouchers)
            
            # Remove unselected vouchers
            to_remove = current_vouchers - new_vouchers
            for voucher_id in to_remove:
                deposit_slip.items.filter(receipt_voucher_id=voucher_id).delete()
            
            # Add new vouchers
            to_add = new_vouchers - current_vouchers
            for voucher_id in to_add:
                try:
                    voucher = ReceiptVoucher.objects.get(id=voucher_id)
                    DepositSlipItem.objects.create(
                        deposit_slip=deposit_slip,
                        receipt_voucher=voucher,
                        amount=voucher.amount,
                        created_by=request.user
                    )
                except ReceiptVoucher.DoesNotExist:
                    continue
            
            # Create audit trail
            DepositSlipAudit.objects.create(
                deposit_slip=deposit_slip,
                action='updated',
                description=f'Deposit slip updated',
                user=request.user
            )
            
            messages.success(request, f'Deposit slip {deposit_slip.slip_number} updated successfully.')
            return redirect('deposit_slip_detail', pk=deposit_slip.pk)
    else:
        deposit_form = DepositSlipForm(instance=deposit_slip)
        voucher_form = ReceiptVoucherSelectionForm()
    
    # Get available receipt vouchers (including currently selected ones)
    available_vouchers = ReceiptVoucher.objects.filter(
        Q(status='received', deposit_slip_items__isnull=True) |
        Q(deposit_slip_items__deposit_slip=deposit_slip)
    ).distinct().order_by('-voucher_date', '-created_at')
    
    context = {
        'deposit_slip': deposit_slip,
        'deposit_form': deposit_form,
        'voucher_form': voucher_form,
        'available_vouchers': available_vouchers,
        'selected_vouchers': deposit_slip.items.values_list('receipt_voucher_id', flat=True),
    }
    
    return render(request, 'deposit_slip/edit.html', context)


@login_required
def deposit_slip_detail(request, pk):
    """View deposit slip details"""
    
    deposit_slip = get_object_or_404(DepositSlip, pk=pk)
    
    context = {
        'deposit_slip': deposit_slip,
        'items': deposit_slip.items.select_related('receipt_voucher').all(),
        'audit_trail': deposit_slip.audit_trail.select_related('user').all()[:10],
    }
    
    return render(request, 'deposit_slip/detail.html', context)


@login_required
def deposit_slip_delete(request, pk):
    """Delete a deposit slip"""
    
    deposit_slip = get_object_or_404(DepositSlip, pk=pk)
    
    if not deposit_slip.can_edit:
        messages.error(request, 'This deposit slip cannot be deleted.')
        return redirect('deposit_slip_detail', pk=pk)
    
    if request.method == 'POST':
        slip_number = deposit_slip.slip_number
        deposit_slip.delete()
        messages.success(request, f'Deposit slip {slip_number} deleted successfully.')
        return redirect('deposit_slip_list')
    
    context = {
        'deposit_slip': deposit_slip,
    }
    
    return render(request, 'deposit_slip/delete.html', context)


@login_required
@require_POST
def deposit_slip_submit(request, pk):
    """Submit a deposit slip for confirmation"""
    
    deposit_slip = get_object_or_404(DepositSlip, pk=pk)
    
    if not deposit_slip.can_submit:
        return JsonResponse({'success': False, 'message': 'Deposit slip cannot be submitted.'})
    
    deposit_slip.status = 'submitted'
    deposit_slip.submitted_by = request.user
    deposit_slip.submitted_at = timezone.now()
    deposit_slip.save()
    
    # Create audit trail
    DepositSlipAudit.objects.create(
        deposit_slip=deposit_slip,
        action='submitted',
        description='Deposit slip submitted for confirmation',
        user=request.user
    )
    
    messages.success(request, f'Deposit slip {deposit_slip.slip_number} submitted successfully.')
    return JsonResponse({'success': True, 'message': 'Deposit slip submitted successfully.'})


@login_required
@require_POST
def deposit_slip_confirm(request, pk):
    """Confirm a submitted deposit slip"""
    
    deposit_slip = get_object_or_404(DepositSlip, pk=pk)
    
    if not deposit_slip.can_confirm:
        return JsonResponse({'success': False, 'message': 'Deposit slip cannot be confirmed.'})
    
    deposit_slip.status = 'confirmed'
    deposit_slip.confirmed_by = request.user
    deposit_slip.confirmed_at = timezone.now()
    deposit_slip.save()
    
    # Create audit trail
    DepositSlipAudit.objects.create(
        deposit_slip=deposit_slip,
        action='confirmed',
        description='Deposit slip confirmed',
        user=request.user
    )
    
    messages.success(request, f'Deposit slip {deposit_slip.slip_number} confirmed successfully.')
    return JsonResponse({'success': True, 'message': 'Deposit slip confirmed successfully.'})


@login_required
@require_GET
def get_available_vouchers(request):
    """AJAX endpoint to get available receipt vouchers"""
    
    # Get filter parameters
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    payer_name = request.GET.get('payer_name')
    receipt_mode = request.GET.get('receipt_mode')
    
    queryset = ReceiptVoucher.objects.filter(
        status='received',
        deposit_slip_items__isnull=True
    )
    
    # Apply filters
    if date_from:
        queryset = queryset.filter(voucher_date__gte=date_from)
    if date_to:
        queryset = queryset.filter(voucher_date__lte=date_to)
    if payer_name:
        queryset = queryset.filter(payer_name__icontains=payer_name)
    if receipt_mode:
        queryset = queryset.filter(receipt_mode=receipt_mode)
    
    vouchers = queryset.order_by('-voucher_date', '-created_at')[:50]
    
    data = []
    for voucher in vouchers:
        data.append({
            'id': voucher.id,
            'voucher_number': voucher.voucher_number,
            'payer_name': voucher.payer_name,
            'receipt_mode': voucher.get_receipt_mode_display(),
            'amount': float(voucher.amount),
            'voucher_date': voucher.voucher_date.isoformat(),
            'reference_number': voucher.reference_number or '',
        })
    
    return JsonResponse({'vouchers': data})


@login_required
@require_GET
def deposit_slip_summary(request):
    """Get deposit slip summary statistics"""
    
    total_slips = DepositSlip.objects.count()
    draft_slips = DepositSlip.objects.filter(status='draft').count()
    submitted_slips = DepositSlip.objects.filter(status='submitted').count()
    confirmed_slips = DepositSlip.objects.filter(status='confirmed').count()
    
    total_amount = DepositSlip.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    confirmed_amount = DepositSlip.objects.filter(status='confirmed').aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Available vouchers for deposit
    available_vouchers = ReceiptVoucher.objects.filter(
        status='received',
        deposit_slip_items__isnull=True
    )
    available_count = available_vouchers.count()
    available_amount = available_vouchers.aggregate(total=Sum('amount'))['total'] or 0
    
    data = {
        'total_slips': total_slips,
        'draft_slips': draft_slips,
        'submitted_slips': submitted_slips,
        'confirmed_slips': confirmed_slips,
        'total_amount': float(total_amount),
        'confirmed_amount': float(confirmed_amount),
        'available_vouchers': available_count,
        'available_amount': float(available_amount),
    }
    
    return JsonResponse(data)
