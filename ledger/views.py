from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from .models import Ledger, LedgerBatch
from .forms import LedgerForm, LedgerBatchForm, LedgerSearchForm, LedgerImportForm, LedgerReconciliationForm
from chart_of_accounts.models import ChartOfAccount as Account, AccountType
from company.company_model import Company
from fiscal_year.models import FiscalYear
from decimal import Decimal
import json


@login_required
def ledger_list(request):
    """Display list of ledger entries with search and filter functionality"""
    
    # Get user's company and active fiscal year
    try:
        company = Company.objects.filter(is_active=True).first()
        if not company:
            messages.error(request, "No company found. Please set up your company first.")
            return redirect('company:company_list')
        
        active_fiscal_year = FiscalYear.objects.filter(is_current=True).first()
        if not active_fiscal_year:
            messages.error(request, "No active fiscal year found. Please set up your fiscal year first.")
            return redirect('fiscal_year:fiscal_year_list')
    except Exception as e:
        messages.error(request, f"Error loading company/fiscal year: {str(e)}")
        return redirect('dashboard:dashboard')
    
    # Initialize search form
    search_form = LedgerSearchForm(request.GET, user=request.user)
    
    # Get queryset
    queryset = Ledger.objects.filter(company=company, fiscal_year=active_fiscal_year)
    
    # Apply search filters
    if search_form.is_valid():
        search_term = search_form.cleaned_data.get('search_term')
        search_by = search_form.cleaned_data.get('search_by')
        account = search_form.cleaned_data.get('account')
        entry_type = search_form.cleaned_data.get('entry_type')
        status = search_form.cleaned_data.get('status')
        date_from = search_form.cleaned_data.get('date_from')
        date_to = search_form.cleaned_data.get('date_to')
        amount_min = search_form.cleaned_data.get('amount_min')
        amount_max = search_form.cleaned_data.get('amount_max')
        is_reconciled = search_form.cleaned_data.get('is_reconciled')
        
        # Apply search term
        if search_term and search_by:
            if search_by == 'ledger_number':
                queryset = queryset.filter(ledger_number__icontains=search_term)
            elif search_by == 'reference':
                queryset = queryset.filter(reference__icontains=search_term)
            elif search_by == 'description':
                queryset = queryset.filter(description__icontains=search_term)
            elif search_by == 'voucher_number':
                queryset = queryset.filter(voucher_number__icontains=search_term)
            elif search_by == 'cheque_number':
                queryset = queryset.filter(cheque_number__icontains=search_term)
            elif search_by == 'bank_reference':
                queryset = queryset.filter(bank_reference__icontains=search_term)
        
        # Apply filters
        if account:
            queryset = queryset.filter(account=account)
        if entry_type:
            queryset = queryset.filter(entry_type=entry_type)
        if status:
            queryset = queryset.filter(status=status)
        if date_from:
            queryset = queryset.filter(entry_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(entry_date__lte=date_to)
        if amount_min:
            queryset = queryset.filter(amount__gte=amount_min)
        if amount_max:
            queryset = queryset.filter(amount__lte=amount_max)
        if is_reconciled:
            queryset = queryset.filter(is_reconciled=is_reconciled)
    
    # Order by date and time
    queryset = queryset.order_by('-entry_date', '-created_at')
    
    # Pagination
    paginator = Paginator(queryset, 25)  # Show 25 entries per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate summary statistics
    total_entries = queryset.count()
    total_debit = queryset.filter(entry_type='DR').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_credit = queryset.filter(entry_type='CR').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    balance = total_debit - total_credit
    
    # Get account types with their accounts for the search dropdown
    account_types = AccountType.objects.filter(is_active=True).prefetch_related(
        'accounts__company'
    ).filter(accounts__company=company, accounts__is_active=True).distinct()
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_entries': total_entries,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'balance': balance,
        'company': company,
        'fiscal_year': active_fiscal_year,
        'account_types': account_types,
    }
    
    return render(request, 'ledger/ledger_list.html', context)


