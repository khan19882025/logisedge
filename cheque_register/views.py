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
from django.core.files.base import ContentFile
import json
import csv
import io
from datetime import datetime, timedelta, date
from decimal import Decimal

from .models import ChequeRegister, ChequeStatusHistory, ChequeAlert
from .forms import (
    ChequeRegisterForm, ChequeFilterForm, BulkStatusUpdateForm, ChequeStatusChangeForm
)
from chart_of_accounts.models import ChartOfAccount
from customer.models import Customer
from company.company_model import Company


@login_required
def cheque_list(request):
    """List view for cheque register entries"""
    
    # Get company
    company = Company.objects.filter(is_active=True).first()
    if not company:
        messages.error(request, "No active company found.")
        return redirect('dashboard:dashboard')
    
    # Get filter parameters
    filter_form = ChequeFilterForm(request.GET)
    
    # Base queryset
    queryset = ChequeRegister.objects.filter(company=company).select_related(
        'customer', 'bank_account', 'created_by'
    )
    
    # Apply filters
    if filter_form.is_valid():
        search = filter_form.cleaned_data.get('search')
        cheque_type = filter_form.cleaned_data.get('cheque_type')
        status = filter_form.cleaned_data.get('status')
        party_type = filter_form.cleaned_data.get('party_type')
        bank_account = filter_form.cleaned_data.get('bank_account')
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')
        amount_min = filter_form.cleaned_data.get('amount_min')
        amount_max = filter_form.cleaned_data.get('amount_max')
        is_post_dated = filter_form.cleaned_data.get('is_post_dated')
        is_overdue = filter_form.cleaned_data.get('is_overdue')
        
        # Search filter
        if search:
            queryset = queryset.filter(
                Q(cheque_number__icontains=search) |
                Q(customer__customer_name__icontains=search) |
                Q(supplier__icontains=search)
            )
        
        # Type filter
        if cheque_type:
            queryset = queryset.filter(cheque_type=cheque_type)
        
        # Status filter
        if status:
            queryset = queryset.filter(status=status)
        
        # Party type filter
        if party_type:
            queryset = queryset.filter(party_type=party_type)
        
        # Bank account filter
        if bank_account:
            queryset = queryset.filter(bank_account=bank_account)
        
        # Date range filter
        if date_from:
            queryset = queryset.filter(cheque_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(cheque_date__lte=date_to)
        
        # Amount range filter
        if amount_min:
            queryset = queryset.filter(amount__gte=amount_min)
        if amount_max:
            queryset = queryset.filter(amount__lte=amount_max)
        
        # Post-dated filter
        if is_post_dated:
            queryset = queryset.filter(is_post_dated=True)
        
        # Overdue filter
        if is_overdue:
            queryset = queryset.filter(
                status='pending',
                cheque_date__lt=timezone.now().date()
            )
    
    # Pagination
    paginator = Paginator(queryset, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get summary statistics
    total_cheques = queryset.count()
    total_amount = queryset.aggregate(total=Sum('amount'))['total'] or 0
    pending_cheques = queryset.filter(status='pending').count()
    overdue_cheques = queryset.filter(
        status='pending',
        cheque_date__lt=timezone.now().date()
    ).count()
    
    # Get bank accounts for filter
    bank_accounts = ChartOfAccount.objects.filter(
        is_active=True
    ).order_by('name')
    
    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'bank_accounts': bank_accounts,
        'total_cheques': total_cheques,
        'total_amount': total_amount,
        'pending_cheques': pending_cheques,
        'overdue_cheques': overdue_cheques,
    }
    
    return render(request, 'cheque_register/cheque_list.html', context)


@login_required
def cheque_create(request):
    """Create new cheque register entry"""
    
    if request.method == 'POST':
        form = ChequeRegisterForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                cheque = form.save(commit=False)
                cheque.created_by = request.user
                
                # Ensure company is set from bank account
                if not cheque.company and cheque.bank_account:
                    cheque.company = cheque.bank_account.company
                
                # If still no company, get first active company
                if not cheque.company:
                    from company.company_model import Company
                    company = Company.objects.filter(is_active=True).first()
                    if company:
                        cheque.company = company
                
                cheque.save()
                
                # Create status history entry
                ChequeStatusHistory.objects.create(
                    cheque=cheque,
                    new_status=cheque.status,
                    changed_by=request.user,
                    remarks="Cheque created"
                )
                
                messages.success(request, f'Cheque "{cheque.cheque_number}" registered successfully.')
                return redirect('cheque_register:cheque_detail', pk=cheque.pk)
            except Exception as e:
                messages.error(request, f'Error creating cheque: {str(e)}')
                # Re-raise the exception for debugging
                raise
    else:
        form = ChequeRegisterForm(user=request.user)
    
    context = {
        'form': form,
        'title': 'Register New Cheque',
        'submit_text': 'Register Cheque',
    }
    
    return render(request, 'cheque_register/cheque_form.html', context)


@login_required
def cheque_edit(request, pk):
    """Edit existing cheque register entry"""
    
    cheque = get_object_or_404(ChequeRegister, pk=pk)
    
    if request.method == 'POST':
        form = ChequeRegisterForm(request.POST, instance=cheque, user=request.user)
        if form.is_valid():
            old_status = cheque.status
            cheque = form.save(commit=False)
            cheque.updated_by = request.user
            
            # Ensure company is set from bank account
            if not cheque.company and cheque.bank_account:
                cheque.company = cheque.bank_account.company
            
            cheque.save()
            
            # Create status history entry if status changed
            if old_status != cheque.status:
                ChequeStatusHistory.objects.create(
                    cheque=cheque,
                    old_status=old_status,
                    new_status=cheque.status,
                    changed_by=request.user,
                    remarks=form.cleaned_data.get('remarks', 'Status changed')
                )
            
            messages.success(request, f'Cheque "{cheque.cheque_number}" updated successfully.')
            return redirect('cheque_register:cheque_detail', pk=cheque.pk)
    else:
        form = ChequeRegisterForm(instance=cheque, user=request.user)
    
    context = {
        'form': form,
        'cheque': cheque,
        'title': 'Edit Cheque',
        'submit_text': 'Update Cheque',
    }
    
    return render(request, 'cheque_register/cheque_form.html', context)


@login_required
def cheque_detail(request, pk):
    """Detail view for cheque register entry"""
    
    cheque = get_object_or_404(ChequeRegister.objects.select_related(
        'customer', 'bank_account', 'created_by', 'updated_by'
    ), pk=pk)
    
    # Get status history
    status_history = cheque.status_history.all()
    
    # Get related alerts
    alerts = cheque.alerts.filter(is_read=False)
    
    context = {
        'cheque': cheque,
        'status_history': status_history,
        'alerts': alerts,
    }
    
    return render(request, 'cheque_register/cheque_detail.html', context)


@login_required
def cheque_status_change(request, pk):
    """Change cheque status"""
    
    cheque = get_object_or_404(ChequeRegister, pk=pk)
    
    if request.method == 'POST':
        form = ChequeStatusChangeForm(request.POST, current_status=cheque.status)
        if form.is_valid():
            old_status = cheque.status
            new_status = form.cleaned_data['new_status']
            clearing_date = form.cleaned_data.get('clearing_date')
            remarks = form.cleaned_data.get('remarks')
            
            # Update cheque status
            cheque.status = new_status
            if new_status == 'cleared' and clearing_date:
                cheque.clearing_date = clearing_date
            elif new_status == 'stopped':
                cheque.stop_payment_date = timezone.now().date()
            
            cheque.updated_by = request.user
            cheque.save()
            
            # Create status history entry
            ChequeStatusHistory.objects.create(
                cheque=cheque,
                old_status=old_status,
                new_status=new_status,
                changed_by=request.user,
                remarks=remarks or f"Status changed from {old_status} to {new_status}"
            )
            
            # Create alert if needed
            if new_status == 'bounced':
                ChequeAlert.objects.create(
                    cheque=cheque,
                    alert_type='bounced',
                    message=f"Cheque {cheque.cheque_number} has been bounced."
                )
            elif new_status == 'cleared':
                ChequeAlert.objects.create(
                    cheque=cheque,
                    alert_type='cleared',
                    message=f"Cheque {cheque.cheque_number} has been cleared."
                )
            
            messages.success(request, f'Cheque status updated to {new_status}.')
            return redirect('cheque_register:cheque_detail', pk=cheque.pk)
    else:
        form = ChequeStatusChangeForm(current_status=cheque.status)
    
    context = {
        'form': form,
        'cheque': cheque,
    }
    
    return render(request, 'cheque_register/cheque_status_change.html', context)


@login_required
@require_http_methods(["POST"])
def bulk_status_update(request):
    """Bulk update cheque statuses"""
    
    cheque_ids = request.POST.getlist('cheque_ids')
    if not cheque_ids:
        messages.error(request, 'No cheques selected.')
        return redirect('cheque_register:cheque_list')
    
    form = BulkStatusUpdateForm(request.POST)
    if form.is_valid():
        new_status = form.cleaned_data['new_status']
        clearing_date = form.cleaned_data.get('clearing_date')
        remarks = form.cleaned_data.get('remarks')
        
        updated_count = 0
        
        with transaction.atomic():
            for cheque_id in cheque_ids:
                try:
                    cheque = ChequeRegister.objects.get(pk=cheque_id)
                    old_status = cheque.status
                    
                    # Update cheque status
                    cheque.status = new_status
                    if new_status == 'cleared' and clearing_date:
                        cheque.clearing_date = clearing_date
                    elif new_status == 'stopped':
                        cheque.stop_payment_date = timezone.now().date()
                    
                    cheque.updated_by = request.user
                    cheque.save()
                    
                    # Create status history entry
                    ChequeStatusHistory.objects.create(
                        cheque=cheque,
                        old_status=old_status,
                        new_status=new_status,
                        changed_by=request.user,
                        remarks=remarks or f"Bulk status update to {new_status}"
                    )
                    
                    updated_count += 1
                    
                except ChequeRegister.DoesNotExist:
                    continue
        
        messages.success(request, f'{updated_count} cheques updated successfully.')
    else:
        messages.error(request, 'Invalid form data.')
    
    return redirect('cheque_register:cheque_list')


@login_required
@csrf_exempt
def ajax_get_party_suggestions(request):
    """AJAX endpoint to get party suggestions"""
    
    party_type = request.GET.get('party_type')
    search_term = request.GET.get('q', '')
    
    if party_type == 'customer':
        queryset = Customer.objects.filter(
            customer_name__icontains=search_term,
            status='active'
        )[:10]
        results = [{'id': c.id, 'text': c.customer_name} for c in queryset]
    elif party_type == 'supplier':
        # For suppliers, we'll return common supplier names from existing cheques
        # In a real application, you might have a separate Supplier model
        supplier_names = ChequeRegister.objects.filter(
            supplier__icontains=search_term,
            party_type='supplier'
        ).values_list('supplier', flat=True).distinct()[:10]
        results = [{'id': name, 'text': name} for name in supplier_names]
    else:
        results = []
    
    return JsonResponse({'results': results})


@login_required
def export_cheques(request):
    """Export cheques to CSV/Excel"""
    
    # Get filter parameters (same as list view)
    filter_form = ChequeFilterForm(request.GET)
    company = Company.objects.filter(is_active=True).first()
    
    queryset = ChequeRegister.objects.filter(company=company).select_related(
        'customer', 'bank_account'
    )
    
    # Apply filters (same logic as list view)
    if filter_form.is_valid():
        # Apply same filters as in cheque_list view
        pass
    
    # Generate CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="cheque_register_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Cheque Number', 'Date', 'Type', 'Party Type', 'Party Name',
        'Amount', 'Bank Account', 'Status', 'Clearing Date', 'Remarks'
    ])
    
    for cheque in queryset:
        writer.writerow([
            cheque.cheque_number,
            cheque.cheque_date,
            cheque.get_cheque_type_display(),
            cheque.get_party_type_display(),
            cheque.get_party_name(),
            cheque.amount,
            cheque.bank_account.account_name,
            cheque.get_status_display(),
            cheque.clearing_date or '',
            cheque.remarks or '',
        ])
    
    return response


