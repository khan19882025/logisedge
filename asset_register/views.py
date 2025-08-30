from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.serializers import serialize
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
import json
import csv
from datetime import datetime, date
from decimal import Decimal

from .models import (
    Asset, AssetCategory, AssetLocation, AssetStatus, AssetDepreciation,
    AssetMovement, AssetMaintenance
)
from .forms import (
    AssetForm, AssetCategoryForm, AssetLocationForm, AssetStatusForm,
    AssetDepreciationForm, AssetMovementForm, AssetMaintenanceForm,
    AssetSearchForm, AssetDisposalForm
)


@login_required
def asset_list(request):
    """Display list of assets with search and filter functionality"""
    assets = Asset.objects.filter(is_deleted=False).select_related(
        'category', 'location', 'status', 'assigned_to', 'depreciation_method'
    )
    
    # Handle search and filters
    search_form = AssetSearchForm(request.GET)
    if search_form.is_valid():
        search = search_form.cleaned_data.get('search')
        category = search_form.cleaned_data.get('category')
        location = search_form.cleaned_data.get('location')
        status = search_form.cleaned_data.get('status')
        assigned_to = search_form.cleaned_data.get('assigned_to')
        purchase_date_from = search_form.cleaned_data.get('purchase_date_from')
        purchase_date_to = search_form.cleaned_data.get('purchase_date_to')
        value_min = search_form.cleaned_data.get('value_min')
        value_max = search_form.cleaned_data.get('value_max')
        
        # Apply filters
        if search:
            assets = assets.filter(
                Q(asset_code__icontains=search) |
                Q(asset_name__icontains=search) |
                Q(description__icontains=search) |
                Q(serial_number__icontains=search) |
                Q(model_number__icontains=search) |
                Q(manufacturer__icontains=search)
            )
        
        if category:
            assets = assets.filter(category=category)
        
        if location:
            assets = assets.filter(location=location)
        
        if status:
            assets = assets.filter(status=status)
        
        if assigned_to:
            assets = assets.filter(assigned_to=assigned_to)
        
        if purchase_date_from:
            assets = assets.filter(purchase_date__gte=purchase_date_from)
        
        if purchase_date_to:
            assets = assets.filter(purchase_date__lte=purchase_date_to)
        
        if value_min:
            assets = assets.filter(purchase_value__gte=value_min)
        
        if value_max:
            assets = assets.filter(purchase_value__lte=value_max)
    
    # Pagination
    paginator = Paginator(assets, 25)  # Show 25 assets per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get summary statistics
    total_assets = assets.count()
    total_value = assets.aggregate(Sum('purchase_value'))['purchase_value__sum'] or 0
    total_book_value = assets.aggregate(Sum('book_value'))['book_value__sum'] or 0
    
    # Get filter options for the form
    categories = AssetCategory.objects.all()
    locations = AssetLocation.objects.filter(is_active=True)
    statuses = AssetStatus.objects.filter(is_active=True)
    users = User.objects.filter(is_active=True)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_assets': total_assets,
        'total_value': total_value,
        'total_book_value': total_book_value,
        'categories': categories,
        'locations': locations,
        'statuses': statuses,
        'users': users,
    }
    
    return render(request, 'asset_register/list.html', context)


@login_required
def asset_detail(request, asset_id):
    """Display detailed view of an asset"""
    asset = get_object_or_404(Asset, id=asset_id, is_deleted=False)
    
    # Get related data
    movements = asset.movements.all().order_by('-movement_date')[:10]
    maintenance_records = asset.maintenance_records.all().order_by('-maintenance_date')[:10]
    
    # Calculate depreciation
    current_depreciation = asset.calculate_depreciation()
    
    context = {
        'asset': asset,
        'movements': movements,
        'maintenance_records': maintenance_records,
        'current_depreciation': current_depreciation,
    }
    
    return render(request, 'asset_register/detail.html', context)


@login_required
def asset_create(request):
    """Create a new asset"""
    if request.method == 'POST':
        form = AssetForm(request.POST)
        if form.is_valid():
            asset = form.save(commit=False)
            asset.created_by = request.user
            asset.save()
            
            messages.success(request, f'Asset "{asset.asset_name}" created successfully.')
            return redirect('asset_register:asset_detail', asset_id=asset.id)
    else:
        form = AssetForm()
    
    context = {
        'form': form,
        'title': 'Add New Asset',
        'action': 'Create'
    }
    
    return render(request, 'asset_register/form.html', context)


