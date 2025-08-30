from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET
from django.template.loader import render_to_string
from .models import BankTransfer, BankTransferAudit, BankTransferTemplate
from .forms import BankTransferForm, BankTransferFilterForm, BankTransferTemplateForm, QuickTransferForm
from chart_of_accounts.models import ChartOfAccount
from multi_currency.models import Currency
from decimal import Decimal
import json


@login_required
def bank_transfer_list(request):
    """List all bank transfers with filtering and pagination"""
    
    # Get filter parameters
    form = BankTransferFilterForm(request.GET)
    transfers = BankTransfer.objects.all()
    
    # Apply filters
    if form.is_valid():
        if form.cleaned_data.get('date_from'):
            transfers = transfers.filter(transfer_date__gte=form.cleaned_data['date_from'])
        if form.cleaned_data.get('date_to'):
            transfers = transfers.filter(transfer_date__lte=form.cleaned_data['date_to'])
        if form.cleaned_data.get('status'):
            transfers = transfers.filter(status=form.cleaned_data['status'])
        if form.cleaned_data.get('transfer_type'):
            transfers = transfers.filter(transfer_type=form.cleaned_data['transfer_type'])
        if form.cleaned_data.get('from_account'):
            transfers = transfers.filter(from_account=form.cleaned_data['from_account'])
        if form.cleaned_data.get('to_account'):
            transfers = transfers.filter(to_account=form.cleaned_data['to_account'])
        if form.cleaned_data.get('currency'):
            transfers = transfers.filter(currency=form.cleaned_data['currency'])
        if form.cleaned_data.get('search'):
            search_term = form.cleaned_data['search']
            transfers = transfers.filter(
                Q(transfer_number__icontains=search_term) |
                Q(reference_number__icontains=search_term) |
                Q(narration__icontains=search_term)
            )
    
    # Pagination
    paginator = Paginator(transfers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filter_form': form,
        'total_count': transfers.count(),
        'total_amount': transfers.aggregate(total=Sum('amount'))['total'] or 0,
    }
    
    return render(request, 'bank_transfer/list.html', context)


