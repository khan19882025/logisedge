from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.urls import reverse
from .models import RecurringEntry, RecurringEntryLine, GeneratedEntry
from .forms import RecurringEntryForm, RecurringEntryLineFormSet, RecurringEntryLineFormSetHelper, GenerateEntriesForm
from chart_of_accounts.models import ChartOfAccount
from manual_journal_entry.models import JournalEntry
import json
from datetime import date, timedelta


@login_required
def recurring_entry_list(request):
    """List all recurring entries with filtering and pagination"""
    entries = RecurringEntry.objects.all().order_by('-created_at')
    
    # Filtering
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    frequency_filter = request.GET.get('frequency', '')
    
    if search:
        entries = entries.filter(
            Q(template_name__icontains=search) |
            Q(narration__icontains=search)
        )
    
    if status_filter:
        entries = entries.filter(status=status_filter)
    
    if frequency_filter:
        entries = entries.filter(frequency=frequency_filter)
    
    # Pagination
    paginator = Paginator(entries, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Summary statistics
    total_entries = entries.count()
    active_entries = entries.filter(status='ACTIVE').count()
    paused_entries = entries.filter(status='PAUSED').count()
    completed_entries = entries.filter(status='COMPLETED').count()
    
    context = {
        'page_obj': page_obj,
        'total_entries': total_entries,
        'active_entries': active_entries,
        'paused_entries': paused_entries,
        'completed_entries': completed_entries,
        'search': search,
        'status_filter': status_filter,
        'frequency_filter': frequency_filter,
    }
    
    return render(request, 'recurring_journal_entry/recurring_entry_list.html', context)


@login_required
def recurring_entry_create(request):
    """Create a new recurring entry"""
    if request.method == 'POST':
        form = RecurringEntryForm(request.POST, user=request.user)
        formset = RecurringEntryLineFormSet(request.POST, instance=form.instance)
        
        if form.is_valid():
            recurring_entry = form.save(commit=False)
            recurring_entry.created_by = request.user
            recurring_entry.save()
            
            # Save formset
            if formset.is_valid():
                formset.instance = recurring_entry
                formset.save()
                
                # Validate totals
                try:
                    RecurringEntryLineFormSetHelper.clean_formset(formset)
                    messages.success(request, 'Recurring entry created successfully!')
                    return redirect('recurring_journal_entry:recurring_entry_detail', pk=recurring_entry.pk)
                except ValidationError as e:
                    recurring_entry.delete()
                    messages.error(request, str(e))
            else:
                recurring_entry.delete()
                messages.error(request, 'Please correct the errors below.')
    else:
        form = RecurringEntryForm(user=request.user)
        formset = RecurringEntryLineFormSet()
    
    context = {
        'form': form,
        'formset': formset,
        'title': 'Create Recurring Entry',
        'submit_text': 'Create Template',
    }
    
    return render(request, 'recurring_journal_entry/recurring_entry_form.html', context)


@login_required
def recurring_entry_edit(request, pk):
    """Edit an existing recurring entry"""
    recurring_entry = get_object_or_404(RecurringEntry, pk=pk)
    
    # Check if entry can be edited
    if recurring_entry.status == 'COMPLETED':
        messages.warning(request, 'Completed entries cannot be edited.')
        return redirect('recurring_journal_entry:recurring_entry_detail', pk=pk)
    
    if request.method == 'POST':
        form = RecurringEntryForm(request.POST, instance=recurring_entry, user=request.user)
        formset = RecurringEntryLineFormSet(request.POST, instance=recurring_entry)
        
        if form.is_valid():
            recurring_entry = form.save(commit=False)
            recurring_entry.updated_by = request.user
            recurring_entry.save()
            
            if formset.is_valid():
                formset.save()
                
                # Validate totals
                try:
                    RecurringEntryLineFormSetHelper.clean_formset(formset)
                    messages.success(request, 'Recurring entry updated successfully!')
                    return redirect('recurring_journal_entry:recurring_entry_detail', pk=recurring_entry.pk)
                except ValidationError as e:
                    messages.error(request, str(e))
            else:
                messages.error(request, 'Please correct the errors below.')
    else:
        form = RecurringEntryForm(instance=recurring_entry, user=request.user)
        formset = RecurringEntryLineFormSet(instance=recurring_entry)
    
    context = {
        'form': form,
        'formset': formset,
        'recurring_entry': recurring_entry,
        'title': 'Edit Recurring Entry',
        'submit_text': 'Update Template',
    }
    
    return render(request, 'recurring_journal_entry/recurring_entry_form.html', context)


@login_required
def recurring_entry_detail(request, pk):
    """View recurring entry details"""
    recurring_entry = get_object_or_404(RecurringEntry, pk=pk)
    
    # Get next posting date
    next_posting_date = recurring_entry.get_next_posting_date()
    
    # Get recent generated entries
    recent_generated = recurring_entry.generated_entries.all()[:10]
    
    # Get statistics
    total_generated = recurring_entry.generated_entries.count()
    total_amount = recurring_entry.generated_entries.aggregate(
        total=Sum('journal_entry__total_debit')
    )['total'] or 0
    
    context = {
        'recurring_entry': recurring_entry,
        'next_posting_date': next_posting_date,
        'recent_generated': recent_generated,
        'total_generated': total_generated,
        'total_amount': total_amount,
    }
    
    return render(request, 'recurring_journal_entry/recurring_entry_detail.html', context)


@login_required
def recurring_entry_delete(request, pk):
    """Delete a recurring entry"""
    recurring_entry = get_object_or_404(RecurringEntry, pk=pk)
    
    if request.method == 'POST':
        if recurring_entry.generated_entries.exists():
            messages.error(request, 'Cannot delete recurring entry with generated entries. Cancel it instead.')
        else:
            recurring_entry.delete()
            messages.success(request, 'Recurring entry deleted successfully!')
            return redirect('recurring_journal_entry:recurring_entry_list')
    
    context = {
        'recurring_entry': recurring_entry,
    }
    
    return render(request, 'recurring_journal_entry/recurring_entry_confirm_delete.html', context)


@login_required
def recurring_entry_pause(request, pk):
    """Pause a recurring entry"""
    recurring_entry = get_object_or_404(RecurringEntry, pk=pk)
    
    if request.method == 'POST':
        if recurring_entry.status == 'ACTIVE':
            recurring_entry.pause()
            messages.success(request, 'Recurring entry paused successfully!')
        else:
            messages.error(request, 'Only active entries can be paused.')
    
    return redirect('recurring_journal_entry:recurring_entry_detail', pk=pk)


@login_required
def recurring_entry_resume(request, pk):
    """Resume a recurring entry"""
    recurring_entry = get_object_or_404(RecurringEntry, pk=pk)
    
    if request.method == 'POST':
        if recurring_entry.status == 'PAUSED':
            recurring_entry.resume()
            messages.success(request, 'Recurring entry resumed successfully!')
        else:
            messages.error(request, 'Only paused entries can be resumed.')
    
    return redirect('recurring_journal_entry:recurring_entry_detail', pk=pk)


@login_required
def recurring_entry_cancel(request, pk):
    """Cancel a recurring entry"""
    recurring_entry = get_object_or_404(RecurringEntry, pk=pk)
    
    if request.method == 'POST':
        if recurring_entry.status in ['ACTIVE', 'PAUSED']:
            recurring_entry.cancel()
            messages.success(request, 'Recurring entry cancelled successfully!')
        else:
            messages.error(request, 'Only active or paused entries can be cancelled.')
    
    return redirect('recurring_journal_entry:recurring_entry_detail', pk=pk)


@login_required
def generate_entry(request, pk):
    """Manually generate a journal entry from recurring template"""
    recurring_entry = get_object_or_404(RecurringEntry, pk=pk)
    
    if request.method == 'POST':
        form = GenerateEntriesForm(recurring_entry, request.POST)
        if form.is_valid():
            posting_date = form.cleaned_data['posting_date']
            auto_post = form.cleaned_data['auto_post']
            
            try:
                # Generate the journal entry
                journal_entry = recurring_entry.generate_journal_entry(posting_date, request.user)
                
                if auto_post:
                    journal_entry.post_entry(request.user)
                    messages.success(request, f'Journal entry generated and posted for {posting_date}!')
                else:
                    messages.success(request, f'Journal entry generated for {posting_date}!')
                
                return redirect('recurring_journal_entry:recurring_entry_detail', pk=pk)
            except Exception as e:
                messages.error(request, f'Error generating entry: {str(e)}')
    else:
        form = GenerateEntriesForm(recurring_entry)
    
    context = {
        'form': form,
        'recurring_entry': recurring_entry,
    }
    
    return render(request, 'recurring_journal_entry/generate_entry.html', context)


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
def recurring_entry_dashboard(request):
    """Dashboard view for recurring entries"""
    # Get recent entries
    recent_entries = RecurringEntry.objects.all().order_by('-created_at')[:10]
    
    # Get statistics
    total_entries = RecurringEntry.objects.count()
    active_entries = RecurringEntry.objects.filter(status='ACTIVE').count()
    paused_entries = RecurringEntry.objects.filter(status='PAUSED').count()
    completed_entries = RecurringEntry.objects.filter(status='COMPLETED').count()
    
    # Get upcoming entries (next 30 days)
    today = date.today()
    upcoming_entries = []
    for entry in RecurringEntry.objects.filter(status='ACTIVE'):
        next_date = entry.get_next_posting_date()
        if next_date and next_date <= today + timedelta(days=30):
            upcoming_entries.append({
                'entry': entry,
                'next_date': next_date,
                'days_until': (next_date - today).days
            })
    
    # Sort by next posting date
    upcoming_entries.sort(key=lambda x: x['next_date'])
    
    # Get monthly statistics for current year
    current_year = timezone.now().year
    monthly_stats = RecurringEntry.objects.filter(
        created_at__year=current_year
    ).values('created_at__month').annotate(
        count=Count('id')
    ).order_by('created_at__month')
    
    # Prepare chart data
    chart_data = {
        'labels': [],
        'data': []
    }
    
    for month_data in monthly_stats:
        month_name = timezone.datetime(current_year, month_data['created_at__month'], 1).strftime('%b')
        chart_data['labels'].append(month_name)
        chart_data['data'].append(month_data['count'])
    
    context = {
        'recent_entries': recent_entries,
        'upcoming_entries': upcoming_entries[:5],  # Show only next 5
        'total_entries': total_entries,
        'active_entries': active_entries,
        'paused_entries': paused_entries,
        'completed_entries': completed_entries,
        'chart_data': json.dumps(chart_data),
    }
    
    return render(request, 'recurring_journal_entry/dashboard.html', context)


@login_required
def generated_entries_list(request, pk):
    """List all generated entries for a recurring template"""
    recurring_entry = get_object_or_404(RecurringEntry, pk=pk)
    generated_entries = recurring_entry.generated_entries.all().order_by('-posting_date')
    
    # Pagination
    paginator = Paginator(generated_entries, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'recurring_entry': recurring_entry,
        'page_obj': page_obj,
    }
    
    return render(request, 'recurring_journal_entry/generated_entries_list.html', context)
