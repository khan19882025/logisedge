from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from .models import AccountType
from .account_type_forms import AccountTypeForm


@login_required
def account_type_list(request):
    """Display list of account types with search and filter functionality"""
    
    # Get all account types
    account_types = AccountType.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')
    
    if search_query:
        account_types = account_types.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    if category_filter:
        account_types = account_types.filter(category=category_filter)
    
    if status_filter:
        if status_filter == 'active':
            account_types = account_types.filter(is_active=True)
        elif status_filter == 'inactive':
            account_types = account_types.filter(is_active=False)
    
    # Order by category and name
    account_types = account_types.order_by('category', 'name')
    
    # Pagination
    paginator = Paginator(account_types, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get counts for summary
    total_account_types = AccountType.objects.count()
    active_account_types = AccountType.objects.filter(is_active=True).count()
    inactive_account_types = AccountType.objects.filter(is_active=False).count()
    
    # Get counts by category
    category_counts = {}
    for category_code, category_name in AccountType.ACCOUNT_CATEGORIES:
        count = AccountType.objects.filter(category=category_code).count()
        category_counts[category_code] = count
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'status_filter': status_filter,
        'categories': AccountType.ACCOUNT_CATEGORIES,
        'total_account_types': total_account_types,
        'active_account_types': active_account_types,
        'inactive_account_types': inactive_account_types,
        'category_counts': category_counts,
    }
    
    return render(request, 'chart_of_accounts/account_type_list.html', context)


@login_required
def account_type_create(request):
    """Create a new account type"""
    
    if request.method == 'POST':
        form = AccountTypeForm(request.POST)
        if form.is_valid():
            account_type = form.save()
            messages.success(request, f'Account type "{account_type.name}" created successfully!')
            return redirect('chart_of_accounts:account_type_list')
    else:
        form = AccountTypeForm()
    
    context = {
        'form': form,
        'title': 'Create Account Type',
        'action': 'Create'
    }
    return render(request, 'chart_of_accounts/account_type_form.html', context)


@login_required
def account_type_edit(request, pk):
    """Edit an existing account type"""
    
    account_type = get_object_or_404(AccountType, pk=pk)
    
    if request.method == 'POST':
        form = AccountTypeForm(request.POST, instance=account_type)
        if form.is_valid():
            form.save()
            messages.success(request, f'Account type "{account_type.name}" updated successfully!')
            return redirect('chart_of_accounts:account_type_list')
    else:
        form = AccountTypeForm(instance=account_type)
    
    context = {
        'form': form,
        'account_type': account_type,
        'title': 'Edit Account Type',
        'action': 'Update'
    }
    return render(request, 'chart_of_accounts/account_type_form.html', context)


@login_required
def account_type_delete(request, pk):
    """Delete an account type"""
    
    account_type = get_object_or_404(AccountType, pk=pk)
    
    # Check if account type has associated accounts
    account_count = account_type.accounts.count()
    
    if request.method == 'POST':
        if account_count > 0:
            messages.error(request, f'Cannot delete account type "{account_type.name}" because it has {account_count} associated accounts.')
        else:
            account_type.delete()
            messages.success(request, f'Account type "{account_type.name}" deleted successfully!')
        return redirect('chart_of_accounts:account_type_list')
    
    context = {
        'account_type': account_type,
        'account_count': account_count
    }
    return render(request, 'chart_of_accounts/account_type_confirm_delete.html', context)


@login_required
def account_type_detail(request, pk):
    """Display account type details"""
    
    account_type = get_object_or_404(AccountType, pk=pk)
    
    # Get associated accounts
    accounts = account_type.accounts.filter(is_active=True).order_by('account_code')
    
    # Get account counts by status
    active_accounts = accounts.filter(is_active=True).count()
    inactive_accounts = account_type.accounts.filter(is_active=False).count()
    
    context = {
        'account_type': account_type,
        'accounts': accounts,
        'active_accounts': active_accounts,
        'inactive_accounts': inactive_accounts,
    }
    
    return render(request, 'chart_of_accounts/account_type_detail.html', context)


@login_required
def account_type_toggle_status(request, pk):
    """Toggle account type active status"""
    
    account_type = get_object_or_404(AccountType, pk=pk)
    
    if request.method == 'POST':
        account_type.is_active = not account_type.is_active
        account_type.save()
        
        status = 'activated' if account_type.is_active else 'deactivated'
        messages.success(request, f'Account type "{account_type.name}" {status} successfully!')
        
        return redirect('chart_of_accounts:account_type_list')
    
    return redirect('chart_of_accounts:account_type_detail', pk=pk)