from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db import transaction
from .models import OpeningBalance, OpeningBalanceEntry
from .forms import OpeningBalanceForm, OpeningBalanceEntryFormSet
from chart_of_accounts.models import ChartOfAccount
from django.db import models


@login_required
def opening_balance_list(request):
    """Display list of all opening balances"""
    opening_balances = OpeningBalance.objects.all().order_by('-created_at')
    
    # Pagination
    paginator = Paginator(opening_balances, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'opening_balances': page_obj,
        'title': 'Opening Balances'
    }
    return render(request, 'opening_balance/opening_balance_list.html', context)


@login_required
def opening_balance_create(request):
    """Create a new opening balance"""
    if request.method == 'POST':
        form = OpeningBalanceForm(request.POST)
        formset = OpeningBalanceEntryFormSet(request.POST, instance=OpeningBalance())
        
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # Create the opening balance
                    opening_balance = form.save(commit=False)
                    opening_balance.created_by = request.user
                    opening_balance.save()
                    
                    # Save the formset
                    formset.instance = opening_balance
                    formset.save()
                    
                    # Validate that total debit equals total credit
                    # Only include entries that have accounts and amounts
                    valid_entries = opening_balance.entries.filter(account__isnull=False, amount__gt=0)
                    total_debit = sum(
                        entry.amount for entry in valid_entries.filter(balance_type='debit')
                    )
                    total_credit = sum(
                        entry.amount for entry in valid_entries.filter(balance_type='credit')
                    )
                    
                    if total_debit != total_credit:
                        # Delete the opening balance if not balanced
                        opening_balance.delete()
                        messages.error(
                            request, 
                            f'Opening balance must be balanced. Total Debit: {total_debit}, Total Credit: {total_credit}'
                        )
                        return render(request, 'opening_balance/opening_balance_form.html', {
                            'form': form,
                            'formset': formset,
                            'title': 'Create Opening Balance'
                        })
                    
                    messages.success(request, 'Opening balance created successfully!')
                    return redirect('opening_balance:opening_balance_detail', pk=opening_balance.pk)
                    
            except Exception as e:
                messages.error(request, f'Error creating opening balance: {str(e)}')
    else:
        form = OpeningBalanceForm()
        formset = OpeningBalanceEntryFormSet(instance=OpeningBalance())
    
    context = {
        'form': form,
        'formset': formset,
        'title': 'Create Opening Balance',
        'submit_text': 'Create Opening Balance'
    }
    return render(request, 'opening_balance/opening_balance_form.html', context)


@login_required
def opening_balance_edit(request, pk):
    """Edit an existing opening balance"""
    opening_balance = get_object_or_404(OpeningBalance, pk=pk)
    
    if request.method == 'POST':
        form = OpeningBalanceForm(request.POST, instance=opening_balance)
        formset = OpeningBalanceEntryFormSet(request.POST, instance=opening_balance)
        
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # Save the opening balance
                    opening_balance = form.save()
                    
                    # Save the formset
                    formset.save()
                    
                    # Validate that total debit equals total credit
                    # Only include entries that have accounts and amounts
                    valid_entries = opening_balance.entries.filter(account__isnull=False, amount__gt=0)
                    total_debit = sum(
                        entry.amount for entry in valid_entries.filter(balance_type='debit')
                    )
                    total_credit = sum(
                        entry.amount for entry in valid_entries.filter(balance_type='credit')
                    )
                    
                    if total_debit != total_credit:
                        messages.error(
                            request, 
                            f'Opening balance must be balanced. Total Debit: {total_debit}, Total Credit: {total_credit}'
                        )
                        return render(request, 'opening_balance/opening_balance_form.html', {
                            'form': form,
                            'formset': formset,
                            'opening_balance': opening_balance,
                            'title': 'Edit Opening Balance'
                        })
                    
                    messages.success(request, 'Opening balance updated successfully!')
                    return redirect('opening_balance:opening_balance_detail', pk=opening_balance.pk)
                    
            except Exception as e:
                messages.error(request, f'Error updating opening balance: {str(e)}')
    else:
        form = OpeningBalanceForm(instance=opening_balance)
        formset = OpeningBalanceEntryFormSet(instance=opening_balance)
    
    context = {
        'form': form,
        'formset': formset,
        'opening_balance': opening_balance,
        'title': 'Edit Opening Balance',
        'submit_text': 'Update Opening Balance'
    }
    return render(request, 'opening_balance/opening_balance_form.html', context)


@login_required
def opening_balance_detail(request, pk):
    """Display details of an opening balance"""
    opening_balance = get_object_or_404(OpeningBalance, pk=pk)
    
    context = {
        'opening_balance': opening_balance,
        'title': f'Opening Balance - {opening_balance.financial_year.name}'
    }
    return render(request, 'opening_balance/opening_balance_detail.html', context)


@login_required
def opening_balance_delete(request, pk):
    """Delete an opening balance"""
    opening_balance = get_object_or_404(OpeningBalance, pk=pk)
    
    if request.method == 'POST':
        try:
            opening_balance.delete()
            messages.success(request, 'Opening balance deleted successfully!')
            return redirect('opening_balance:opening_balance_list')
        except Exception as e:
            messages.error(request, f'Error deleting opening balance: {str(e)}')
    
    context = {
        'opening_balance': opening_balance,
        'title': 'Delete Opening Balance'
    }
    return render(request, 'opening_balance/opening_balance_confirm_delete.html', context)


@login_required
@require_http_methods(["GET"])
def ajax_account_search(request):
    """AJAX endpoint for account search"""
    query = request.GET.get('q', '')
    page = request.GET.get('page', 1)
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    accounts = ChartOfAccount.objects.filter(
        is_active=True
    ).filter(
        models.Q(account_code__icontains=query) |
        models.Q(name__icontains=query)
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