@login_required
def bank_transfer_create(request):
    """Create a new bank transfer"""
    
    if request.method == 'POST':
        form = BankTransferForm(request.POST)
        
        if form.is_valid():
            transfer = form.save(commit=False)
            transfer.created_by = request.user
            transfer.save()
            
            # Create audit trail
            BankTransferAudit.objects.create(
                transfer=transfer,
                action='created',
                description=f'Bank transfer created from {transfer.from_account.name} to {transfer.to_account.name}',
                user=request.user
            )
            
            messages.success(request, f'Bank transfer {transfer.transfer_number} created successfully.')
            return redirect('bank_transfer:detail', pk=transfer.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BankTransferForm()
    
    # Get available templates
    templates = BankTransferTemplate.objects.filter(is_active=True)
    
    context = {
        'form': form,
        'templates': templates,
    }
    
    return render(request, 'bank_transfer/create.html', context)


@login_required
def bank_transfer_edit(request, pk):
    """Edit an existing bank transfer"""
    
    transfer = get_object_or_404(BankTransfer, pk=pk)
    
    if not transfer.can_edit:
        messages.error(request, 'This bank transfer cannot be edited.')
        return redirect('bank_transfer:detail', pk=pk)
    
    if request.method == 'POST':
        form = BankTransferForm(request.POST, instance=transfer)
        
        if form.is_valid():
            transfer = form.save(commit=False)
            transfer.updated_by = request.user
            transfer.save()
            
            # Create audit trail
            BankTransferAudit.objects.create(
                transfer=transfer,
                action='updated',
                description=f'Bank transfer updated',
                user=request.user
            )
            
            messages.success(request, f'Bank transfer {transfer.transfer_number} updated successfully.')
            return redirect('bank_transfer:detail', pk=transfer.pk)
    else:
        form = BankTransferForm(instance=transfer)
    
    context = {
        'transfer': transfer,
        'form': form,
    }
    
    return render(request, 'bank_transfer/edit.html', context)


@login_required
def bank_transfer_detail(request, pk):
    """View bank transfer details"""
    
    transfer = get_object_or_404(BankTransfer, pk=pk)
    
    context = {
        'transfer': transfer,
        'audit_trail': transfer.audit_trail.select_related('user').all()[:10],
    }
    
    return render(request, 'bank_transfer/detail.html', context)


@login_required
def bank_transfer_delete(request, pk):
    """Delete a bank transfer"""
    
    transfer = get_object_or_404(BankTransfer, pk=pk)
    
    if not transfer.can_edit:
        messages.error(request, 'This bank transfer cannot be deleted.')
        return redirect('bank_transfer:detail', pk=pk)
    
    if request.method == 'POST':
        transfer_number = transfer.transfer_number
        transfer.delete()
        messages.success(request, f'Bank transfer {transfer_number} deleted successfully.')
        return redirect('bank_transfer:list')
    
    context = {
        'transfer': transfer,
    }
    
    return render(request, 'bank_transfer/delete.html', context)


@login_required
@require_POST
def bank_transfer_complete(request, pk):
    """Complete a bank transfer"""
    
    transfer = get_object_or_404(BankTransfer, pk=pk)
    
    if not transfer.can_complete:
        return JsonResponse({'success': False, 'message': 'Bank transfer cannot be completed.'})
    
    transfer.status = 'completed'
    transfer.completed_by = request.user
    transfer.completed_at = timezone.now()
    transfer.save()
    
    # Create audit trail
    BankTransferAudit.objects.create(
        transfer=transfer,
        action='completed',
        description='Bank transfer completed',
        user=request.user
    )
    
    messages.success(request, f'Bank transfer {transfer.transfer_number} completed successfully.')
    return JsonResponse({'success': True, 'message': 'Bank transfer completed successfully.'})


@login_required
@require_POST
def bank_transfer_cancel(request, pk):
    """Cancel a bank transfer"""
    
    transfer = get_object_or_404(BankTransfer, pk=pk)
    
    if not transfer.can_cancel:
        return JsonResponse({'success': False, 'message': 'Bank transfer cannot be cancelled.'})
    
    transfer.status = 'cancelled'
    transfer.cancelled_by = request.user
    transfer.cancelled_at = timezone.now()
    transfer.save()
    
    # Create audit trail
    BankTransferAudit.objects.create(
        transfer=transfer,
        action='cancelled',
        description='Bank transfer cancelled',
        user=request.user
    )
    
    messages.success(request, f'Bank transfer {transfer.transfer_number} cancelled successfully.')
    return JsonResponse({'success': True, 'message': 'Bank transfer cancelled successfully.'})


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
def get_account_currencies(request):
    """AJAX endpoint to get account currencies for exchange rate calculation"""
    
    from_account_id = request.GET.get('from_account_id')
    to_account_id = request.GET.get('to_account_id')
    
    if not from_account_id or not to_account_id:
        return JsonResponse({'error': 'Both account IDs are required'})
    
    try:
        from_account = ChartOfAccount.objects.get(id=from_account_id)
        to_account = ChartOfAccount.objects.get(id=to_account_id)
        
        return JsonResponse({
            'from_currency': {
                'id': from_account.currency.id,
                'name': from_account.currency.name,
                'code': from_account.currency.code
            },
            'to_currency': {
                'id': to_account.currency.id,
                'name': to_account.currency.name,
                'code': to_account.currency.code
            },
            'is_multi_currency': from_account.currency.id != to_account.currency.id
        })
    except ChartOfAccount.DoesNotExist:
        return JsonResponse({'error': 'Account not found'})


@login_required
@require_GET
def bank_transfer_summary(request):
    """Get bank transfer summary statistics"""
    
    total_transfers = BankTransfer.objects.count()
    draft_transfers = BankTransfer.objects.filter(status='draft').count()
    pending_transfers = BankTransfer.objects.filter(status='pending').count()
    completed_transfers = BankTransfer.objects.filter(status='completed').count()
    
    total_amount = BankTransfer.objects.aggregate(total=Sum('amount'))['total'] or 0
    completed_amount = BankTransfer.objects.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0
    
    # Multi-currency transfers
    multi_currency_count = BankTransfer.objects.filter(exchange_rate__gt=1).count()
    
    data = {
        'total_transfers': total_transfers,
        'draft_transfers': draft_transfers,
        'pending_transfers': pending_transfers,
        'completed_transfers': completed_transfers,
        'total_amount': float(total_amount),
        'completed_amount': float(completed_amount),
        'multi_currency_count': multi_currency_count,
    }
    
    return JsonResponse(data)


@login_required
def quick_transfer(request):
    """Quick transfer form for simple transfers"""
    
    if request.method == 'POST':
        form = QuickTransferForm(request.POST)
        
        if form.is_valid():
            transfer = BankTransfer(
                transfer_date=timezone.now().date(),
                transfer_type='internal',
                from_account=form.cleaned_data['from_account'],
                to_account=form.cleaned_data['to_account'],
                amount=form.cleaned_data['amount'],
                currency=form.cleaned_data['from_account'].currency,
                exchange_rate=1.000000,
                narration=form.cleaned_data.get('narration', ''),
                created_by=request.user
            )
            transfer.save()
            
            # Create audit trail
            BankTransferAudit.objects.create(
                transfer=transfer,
                action='created',
                description=f'Quick transfer created from {transfer.from_account.name} to {transfer.to_account.name}',
                user=request.user
            )
            
            messages.success(request, f'Quick transfer {transfer.transfer_number} created successfully.')
            return redirect('bank_transfer:detail', pk=transfer.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = QuickTransferForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'bank_transfer/quick_transfer.html', context)


@login_required
def template_list(request):
    """List bank transfer templates"""
    
    templates = BankTransferTemplate.objects.filter(is_active=True)
    
    context = {
        'templates': templates,
    }
    
    return render(request, 'bank_transfer/template_list.html', context)


@login_required
def template_create(request):
    """Create a new bank transfer template"""
    
    if request.method == 'POST':
        form = BankTransferTemplateForm(request.POST)
        
        if form.is_valid():
            template = form.save(commit=False)
            template.created_by = request.user
            template.save()
            
            messages.success(request, f'Template "{template.name}" created successfully.')
            return redirect('bank_transfer:template_list')
    else:
        form = BankTransferTemplateForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'bank_transfer/template_form.html', context)


