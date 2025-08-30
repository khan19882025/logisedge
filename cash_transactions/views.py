from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.db.models import Q, Sum
from django.utils import timezone
from django.core.paginator import Paginator
from .models import CashTransaction, CashTransactionAudit, CashBalance
from .forms import CashTransactionForm, CashTransactionFilterForm, QuickCashTransactionForm
from chart_of_accounts.models import ChartOfAccount
from multi_currency.models import Currency

@login_required
def cash_transaction_list(request):
    """List all cash transactions with filtering and pagination"""
    
    # Get filter parameters
    form = CashTransactionFilterForm(request.GET)
    transactions = CashTransaction.objects.all()
    
    # Apply filters
    if form.is_valid():
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        status = form.cleaned_data.get('status')
        transaction_type = form.cleaned_data.get('transaction_type')
        category = form.cleaned_data.get('category')
        from_account = form.cleaned_data.get('from_account')
        to_account = form.cleaned_data.get('to_account')
        currency = form.cleaned_data.get('currency')
        location = form.cleaned_data.get('location')
        search = form.cleaned_data.get('search')
        
        if date_from:
            transactions = transactions.filter(transaction_date__gte=date_from)
        if date_to:
            transactions = transactions.filter(transaction_date__lte=date_to)
        if status:
            transactions = transactions.filter(status=status)
        if transaction_type:
            transactions = transactions.filter(transaction_type=transaction_type)
        if category:
            transactions = transactions.filter(category=category)
        if from_account:
            transactions = transactions.filter(from_account=from_account)
        if to_account:
            transactions = transactions.filter(to_account=to_account)
        if currency:
            transactions = transactions.filter(currency=currency)
        if location:
            transactions = transactions.filter(location__icontains=location)
        if search:
            transactions = transactions.filter(
                Q(transaction_number__icontains=search) |
                Q(reference_number__icontains=search) |
                Q(narration__icontains=search)
            )
    
    # Pagination
    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Summary statistics
    total_transactions = transactions.count()
    total_cash_in = transactions.filter(transaction_type='cash_in').aggregate(total=Sum('amount'))['total'] or 0
    total_cash_out = transactions.filter(transaction_type='cash_out').aggregate(total=Sum('amount'))['total'] or 0
    net_cash_flow = total_cash_in - total_cash_out
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'total_transactions': total_transactions,
        'total_cash_in': total_cash_in,
        'total_cash_out': total_cash_out,
        'net_cash_flow': net_cash_flow,
    }
    
    return render(request, 'cash_transactions/list.html', context)


@login_required
def cash_transaction_create(request):
    """Create a new cash transaction"""
    
    if request.method == 'POST':
        form = CashTransactionForm(request.POST, request.FILES)
        
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.created_by = request.user
            transaction.save()
            
            # Create audit trail
            CashTransactionAudit.objects.create(
                transaction=transaction,
                action='created',
                description=f'Cash transaction created: {transaction.get_transaction_type_display()} - {transaction.get_category_display()}',
                user=request.user
            )
            
            messages.success(request, f'Cash transaction {transaction.transaction_number} created successfully.')
            return redirect('cash_transactions:detail', pk=transaction.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CashTransactionForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'cash_transactions/create.html', context)