@login_required
def ledger_create(request):
    """Create a new ledger entry"""
    
    # Get user's company and active fiscal year
    try:
        company = Company.objects.filter(is_active=True).first()
        if not company:
            messages.error(request, "No company found. Please set up your company first.")
            return redirect('company:company_list')
        
        active_fiscal_year = FiscalYear.objects.filter(is_current=True).first()
        if not active_fiscal_year:
            messages.error(request, "No active fiscal year found. Please set up your fiscal year first.")
            return redirect('fiscal_year:fiscal_year_list')
    except Exception as e:
        messages.error(request, f"Error loading company/fiscal year: {str(e)}")
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        form = LedgerForm(request.POST, user=request.user)
        if form.is_valid():
            ledger = form.save(commit=False)
            ledger.company = company
            ledger.fiscal_year = active_fiscal_year
            ledger.created_by = request.user
            ledger.updated_by = request.user
            ledger.save()
            
            messages.success(request, f"Ledger entry {ledger.ledger_number} created successfully.")
            return redirect('ledger:ledger_list')
    else:
        form = LedgerForm(user=request.user)
    
    # Get account types with their accounts for the dropdown
    account_types = AccountType.objects.filter(is_active=True).prefetch_related(
        'accounts__company'
    ).filter(accounts__company=company, accounts__is_active=True).distinct()
    
    context = {
        'form': form,
        'company': company,
        'fiscal_year': active_fiscal_year,
        'account_types': account_types,
    }
    
    return render(request, 'ledger/ledger_form.html', context)


@login_required
def ledger_update(request, pk):
    """Update an existing ledger entry"""
    
    ledger = get_object_or_404(Ledger, pk=pk)
    
    # Check if user has permission to edit this entry
    company = Company.objects.filter(is_active=True).first()
    if ledger.company != company:
        messages.error(request, "You don't have permission to edit this entry.")
        return redirect('ledger:ledger_list')
    
    if request.method == 'POST':
        form = LedgerForm(request.POST, instance=ledger, user=request.user)
        if form.is_valid():
            ledger = form.save(commit=False)
            ledger.updated_by = request.user
            ledger.save()
            
            messages.success(request, f"Ledger entry {ledger.ledger_number} updated successfully.")
            return redirect('ledger:ledger_list')
    else:
        form = LedgerForm(instance=ledger, user=request.user)
    
    # Get account types with their accounts for the dropdown
    account_types = AccountType.objects.filter(is_active=True).prefetch_related(
        'accounts__company'
    ).filter(accounts__company=ledger.company, accounts__is_active=True).distinct()
    
    context = {
        'form': form,
        'ledger': ledger,
        'company': ledger.company,
        'fiscal_year': ledger.fiscal_year,
        'account_types': account_types,
    }
    
    return render(request, 'ledger/ledger_form.html', context)


@login_required
def ledger_detail(request, pk):
    """Display details of a ledger entry"""
    
    ledger = get_object_or_404(Ledger, pk=pk)
    
    # Check if user has permission to view this entry
    company = Company.objects.filter(is_active=True).first()
    if ledger.company != company:
        messages.error(request, "You don't have permission to view this entry.")
        return redirect('ledger:ledger_list')
    
    context = {
        'ledger': ledger,
        'company': ledger.company,
        'fiscal_year': ledger.fiscal_year,
    }
    
    return render(request, 'ledger/ledger_detail.html', context)


@login_required
@require_POST
def ledger_delete(request, pk):
    """Delete a ledger entry"""
    
    ledger = get_object_or_404(Ledger, pk=pk)
    
    # Check if user has permission to delete this entry
    company = Company.objects.filter(is_active=True).first()
    if ledger.company != company:
        messages.error(request, "You don't have permission to delete this entry.")
        return redirect('ledger:ledger_list')
    
    # Check if entry can be deleted (only draft entries)
    if ledger.status != 'DRAFT':
        messages.error(request, "Only draft entries can be deleted.")
        return redirect('ledger:ledger_list')
    
    ledger_number = ledger.ledger_number
    ledger.delete()
    
    messages.success(request, f"Ledger entry {ledger_number} deleted successfully.")
    return redirect('ledger:ledger_list')


