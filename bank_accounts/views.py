from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from django.utils import timezone
from django.db import transaction
import json
import csv
from io import StringIO

from .models import BankAccount, BankAccountTransaction
from .forms import BankAccountForm, BankAccountSearchForm, BankAccountTransactionForm, BankAccountBulkActionForm
from company.company_model import Company
from chart_of_accounts.models import ChartOfAccount


@login_required
def bank_account_list(request):
    """List view for bank accounts with search and filters"""
    
    # Get search form data
    search_form = BankAccountSearchForm(request.GET)
    
    # Get company
    company = Company.objects.filter(is_active=True).first()
    if not company:
        messages.error(request, "No active company found.")
        return redirect('dashboard:dashboard')
    
    # Base queryset
    queryset = BankAccount.objects.filter(company=company).select_related(
        'currency', 'chart_account'
    )
    
    # Apply filters
    if search_form.is_valid():
        search_term = search_form.cleaned_data.get('search_term')
        search_by = search_form.cleaned_data.get('search_by', 'bank_name')
        account_type = search_form.cleaned_data.get('account_type')
        currency = search_form.cleaned_data.get('currency')
        status = search_form.cleaned_data.get('status')
        is_default = search_form.cleaned_data.get('is_default')
        
        # Search filter
        if search_term:
            if search_by == 'bank_name':
                queryset = queryset.filter(bank_name__icontains=search_term)
            elif search_by == 'account_number':
                queryset = queryset.filter(account_number__icontains=search_term)
            elif search_by == 'branch_name':
                queryset = queryset.filter(branch_name__icontains=search_term)
        
        # Type filter
        if account_type:
            queryset = queryset.filter(account_type=account_type)
        
        # Currency filter
        if currency:
            queryset = queryset.filter(currency=currency)
        
        # Status filter
        if status:
            queryset = queryset.filter(status=status)
        
        # Default account filter
        if is_default == 'payments':
            queryset = queryset.filter(is_default_for_payments=True)
        elif is_default == 'receipts':
            queryset = queryset.filter(is_default_for_receipts=True)
    
    # Pagination
    paginator = Paginator(queryset, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Summary statistics
    total_accounts = queryset.count()
    active_accounts = queryset.filter(status='active').count()
    total_balance = queryset.aggregate(total=Sum('current_balance'))['total'] or 0
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_accounts': total_accounts,
        'active_accounts': active_accounts,
        'total_balance': total_balance,
        'company': company,
    }
    
    return render(request, 'bank_accounts/bank_account_list.html', context)


@login_required
def bank_account_create(request):
    """Create new bank account"""
    
    if request.method == 'POST':
        form = BankAccountForm(request.POST, user=request.user)
        if form.is_valid():
            bank_account = form.save(commit=False)
            bank_account.company = Company.objects.filter(is_active=True).first()
            bank_account.created_by = request.user
            bank_account.current_balance = form.cleaned_data['opening_balance']
            bank_account.save()
            
            messages.success(request, f'Bank account "{bank_account.bank_name}" created successfully.')
            return redirect('bank_accounts:bank_account_detail', pk=bank_account.pk)
    else:
        form = BankAccountForm(user=request.user)
    
    context = {
        'form': form,
        'title': 'Create Bank Account',
        'submit_text': 'Create Account',
    }
    
    return render(request, 'bank_accounts/bank_account_form.html', context)


@login_required
def bank_account_edit(request, pk):
    """Edit existing bank account"""
    
    bank_account = get_object_or_404(BankAccount, pk=pk)
    
    if request.method == 'POST':
        form = BankAccountForm(request.POST, instance=bank_account, user=request.user)
        if form.is_valid():
            bank_account = form.save(commit=False)
            bank_account.updated_by = request.user
            bank_account.save()
            
            messages.success(request, f'Bank account "{bank_account.bank_name}" updated successfully.')
            return redirect('bank_accounts:bank_account_detail', pk=bank_account.pk)
    else:
        form = BankAccountForm(instance=bank_account, user=request.user)
    
    context = {
        'form': form,
        'bank_account': bank_account,
        'title': 'Edit Bank Account',
        'submit_text': 'Update Account',
    }
    
    return render(request, 'bank_accounts/bank_account_form.html', context)


