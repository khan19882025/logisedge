from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, F
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.serializers import serialize
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.db import transaction
import json
import csv
from datetime import datetime, date
from decimal import Decimal

from .models import (
    DisposalRequest, DisposalItem, DisposalDocument, DisposalApproval,
    DisposalType, ApprovalLevel, DisposalAuditLog, DisposalNotification,
    DisposalJournalEntry, DisposalJournalLine
)
from .forms import (
    DisposalRequestForm, DisposalItemFormSet, AssetSelectionForm,
    DisposalDocumentForm, DisposalApprovalForm, DisposalReversalForm,
    DisposalSearchForm, BulkDisposalForm, ApprovalLevelForm
)
from asset_register.models import Asset, AssetStatus, AssetCategory, AssetLocation
from chart_of_accounts.models import ChartOfAccount


@login_required
def disposal_list(request):
    """Display list of disposal requests with search and filter functionality"""
    disposal_requests = DisposalRequest.objects.select_related(
        'disposal_type', 'created_by', 'asset_account', 'disposal_account'
    ).prefetch_related('disposal_items__asset')
    
    # Handle search and filters
    search_form = DisposalSearchForm(request.GET)
    if search_form.is_valid():
        search = search_form.cleaned_data.get('search')
        status = search_form.cleaned_data.get('status')
        disposal_type = search_form.cleaned_data.get('disposal_type')
        created_by = search_form.cleaned_data.get('created_by')
        date_from = search_form.cleaned_data.get('date_from')
        date_to = search_form.cleaned_data.get('date_to')
        is_batch = search_form.cleaned_data.get('is_batch')
        
        # Apply filters
        if search:
            disposal_requests = disposal_requests.filter(
                Q(request_id__icontains=search) |
                Q(title__icontains=search) |
                Q(disposal_items__asset__asset_name__icontains=search) |
                Q(disposal_items__asset__asset_code__icontains=search)
            ).distinct()
        
        if status:
            disposal_requests = disposal_requests.filter(status=status)
        
        if disposal_type:
            disposal_requests = disposal_requests.filter(disposal_type=disposal_type)
        
        if created_by:
            disposal_requests = disposal_requests.filter(created_by=created_by)
        
        if date_from:
            disposal_requests = disposal_requests.filter(disposal_date__gte=date_from)
        
        if date_to:
            disposal_requests = disposal_requests.filter(disposal_date__lte=date_to)
        
        if is_batch:
            disposal_requests = disposal_requests.filter(is_batch=(is_batch == 'True'))
    
    # Pagination
    paginator = Paginator(disposal_requests, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get summary statistics
    total_requests = disposal_requests.count()
    pending_approval = disposal_requests.filter(status='pending_approval').count()
    approved_requests = disposal_requests.filter(status='approved').count()
    disposed_assets = disposal_requests.filter(status='disposed').count()
    
    # Get filter options
    disposal_types = DisposalType.objects.filter(is_active=True)
    users = User.objects.filter(is_active=True)
    
    # Add permission checks to context
    can_approve_disposal = request.user.has_perm('dispose_asset.can_approve_disposal')
    can_dispose_asset = request.user.has_perm('dispose_asset.can_dispose_asset')
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_requests': total_requests,
        'pending_approval': pending_approval,
        'approved_requests': approved_requests,
        'disposed_assets': disposed_assets,
        'disposal_types': disposal_types,
        'users': users,
        'can_approve_disposal': can_approve_disposal,
        'can_dispose_asset': can_dispose_asset,
    }
    
    return render(request, 'dispose_asset/list.html', context)