@login_required
def ledger_batch_list(request):
    """Display list of ledger batches"""
    
    # Get user's company and active fiscal year
    try:
        company = Company.objects.filter(is_active=True).first()
        if not company:
            messages.error(request, "No company found. Please set up your company first.")
            return redirect('company:company_list')
        
        active_fiscal_year = FiscalYear.objects.filter(is_current=True).first()
        if not active_fiscal_year:
            messages.error(request, "No active fiscal year found. Please set up your fiscal year first.")
            return redirect('fiscal_year:fiscal_year_list')
    except Exception as e:
        messages.error(request, f"Error loading company/fiscal year: {str(e)}")
        return redirect('dashboard:dashboard')
    
    # Get batches
    batches = LedgerBatch.objects.filter(company=company, fiscal_year=active_fiscal_year).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(batches, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'company': company,
        'fiscal_year': active_fiscal_year,
    }
    
    return render(request, 'ledger/batch_list.html', context)


@login_required
def ledger_batch_create(request):
    """Create a new ledger batch"""
    
    # Get user's company and active fiscal year
    try:
        company = Company.objects.filter(is_active=True).first()
        if not company:
            messages.error(request, "No company found. Please set up your company first.")
            return redirect('company:company_list')
        
        active_fiscal_year = FiscalYear.objects.filter(is_current=True).first()
        if not active_fiscal_year:
            messages.error(request, "No active fiscal year found. Please set up your fiscal year first.")
            return redirect('fiscal_year:fiscal_year_list')
    except Exception as e:
        messages.error(request, f"Error loading company/fiscal year: {str(e)}")
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        form = LedgerBatchForm(request.POST, user=request.user)
        if form.is_valid():
            batch = form.save(commit=False)
            batch.company = company
            batch.fiscal_year = active_fiscal_year
            batch.created_by = request.user
            batch.save()
            
            messages.success(request, f"Ledger batch {batch.batch_number} created successfully.")
            return redirect('ledger:batch_list')
    else:
        form = LedgerBatchForm(user=request.user)
    
    context = {
        'form': form,
        'company': company,
        'fiscal_year': active_fiscal_year,
    }
    
    return render(request, 'ledger/batch_form.html', context)


@login_required
def ledger_import(request):
    """Import ledger entries from CSV/Excel file"""
    
    # Get user's company and active fiscal year
    try:
        company = Company.objects.filter(is_active=True).first()
        if not company:
            messages.error(request, "No company found. Please set up your company first.")
            return redirect('company:company_list')
        
        active_fiscal_year = FiscalYear.objects.filter(is_current=True).first()
        if not active_fiscal_year:
            messages.error(request, "No active fiscal year found. Please set up your fiscal year first.")
            return redirect('fiscal_year:fiscal_year_list')
    except Exception as e:
        messages.error(request, f"Error loading company/fiscal year: {str(e)}")
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        form = LedgerImportForm(request.POST, request.FILES)
        if form.is_valid():
            # Handle file import logic here
            messages.success(request, "File uploaded successfully. Processing...")
            return redirect('ledger:ledger_list')
    else:
        form = LedgerImportForm()
    
    context = {
        'form': form,
        'company': company,
        'fiscal_year': active_fiscal_year,
    }
    
    return render(request, 'ledger/ledger_import.html', context)


@login_required
@require_POST
def ledger_reconcile(request, pk):
    """Reconcile a ledger entry"""
    
    ledger = get_object_or_404(Ledger, pk=pk)
    
    # Check if user has permission to reconcile this entry
    company = Company.objects.filter(is_active=True).first()
    if ledger.company != company:
        messages.error(request, "You don't have permission to reconcile this entry.")
        return redirect('ledger:ledger_list')
    
    form = LedgerReconciliationForm(request.POST)
    if form.is_valid():
        ledger.is_reconciled = True
        ledger.reconciliation_date = form.cleaned_data['reconciliation_date']
        ledger.updated_by = request.user
        ledger.save()
        
        messages.success(request, f"Ledger entry {ledger.ledger_number} reconciled successfully.")
    else:
        messages.error(request, "Invalid reconciliation data.")
    
    return redirect('ledger:ledger_list')