@login_required
def bank_account_detail(request, pk):
    """Detail view for bank account"""
    
    bank_account = get_object_or_404(BankAccount.objects.select_related(
        'currency', 'chart_account', 'company'
    ), pk=pk)
    
    # Get recent transactions
    recent_transactions = BankAccountTransaction.objects.filter(
        bank_account=bank_account
    ).order_by('-transaction_date', '-created_at')[:10]
    
    # Get transaction statistics
    transaction_stats = BankAccountTransaction.objects.filter(
        bank_account=bank_account
    ).aggregate(
        total_credits=Sum('amount', filter=Q(transaction_type='credit')),
        total_debits=Sum('amount', filter=Q(transaction_type='debit')),
        transaction_count=Count('id')
    )
    
    context = {
        'bank_account': bank_account,
        'recent_transactions': recent_transactions,
        'transaction_stats': transaction_stats,
    }
    
    return render(request, 'bank_accounts/bank_account_detail.html', context)


@login_required
@require_http_methods(["POST"])
def bank_account_delete(request, pk):
    """Delete bank account"""
    
    bank_account = get_object_or_404(BankAccount, pk=pk)
    
    if bank_account.can_be_deleted():
        bank_account.delete()
        messages.success(request, f'Bank account "{bank_account.bank_name}" deleted successfully.')
    else:
        messages.error(request, 'Cannot delete account with balance or transactions.')
    
    return redirect('bank_accounts:bank_account_list')


@login_required
def bank_account_toggle_status(request, pk):
    """Toggle bank account status"""
    
    bank_account = get_object_or_404(BankAccount, pk=pk)
    
    if bank_account.status == 'active':
        bank_account.status = 'inactive'
        status_text = 'deactivated'
    else:
        bank_account.status = 'active'
        status_text = 'activated'
    
    bank_account.updated_by = request.user
    bank_account.save()
    
    messages.success(request, f'Bank account "{bank_account.bank_name}" {status_text} successfully.')
    
    return redirect('bank_accounts:bank_account_list')


@login_required
def bank_account_transactions(request, pk):
    """View transactions for a bank account"""
    
    bank_account = get_object_or_404(BankAccount, pk=pk)
    
    # Get all transactions with pagination
    transactions = BankAccountTransaction.objects.filter(
        bank_account=bank_account
    ).order_by('-transaction_date', '-created_at')
    
    paginator = Paginator(transactions, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'bank_account': bank_account,
        'page_obj': page_obj,
    }
    
    return render(request, 'bank_accounts/bank_account_transactions.html', context)


@login_required
def bank_account_add_transaction(request, pk):
    """Add transaction to bank account"""
    
    bank_account = get_object_or_404(BankAccount, pk=pk)
    
    if request.method == 'POST':
        form = BankAccountTransactionForm(request.POST, bank_account=bank_account)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.bank_account = bank_account
            transaction.created_by = request.user
            transaction.save()
            
            messages.success(request, 'Transaction added successfully.')
            return redirect('bank_accounts:bank_account_transactions', pk=bank_account.pk)
    else:
        form = BankAccountTransactionForm(bank_account=bank_account)
    
    context = {
        'form': form,
        'bank_account': bank_account,
        'title': 'Add Transaction',
        'submit_text': 'Add Transaction',
    }
    
    return render(request, 'bank_accounts/bank_account_transaction_form.html', context)