@login_required
def disposal_detail(request, disposal_id):
    """Display detailed view of a disposal request"""
    disposal_request = get_object_or_404(DisposalRequest, id=disposal_id)
    
    # Get related data
    disposal_items = disposal_request.disposal_items.select_related('asset').all()
    documents = disposal_request.documents.all()
    approvals = disposal_request.approvals.select_related('approver', 'approval_level').order_by('approval_level__level')
    audit_logs = disposal_request.audit_logs.select_related('user').order_by('-timestamp')[:20]
    journal_entries = disposal_request.journal_entries.all()
    
    # Check if user can approve
    can_approve = request.user.has_perm('dispose_asset.can_approve_disposal')
    
    # Get approval form if user can approve
    approval_form = None
    if can_approve and disposal_request.status == 'pending_approval':
        approval_form = DisposalApprovalForm(disposal_request=disposal_request)
    
    # Get reversal form if user can reverse
    reversal_form = None
    if request.user.has_perm('dispose_asset.can_reverse_disposal') and disposal_request.status == 'disposed':
        reversal_form = DisposalReversalForm()
    
    context = {
        'disposal_request': disposal_request,
        'disposal_items': disposal_items,
        'documents': documents,
        'approvals': approvals,
        'audit_logs': audit_logs,
        'journal_entries': journal_entries,
        'can_approve': can_approve,
        'approval_form': approval_form,
        'reversal_form': reversal_form,
    }
    
    return render(request, 'dispose_asset/detail.html', context)