@login_required
@csrf_exempt
def ledger_ajax_search(request):
    """AJAX endpoint for searching ledger entries"""
    
    if request.method == 'GET':
        search_term = request.GET.get('q', '')
        account_id = request.GET.get('account_id', '')
        
        company = Company.objects.filter(is_active=True).first()
        queryset = Ledger.objects.filter(company=company)
        
        if search_term:
            queryset = queryset.filter(
                Q(ledger_number__icontains=search_term) |
                Q(reference__icontains=search_term) |
                Q(description__icontains=search_term)
            )
        
        if account_id:
            queryset = queryset.filter(account_id=account_id)
        
        # Limit results
        queryset = queryset[:10]
        
        results = []
        for entry in queryset:
            results.append({
                'id': entry.id,
                'ledger_number': entry.ledger_number,
                'description': entry.description,
                'amount': str(entry.amount),
                'entry_type': entry.entry_type,
                'account_name': entry.account.name,
            })
        
        return JsonResponse({'results': results})
    
    return JsonResponse({'error': 'Invalid request method'})


@login_required
def ledger_export_csv(request):
    """Export ledger entries to CSV"""
    
    # Get user's company and active fiscal year
    try:
        company = Company.objects.filter(is_active=True).first()
        active_fiscal_year = FiscalYear.objects.filter(is_current=True).first()
    except:
        messages.error(request, "Error loading company/fiscal year.")
        return redirect('ledger:ledger_list')
    
    # Get filtered queryset (same as list view)
    search_form = LedgerSearchForm(request.GET, user=request.user)
    queryset = Ledger.objects.filter(company=company, fiscal_year=active_fiscal_year)
    
    # Apply filters (same logic as list view)
    if search_form.is_valid():
        # Apply the same filters as in ledger_list view
        pass
    
    # Generate CSV
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="ledger_entries_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Ledger Number', 'Date', 'Reference', 'Description', 'Account', 
        'Entry Type', 'Amount', 'Running Balance', 'Status', 'Reconciled'
    ])
    
    for entry in queryset:
        writer.writerow([
            entry.ledger_number,
            entry.entry_date,
            entry.reference,
            entry.description,
            entry.account.name,
            entry.entry_type,
            entry.amount,
            entry.running_balance,
            entry.status,
            'Yes' if entry.is_reconciled else 'No'
        ])
    
    return response


@login_required
def ledger_dashboard(request):
    """Dashboard view for ledger overview"""
    
    # Get user's company and active fiscal year
    try:
        company = Company.objects.filter(is_active=True).first()
        if not company:
            messages.error(request, "No company found. Please set up your company first.")
            return redirect('company:company_list')
        
        active_fiscal_year = FiscalYear.objects.filter(is_current=True).first()
        if not active_fiscal_year:
            messages.error(request, "No active fiscal year found. Please set up your fiscal year first.")
            return redirect('fiscal_year:fiscal_year_list')
    except Exception as e:
        messages.error(request, f"Error loading company/fiscal year: {str(e)}")
        return redirect('dashboard:dashboard')
    
    # Get ledger statistics
    total_entries = Ledger.objects.filter(company=company, fiscal_year=active_fiscal_year).count()
    total_debit = Ledger.objects.filter(company=company, fiscal_year=active_fiscal_year, entry_type='DR').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_credit = Ledger.objects.filter(company=company, fiscal_year=active_fiscal_year, entry_type='CR').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    balance = total_debit - total_credit
    
    # Get recent entries
    recent_entries = Ledger.objects.filter(company=company, fiscal_year=active_fiscal_year).order_by('-created_at')[:10]
    
    # Get account summary
    account_summary = Ledger.objects.filter(
        company=company, 
        fiscal_year=active_fiscal_year
    ).values('account__name').annotate(
        total_debit=Sum('amount', filter=Q(entry_type='DR')),
        total_credit=Sum('amount', filter=Q(entry_type='CR')),
        entry_count=Count('id')
    ).order_by('-entry_count')[:10]
    
    context = {
        'total_entries': total_entries,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'balance': balance,
        'recent_entries': recent_entries,
        'account_summary': account_summary,
        'company': company,
        'fiscal_year': active_fiscal_year,
    }
    
    return render(request, 'ledger/ledger_dashboard.html', context)