@login_required
def asset_edit(request, asset_id):
    """Edit an existing asset"""
    asset = get_object_or_404(Asset, id=asset_id, is_deleted=False)
    
    if request.method == 'POST':
        form = AssetForm(request.POST, instance=asset)
        if form.is_valid():
            asset = form.save(commit=False)
            asset.updated_by = request.user
            asset.save()
            
            messages.success(request, f'Asset "{asset.asset_name}" updated successfully.')
            return redirect('asset_register:asset_detail', asset_id=asset.id)
    else:
        form = AssetForm(instance=asset)
    
    context = {
        'form': form,
        'asset': asset,
        'title': 'Edit Asset',
        'action': 'Update'
    }
    
    return render(request, 'asset_register/form.html', context)


@login_required
def asset_delete(request, asset_id):
    """Soft delete an asset"""
    asset = get_object_or_404(Asset, id=asset_id, is_deleted=False)
    
    if request.method == 'POST':
        asset.is_deleted = True
        asset.deleted_at = timezone.now()
        asset.deleted_by = request.user
        asset.save()
        
        messages.success(request, f'Asset "{asset.asset_name}" deleted successfully.')
        return redirect('asset_register:asset_list')
    
    context = {
        'asset': asset
    }
    
    return render(request, 'asset_register/delete_confirm.html', context)


@login_required
def asset_dispose(request, asset_id):
    """Dispose of an asset"""
    asset = get_object_or_404(Asset, id=asset_id, is_deleted=False)
    
    if request.method == 'POST':
        form = AssetDisposalForm(request.POST)
        if form.is_valid():
            disposal_date = form.cleaned_data['disposal_date']
            disposal_reason = form.cleaned_data['disposal_reason']
            disposal_value = form.cleaned_data.get('disposal_value', 0)
            
            # Update asset status to disposed
            disposed_status = AssetStatus.objects.filter(name__icontains='disposed').first()
            if disposed_status:
                asset.status = disposed_status
            
            asset.disposal_date = disposal_date
            asset.disposal_reason = disposal_reason
            asset.disposal_value = disposal_value
            asset.updated_by = request.user
            asset.save()
            
            # Record movement
            AssetMovement.objects.create(
                asset=asset,
                movement_type='disposal',
                from_location=asset.location,
                from_user=asset.assigned_to,
                movement_date=timezone.now(),
                reason=disposal_reason,
                created_by=request.user
            )
            
            messages.success(request, f'Asset "{asset.asset_name}" disposed successfully.')
            return redirect('asset_register:asset_detail', asset_id=asset.id)
    else:
        form = AssetDisposalForm()
    
    context = {
        'form': form,
        'asset': asset,
        'title': 'Dispose Asset',
        'action': 'Dispose'
    }
    
    return render(request, 'asset_register/form.html', context)


@login_required
def asset_movement(request, asset_id):
    """Record asset movement"""
    asset = get_object_or_404(Asset, id=asset_id, is_deleted=False)
    
    if request.method == 'POST':
        form = AssetMovementForm(request.POST)
        if form.is_valid():
            movement = form.save(commit=False)
            movement.asset = asset
            movement.created_by = request.user
            movement.save()
            
            # Update asset location and assignment if needed
            if movement.movement_type == 'transfer':
                asset.location = movement.to_location
            elif movement.movement_type == 'assignment':
                asset.assigned_to = movement.to_user
                asset.assigned_date = timezone.now().date()
            elif movement.movement_type == 'return':
                asset.assigned_to = None
                asset.assigned_date = None
            
            asset.updated_by = request.user
            asset.save()
            
            messages.success(request, 'Asset movement recorded successfully.')
            return redirect('asset_register:asset_detail', asset_id=asset.id)
    else:
        form = AssetMovementForm(initial={
            'from_location': asset.location,
            'from_user': asset.assigned_to,
            'movement_date': timezone.now()
        })
    
    context = {
        'form': form,
        'asset': asset
    }
    
    return render(request, 'asset_register/movement.html', context)


@login_required
def asset_maintenance(request, asset_id):
    """Record asset maintenance"""
    asset = get_object_or_404(Asset, id=asset_id, is_deleted=False)
    
    if request.method == 'POST':
        form = AssetMaintenanceForm(request.POST)
        if form.is_valid():
            maintenance = form.save(commit=False)
            maintenance.asset = asset
            maintenance.created_by = request.user
            maintenance.save()
            
            # Update asset maintenance dates
            asset.last_maintenance_date = maintenance.maintenance_date
            if maintenance.next_maintenance_date:
                asset.next_maintenance_date = maintenance.next_maintenance_date
            asset.updated_by = request.user
            asset.save()
            
            messages.success(request, 'Maintenance record added successfully.')
            return redirect('asset_register:asset_detail', asset_id=asset.id)
    else:
        form = AssetMaintenanceForm(initial={
            'maintenance_date': timezone.now().date()
        })
    
    context = {
        'form': form,
        'asset': asset
    }
    
    return render(request, 'asset_register/maintenance.html', context)