@login_required
def dashboard(request):
    """Dashboard view for cheque register overview"""
    
    company = Company.objects.filter(is_active=True).first()
    if not company:
        messages.error(request, "No active company found.")
        return redirect('dashboard:dashboard')
    
    # Get recent cheques
    recent_cheques = ChequeRegister.objects.filter(
        company=company
    ).select_related('customer', 'bank_account').order_by('-created_at')[:10]
    
    # Get statistics
    total_cheques = ChequeRegister.objects.filter(company=company).count()
    total_amount = ChequeRegister.objects.filter(company=company).aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    pending_cheques = ChequeRegister.objects.filter(
        company=company,
        status='pending'
    ).count()
    
    overdue_cheques = ChequeRegister.objects.filter(
        company=company,
        status='pending',
        cheque_date__lt=timezone.now().date()
    ).count()
    
    post_dated_cheques = ChequeRegister.objects.filter(
        company=company,
        is_post_dated=True
    ).count()
    
    # Get alerts
    alerts = ChequeAlert.objects.filter(
        cheque__company=company,
        is_read=False
    ).select_related('cheque')[:5]
    
    context = {
        'recent_cheques': recent_cheques,
        'total_cheques': total_cheques,
        'total_amount': total_amount,
        'pending_cheques': pending_cheques,
        'overdue_cheques': overdue_cheques,
        'post_dated_cheques': post_dated_cheques,
        'alerts': alerts,
    }
    
    return render(request, 'cheque_register/dashboard.html', context)
