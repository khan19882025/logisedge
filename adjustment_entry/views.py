from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from decimal import Decimal
import json

from .models import AdjustmentEntry, AdjustmentEntryDetail, AdjustmentEntryAudit
from .forms import AdjustmentEntryForm, AdjustmentEntryDetailInlineFormSet, AdjustmentEntrySearchForm


@login_required
def adjustment_entry_list(request):
    """List all adjustment entries with search and filtering"""
    search_form = AdjustmentEntrySearchForm(request.GET)
    adjustment_entries = AdjustmentEntry.objects.all()
    
    # Apply search filters
    if search_form.is_valid():
        search_type = search_form.cleaned_data.get('search_type')
        search_term = search_form.cleaned_data.get('search_term')
        status = search_form.cleaned_data.get('status')
        adjustment_type = search_form.cleaned_data.get('adjustment_type')
        date_from = search_form.cleaned_data.get('date_from')
        date_to = search_form.cleaned_data.get('date_to')
        
        if search_term:
            if search_type == 'voucher_number':
                adjustment_entries = adjustment_entries.filter(voucher_number__icontains=search_term)
            elif search_type == 'narration':
                adjustment_entries = adjustment_entries.filter(narration__icontains=search_term)
            elif search_type == 'reference_number':
                adjustment_entries = adjustment_entries.filter(reference_number__icontains=search_term)
            elif search_type == 'account':
                adjustment_entries = adjustment_entries.filter(entries__account__name__icontains=search_term).distinct()
        
        if status:
            adjustment_entries = adjustment_entries.filter(status=status)
        
        if adjustment_type:
            adjustment_entries = adjustment_entries.filter(adjustment_type=adjustment_type)
        
        if date_from:
            adjustment_entries = adjustment_entries.filter(date__gte=date_from)
        
        if date_to:
            adjustment_entries = adjustment_entries.filter(date__lte=date_to)
    
    # Pagination
    paginator = Paginator(adjustment_entries, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Summary statistics
    total_entries = adjustment_entries.count()
    draft_entries = adjustment_entries.filter(status='draft').count()
    posted_entries = adjustment_entries.filter(status='posted').count()
    cancelled_entries = adjustment_entries.filter(status='cancelled').count()
    
    # Adjustment type statistics
    adjustment_type_stats = {}
    for choice in AdjustmentEntry.ADJUSTMENT_TYPE_CHOICES:
        adjustment_type_stats[choice[1]] = adjustment_entries.filter(adjustment_type=choice[0]).count()
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_entries': total_entries,
        'draft_entries': draft_entries,
        'posted_entries': posted_entries,
        'cancelled_entries': cancelled_entries,
        'adjustment_type_stats': adjustment_type_stats,
    }
    
    return render(request, 'adjustment_entry/adjustment_entry_list.html', context)


@login_required
def adjustment_entry_create(request):
    """Create a new adjustment entry"""
    if request.method == 'POST':
        form = AdjustmentEntryForm(request.POST)
        formset = AdjustmentEntryDetailInlineFormSet(request.POST, instance=form.instance)
        
        if form.is_valid() and formset.is_valid():
            adjustment_entry = form.save(commit=False)
            adjustment_entry.created_by = request.user
            adjustment_entry.save()
            
            # Save audit trail
            AdjustmentEntryAudit.objects.create(
                adjustment_entry=adjustment_entry,
                action='created',
                description=f'Adjustment entry created by {request.user.get_full_name()}',
                user=request.user
            )
            
            # Save formset
            formset.instance = adjustment_entry
            formset.save()
            
            messages.success(request, f'Adjustment entry {adjustment_entry.voucher_number} created successfully.')
            return redirect('adjustment_entry:adjustment_entry_detail', pk=adjustment_entry.pk)
    else:
        form = AdjustmentEntryForm()
        formset = AdjustmentEntryDetailInlineFormSet()
    
    context = {
        'form': form,
        'formset': formset,
        'title': 'Create Adjustment Entry',
        'submit_text': 'Create Entry',
    }
    
    return render(request, 'adjustment_entry/adjustment_entry_form.html', context)