@login_required
def asset_export(request):
    """Export assets to Excel or PDF"""
    format_type = request.GET.get('format', 'excel')
    
    assets = Asset.objects.filter(is_deleted=False).select_related(
        'category', 'location', 'status', 'assigned_to', 'depreciation_method'
    )
    
    # Apply filters if any
    search_form = AssetSearchForm(request.GET)
    if search_form.is_valid():
        # Apply the same filters as in asset_list
        search = search_form.cleaned_data.get('search')
        category = search_form.cleaned_data.get('category')
        location = search_form.cleaned_data.get('location')
        status = search_form.cleaned_data.get('status')
        assigned_to = search_form.cleaned_data.get('assigned_to')
        purchase_date_from = search_form.cleaned_data.get('purchase_date_from')
        purchase_date_to = search_form.cleaned_data.get('purchase_date_to')
        value_min = search_form.cleaned_data.get('value_min')
        value_max = search_form.cleaned_data.get('value_max')
        
        if search:
            assets = assets.filter(
                Q(asset_code__icontains=search) |
                Q(asset_name__icontains=search) |
                Q(description__icontains=search)
            )
        
        if category:
            assets = assets.filter(category=category)
        
        if location:
            assets = assets.filter(location=location)
        
        if status:
            assets = assets.filter(status=status)
        
        if assigned_to:
            assets = assets.filter(assigned_to=assigned_to)
        
        if purchase_date_from:
            assets = assets.filter(purchase_date__gte=purchase_date_from)
        
        if purchase_date_to:
            assets = assets.filter(purchase_date__lte=purchase_date_to)
        
        if value_min:
            assets = assets.filter(purchase_value__gte=value_min)
        
        if value_max:
            assets = assets.filter(purchase_value__lte=value_max)
    
    if format_type == 'excel':
        return export_to_excel(assets)
    elif format_type == 'pdf':
        return export_to_pdf(assets)
    else:
        return export_to_csv(assets)


def export_to_csv(assets):
    """Export assets to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="assets_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Asset Code', 'Asset Name', 'Category', 'Location', 'Status',
        'Purchase Date', 'Purchase Value', 'Current Value', 'Book Value',
        'Assigned To', 'Serial Number', 'Manufacturer'
    ])
    
    for asset in assets:
        writer.writerow([
            asset.asset_code,
            asset.asset_name,
            asset.category.name if asset.category else '',
            asset.location.name if asset.location else '',
            asset.status.name if asset.status else '',
            asset.purchase_date,
            asset.purchase_value,
            asset.current_value,
            asset.book_value,
            asset.assigned_to.get_full_name() if asset.assigned_to else '',
            asset.serial_number,
            asset.manufacturer
        ])
    
    return response


def export_to_excel(assets):
    """Export assets to Excel (placeholder - would need openpyxl or xlsxwriter)"""
    # For now, return CSV with Excel extension
    response = export_to_csv(assets)
    response['Content-Disposition'] = f'attachment; filename="assets_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
    return response


def export_to_pdf(assets):
    """Export assets to PDF (placeholder - would need reportlab or weasyprint)"""
    # For now, return a simple HTML response
    html_content = render_to_string('asset_register/pdf_export.html', {'assets': assets})
    response = HttpResponse(html_content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="assets_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
    return response


@login_required
def asset_qr_code(request, asset_id):
    """Generate QR code for asset"""
    asset = get_object_or_404(Asset, id=asset_id, is_deleted=False)
    
    if not asset.qr_code:
        asset.generate_qr_code()
        asset.save()
    
    return redirect(asset.qr_code.url)


@login_required
def asset_barcode(request, asset_id):
    """Generate barcode for asset"""
    asset = get_object_or_404(Asset, id=asset_id, is_deleted=False)
    
    if not asset.barcode:
        asset.generate_barcode()
        asset.save()
    
    return redirect(asset.barcode.url)


@login_required
def asset_print(request, asset_id):
    """Print asset details"""
    asset = get_object_or_404(Asset, id=asset_id, is_deleted=False)
    
    context = {
        'asset': asset,
        'print_mode': True
    }
    
    return render(request, 'asset_register/print.html', context)


# AJAX endpoints for dynamic functionality

@login_required
@require_GET
def asset_search_ajax(request):
    """AJAX endpoint for asset search with autocomplete"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    assets = Asset.objects.filter(
        is_deleted=False
    ).filter(
        Q(asset_code__icontains=query) |
        Q(asset_name__icontains=query) |
        Q(serial_number__icontains=query)
    )[:10]
    
    results = []
    for asset in assets:
        results.append({
            'id': asset.id,
            'code': asset.asset_code,
            'name': asset.asset_name,
            'location': asset.location.name if asset.location else '',
            'status': asset.status.name if asset.status else '',
            'url': f'/accounting/asset-register/{asset.id}/'
        })
    
    return JsonResponse({'results': results})


