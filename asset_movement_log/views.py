from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from datetime import datetime, timedelta
import json

from .models import AssetMovementLog, AssetMovementTemplate, AssetMovementSettings
from .forms import (
    AssetMovementLogForm, AssetMovementLogSearchForm, AssetMovementLogExportForm,
    AssetMovementTemplateForm, AssetMovementSettingsForm, QuickMovementForm
)


class AssetManagerRequiredMixin(UserPassesTestMixin):
    """Mixin to require asset manager permissions"""
    
    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.is_staff or 
            self.request.user.groups.filter(name='Asset Manager').exists()
        )


@login_required
def asset_movement_dashboard(request):
    """Dashboard for asset movement logs"""
    # Get recent movements
    recent_movements = AssetMovementLog.objects.select_related(
        'asset', 'from_location', 'to_location', 'moved_by'
    ).order_by('-movement_date')[:10]
    
    # Get movement statistics
    total_movements = AssetMovementLog.objects.count()
    pending_movements = AssetMovementLog.objects.filter(is_completed=False).count()
    overdue_movements = AssetMovementLog.objects.filter(
        estimated_duration__isnull=False,
        actual_return_date__isnull=True
    ).count()
    
    # Get movements by type
    movements_by_type = AssetMovementLog.objects.values('movement_type').annotate(
        count=Count('movement_id')
    ).order_by('-count')
    
    # Get movements by location
    movements_by_location = AssetMovementLog.objects.values('to_location__name').annotate(
        count=Count('movement_id')
    ).filter(to_location__isnull=False).order_by('-count')[:5]
    
    # Get monthly movement trends
    current_month = timezone.now().month
    current_year = timezone.now().year
    monthly_movements = AssetMovementLog.objects.filter(
        movement_date__year=current_year,
        movement_date__month=current_month
    ).count()
    
    context = {
        'recent_movements': recent_movements,
        'total_movements': total_movements,
        'pending_movements': pending_movements,
        'overdue_movements': overdue_movements,
        'movements_by_type': movements_by_type,
        'movements_by_location': movements_by_location,
        'monthly_movements': monthly_movements,
    }
    
    return render(request, 'asset_movement_log/dashboard.html', context)


class AssetMovementLogListView(LoginRequiredMixin, ListView):
    """List view for asset movement logs with search and filtering"""
    model = AssetMovementLog
    template_name = 'asset_movement_log/movement_list.html'
    context_object_name = 'movements'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = AssetMovementLog.objects.select_related(
            'asset', 'from_location', 'to_location', 'moved_by', 'from_user', 'to_user'
        ).order_by('-movement_date')
        
        # Apply search and filters
        form = AssetMovementLogSearchForm(self.request.GET)
        if form.is_valid():
            search = form.cleaned_data.get('search')
            if search:
                queryset = queryset.filter(
                    Q(asset__asset_code__icontains=search) |
                    Q(asset__asset_name__icontains=search) |
                    Q(notes__icontains=search) |
                    Q(reason_description__icontains=search)
                )
            
            # Date range filter
            date_from = form.cleaned_data.get('date_from')
            date_to = form.cleaned_data.get('date_to')
            if date_from:
                queryset = queryset.filter(movement_date__date__gte=date_from)
            if date_to:
                queryset = queryset.filter(movement_date__date__lte=date_to)
            
            # Other filters
            movement_type = form.cleaned_data.get('movement_type')
            if movement_type:
                queryset = queryset.filter(movement_type=movement_type)
            
            movement_reason = form.cleaned_data.get('movement_reason')
            if movement_reason:
                queryset = queryset.filter(movement_reason=movement_reason)
            
            from_location = form.cleaned_data.get('from_location')
            if from_location:
                queryset = queryset.filter(from_location=from_location)
            
            to_location = form.cleaned_data.get('to_location')
            if to_location:
                queryset = queryset.filter(to_location=to_location)
            
            moved_by = form.cleaned_data.get('moved_by')
            if moved_by:
                queryset = queryset.filter(moved_by=moved_by)
            
            is_completed = form.cleaned_data.get('is_completed')
            if is_completed:
                queryset = queryset.filter(is_completed=is_completed == 'True')
            
            is_approved = form.cleaned_data.get('is_approved')
            if is_approved:
                queryset = queryset.filter(is_approved=is_approved == 'True')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = AssetMovementLogSearchForm(self.request.GET)
        return context


