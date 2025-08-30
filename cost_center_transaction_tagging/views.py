from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from decimal import Decimal
import json

from .models import (
    TransactionTagging, DefaultCostCenterMapping, TransactionTaggingRule,
    TransactionTaggingAuditLog, TransactionTaggingReport
)
from .forms import (
    TransactionTaggingForm, DefaultCostCenterMappingForm, TransactionTaggingRuleForm,
    TransactionTaggingReportForm, TransactionTaggingSearchForm, BulkTransactionTaggingForm
)
from cost_center_management.models import CostCenter


@login_required
def dashboard(request):
    """Dashboard view for transaction tagging"""
    # Get statistics
    total_transactions = TransactionTagging.objects.filter(is_active=True).count()
    total_amount = TransactionTagging.objects.filter(is_active=True).aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    
    # Get recent transactions
    recent_transactions = TransactionTagging.objects.filter(is_active=True).order_by('-created_at')[:10]
    
    # Get cost center statistics
    cost_center_stats = CostCenter.objects.filter(is_active=True).annotate(
        transaction_count=Count('tagged_transactions'),
        total_amount=Sum('tagged_transactions__amount')
    ).order_by('-total_amount')[:5]
    
    # Calculate percentages for cost center stats
    for stat in cost_center_stats:
        if total_amount > 0 and stat.total_amount:
            stat.percentage = (stat.total_amount / total_amount) * 100
        else:
            stat.percentage = 0
    
    # Get transaction type distribution
    transaction_types = TransactionTagging.objects.filter(is_active=True).values('transaction_type').annotate(
        count=Count('id'),
        total_amount=Sum('amount')
    )
    
    context = {
        'total_transactions': total_transactions,
        'total_amount': total_amount,
        'recent_transactions': recent_transactions,
        'cost_center_stats': cost_center_stats,
        'transaction_types': transaction_types,
    }
    
    return render(request, 'cost_center_transaction_tagging/dashboard.html', context)


@login_required
def transaction_tagging_list(request):
    """List view for transaction taggings"""
    search_form = TransactionTaggingSearchForm(request.GET)
    transactions = TransactionTagging.objects.filter(is_active=True)
    
    # Apply search filters
    if search_form.is_valid():
        if search_form.cleaned_data.get('transaction_id'):
            transactions = transactions.filter(
                transaction_id__icontains=search_form.cleaned_data['transaction_id']
            )
        
        if search_form.cleaned_data.get('reference_number'):
            transactions = transactions.filter(
                reference_number__icontains=search_form.cleaned_data['reference_number']
            )
        
        if search_form.cleaned_data.get('transaction_type'):
            transactions = transactions.filter(
                transaction_type=search_form.cleaned_data['transaction_type']
            )
        
        if search_form.cleaned_data.get('cost_center'):
            transactions = transactions.filter(
                cost_center=search_form.cleaned_data['cost_center']
            )
        
        if search_form.cleaned_data.get('status'):
            transactions = transactions.filter(
                status=search_form.cleaned_data['status']
            )
        
        if search_form.cleaned_data.get('start_date'):
            transactions = transactions.filter(
                transaction_date__gte=search_form.cleaned_data['start_date']
            )
        
        if search_form.cleaned_data.get('end_date'):
            transactions = transactions.filter(
                transaction_date__lte=search_form.cleaned_data['end_date']
            )
        
        if search_form.cleaned_data.get('min_amount'):
            transactions = transactions.filter(
                amount__gte=search_form.cleaned_data['min_amount']
            )
        
        if search_form.cleaned_data.get('max_amount'):
            transactions = transactions.filter(
                amount__lte=search_form.cleaned_data['max_amount']
            )
    
    # Pagination
    paginator = Paginator(transactions, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_count': transactions.count(),
    }
    
    return render(request, 'cost_center_transaction_tagging/transaction_tagging_list.html', context)


@login_required
@permission_required('cost_center_transaction_tagging.add_transactiontagging', raise_exception=True)
def transaction_tagging_create(request):
    """Create view for transaction tagging"""
    if request.method == 'POST':
        form = TransactionTaggingForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.created_by = request.user
            transaction.save()
            
            # Create audit log
            TransactionTaggingAuditLog.objects.create(
                transaction_tagging=transaction,
                action='create',
                user=request.user
            )
            
            messages.success(request, 'Transaction tagging created successfully.')
            return redirect('cost_center_transaction_tagging:transaction_tagging_detail', pk=transaction.pk)
    else:
        form = TransactionTaggingForm()
    
    context = {
        'form': form,
        'title': 'Create Transaction Tagging',
    }
    
    return render(request, 'cost_center_transaction_tagging/transaction_tagging_form.html', context)