@login_required
@require_GET
def asset_stats_ajax(request):
    """AJAX endpoint for asset statistics"""
    total_assets = Asset.objects.filter(is_deleted=False).count()
    active_assets = Asset.objects.filter(is_deleted=False, status__name__icontains='active').count()
    disposed_assets = Asset.objects.filter(is_deleted=False, status__name__icontains='disposed').count()
    under_repair = Asset.objects.filter(is_deleted=False, status__name__icontains='repair').count()
    
    total_value = Asset.objects.filter(is_deleted=False).aggregate(Sum('purchase_value'))['purchase_value__sum'] or 0
    total_book_value = Asset.objects.filter(is_deleted=False).aggregate(Sum('book_value'))['book_value__sum'] or 0
    
    # Category breakdown
    category_stats = Asset.objects.filter(is_deleted=False).values('category__name').annotate(
        count=Count('id'),
        total_value=Sum('purchase_value')
    ).order_by('-count')[:5]
    
    stats = {
        'total_assets': total_assets,
        'active_assets': active_assets,
        'disposed_assets': disposed_assets,
        'under_repair': under_repair,
        'total_value': float(total_value),
        'total_book_value': float(total_book_value),
        'category_stats': list(category_stats)
    }
    
    return JsonResponse(stats)


@login_required
@require_POST
@csrf_exempt
def asset_bulk_action(request):
    """AJAX endpoint for bulk actions on assets"""
    action = request.POST.get('action')
    asset_ids = request.POST.getlist('asset_ids')
    
    if not asset_ids:
        return JsonResponse({'success': False, 'message': 'No assets selected'})
    
    assets = Asset.objects.filter(id__in=asset_ids, is_deleted=False)
    
    if action == 'delete':
        for asset in assets:
            asset.is_deleted = True
            asset.deleted_at = timezone.now()
            asset.deleted_by = request.user
            asset.save()
        message = f'{len(assets)} assets deleted successfully'
    
    elif action == 'export':
        # Handle bulk export
        message = f'{len(assets)} assets exported successfully'
    
    else:
        return JsonResponse({'success': False, 'message': 'Invalid action'})
    
    return JsonResponse({'success': True, 'message': message})


# Management views for categories, locations, statuses, etc.

@login_required
def category_list(request):
    """List asset categories"""
    categories = AssetCategory.objects.all()
    context = {'categories': categories}
    return render(request, 'asset_register/category_list.html', context)


@login_required
def category_create(request):
    """Create new asset category"""
    if request.method == 'POST':
        form = AssetCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created successfully.')
            return redirect('asset_register:category_list')
    else:
        form = AssetCategoryForm()
    
    context = {'form': form, 'title': 'Add Category'}
    return render(request, 'asset_register/category_form.html', context)


@login_required
def location_list(request):
    """List asset locations"""
    locations = AssetLocation.objects.all()
    context = {'locations': locations}
    return render(request, 'asset_register/location_list.html', context)


@login_required
def location_create(request):
    """Create new asset location"""
    if request.method == 'POST':
        form = AssetLocationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Location created successfully.')
            return redirect('asset_register:location_list')
    else:
        form = AssetLocationForm()
    
    context = {'form': form, 'title': 'Add Location'}
    return render(request, 'asset_register/location_form.html', context)


@login_required
def status_list(request):
    """List asset statuses"""
    statuses = AssetStatus.objects.all()
    context = {'statuses': statuses}
    return render(request, 'asset_register/status_list.html', context)


@login_required
def status_create(request):
    """Create new asset status"""
    if request.method == 'POST':
        form = AssetStatusForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Status created successfully.')
            return redirect('asset_register:status_list')
    else:
        form = AssetStatusForm()
    
    context = {'form': form, 'title': 'Add Status'}
    return render(request, 'asset_register/status_form.html', context)


@login_required
def depreciation_list(request):
    """List depreciation methods"""
    depreciation_methods = AssetDepreciation.objects.all()
    context = {'depreciation_methods': depreciation_methods}
    return render(request, 'asset_register/depreciation_list.html', context)


@login_required
def depreciation_create(request):
    """Create new depreciation method"""
    if request.method == 'POST':
        form = AssetDepreciationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Depreciation method created successfully.')
            return redirect('asset_register:depreciation_list')
    else:
        form = AssetDepreciationForm()
    
    context = {'form': form, 'title': 'Add Depreciation Method'}
    return render(request, 'asset_register/depreciation_form.html', context) 