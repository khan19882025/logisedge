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

from .models import ContraEntry, ContraEntryDetail, ContraEntryAudit
from .forms import ContraEntryForm, ContraEntryDetailInlineFormSet, ContraEntrySearchForm


@login_required
def contra_entry_list(request):
    """List all contra entries with search and filtering"""
    search_form = ContraEntrySearchForm(request.GET)
    contra_entries = ContraEntry.objects.all()
    
    # Apply search filters
    if search_form.is_valid():
        search_type = search_form.cleaned_data.get('search_type')
        search_term = search_form.cleaned_data.get('search_term')
        status = search_form.cleaned_data.get('status')
        date_from = search_form.cleaned_data.get('date_from')
        date_to = search_form.cleaned_data.get('date_to')
        
        if search_term:
            if search_type == 'voucher_number':
                contra_entries = contra_entries.filter(voucher_number__icontains=search_term)
            elif search_type == 'narration':
                contra_entries = contra_entries.filter(narration__icontains=search_term)
            elif search_type == 'reference_number':
                contra_entries = contra_entries.filter(reference_number__icontains=search_term)
            elif search_type == 'account':
                contra_entries = contra_entries.filter(entries__account__name__icontains=search_term).distinct()
        
        if status:
            contra_entries = contra_entries.filter(status=status)
        
        if date_from:
            contra_entries = contra_entries.filter(date__gte=date_from)
        
        if date_to:
            contra_entries = contra_entries.filter(date__lte=date_to)
    
    # Pagination
    paginator = Paginator(contra_entries, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Summary statistics
    total_entries = contra_entries.count()
    draft_entries = contra_entries.filter(status='draft').count()
    posted_entries = contra_entries.filter(status='posted').count()
    cancelled_entries = contra_entries.filter(status='cancelled').count()
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_entries': total_entries,
        'draft_entries': draft_entries,
        'posted_entries': posted_entries,
        'cancelled_entries': cancelled_entries,
    }
    
    return render(request, 'contra_entry/contra_entry_list.html', context)


@login_required
def contra_entry_create(request):
    """Create a new contra entry"""
    if request.method == 'POST':
        form = ContraEntryForm(request.POST)
        formset = ContraEntryDetailInlineFormSet(request.POST, instance=form.instance)
        
        if form.is_valid() and formset.is_valid():
            contra_entry = form.save(commit=False)
            contra_entry.created_by = request.user
            contra_entry.save()
            
            # Save audit trail
            ContraEntryAudit.objects.create(
                contra_entry=contra_entry,
                action='created',
                description=f'Contra entry created by {request.user.get_full_name()}',
                user=request.user
            )
            
            # Save formset
            formset.instance = contra_entry
            formset.save()
            
            messages.success(request, f'Contra entry {contra_entry.voucher_number} created successfully.')
            return redirect('contra_entry_detail', pk=contra_entry.pk)
    else:
        form = ContraEntryForm()
        formset = ContraEntryDetailInlineFormSet()
    
    context = {
        'form': form,
        'formset': formset,
        'title': 'Create Contra Entry',
        'submit_text': 'Create Entry',
    }
    
    return render(request, 'contra_entry/contra_entry_form.html', context)


@login_required
def contra_entry_edit(request, pk):
    """Edit an existing contra entry"""
    contra_entry = get_object_or_404(ContraEntry, pk=pk)
    
    if not contra_entry.can_edit:
        messages.error(request, 'This contra entry cannot be edited.')
        return redirect('contra_entry_detail', pk=pk)
    
    if request.method == 'POST':
        form = ContraEntryForm(request.POST, instance=contra_entry)
        formset = ContraEntryDetailInlineFormSet(request.POST, instance=contra_entry)
        
        if form.is_valid() and formset.is_valid():
            contra_entry = form.save(commit=False)
            contra_entry.updated_by = request.user
            contra_entry.save()
            
            # Save audit trail
            ContraEntryAudit.objects.create(
                contra_entry=contra_entry,
                action='updated',
                description=f'Contra entry updated by {request.user.get_full_name()}',
                user=request.user
            )
            
            # Save formset
            formset.save()
            
            messages.success(request, f'Contra entry {contra_entry.voucher_number} updated successfully.')
            return redirect('contra_entry_detail', pk=contra_entry.pk)
    else:
        form = ContraEntryForm(instance=contra_entry)
        formset = ContraEntryDetailInlineFormSet(instance=contra_entry)
    
    context = {
        'form': form,
        'formset': formset,
        'contra_entry': contra_entry,
        'title': 'Edit Contra Entry',
        'submit_text': 'Update Entry',
    }
    
    return render(request, 'contra_entry/contra_entry_form.html', context)