@login_required
def adjustment_entry_edit(request, pk):
    """Edit an existing adjustment entry"""
    adjustment_entry = get_object_or_404(AdjustmentEntry, pk=pk)
    
    if not adjustment_entry.can_edit:
        messages.error(request, 'This adjustment entry cannot be edited.')
        return redirect('adjustment_entry:adjustment_entry_detail', pk=pk)
    
    if request.method == 'POST':
        form = AdjustmentEntryForm(request.POST, instance=adjustment_entry)
        formset = AdjustmentEntryDetailInlineFormSet(request.POST, instance=adjustment_entry)
        
        if form.is_valid() and formset.is_valid():
            adjustment_entry = form.save(commit=False)
            adjustment_entry.updated_by = request.user
            adjustment_entry.save()
            
            # Save audit trail
            AdjustmentEntryAudit.objects.create(
                adjustment_entry=adjustment_entry,
                action='updated',
                description=f'Adjustment entry updated by {request.user.get_full_name()}',
                user=request.user
            )
            
            # Save formset
            formset.save()
            
            messages.success(request, f'Adjustment entry {adjustment_entry.voucher_number} updated successfully.')
            return redirect('adjustment_entry:adjustment_entry_detail', pk=adjustment_entry.pk)
    else:
        form = AdjustmentEntryForm(instance=adjustment_entry)
        formset = AdjustmentEntryDetailInlineFormSet(instance=adjustment_entry)
    
    context = {
        'form': form,
        'formset': formset,
        'adjustment_entry': adjustment_entry,
        'title': 'Edit Adjustment Entry',
        'submit_text': 'Update Entry',
    }
    
    return render(request, 'adjustment_entry/adjustment_entry_form.html', context)


@login_required
def adjustment_entry_detail(request, pk):
    """View adjustment entry details"""
    adjustment_entry = get_object_or_404(AdjustmentEntry, pk=pk)
    
    context = {
        'adjustment_entry': adjustment_entry,
        'entries': adjustment_entry.entries.all(),
        'audit_trail': adjustment_entry.audit_trail.all()[:10],  # Last 10 audit entries
    }
    
    return render(request, 'adjustment_entry/adjustment_entry_detail.html', context)


@login_required
def adjustment_entry_delete(request, pk):
    """Delete an adjustment entry"""
    adjustment_entry = get_object_or_404(AdjustmentEntry, pk=pk)
    
    if not adjustment_entry.can_edit:
        messages.error(request, 'This adjustment entry cannot be deleted.')
        return redirect('adjustment_entry:adjustment_entry_detail', pk=pk)
    
    if request.method == 'POST':
        voucher_number = adjustment_entry.voucher_number
        adjustment_entry.delete()
        messages.success(request, f'Adjustment entry {voucher_number} deleted successfully.')
        return redirect('adjustment_entry:adjustment_entry_list')
    
    context = {
        'adjustment_entry': adjustment_entry,
    }
    
    return render(request, 'adjustment_entry/adjustment_entry_confirm_delete.html', context)


@login_required
@require_POST
def adjustment_entry_post(request, pk):
    """Post an adjustment entry"""
    adjustment_entry = get_object_or_404(AdjustmentEntry, pk=pk)
    
    if not adjustment_entry.can_post:
        messages.error(request, 'This adjustment entry cannot be posted.')
        return redirect('adjustment_entry:adjustment_entry_detail', pk=pk)
    
    try:
        adjustment_entry.status = 'posted'
        adjustment_entry.posted_at = timezone.now()
        adjustment_entry.posted_by = request.user
        adjustment_entry.save()
        
        # Create audit trail
        AdjustmentEntryAudit.objects.create(
            adjustment_entry=adjustment_entry,
            action='posted',
            description=f'Adjustment entry posted by {request.user.get_full_name()}',
            user=request.user
        )
        
        messages.success(request, f'Adjustment entry {adjustment_entry.voucher_number} posted successfully.')
    except Exception as e:
        messages.error(request, f'Error posting adjustment entry: {str(e)}')
    
    return redirect('adjustment_entry:adjustment_entry_detail', pk=pk)


@login_required
@require_POST
def adjustment_entry_cancel(request, pk):
    """Cancel an adjustment entry"""
    adjustment_entry = get_object_or_404(AdjustmentEntry, pk=pk)
    
    if not adjustment_entry.can_cancel:
        messages.error(request, 'This adjustment entry cannot be cancelled.')
        return redirect('adjustment_entry:adjustment_entry_detail', pk=pk)
    
    try:
        adjustment_entry.status = 'cancelled'
        adjustment_entry.save()
        
        # Create audit trail
        AdjustmentEntryAudit.objects.create(
            adjustment_entry=adjustment_entry,
            action='cancelled',
            description=f'Adjustment entry cancelled by {request.user.get_full_name()}',
            user=request.user
        )
        
        messages.success(request, f'Adjustment entry {adjustment_entry.voucher_number} cancelled successfully.')
    except Exception as e:
        messages.error(request, f'Error cancelling adjustment entry: {str(e)}')
    
    return redirect('adjustment_entry:adjustment_entry_detail', pk=pk)