@login_required
def transaction_tagging_detail(request, pk):
    """Detail view for transaction tagging"""
    transaction = get_object_or_404(TransactionTagging, pk=pk)
    
    context = {
        'transaction': transaction,
    }
    
    return render(request, 'cost_center_transaction_tagging/transaction_tagging_detail.html', context)


@login_required
@permission_required('cost_center_transaction_tagging.change_transactiontagging', raise_exception=True)
def transaction_tagging_update(request, pk):
    """Update view for transaction tagging"""
    transaction = get_object_or_404(TransactionTagging, pk=pk)
    
    if request.method == 'POST':
        form = TransactionTaggingForm(request.POST, instance=transaction)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.updated_by = request.user
            transaction.save()
            
            # Create audit log
            TransactionTaggingAuditLog.objects.create(
                transaction_tagging=transaction,
                action='update',
                user=request.user
            )
            
            messages.success(request, 'Transaction tagging updated successfully.')
            return redirect('cost_center_transaction_tagging:transaction_tagging_detail', pk=transaction.pk)
    else:
        form = TransactionTaggingForm(instance=transaction)
    
    context = {
        'form': form,
        'transaction': transaction,
        'title': 'Update Transaction Tagging',
    }
    
    return render(request, 'cost_center_transaction_tagging/transaction_tagging_form.html', context)


@login_required
@permission_required('cost_center_transaction_tagging.delete_transactiontagging', raise_exception=True)
def transaction_tagging_delete(request, pk):
    """Delete view for transaction tagging"""
    transaction = get_object_or_404(TransactionTagging, pk=pk)
    
    if request.method == 'POST':
        # Create audit log before deletion
        TransactionTaggingAuditLog.objects.create(
            transaction_tagging=transaction,
            action='delete',
            user=request.user
        )
        
        transaction.is_active = False
        transaction.save()
        
        messages.success(request, 'Transaction tagging deleted successfully.')
        return redirect('cost_center_transaction_tagging:transaction_tagging_list')
    
    context = {
        'transaction': transaction,
    }
    
    return render(request, 'cost_center_transaction_tagging/transaction_tagging_confirm_delete.html', context)