@login_required
def cash_transaction_edit(request, pk):
    """Edit an existing cash transaction"""
    
    transaction = get_object_or_404(CashTransaction, pk=pk)
    
    if not transaction.can_edit:
        messages.error(request, 'This cash transaction cannot be edited.')
        return redirect('cash_transactions:detail', pk=pk)
    
    if request.method == 'POST':
        form = CashTransactionForm(request.POST, request.FILES, instance=transaction)
        
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.updated_by = request.user
            transaction.save()
            
            # Create audit trail
            CashTransactionAudit.objects.create(
                transaction=transaction,
                action='updated',
                description=f'Cash transaction updated',
                user=request.user
            )
            
            messages.success(request, f'Cash transaction {transaction.transaction_number} updated successfully.')
            return redirect('cash_transactions:detail', pk=transaction.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CashTransactionForm(instance=transaction)
    
    context = {
        'transaction': transaction,
        'form': form,
    }
    
    return render(request, 'cash_transactions/edit.html', context)


@login_required
def cash_transaction_detail(request, pk):
    """View cash transaction details"""
    
    transaction = get_object_or_404(CashTransaction, pk=pk)
    
    context = {
        'transaction': transaction,
        'audit_trail': transaction.audit_trail.select_related('user').all()[:10],
    }
    
    return render(request, 'cash_transactions/detail.html', context)


@login_required
def cash_transaction_delete(request, pk):
    """Delete a cash transaction"""
    
    transaction = get_object_or_404(CashTransaction, pk=pk)
    
    if not transaction.can_edit:
        messages.error(request, 'This cash transaction cannot be deleted.')
        return redirect('cash_transactions:detail', pk=pk)
    
    if request.method == 'POST':
        transaction_number = transaction.transaction_number
        transaction.delete()
        messages.success(request, f'Cash transaction {transaction_number} deleted successfully.')
        return redirect('cash_transactions:list')
    
    context = {
        'transaction': transaction,
    }
    
    return render(request, 'cash_transactions/delete.html', context)


@login_required
@require_POST
def cash_transaction_post(request, pk):
    """Post a cash transaction"""
    
    transaction = get_object_or_404(CashTransaction, pk=pk)
    
    if not transaction.can_post:
        return JsonResponse({'success': False, 'message': 'Cash transaction cannot be posted.'})
    
    transaction.status = 'posted'
    transaction.posted_by = request.user
    transaction.posted_at = timezone.now()
    transaction.save()
    
    # Update cash balance
    if transaction.location:
        balance, created = CashBalance.objects.get_or_create(
            location=transaction.location,
            currency=transaction.currency,
            defaults={'balance': 0}
        )
        balance.update_balance(transaction.amount, transaction.transaction_type)
    
    # Create audit trail
    CashTransactionAudit.objects.create(
        transaction=transaction,
        action='posted',
        description='Cash transaction posted',
        user=request.user
    )
    
    messages.success(request, f'Cash transaction {transaction.transaction_number} posted successfully.')
    return JsonResponse({'success': True, 'message': 'Cash transaction posted successfully.'})


@login_required
@require_POST
def cash_transaction_cancel(request, pk):
    """Cancel a cash transaction"""
    
    transaction = get_object_or_404(CashTransaction, pk=pk)
    
    if not transaction.can_cancel:
        return JsonResponse({'success': False, 'message': 'Cash transaction cannot be cancelled.'})
    
    transaction.status = 'cancelled'
    transaction.save()
    
    # Create audit trail
    CashTransactionAudit.objects.create(
        transaction=transaction,
        action='cancelled',
        description='Cash transaction cancelled',
        user=request.user
    )
    
    messages.success(request, f'Cash transaction {transaction.transaction_number} cancelled successfully.')
    return JsonResponse({'success': True, 'message': 'Cash transaction cancelled successfully.'})


@login_required
def quick_transaction(request):
    """Quick cash transaction form for simple transactions"""
    
    if request.method == 'POST':
        form = QuickCashTransactionForm(request.POST)
        
        if form.is_valid():
            transaction_type = form.cleaned_data['transaction_type']
            account = form.cleaned_data['account']
            
            # Create transaction based on type
            if transaction_type == 'cash_in':
                transaction = CashTransaction(
                    transaction_date=timezone.now().date(),
                    transaction_type=transaction_type,
                    category=form.cleaned_data['category'],
                    to_account=account,
                    amount=form.cleaned_data['amount'],
                    currency=Currency.objects.get(id=3),  # AED
                    location=form.cleaned_data.get('location', ''),
                    narration=form.cleaned_data.get('narration', ''),
                    created_by=request.user
                )
            else:  # cash_out
                transaction = CashTransaction(
                    transaction_date=timezone.now().date(),
                    transaction_type=transaction_type,
                    category=form.cleaned_data['category'],
                    from_account=account,
                    amount=form.cleaned_data['amount'],
                    currency=Currency.objects.get(id=3),  # AED
                    location=form.cleaned_data.get('location', ''),
                    narration=form.cleaned_data.get('narration', ''),
                    created_by=request.user
                )
            
            transaction.save()
            
            # Create audit trail
            CashTransactionAudit.objects.create(
                transaction=transaction,
                action='created',
                description=f'Quick cash transaction created: {transaction.get_transaction_type_display()} - {transaction.get_category_display()}',
                user=request.user
            )
            
            messages.success(request, f'Quick cash transaction {transaction.transaction_number} created successfully.')
            return redirect('cash_transactions:detail', pk=transaction.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = QuickCashTransactionForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'cash_transactions/quick_transaction.html', context)


@login_required
@require_GET
def get_account_balance(request):
    """AJAX endpoint to get account balance"""
    
    account_id = request.GET.get('account_id')
    
    if not account_id:
        return JsonResponse({'error': 'Account ID is required'})
    
    try:
        account = ChartOfAccount.objects.get(id=account_id)
        balance = account.current_balance
        currency = account.currency
        
        return JsonResponse({
            'balance': float(balance),
            'currency': currency.name,
            'currency_code': currency.code
        })
    except ChartOfAccount.DoesNotExist:
        return JsonResponse({'error': 'Account not found'})


@login_required
@require_GET
def get_cash_balance(request):
    """AJAX endpoint to get cash balance at location"""
    
    location = request.GET.get('location')
    currency_id = request.GET.get('currency_id', 3)  # Default to AED
    
    if not location:
        return JsonResponse({'error': 'Location is required'})
    
    try:
        balance = CashBalance.objects.get(location=location, currency_id=currency_id)
        return JsonResponse({
            'balance': float(balance.balance),
            'currency_code': balance.currency.code
        })
    except CashBalance.DoesNotExist:
        return JsonResponse({
            'balance': 0.00,
            'currency_code': 'AED'
        })


@login_required
@require_GET
def cash_transaction_summary(request):
    """Get cash transaction summary statistics"""
    
    total_transactions = CashTransaction.objects.count()
    draft_transactions = CashTransaction.objects.filter(status='draft').count()
    posted_transactions = CashTransaction.objects.filter(status='posted').count()
    cancelled_transactions = CashTransaction.objects.filter(status='cancelled').count()
    
    total_cash_in = CashTransaction.objects.filter(transaction_type='cash_in').aggregate(total=Sum('amount'))['total'] or 0
    total_cash_out = CashTransaction.objects.filter(transaction_type='cash_out').aggregate(total=Sum('amount'))['total'] or 0
    net_cash_flow = total_cash_in - total_cash_out
    
    # Category breakdown
    category_stats = {}
    for category_code, category_name in CashTransaction.CATEGORIES:
        count = CashTransaction.objects.filter(category=category_code).count()
        amount = CashTransaction.objects.filter(category=category_code).aggregate(total=Sum('amount'))['total'] or 0
        category_stats[category_name] = {
            'count': count,
            'amount': float(amount)
        }
    
    data = {
        'total_transactions': total_transactions,
        'draft_transactions': draft_transactions,
        'posted_transactions': posted_transactions,
        'cancelled_transactions': cancelled_transactions,
        'total_cash_in': float(total_cash_in),
        'total_cash_out': float(total_cash_out),
        'net_cash_flow': float(net_cash_flow),
        'category_stats': category_stats,
    }
    
    return JsonResponse(data)