@login_required
def template_edit(request, pk):
    """Edit a bank transfer template"""
    
    template = get_object_or_404(BankTransferTemplate, pk=pk)
    
    if request.method == 'POST':
        form = BankTransferTemplateForm(request.POST, instance=template)
        
        if form.is_valid():
            form.save()
            messages.success(request, f'Template "{template.name}" updated successfully.')
            return redirect('bank_transfer:template_list')
    else:
        form = BankTransferTemplateForm(instance=template)
    
    context = {
        'template': template,
        'form': form,
    }
    
    return render(request, 'bank_transfer/template_form.html', context)


@login_required
def template_delete(request, pk):
    """Delete a bank transfer template"""
    
    template = get_object_or_404(BankTransferTemplate, pk=pk)
    
    if request.method == 'POST':
        template_name = template.name
        template.delete()
        messages.success(request, f'Template "{template_name}" deleted successfully.')
        return redirect('bank_transfer:template_list')
    
    context = {
        'template': template,
    }
    
    return render(request, 'bank_transfer/template_delete.html', context)


@login_required
@require_GET
def load_template(request, pk):
    """Load template data for creating a transfer"""
    
    template = get_object_or_404(BankTransferTemplate, pk=pk)
    
    data = {
        'from_account': template.from_account.id,
        'to_account': template.to_account.id,
        'amount': float(template.default_amount),
        'currency': template.default_currency.id,
        'narration': template.default_narration or '',
    }
    
    return JsonResponse(data)