@login_required
def default_mapping_list(request):
    """List view for default cost center mappings"""
    mappings = DefaultCostCenterMapping.objects.filter(is_active=True)
    
    # Pagination
    paginator = Paginator(mappings, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    
    return render(request, 'cost_center_transaction_tagging/default_mapping_list.html', context)


@login_required
@permission_required('cost_center_transaction_tagging.add_defaultcostcentermapping', raise_exception=True)
def default_mapping_create(request):
    """Create view for default cost center mapping"""
    if request.method == 'POST':
        form = DefaultCostCenterMappingForm(request.POST)
        if form.is_valid():
            mapping = form.save(commit=False)
            mapping.created_by = request.user
            mapping.save()
            
            messages.success(request, 'Default cost center mapping created successfully.')
            return redirect('cost_center_transaction_tagging:default_mapping_list')
    else:
        form = DefaultCostCenterMappingForm()
    
    context = {
        'form': form,
        'title': 'Create Default Cost Center Mapping',
    }
    
    return render(request, 'cost_center_transaction_tagging/default_mapping_form.html', context)


@login_required
@permission_required('cost_center_transaction_tagging.change_defaultcostcentermapping', raise_exception=True)
def default_mapping_update(request, pk):
    """Update view for default cost center mapping"""
    mapping = get_object_or_404(DefaultCostCenterMapping, pk=pk)
    
    if request.method == 'POST':
        form = DefaultCostCenterMappingForm(request.POST, instance=mapping)
        if form.is_valid():
            mapping = form.save(commit=False)
            mapping.updated_by = request.user
            mapping.save()
            
            messages.success(request, 'Default cost center mapping updated successfully.')
            return redirect('cost_center_transaction_tagging:default_mapping_list')
    else:
        form = DefaultCostCenterMappingForm(instance=mapping)
    
    context = {
        'form': form,
        'mapping': mapping,
        'title': 'Update Default Cost Center Mapping',
    }
    
    return render(request, 'cost_center_transaction_tagging/default_mapping_form.html', context)


@login_required
def transaction_tagging_rule_list(request):
    """List view for transaction tagging rules"""
    rules = TransactionTaggingRule.objects.filter(is_active=True)
    
    # Pagination
    paginator = Paginator(rules, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    
    return render(request, 'cost_center_transaction_tagging/transaction_tagging_rule_list.html', context)


@login_required
@permission_required('cost_center_transaction_tagging.add_transactiontaggingrule', raise_exception=True)
def transaction_tagging_rule_create(request):
    """Create view for transaction tagging rule"""
    if request.method == 'POST':
        form = TransactionTaggingRuleForm(request.POST)
        if form.is_valid():
            rule = form.save(commit=False)
            rule.created_by = request.user
            rule.save()
            
            messages.success(request, 'Transaction tagging rule created successfully.')
            return redirect('cost_center_transaction_tagging:transaction_tagging_rule_list')
    else:
        form = TransactionTaggingRuleForm()
    
    context = {
        'form': form,
        'title': 'Create Transaction Tagging Rule',
    }
    
    return render(request, 'cost_center_transaction_tagging/transaction_tagging_rule_form.html', context)


@login_required
@permission_required('cost_center_transaction_tagging.change_transactiontaggingrule', raise_exception=True)
def transaction_tagging_rule_update(request, pk):
    """Update view for transaction tagging rule"""
    rule = get_object_or_404(TransactionTaggingRule, pk=pk)
    
    if request.method == 'POST':
        form = TransactionTaggingRuleForm(request.POST, instance=rule)
        if form.is_valid():
            rule = form.save(commit=False)
            rule.updated_by = request.user
            rule.save()
            
            messages.success(request, 'Transaction tagging rule updated successfully.')
            return redirect('cost_center_transaction_tagging:transaction_tagging_rule_list')
    else:
        form = TransactionTaggingRuleForm(instance=rule)
    
    context = {
        'form': form,
        'rule': rule,
        'title': 'Update Transaction Tagging Rule',
    }
    
    return render(request, 'cost_center_transaction_tagging/transaction_tagging_rule_form.html', context)


@login_required
def transaction_tagging_report_list(request):
    """List view for transaction tagging reports"""
    reports = TransactionTaggingReport.objects.all()
    
    # Pagination
    paginator = Paginator(reports, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    
    return render(request, 'cost_center_transaction_tagging/transaction_tagging_report_list.html', context)


@login_required
@permission_required('cost_center_transaction_tagging.add_transactiontaggingreport', raise_exception=True)
def transaction_tagging_report_create(request):
    """Create view for transaction tagging report"""
    if request.method == 'POST':
        form = TransactionTaggingReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.generated_by = request.user
            
            # Generate report data based on type
            report.report_data = generate_report_data(report)
            report.save()
            
            messages.success(request, 'Transaction tagging report generated successfully.')
            return redirect('cost_center_transaction_tagging:transaction_tagging_report_detail', pk=report.pk)
    else:
        form = TransactionTaggingReportForm()
    
    context = {
        'form': form,
        'title': 'Generate Transaction Tagging Report',
    }
    
    return render(request, 'cost_center_transaction_tagging/transaction_tagging_report_form.html', context)


@login_required
def transaction_tagging_report_detail(request, pk):
    """Detail view for transaction tagging report"""
    report = get_object_or_404(TransactionTaggingReport, pk=pk)
    
    context = {
        'report': report,
    }
    
    return render(request, 'cost_center_transaction_tagging/transaction_tagging_report_detail.html', context)


@login_required
def bulk_transaction_tagging(request):
    """Bulk transaction tagging view"""
    if request.method == 'POST':
        form = BulkTransactionTaggingForm(request.POST)
        if form.is_valid():
            transaction_ids = form.cleaned_data['transaction_ids']
            cost_center = form.cleaned_data['cost_center']
            
            # Update transactions
            updated_count = 0
            for transaction_id in transaction_ids:
                try:
                    transaction = TransactionTagging.objects.get(
                        transaction_id=transaction_id,
                        is_active=True
                    )
                    transaction.cost_center = cost_center
                    transaction.updated_by = request.user
                    transaction.save()
                    
                    # Create audit log
                    TransactionTaggingAuditLog.objects.create(
                        transaction_tagging=transaction,
                        action='update',
                        field_name='cost_center',
                        old_value=str(transaction.cost_center),
                        new_value=str(cost_center),
                        user=request.user
                    )
                    
                    updated_count += 1
                except TransactionTagging.DoesNotExist:
                    continue
            
            messages.success(request, f'Successfully updated {updated_count} transactions.')
            return redirect('cost_center_transaction_tagging:transaction_tagging_list')
    else:
        form = BulkTransactionTaggingForm()
    
    context = {
        'form': form,
        'title': 'Bulk Transaction Tagging',
    }
    
    return render(request, 'cost_center_transaction_tagging/bulk_transaction_tagging.html', context)


@login_required
@csrf_exempt
def get_default_cost_center(request):
    """API endpoint to get default cost center for entity"""
    if request.method == 'POST':
        data = json.loads(request.body)
        mapping_type = data.get('mapping_type')
        entity_id = data.get('entity_id')
        
        try:
            mapping = DefaultCostCenterMapping.objects.get(
                mapping_type=mapping_type,
                entity_id=entity_id,
                is_active=True
            )
            return JsonResponse({
                'success': True,
                'cost_center_id': str(mapping.cost_center.id),
                'cost_center_code': mapping.cost_center.code,
                'cost_center_name': mapping.cost_center.name,
            })
        except DefaultCostCenterMapping.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'No default cost center found for this entity'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


def generate_report_data(report):
    """Generate report data based on report type"""
    transactions = TransactionTagging.objects.filter(
        is_active=True,
        transaction_date__gte=report.start_date,
        transaction_date__lte=report.end_date
    )
    
    if report.cost_center:
        transactions = transactions.filter(cost_center=report.cost_center)
    
    if report.report_type == 'cost_center_pl':
        # Generate P&L data
        data = {
            'cost_centers': [],
            'total_revenue': 0,
            'total_expenses': 0,
        }
        
        cost_centers = CostCenter.objects.filter(is_active=True)
        for cost_center in cost_centers:
            cost_center_transactions = transactions.filter(cost_center=cost_center)
            revenue = cost_center_transactions.filter(
                transaction_type__in=['sales_invoice', 'receipt']
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            expenses = cost_center_transactions.filter(
                transaction_type__in=['expense_claim', 'purchase_invoice', 'payment']
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            net_income = revenue - expenses
            
            data['cost_centers'].append({
                'cost_center_code': cost_center.code,
                'cost_center_name': cost_center.name,
                'revenue': float(revenue),
                'expenses': float(expenses),
                'net_income': float(net_income),
            })
            
            data['total_revenue'] += float(revenue)
            data['total_expenses'] += float(expenses)
    
    elif report.report_type == 'expense_summary':
        # Generate expense summary data
        data = {
            'expenses_by_cost_center': [],
            'expenses_by_type': [],
            'total_expenses': 0,
        }
        
        # Expenses by cost center
        cost_center_expenses = transactions.filter(
            transaction_type__in=['expense_claim', 'purchase_invoice', 'payment']
        ).values('cost_center__code', 'cost_center__name').annotate(
            total=Sum('amount')
        ).order_by('-total')
        
        for item in cost_center_expenses:
            data['expenses_by_cost_center'].append({
                'cost_center_code': item['cost_center__code'],
                'cost_center_name': item['cost_center__name'],
                'total': float(item['total']),
            })
            data['total_expenses'] += float(item['total'])
        
        # Expenses by type
        type_expenses = transactions.filter(
            transaction_type__in=['expense_claim', 'purchase_invoice', 'payment']
        ).values('transaction_type').annotate(
            total=Sum('amount')
        ).order_by('-total')
        
        for item in type_expenses:
            data['expenses_by_type'].append({
                'transaction_type': item['transaction_type'],
                'total': float(item['total']),
            })
    
    elif report.report_type == 'budget_variance':
        # Generate budget variance data
        data = {
            'budget_variance': [],
            'total_budget': 0,
            'total_actual': 0,
            'total_variance': 0,
        }
        
        cost_centers = CostCenter.objects.filter(is_active=True)
        for cost_center in cost_centers:
            budget_amount = cost_center.budget_amount
            actual_amount = transactions.filter(cost_center=cost_center).aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0.00')
            
            variance = budget_amount - actual_amount
            utilization_percentage = (actual_amount / budget_amount * 100) if budget_amount > 0 else 0
            
            data['budget_variance'].append({
                'cost_center_code': cost_center.code,
                'cost_center_name': cost_center.name,
                'budget_amount': float(budget_amount),
                'actual_amount': float(actual_amount),
                'variance': float(variance),
                'utilization_percentage': float(utilization_percentage),
            })
            
            data['total_budget'] += float(budget_amount)
            data['total_actual'] += float(actual_amount)
        
        data['total_variance'] = data['total_budget'] - data['total_actual']
    
    else:  # transaction_list
        # Generate transaction list data
        data = {
            'transactions': [],
            'total_count': transactions.count(),
            'total_amount': 0,
        }
        
        for transaction in transactions[:1000]:  # Limit to 1000 transactions
            data['transactions'].append({
                'transaction_id': transaction.transaction_id,
                'reference_number': transaction.reference_number,
                'transaction_type': transaction.transaction_type,
                'cost_center_code': transaction.cost_center.code,
                'cost_center_name': transaction.cost_center.name,
                'amount': float(transaction.amount),
                'currency': transaction.currency,
                'transaction_date': transaction.transaction_date.isoformat(),
                'description': transaction.description,
                'status': transaction.status,
            })
            data['total_amount'] += float(transaction.amount)
    
    return data