@login_required
def contra_entry_detail(request, pk):
    """View contra entry details"""
    contra_entry = get_object_or_404(ContraEntry, pk=pk)
    
    context = {
        'contra_entry': contra_entry,
        'entries': contra_entry.entries.all(),
        'audit_trail': contra_entry.audit_trail.all()[:10],  # Last 10 audit entries
    }
    
    return render(request, 'contra_entry/contra_entry_detail.html', context)


@login_required
def contra_entry_delete(request, pk):
    """Delete a contra entry"""
    contra_entry = get_object_or_404(ContraEntry, pk=pk)
    
    if not contra_entry.can_edit:
        messages.error(request, 'This contra entry cannot be deleted.')
        return redirect('contra_entry_detail', pk=pk)
    
    if request.method == 'POST':
        voucher_number = contra_entry.voucher_number
        contra_entry.delete()
        messages.success(request, f'Contra entry {voucher_number} deleted successfully.')
        return redirect('contra_entry_list')
    
    context = {
        'contra_entry': contra_entry,
    }
    
    return render(request, 'contra_entry/contra_entry_confirm_delete.html', context)


@login_required
@require_POST
def contra_entry_post(request, pk):
    """Post a contra entry"""
    contra_entry = get_object_or_404(ContraEntry, pk=pk)
    
    if not contra_entry.can_post:
        messages.error(request, 'This contra entry cannot be posted.')
        return redirect('contra_entry_detail', pk=pk)
    
    try:
        contra_entry.status = 'posted'
        contra_entry.posted_at = timezone.now()
        contra_entry.posted_by = request.user
        contra_entry.save()
        
        # Create audit trail
        ContraEntryAudit.objects.create(
            contra_entry=contra_entry,
            action='posted',
            description=f'Contra entry posted by {request.user.get_full_name()}',
            user=request.user
        )
        
        messages.success(request, f'Contra entry {contra_entry.voucher_number} posted successfully.')
    except Exception as e:
        messages.error(request, f'Error posting contra entry: {str(e)}')
    
    return redirect('contra_entry_detail', pk=pk)


@login_required
@require_POST
def contra_entry_cancel(request, pk):
    """Cancel a contra entry"""
    contra_entry = get_object_or_404(ContraEntry, pk=pk)
    
    if not contra_entry.can_cancel:
        messages.error(request, 'This contra entry cannot be cancelled.')
        return redirect('contra_entry_detail', pk=pk)
    
    try:
        contra_entry.status = 'cancelled'
        contra_entry.save()
        
        # Create audit trail
        ContraEntryAudit.objects.create(
            contra_entry=contra_entry,
            action='cancelled',
            description=f'Contra entry cancelled by {request.user.get_full_name()}',
            user=request.user
        )
        
        messages.success(request, f'Contra entry {contra_entry.voucher_number} cancelled successfully.')
    except Exception as e:
        messages.error(request, f'Error cancelling contra entry: {str(e)}')
    
    return redirect('contra_entry_detail', pk=pk)


@login_required
def contra_entry_print(request, pk):
    """Print contra entry"""
    contra_entry = get_object_or_404(ContraEntry, pk=pk)
    
    context = {
        'contra_entry': contra_entry,
        'entries': contra_entry.entries.all(),
    }
    
    return render(request, 'contra_entry/contra_entry_print.html', context)


# AJAX Views
@login_required
def ajax_account_search(request):
    """AJAX endpoint for account search"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    from chart_of_accounts.models import ChartOfAccount
    accounts = ChartOfAccount.objects.filter(
        Q(name__icontains=query) | Q(account_code__icontains=query),
        account_type__name__in=['Bank', 'Cash']
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
def ajax_contra_entry_summary(request):
    """AJAX endpoint for contra entry summary statistics"""
    try:
        # Get date range from request
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        
        queryset = ContraEntry.objects.all()
        
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        
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
        
        summary = {
            'total_entries': total_entries,
            'draft_entries': draft_entries,
            'posted_entries': posted_entries,
            'cancelled_entries': cancelled_entries,
            'total_debit': float(total_debit),
            'total_credit': float(total_credit),
        }
        
        return JsonResponse({'success': True, 'summary': summary})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def ajax_validate_contra_entry(request):
    """AJAX endpoint for validating contra entry before save"""
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