class AssetMovementLogCreateView(LoginRequiredMixin, AssetManagerRequiredMixin, CreateView):
    """Create view for asset movement logs"""
    model = AssetMovementLog
    form_class = AssetMovementLogForm
    template_name = 'asset_movement_log/movement_form.html'
    success_url = reverse_lazy('asset_movement_log:movement_list')
    
    def form_valid(self, form):
        form.instance.moved_by = self.request.user
        form.instance.created_by = self.request.user
        
        # Auto-approve if settings allow
        settings = AssetMovementSettings.get_settings()
        if settings.auto_approve_assignments and form.instance.movement_type == 'assignment':
            form.instance.is_approved = True
            form.instance.approved_by = self.request.user
            form.instance.approved_date = timezone.now()
        
        messages.success(self.request, 'Asset movement log created successfully.')
        return super().form_valid(form)


class AssetMovementLogUpdateView(LoginRequiredMixin, AssetManagerRequiredMixin, UpdateView):
    """Update view for asset movement logs"""
    model = AssetMovementLog
    form_class = AssetMovementLogForm
    template_name = 'asset_movement_log/movement_form.html'
    success_url = reverse_lazy('asset_movement_log:movement_list')
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Asset movement log updated successfully.')
        return super().form_valid(form)


class AssetMovementLogDetailView(LoginRequiredMixin, DetailView):
    """Detail view for asset movement logs"""
    model = AssetMovementLog
    template_name = 'asset_movement_log/movement_detail.html'
    context_object_name = 'movement'


class AssetMovementLogDeleteView(LoginRequiredMixin, AssetManagerRequiredMixin, DeleteView):
    """Delete view for asset movement logs"""
    model = AssetMovementLog
    template_name = 'asset_movement_log/movement_confirm_delete.html'
    success_url = reverse_lazy('asset_movement_log:movement_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Asset movement log deleted successfully.')
        return super().delete(request, *args, **kwargs)


@login_required
def asset_movement_export(request):
    """Export asset movement logs"""
    if request.method == 'POST':
        form = AssetMovementLogExportForm(request.POST)
        if form.is_valid():
            export_format = form.cleaned_data['export_format']
            include_details = form.cleaned_data['include_details']
            date_range = form.cleaned_data['date_range']
            
            # Get queryset based on date range
            queryset = AssetMovementLog.objects.select_related(
                'asset', 'from_location', 'to_location', 'moved_by'
            )
            
            if date_range == 'today':
                queryset = queryset.filter(movement_date__date=timezone.now().date())
            elif date_range == 'week':
                start_date = timezone.now().date() - timedelta(days=7)
                queryset = queryset.filter(movement_date__date__gte=start_date)
            elif date_range == 'month':
                start_date = timezone.now().date() - timedelta(days=30)
                queryset = queryset.filter(movement_date__date__gte=start_date)
            elif date_range == 'quarter':
                start_date = timezone.now().date() - timedelta(days=90)
                queryset = queryset.filter(movement_date__date__gte=start_date)
            elif date_range == 'year':
                start_date = timezone.now().date() - timedelta(days=365)
                queryset = queryset.filter(movement_date__date__gte=start_date)
            elif date_range == 'custom':
                custom_date_from = form.cleaned_data.get('custom_date_from')
                custom_date_to = form.cleaned_data.get('custom_date_to')
                if custom_date_from:
                    queryset = queryset.filter(movement_date__date__gte=custom_date_from)
                if custom_date_to:
                    queryset = queryset.filter(movement_date__date__lte=custom_date_to)
            
            # Generate export based on format
            if export_format == 'csv':
                return export_to_csv(queryset, include_details)
            elif export_format == 'excel':
                return export_to_excel(queryset, include_details)
            elif export_format == 'pdf':
                return export_to_pdf(queryset, include_details)
    else:
        form = AssetMovementLogExportForm()
    
    return render(request, 'asset_movement_log/export.html', {'form': form})


