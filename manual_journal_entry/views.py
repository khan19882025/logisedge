from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.urls import reverse
from .models import JournalEntry, JournalEntryLine
from .forms import JournalEntryForm, JournalEntryLineFormSet, JournalEntryLineFormSetHelper
from chart_of_accounts.models import ChartOfAccount
import json


@login_required
def journal_entry_list(request):
    """List all journal entries with filtering and pagination"""
    entries = JournalEntry.objects.all().order_by('-date', '-created_at')
    
    # Filtering
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if search:
        entries = entries.filter(
            Q(voucher_number__icontains=search) |
            Q(narration__icontains=search) |
            Q(reference_number__icontains=search)
        )
    
    if status_filter:
        entries = entries.filter(status=status_filter)
    
    if date_from:
        entries = entries.filter(date__gte=date_from)
    
    if date_to:
        entries = entries.filter(date__lte=date_to)
    
    # Pagination
    paginator = Paginator(entries, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Summary statistics
    total_entries = entries.count()
    posted_entries = entries.filter(status='POSTED').count()
    draft_entries = entries.filter(status='DRAFT').count()
    void_entries = entries.filter(status='VOID').count()
    
    context = {
        'page_obj': page_obj,
        'total_entries': total_entries,
        'posted_entries': posted_entries,
        'draft_entries': draft_entries,
        'void_entries': void_entries,
        'search': search,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'manual_journal_entry/journal_entry_list.html', context)


@login_required
def journal_entry_create(request):
    """Create a new journal entry"""
    if request.method == 'POST':
        form = JournalEntryForm(request.POST, user=request.user)
        formset = JournalEntryLineFormSet(request.POST, instance=form.instance)
        
        if form.is_valid():
            journal_entry = form.save(commit=False)
            journal_entry.created_by = request.user
            journal_entry.save()
            
            # Save formset
            if formset.is_valid():
                formset.instance = journal_entry
                formset.save()
                
                # Validate totals
                try:
                    JournalEntryLineFormSetHelper.clean_formset(formset)
                    messages.success(request, 'Journal entry created successfully!')
                    return redirect('manual_journal_entry:journal_entry_detail', pk=journal_entry.pk)
                except ValidationError as e:
                    journal_entry.delete()
                    messages.error(request, str(e))
            else:
                journal_entry.delete()
                messages.error(request, 'Please correct the errors below.')
    else:
        form = JournalEntryForm(user=request.user)
        formset = JournalEntryLineFormSet()
    
    context = {
        'form': form,
        'formset': formset,
        'title': 'Create Journal Entry',
        'submit_text': 'Create Entry',
    }
    
    return render(request, 'manual_journal_entry/journal_entry_form.html', context)


@login_required
def journal_entry_edit(request, pk):
    """Edit an existing journal entry"""
    journal_entry = get_object_or_404(JournalEntry, pk=pk)
    
    # Check if entry can be edited
    if journal_entry.status == 'POSTED':
        messages.warning(request, 'Posted entries cannot be edited. Please void the entry first.')
        return redirect('manual_journal_entry:journal_entry_detail', pk=pk)
    
    if request.method == 'POST':
        form = JournalEntryForm(request.POST, instance=journal_entry, user=request.user)
        formset = JournalEntryLineFormSet(request.POST, instance=journal_entry)
        
        if form.is_valid():
            journal_entry = form.save(commit=False)
            journal_entry.updated_by = request.user
            journal_entry.save()
            
            if formset.is_valid():
                formset.save()
                
                # Validate totals
                try:
                    JournalEntryLineFormSetHelper.clean_formset(formset)
                    messages.success(request, 'Journal entry updated successfully!')
                    return redirect('manual_journal_entry:journal_entry_detail', pk=journal_entry.pk)
                except ValidationError as e:
                    messages.error(request, str(e))
            else:
                messages.error(request, 'Please correct the errors below.')
    else:
        form = JournalEntryForm(instance=journal_entry, user=request.user)
        formset = JournalEntryLineFormSet(instance=journal_entry)
    
    context = {
        'form': form,
        'formset': formset,
        'journal_entry': journal_entry,
        'title': 'Edit Journal Entry',
        'submit_text': 'Update Entry',
    }
    
    return render(request, 'manual_journal_entry/journal_entry_form.html', context)


@login_required
def journal_entry_detail(request, pk):
    """View journal entry details"""
    journal_entry = get_object_or_404(JournalEntry, pk=pk)
    
    context = {
        'journal_entry': journal_entry,
    }
    
    return render(request, 'manual_journal_entry/journal_entry_detail.html', context)


@login_required
def journal_entry_delete(request, pk):
    """Delete a journal entry"""
    journal_entry = get_object_or_404(JournalEntry, pk=pk)
    
    if request.method == 'POST':
        if journal_entry.status == 'POSTED':
            messages.error(request, 'Posted entries cannot be deleted. Please void the entry first.')
        else:
            journal_entry.delete()
            messages.success(request, 'Journal entry deleted successfully!')
            return redirect('manual_journal_entry:journal_entry_list')
    
    context = {
        'journal_entry': journal_entry,
    }
    
    return render(request, 'manual_journal_entry/journal_entry_confirm_delete.html', context)


@login_required
def journal_entry_post(request, pk):
    """Post a journal entry"""
    journal_entry = get_object_or_404(JournalEntry, pk=pk)
    
    if request.method == 'POST':
        if journal_entry.status == 'DRAFT':
            if journal_entry.is_balanced:
                journal_entry.post_entry(request.user)
                messages.success(request, 'Journal entry posted successfully!')
            else:
                messages.error(request, 'Journal entry must be balanced before posting.')
        else:
            messages.error(request, 'Only draft entries can be posted.')
    
    return redirect('manual_journal_entry:journal_entry_detail', pk=pk)


@login_required
def journal_entry_void(request, pk):
    """Void a journal entry"""
    journal_entry = get_object_or_404(JournalEntry, pk=pk)
    
    if request.method == 'POST':
        if journal_entry.status == 'POSTED':
            journal_entry.void_entry(request.user)
            messages.success(request, 'Journal entry voided successfully!')
        else:
            messages.error(request, 'Only posted entries can be voided.')
    
    return redirect('manual_journal_entry:journal_entry_detail', pk=pk)


@login_required
@require_http_methods(["GET"])
def ajax_account_search(request):
    """AJAX endpoint for account search"""
    query = request.GET.get('q', '')
    page = request.GET.get('page', 1)
    
    if len(query) < 2:
        return JsonResponse({'results': [], 'pagination': {'more': False}})
    
    accounts = ChartOfAccount.objects.filter(
        Q(account_code__icontains=query) |
        Q(name__icontains=query),
        is_active=True
    ).order_by('account_code')[:20]
    
    results = []
    for account in accounts:
        results.append({
            'id': account.id,
            'text': f"{account.account_code} - {account.name}",
            'account_code': account.account_code,
            'account_name': account.name,
        })
    
    return JsonResponse({
        'results': results,
        'pagination': {'more': False}
    })


@login_required
def journal_entry_dashboard(request):
    """Dashboard view for journal entries"""
    # Get recent entries
    recent_entries = JournalEntry.objects.all().order_by('-created_at')[:10]
    
    # Get statistics
    total_entries = JournalEntry.objects.count()
    posted_entries = JournalEntry.objects.filter(status='POSTED').count()
    draft_entries = JournalEntry.objects.filter(status='DRAFT').count()
    void_entries = JournalEntry.objects.filter(status='VOID').count()
    
    # Get monthly totals for current year
    current_year = timezone.now().year
    monthly_totals = JournalEntry.objects.filter(
        date__year=current_year,
        status='POSTED'
    ).values('date__month').annotate(
        total_debit=Sum('total_debit'),
        total_credit=Sum('total_credit')
    ).order_by('date__month')
    
    # Prepare chart data
    chart_data = {
        'labels': [],
        'debit_data': [],
        'credit_data': []
    }
    
    for month_data in monthly_totals:
        month_name = timezone.datetime(current_year, month_data['date__month'], 1).strftime('%b')
        chart_data['labels'].append(month_name)
        chart_data['debit_data'].append(float(month_data['total_debit'] or 0))
        chart_data['credit_data'].append(float(month_data['total_credit'] or 0))
    
    context = {
        'recent_entries': recent_entries,
        'total_entries': total_entries,
        'posted_entries': posted_entries,
        'draft_entries': draft_entries,
        'void_entries': void_entries,
        'chart_data': json.dumps(chart_data),
    }
    
    return render(request, 'manual_journal_entry/dashboard.html', context) 