@login_required
def disposal_create(request):
    """Create a new disposal request"""
    if request.method == 'POST':
        form = DisposalRequestForm(request.POST)
        item_formset = DisposalItemFormSet(request.POST, instance=DisposalRequest())
        
        if form.is_valid() and item_formset.is_valid():
            with transaction.atomic():
                # Create disposal request
                disposal_request = form.save(commit=False)
                disposal_request.created_by = request.user
                disposal_request.save()
                
                # Save disposal items
                item_formset.instance = disposal_request
                item_formset.save()
                
                # Create audit log
                DisposalAuditLog.objects.create(
                    disposal_request=disposal_request,
                    action='create',
                    description=f'Disposal request created: {disposal_request.title}',
                    user=request.user,
                    ip_address=request.META.get('REMOTE_ADDR', ''),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                messages.success(request, f'Disposal request "{disposal_request.title}" created successfully.')
                return redirect('dispose_asset:disposal_detail', disposal_id=disposal_request.id)
    else:
        form = DisposalRequestForm()
        item_formset = DisposalItemFormSet(instance=DisposalRequest())
    
    context = {
        'form': form,
        'item_formset': item_formset,
        'title': 'Create Disposal Request',
        'action': 'Create'
    }
    
    return render(request, 'dispose_asset/form.html', context)


@login_required
def disposal_edit(request, disposal_id):
    """Edit an existing disposal request"""
    disposal_request = get_object_or_404(DisposalRequest, id=disposal_id)
    
    # Check if user can edit
    if not (request.user == disposal_request.created_by or request.user.has_perm('dispose_asset.can_edit_disposal')):
        messages.error(request, 'You do not have permission to edit this disposal request.')
        return redirect('dispose_asset:disposal_detail', disposal_id=disposal_request.id)
    
    # Check if disposal can be edited
    if disposal_request.status not in ['draft', 'rejected']:
        messages.error(request, 'This disposal request cannot be edited.')
        return redirect('dispose_asset:disposal_detail', disposal_id=disposal_request.id)
    
    if request.method == 'POST':
        form = DisposalRequestForm(request.POST, instance=disposal_request)
        item_formset = DisposalItemFormSet(request.POST, instance=disposal_request)
        
        if form.is_valid() and item_formset.is_valid():
            with transaction.atomic():
                # Update disposal request
                disposal_request = form.save(commit=False)
                disposal_request.updated_by = request.user
                disposal_request.save()
                
                # Update disposal items
                item_formset.save()
                
                # Create audit log
                DisposalAuditLog.objects.create(
                    disposal_request=disposal_request,
                    action='update',
                    description=f'Disposal request updated: {disposal_request.title}',
                    user=request.user,
                    ip_address=request.META.get('REMOTE_ADDR', ''),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                messages.success(request, f'Disposal request "{disposal_request.title}" updated successfully.')
                return redirect('dispose_asset:disposal_detail', disposal_id=disposal_request.id)
    else:
        form = DisposalRequestForm(instance=disposal_request)
        item_formset = DisposalItemFormSet(instance=disposal_request)
    
    context = {
        'form': form,
        'item_formset': item_formset,
        'disposal_request': disposal_request,
        'title': 'Edit Disposal Request',
        'action': 'Update'
    }
    
    return render(request, 'dispose_asset/form.html', context)


@login_required
def disposal_submit(request, disposal_id):
    """Submit a disposal request for approval"""
    disposal_request = get_object_or_404(DisposalRequest, id=disposal_id)
    
    # Check if user can submit
    if not (request.user == disposal_request.created_by or request.user.has_perm('dispose_asset.can_submit_disposal')):
        messages.error(request, 'You do not have permission to submit this disposal request.')
        return redirect('dispose_asset:disposal_detail', disposal_id=disposal_request.id)
    
    # Check if disposal can be submitted
    if disposal_request.status != 'draft':
        messages.error(request, 'This disposal request cannot be submitted.')
        return redirect('dispose_asset:disposal_detail', disposal_id=disposal_request.id)
    
    # Validate disposal request
    if not disposal_request.disposal_items.exists():
        messages.error(request, 'At least one asset must be selected for disposal.')
        return redirect('dispose_asset:disposal_detail', disposal_id=disposal_request.id)
    
    with transaction.atomic():
        # Update status
        disposal_request.status = 'pending_approval'
        disposal_request.submitted_at = timezone.now()
        disposal_request.save()
        
        # Create audit log
        DisposalAuditLog.objects.create(
            disposal_request=disposal_request,
            action='submit',
            description=f'Disposal request submitted for approval',
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Create notification for approvers
        _create_approval_notifications(disposal_request)
        
        messages.success(request, f'Disposal request "{disposal_request.title}" submitted successfully.')
    
    return redirect('dispose_asset:disposal_detail', disposal_id=disposal_request.id)


@login_required
@permission_required('dispose_asset.can_approve_disposal')
def disposal_approve(request, disposal_id):
    """Approve or reject a disposal request"""
    disposal_request = get_object_or_404(DisposalRequest, id=disposal_id)
    
    if disposal_request.status != 'pending_approval':
        messages.error(request, 'This disposal request is not pending approval.')
        return redirect('dispose_asset:disposal_detail', disposal_id=disposal_request.id)
    
    if request.method == 'POST':
        form = DisposalApprovalForm(request.POST, disposal_request=disposal_request)
        
        if form.is_valid():
            with transaction.atomic():
                approval = form.save(commit=False)
                approval.disposal_request = disposal_request
                approval.approver = request.user
                approval.ip_address = request.META.get('REMOTE_ADDR', '')
                approval.save()
                
                # Update disposal request status
                action = form.cleaned_data['action']
                if action == 'approve':
                    disposal_request.current_approval_level += 1
                    
                    # Check if all approvals are complete
                    if _is_approval_complete(disposal_request):
                        disposal_request.status = 'approved'
                        disposal_request.save()
                        
                        # Create notification
                        _create_approval_complete_notification(disposal_request)
                    else:
                        disposal_request.save()
                        # Create notification for next approver
                        _create_approval_notifications(disposal_request)
                        
                elif action == 'reject':
                    disposal_request.status = 'rejected'
                    disposal_request.save()
                    
                    # Create notification
                    _create_rejection_notification(disposal_request, approval)
                
                # Create audit log
                DisposalAuditLog.objects.create(
                    disposal_request=disposal_request,
                    action=action,
                    description=f'Disposal request {action}d by {request.user.get_full_name()}',
                    user=request.user,
                    ip_address=request.META.get('REMOTE_ADDR', ''),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                messages.success(request, f'Disposal request {action}d successfully.')
                return redirect('dispose_asset:disposal_detail', disposal_id=disposal_request.id)
    else:
        form = DisposalApprovalForm(disposal_request=disposal_request)
    
    # Calculate approval percentage
    if disposal_request.required_approval_levels > 0:
        approval_percentage = (disposal_request.current_approval_level / disposal_request.required_approval_levels) * 100
    else:
        approval_percentage = 0
    
    context = {
        'disposal_request': disposal_request,
        'form': form,
        'approval_percentage': approval_percentage,
    }
    
    return render(request, 'dispose_asset/approve.html', context)


@login_required
@permission_required('dispose_asset.can_dispose_asset')
def disposal_execute(request, disposal_id):
    """Execute the disposal (mark assets as disposed and create journal entries)"""
    disposal_request = get_object_or_404(DisposalRequest, id=disposal_id)
    
    if disposal_request.status != 'approved':
        messages.error(request, 'This disposal request is not approved.')
        return redirect('dispose_asset:disposal_detail', disposal_id=disposal_request.id)
    
    with transaction.atomic():
        # Mark assets as disposed
        disposed_status = AssetStatus.objects.filter(name__icontains='disposed').first()
        if not disposed_status:
            disposed_status = AssetStatus.objects.create(name='Disposed', is_active=True)
        
        for item in disposal_request.disposal_items.all():
            item.asset.status = disposed_status
            item.asset.disposal_date = disposal_request.disposal_date
            item.asset.disposal_value = item.final_disposal_value
            item.asset.save()
            
            item.is_disposed = True
            item.disposed_at = timezone.now()
            item.save()
        
        # Update disposal request status
        disposal_request.status = 'disposed'
        disposal_request.disposed_at = timezone.now()
        disposal_request.save()
        
        # Create journal entries
        _create_journal_entries(disposal_request)
        
        # Create audit log
        DisposalAuditLog.objects.create(
            disposal_request=disposal_request,
            action='dispose',
            description=f'Assets disposed and journal entries created',
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Create notification
        _create_disposal_complete_notification(disposal_request)
        
        messages.success(request, f'Assets disposed successfully and journal entries created.')
    
    return redirect('dispose_asset:disposal_detail', disposal_id=disposal_request.id)


@login_required
@permission_required('dispose_asset.can_reverse_disposal')
def disposal_reverse(request, disposal_id):
    """Reverse a disposal"""
    disposal_request = get_object_or_404(DisposalRequest, id=disposal_id)
    
    if disposal_request.status != 'disposed':
        messages.error(request, 'This disposal request is not disposed.')
        return redirect('dispose_asset:disposal_detail', disposal_id=disposal_request.id)
    
    if request.method == 'POST':
        form = DisposalReversalForm(request.POST)
        
        if form.is_valid():
            with transaction.atomic():
                # Restore assets to active status
                active_status = AssetStatus.objects.filter(name__icontains='active').first()
                if not active_status:
                    active_status = AssetStatus.objects.create(name='Active', is_active=True)
                
                for item in disposal_request.disposal_items.all():
                    item.asset.status = active_status
                    item.asset.disposal_date = None
                    item.asset.disposal_value = None
                    item.asset.save()
                    
                    item.is_disposed = False
                    item.disposed_at = None
                    item.save()
                
                # Update disposal request status
                disposal_request.status = 'reversed'
                disposal_request.reversed_by = request.user
                disposal_request.reversed_at = timezone.now()
                disposal_request.reversal_reason = form.cleaned_data['reversal_reason']
                disposal_request.save()
                
                # Create reversal journal entries
                _create_reversal_journal_entries(disposal_request)
                
                # Create audit log
                DisposalAuditLog.objects.create(
                    disposal_request=disposal_request,
                    action='reverse',
                    description=f'Disposal reversed: {form.cleaned_data["reversal_reason"]}',
                    user=request.user,
                    ip_address=request.META.get('REMOTE_ADDR', ''),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                # Create notification
                _create_reversal_notification(disposal_request)
                
                messages.success(request, 'Disposal reversed successfully.')
                return redirect('dispose_asset:disposal_detail', disposal_id=disposal_request.id)
    else:
        form = DisposalReversalForm()
    
    context = {
        'disposal_request': disposal_request,
        'form': form,
    }
    
    return render(request, 'dispose_asset/reverse.html', context)


@login_required
def asset_selection(request):
    """Asset selection page for disposal requests"""
    if request.method == 'POST':
        form = AssetSelectionForm(request.POST)
        
        if form.is_valid():
            selected_assets = form.cleaned_data.get('selected_assets')
            
            if selected_assets:
                # Store selected assets in session for disposal form
                request.session['selected_assets'] = [asset.id for asset in selected_assets]
                messages.success(request, f'{len(selected_assets)} assets selected for disposal.')
                return redirect('dispose_asset:disposal_create')
            else:
                messages.error(request, 'Please select at least one asset.')
    else:
        form = AssetSelectionForm()
    
    # Get assets for display
    assets = Asset.objects.filter(
        is_deleted=False,
        status__name__in=['Active', 'Available']
    ).select_related('category', 'location', 'status', 'assigned_to')
    
    # Apply filters from form
    if form.is_valid():
        search = form.cleaned_data.get('search')
        category = form.cleaned_data.get('category')
        location = form.cleaned_data.get('location')
        status = form.cleaned_data.get('status')
        assigned_to = form.cleaned_data.get('assigned_to')
        
        if search:
            assets = assets.filter(
                Q(asset_name__icontains=search) |
                Q(asset_code__icontains=search) |
                Q(serial_number__icontains=search)
            )
        
        if category:
            assets = assets.filter(category=category)
        
        if location:
            assets = assets.filter(location=location)
        
        if status:
            assets = assets.filter(status=status)
        
        if assigned_to:
            assets = assets.filter(assigned_to=assigned_to)
    
    # Pagination
    paginator = Paginator(assets, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'page_obj': page_obj,
    }
    
    return render(request, 'dispose_asset/asset_selection.html', context)


@login_required
def bulk_disposal(request):
    """Bulk disposal functionality"""
    if request.method == 'POST':
        form = BulkDisposalForm(request.POST)
        
        if form.is_valid():
            # Get selected assets from session
            selected_asset_ids = request.session.get('selected_assets', [])
            
            if not selected_asset_ids:
                messages.error(request, 'No assets selected for bulk disposal.')
                return redirect('dispose_asset:asset_selection')
            
            with transaction.atomic():
                # Create disposal request
                disposal_request = DisposalRequest.objects.create(
                    title=form.cleaned_data['reason'][:200],
                    description=f"Bulk disposal of {len(selected_asset_ids)} assets",
                    is_batch=True,
                    disposal_type=form.cleaned_data['disposal_type'],
                    disposal_date=form.cleaned_data['disposal_date'],
                    disposal_value=form.cleaned_data.get('disposal_value', 0),
                    reason=form.cleaned_data['reason'],
                    remarks=form.cleaned_data.get('remarks', ''),
                    asset_account=form.cleaned_data['asset_account'],
                    disposal_account=form.cleaned_data['disposal_account'],
                    created_by=request.user
                )
                
                # Create disposal items
                assets = Asset.objects.filter(id__in=selected_asset_ids)
                for asset in assets:
                    DisposalItem.objects.create(
                        disposal_request=disposal_request,
                        asset=asset
                    )
                
                # Clear session
                del request.session['selected_assets']
                
                # Create audit log
                DisposalAuditLog.objects.create(
                    disposal_request=disposal_request,
                    action='create',
                    description=f'Bulk disposal request created for {len(selected_asset_ids)} assets',
                    user=request.user,
                    ip_address=request.META.get('REMOTE_ADDR', ''),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                messages.success(request, f'Bulk disposal request created successfully for {len(selected_asset_ids)} assets.')
                return redirect('dispose_asset:disposal_detail', disposal_id=disposal_request.id)
    else:
        form = BulkDisposalForm()
    
    # Get context data for filters
    context = {
        'form': form,
        'categories': AssetCategory.objects.all(),
        'locations': AssetLocation.objects.filter(is_active=True),
        'users': User.objects.filter(is_active=True),
        'disposal_types': DisposalType.objects.filter(is_active=True),
        'asset_accounts': ChartOfAccount.objects.filter(
            account_type__category='ASSET',
            is_active=True
        ).order_by('name'),
        'disposal_accounts': ChartOfAccount.objects.filter(
            account_type__category='EXPENSE',
            is_active=True
        ).order_by('name'),
    }
    
    return render(request, 'dispose_asset/bulk_disposal.html', context)


# AJAX endpoints
@login_required
@require_POST
@csrf_exempt
def asset_search_ajax(request):
    """AJAX endpoint for asset search with pagination"""
    try:
        # Get filter parameters
        search = request.POST.get('search', '')
        category_id = request.POST.get('category', '')
        location_id = request.POST.get('location', '')
        status = request.POST.get('status', '')
        assigned_to_id = request.POST.get('assigned_to', '')
        page = int(request.POST.get('page', 1))
        per_page = 12
        
        # Build queryset
        queryset = Asset.objects.filter(
            is_deleted=False,
            status__name__in=['Active', 'Available']
        ).select_related('category', 'location', 'status', 'assigned_to')
        
        # Apply filters
        if search:
            queryset = queryset.filter(
                Q(asset_name__icontains=search) |
                Q(asset_code__icontains=search) |
                Q(serial_number__icontains=search)
            )
        
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        if location_id:
            queryset = queryset.filter(location_id=location_id)
        
        if status:
            queryset = queryset.filter(status__name=status)
        
        if assigned_to_id:
            queryset = queryset.filter(assigned_to_id=assigned_to_id)
        
        # Order by asset code
        queryset = queryset.order_by('asset_code')
        
        # Paginate
        paginator = Paginator(queryset, per_page)
        assets_page = paginator.get_page(page)
        
        # Prepare asset data
        asset_data = []
        for asset in assets_page:
            asset_data.append({
                'id': asset.id,
                'asset_code': asset.asset_code,
                'asset_name': asset.asset_name,
                'category': asset.category.name if asset.category else '',
                'location': asset.location.name if asset.location else '',
                'status': asset.status.name if asset.status else '',
                'assigned_to': asset.assigned_to.get_full_name() if asset.assigned_to else 'Unassigned',
                'book_value': float(asset.book_value),
                'serial_number': asset.serial_number or '',
            })
        
        # Prepare pagination data
        pagination_data = {
            'current_page': page,
            'total_pages': paginator.num_pages,
            'has_previous': assets_page.has_previous(),
            'has_next': assets_page.has_next(),
            'previous_page_number': assets_page.previous_page_number() if assets_page.has_previous() else None,
            'next_page_number': assets_page.next_page_number() if assets_page.has_next() else None,
            'total_count': paginator.count,
        }
        
        return JsonResponse({
            'success': True,
            'assets': asset_data,
            'pagination': pagination_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_POST
@csrf_exempt
def disposal_stats_ajax(request):
    """AJAX endpoint for disposal statistics"""
    try:
        data = json.loads(request.body)
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        
        queryset = DisposalRequest.objects.all()
        
        if date_from:
            queryset = queryset.filter(disposal_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(disposal_date__lte=date_to)
        
        stats = {
            'total_requests': queryset.count(),
            'pending_approval': queryset.filter(status='pending_approval').count(),
            'approved': queryset.filter(status='approved').count(),
            'disposed': queryset.filter(status='disposed').count(),
            'rejected': queryset.filter(status='rejected').count(),
        }
        
        return JsonResponse(stats)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# Helper methods
def _is_approval_complete(disposal_request):
    """Check if all required approvals are complete"""
    # This is a simplified version - in a real system, you'd check against configured approval levels
    return disposal_request.current_approval_level >= 2  # Assuming 2 levels of approval


def _create_approval_notifications(disposal_request):
    """Create notifications for approvers"""
    # This is a placeholder - in a real system, you'd send actual notifications
    pass


def _create_approval_complete_notification(disposal_request):
    """Create notification when approval is complete"""
    # This is a placeholder - in a real system, you'd send actual notifications
    pass


def _create_rejection_notification(disposal_request, approval):
    """Create notification for rejection"""
    # This is a placeholder - in a real system, you'd send actual notifications
    pass


def _create_disposal_complete_notification(disposal_request):
    """Create notification when disposal is complete"""
    # This is a placeholder - in a real system, you'd send actual notifications
    pass


def _create_reversal_notification(disposal_request):
    """Create notification for reversal"""
    # This is a placeholder - in a real system, you'd send actual notifications
    pass


def _create_journal_entries(disposal_request):
    """Create journal entries for disposal"""
    # This is a simplified version - in a real system, you'd create proper journal entries
    journal_entry = DisposalJournalEntry.objects.create(
        disposal_request=disposal_request,
        entry_date=disposal_request.disposal_date,
        reference=f"DR-{disposal_request.request_id}",
        description=f"Disposal of assets: {disposal_request.title}",
        total_debit=disposal_request.total_asset_value,
        total_credit=disposal_request.total_asset_value,
        created_by=disposal_request.created_by
    )
    
    # Create journal lines based on disposal type
    if disposal_request.disposal_type.name.lower() == 'sold':
        # For sale: Dr. Bank, Cr. Asset, Dr./Cr. Gain/Loss
        if disposal_request.bank_account:
            DisposalJournalLine.objects.create(
                journal_entry=journal_entry,
                account=disposal_request.bank_account,
                description="Cash received from asset sale",
                debit_amount=disposal_request.disposal_value,
                credit_amount=0,
                line_number=1
            )
        
        if disposal_request.asset_account:
            DisposalJournalLine.objects.create(
                journal_entry=journal_entry,
                account=disposal_request.asset_account,
                description="Asset removed from books",
                debit_amount=0,
                credit_amount=disposal_request.total_asset_value,
                line_number=2
            )
        
        # Gain/Loss account
        if disposal_request.disposal_account:
            gain_loss = disposal_request.gain_loss_amount
            if gain_loss != 0:
                DisposalJournalLine.objects.create(
                    journal_entry=journal_entry,
                    account=disposal_request.disposal_account,
                    description="Gain/Loss on disposal",
                    debit_amount=0 if gain_loss > 0 else abs(gain_loss),
                    credit_amount=gain_loss if gain_loss > 0 else 0,
                    line_number=3
                )
    else:
        # For scrap/donation/loss: Dr. Loss, Cr. Asset
        if disposal_request.disposal_account:
            DisposalJournalLine.objects.create(
                journal_entry=journal_entry,
                account=disposal_request.disposal_account,
                description=f"Loss on {disposal_request.disposal_type.name.lower()}",
                debit_amount=disposal_request.total_asset_value,
                credit_amount=0,
                line_number=1
            )
        
        if disposal_request.asset_account:
            DisposalJournalLine.objects.create(
                journal_entry=journal_entry,
                account=disposal_request.asset_account,
                description="Asset removed from books",
                debit_amount=0,
                credit_amount=disposal_request.total_asset_value,
                line_number=2
            )


def _create_reversal_journal_entries(disposal_request):
    """Create reversal journal entries"""
    # This is a simplified version - in a real system, you'd create proper reversal entries
    journal_entry = DisposalJournalEntry.objects.create(
        disposal_request=disposal_request,
        entry_date=timezone.now().date(),
        reference=f"DR-REV-{disposal_request.request_id}",
        description=f"Reversal of disposal: {disposal_request.title}",
        total_debit=disposal_request.total_asset_value,
        total_credit=disposal_request.total_asset_value,
        created_by=disposal_request.reversed_by,
        is_reversed=True,
        reversed_at=timezone.now(),
        reversed_by=disposal_request.reversed_by
    )
    
    # Create reversal lines (opposite of original entries)
    if disposal_request.asset_account:
        DisposalJournalLine.objects.create(
            journal_entry=journal_entry,
            account=disposal_request.asset_account,
            description="Asset restored to books",
            debit_amount=disposal_request.total_asset_value,
            credit_amount=0,
            line_number=1
        )
    
    if disposal_request.disposal_account:
        DisposalJournalLine.objects.create(
            journal_entry=journal_entry,
            account=disposal_request.disposal_account,
            description="Reversal of disposal loss",
            debit_amount=0,
            credit_amount=disposal_request.total_asset_value,
            line_number=2
        )