@login_required
def adjustment_entry_print(request, pk):
    """Print adjustment entry"""
    adjustment_entry = get_object_or_404(AdjustmentEntry, pk=pk)
    
    context = {
        'adjustment_entry': adjustment_entry,
        'entries': adjustment_entry.entries.all(),
    }
    
    return render(request, 'adjustment_entry/adjustment_entry_print.html', context)


# AJAX Views
@login_required
def ajax_account_search(request):
    """AJAX endpoint for account search"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    from chart_of_accounts.models import ChartOfAccount
    accounts = ChartOfAccount.objects.filter(
        Q(name__icontains=query) | Q(account_code__icontains=query)
    ).order_by('name')[:10]
    
    results = []
    for account in accounts:
        results.append({
            'id': account.id,
            'text': f'{account.account_code} - {account.name}',
            'account_code': account.account_code,
            'account_name': account.name,
        })
    
    return JsonResponse({'results': results})


@login_required
def ajax_adjustment_entry_summary(request):
    """AJAX endpoint for adjustment entry summary statistics"""
    try:
        # Get date range from request
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        adjustment_type = request.GET.get('adjustment_type')
        
        queryset = AdjustmentEntry.objects.all()
        
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        if adjustment_type:
            queryset = queryset.filter(adjustment_type=adjustment_type)
        
        # Calculate statistics
        total_entries = queryset.count()
        draft_entries = queryset.filter(status='draft').count()
        posted_entries = queryset.filter(status='posted').count()
        cancelled_entries = queryset.filter(status='cancelled').count()
        
        # Calculate total amounts
        total_debit = queryset.aggregate(
            total=Sum('entries__debit')
        )['total'] or Decimal('0.00')
        
        total_credit = queryset.aggregate(
            total=Sum('entries__credit')
        )['total'] or Decimal('0.00')
        
        # Adjustment type breakdown
        adjustment_type_breakdown = {}
        for choice in AdjustmentEntry.ADJUSTMENT_TYPE_CHOICES:
            count = queryset.filter(adjustment_type=choice[0]).count()
            if count > 0:
                adjustment_type_breakdown[choice[1]] = count
        
        summary = {
            'total_entries': total_entries,
            'draft_entries': draft_entries,
            'posted_entries': posted_entries,
            'cancelled_entries': cancelled_entries,
            'total_debit': float(total_debit),
            'total_credit': float(total_credit),
            'adjustment_type_breakdown': adjustment_type_breakdown,
        }
        
        return JsonResponse({'success': True, 'summary': summary})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def ajax_validate_adjustment_entry(request):
    """AJAX endpoint for validating adjustment entry before save"""
    try:
        data = json.loads(request.body)
        entries = data.get('entries', [])
        
        if len(entries) < 2:
            return JsonResponse({
                'valid': False,
                'errors': ['At least two entries are required (one debit, one credit).']
            })
        
        total_debit = Decimal('0.00')
        total_credit = Decimal('0.00')
        has_debit = False
        has_credit = False
        errors = []
        
        for entry in entries:
            if entry.get('debit'):
                total_debit += Decimal(str(entry['debit']))
                has_debit = True
            elif entry.get('credit'):
                total_credit += Decimal(str(entry['credit']))
                has_credit = True
            else:
                errors.append('Each entry must have either debit or credit amount.')
        
        if not has_debit:
            errors.append('At least one debit entry is required.')
        
        if not has_credit:
            errors.append('At least one credit entry is required.')
        
        if total_debit != total_credit:
            errors.append(f'Total debit ({total_debit}) must equal total credit ({total_credit}).')
        
        return JsonResponse({
            'valid': len(errors) == 0,
            'errors': errors,
            'total_debit': float(total_debit),
            'total_credit': float(total_credit),
        })
    
    except Exception as e:
        return JsonResponse({
            'valid': False,
            'errors': [f'Validation error: {str(e)}']
        })