@login_required
@csrf_exempt
def ajax_account_search(request):
    """AJAX endpoint for searching chart accounts"""
    
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    accounts = ChartOfAccount.objects.filter(
        Q(account_code__icontains=query) | Q(name__icontains=query),
        account_type__category='ASSET',
        is_active=True
    ).order_by('account_code')[:20]
    
    results = []
    for account in accounts:
        results.append({
            'id': account.id,
            'account_code': account.account_code,
            'account_name': account.name,
            'text': f"{account.account_code} - {account.name}"
        })
    
    return JsonResponse({'results': results})


@login_required
def export_bank_accounts(request):
    """Export bank accounts to Excel/CSV"""
    
    # Get filtered queryset
    search_form = BankAccountSearchForm(request.GET)
    company = Company.objects.filter(is_active=True).first()
    
    queryset = BankAccount.objects.filter(company=company).select_related(
        'currency', 'chart_account'
    )
    
    if search_form.is_valid():
        # Apply same filters as list view
        search_term = search_form.cleaned_data.get('search_term')
        search_by = search_form.cleaned_data.get('search_by', 'bank_name')
        account_type = search_form.cleaned_data.get('account_type')
        currency = search_form.cleaned_data.get('currency')
        status = search_form.cleaned_data.get('status')
        
        if search_term:
            if search_by == 'bank_name':
                queryset = queryset.filter(bank_name__icontains=search_term)
            elif search_by == 'account_number':
                queryset = queryset.filter(account_number__icontains=search_term)
            elif search_by == 'branch_name':
                queryset = queryset.filter(branch_name__icontains=search_term)
        
        if account_type:
            queryset = queryset.filter(account_type=account_type)
        if currency:
            queryset = queryset.filter(currency=currency)
        if status:
            queryset = queryset.filter(status=status)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="bank_accounts_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Bank Name', 'Account Number', 'Account Type', 'Branch Name', 'IFSC Code',
        'Currency', 'Current Balance', 'Status', 'Default for Payments', 'Default for Receipts'
    ])
    
    for account in queryset:
        writer.writerow([
            account.bank_name,
            account.masked_account_number,
            account.get_account_type_display(),
            account.branch_name or '',
            account.ifsc_code or '',
            account.currency.code,
            account.current_balance,
            account.get_status_display(),
            'Yes' if account.is_default_for_payments else 'No',
            'Yes' if account.is_default_for_receipts else 'No',
        ])
    
    return response


@login_required
def bank_account_dashboard(request):
    """Dashboard view for bank accounts overview"""
    
    company = Company.objects.filter(is_active=True).first()
    if not company:
        messages.error(request, "No active company found.")
        return redirect('dashboard:dashboard')
    
    # Get all bank accounts
    bank_accounts = BankAccount.objects.filter(company=company).select_related('currency')
    
    # Calculate statistics
    total_accounts = bank_accounts.count()
    active_accounts = bank_accounts.filter(status='active').count()
    total_balance = bank_accounts.aggregate(total=Sum('current_balance'))['total'] or 0
    
    # Get accounts by currency
    accounts_by_currency = {}
    for account in bank_accounts:
        currency_code = account.currency.code
        if currency_code not in accounts_by_currency:
            accounts_by_currency[currency_code] = {
                'currency': account.currency,
                'accounts': [],
                'total_balance': 0
            }
        accounts_by_currency[currency_code]['accounts'].append(account)
        accounts_by_currency[currency_code]['total_balance'] += account.current_balance
    
    # Get recent transactions
    recent_transactions = BankAccountTransaction.objects.filter(
        bank_account__company=company
    ).select_related('bank_account').order_by('-created_at')[:10]
    
    context = {
        'total_accounts': total_accounts,
        'active_accounts': active_accounts,
        'total_balance': total_balance,
        'accounts_by_currency': accounts_by_currency,
        'recent_transactions': recent_transactions,
        'bank_accounts': bank_accounts,
    }
    
    return render(request, 'bank_accounts/bank_account_dashboard.html', context)