def export_to_csv(queryset, include_details):
    """Export to CSV format"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="asset_movements.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Movement ID', 'Asset Code', 'Asset Name', 'Movement Type', 'Movement Date',
        'From Location', 'To Location', 'Moved By', 'Reason', 'Notes', 'Status'
    ])
    
    for movement in queryset:
        writer.writerow([
            movement.movement_id,
            movement.asset.asset_code,
            movement.asset.asset_name,
            movement.get_movement_type_display(),
            movement.movement_date.strftime('%Y-%m-%d %H:%M'),
            movement.from_location.name if movement.from_location else '',
            movement.to_location.name if movement.to_location else '',
            movement.moved_by.get_full_name() or movement.moved_by.username,
            movement.get_movement_reason_display(),
            movement.notes,
            'Completed' if movement.is_completed else 'Pending'
        ])
    
    return response


def export_to_excel(queryset, include_details):
    """Export to Excel format"""
    # This would require openpyxl or xlsxwriter
    # For now, return CSV
    return export_to_csv(queryset, include_details)


def export_to_pdf(queryset, include_details):
    """Export to PDF format"""
    # This would require reportlab or weasyprint
    # For now, return CSV
    return export_to_csv(queryset, include_details)


@login_required
def asset_movement_api(request):
    """API endpoint for asset movement data"""
    if request.method == 'GET':
        movements = AssetMovementLog.objects.select_related(
            'asset', 'from_location', 'to_location', 'moved_by'
        ).order_by('-movement_date')[:50]
        
        data = []
        for movement in movements:
            data.append({
                'id': str(movement.movement_id),
                'asset_code': movement.asset.asset_code,
                'asset_name': movement.asset.asset_name,
                'movement_type': movement.get_movement_type_display(),
                'movement_date': movement.movement_date.strftime('%Y-%m-%d %H:%M'),
                'from_location': movement.from_location.name if movement.from_location else '',
                'to_location': movement.to_location.name if movement.to_location else '',
                'moved_by': movement.moved_by.get_full_name() or movement.moved_by.username,
                'status': 'Completed' if movement.is_completed else 'Pending'
            })
        
        return JsonResponse({'movements': data})
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)


@login_required
def quick_movement_create(request):
    """Quick create movement form"""
    if request.method == 'POST':
        form = QuickMovementForm(request.POST)
        if form.is_valid():
            movement = form.save(commit=False)
            movement.moved_by = request.user
            movement.created_by = request.user
            movement.movement_date = timezone.now()
            movement.save()
            
            messages.success(request, 'Asset movement created successfully.')
            return redirect('asset_movement_log:movement_list')
    else:
        form = QuickMovementForm()
    
    return render(request, 'asset_movement_log/quick_movement.html', {'form': form})


# Template views
class AssetMovementTemplateListView(LoginRequiredMixin, ListView):
    """List view for asset movement templates"""
    model = AssetMovementTemplate
    template_name = 'asset_movement_log/template_list.html'
    context_object_name = 'templates'
    paginate_by = 20


class AssetMovementTemplateCreateView(LoginRequiredMixin, AssetManagerRequiredMixin, CreateView):
    """Create view for asset movement templates"""
    model = AssetMovementTemplate
    form_class = AssetMovementTemplateForm
    template_name = 'asset_movement_log/template_form.html'
    success_url = reverse_lazy('asset_movement_log:template_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Asset movement template created successfully.')
        return super().form_valid(form)


class AssetMovementTemplateUpdateView(LoginRequiredMixin, AssetManagerRequiredMixin, UpdateView):
    """Update view for asset movement templates"""
    model = AssetMovementTemplate
    form_class = AssetMovementTemplateForm
    template_name = 'asset_movement_log/template_form.html'
    success_url = reverse_lazy('asset_movement_log:template_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Asset movement template updated successfully.')
        return super().form_valid(form)


class AssetMovementTemplateDeleteView(LoginRequiredMixin, AssetManagerRequiredMixin, DeleteView):
    """Delete view for asset movement templates"""
    model = AssetMovementTemplate
    template_name = 'asset_movement_log/template_confirm_delete.html'
    success_url = reverse_lazy('asset_movement_log:template_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Asset movement template deleted successfully.')
        return super().delete(request, *args, **kwargs)


@login_required
def asset_movement_settings(request):
    """Asset movement settings view"""
    settings = AssetMovementSettings.get_settings()
    
    if request.method == 'POST':
        form = AssetMovementSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, 'Asset movement settings updated successfully.')
            return redirect('asset_movement_log:settings')
    else:
        form = AssetMovementSettingsForm(instance=settings)
    
    return render(request, 'asset_movement_log/settings.html', {'form': form})
