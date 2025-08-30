from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Sum, Count, DecimalField
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator
from django.utils import timezone
from django.template.loader import render_to_string
from django.conf import settings

from decimal import Decimal
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import json

from .models import DepreciationSchedule, DepreciationEntry, DepreciationSettings
from .forms import (
    DepreciationScheduleForm, DepreciationScheduleFilterForm, DepreciationEntryFilterForm,
    DepreciationSettingsForm, DepreciationCalculationForm, DepreciationPostingForm,
    DepreciationExportForm, AssetDepreciationForm
)
from asset_register.models import Asset, AssetCategory
from chart_of_accounts.models import ChartOfAccount


class AssetManagerRequiredMixin(UserPassesTestMixin):
    """Mixin to require Asset Manager or Finance Manager role"""
    
    def test_func(self):
        user = self.request.user
        # Check if user has required permissions (you may need to adjust based on your permission system)
        return user.is_authenticated and (
            user.is_superuser or 
            user.groups.filter(name__in=['Asset Manager', 'Finance Manager']).exists() or
            user.has_perm('depreciation_schedule.can_run_depreciation')
        )


@login_required
def depreciation_dashboard(request):
    """Dashboard for depreciation schedule module"""
    
    # Get summary statistics
    total_schedules = DepreciationSchedule.objects.count()
    calculated_schedules = DepreciationSchedule.objects.filter(status='calculated').count()
    posted_schedules = DepreciationSchedule.objects.filter(status='posted').count()
    
    # Get total depreciation for current year
    current_year = date.today().year
    current_year_depreciation = DepreciationSchedule.objects.filter(
        start_date__year=current_year,
        status='posted'
    ).aggregate(
        total=Coalesce(Sum('total_depreciation'), Decimal('0.00'))
    )['total']
    
    # Get recent schedules
    recent_schedules = DepreciationSchedule.objects.order_by('-created_at')[:5]
    
    # Get asset statistics
    total_assets = Asset.objects.filter(is_deleted=False).count()
    depreciable_assets = Asset.objects.filter(
        is_deleted=False,
        disposal_date__isnull=True,
        purchase_value__gt=0,
        useful_life_years__gt=0
    ).count()
    
    # Get monthly depreciation trend (last 12 months)
    monthly_depreciation = []
    for i in range(12):
        month_date = date.today() - relativedelta(months=i)
        month_depreciation = DepreciationSchedule.objects.filter(
            start_date__year=month_date.year,
            start_date__month=month_date.month,
            status='posted'
        ).aggregate(
            total=Coalesce(Sum('total_depreciation'), Decimal('0.00'))
        )['total']
        
        monthly_depreciation.append({
            'month': month_date.strftime('%Y-%m'),
            'amount': float(month_depreciation)
        })
    
    monthly_depreciation.reverse()
    
    context = {
        'total_schedules': total_schedules,
        'calculated_schedules': calculated_schedules,
        'posted_schedules': posted_schedules,
        'current_year_depreciation': current_year_depreciation,
        'recent_schedules': recent_schedules,
        'total_assets': total_assets,
        'depreciable_assets': depreciable_assets,
        'monthly_depreciation': monthly_depreciation,
    }
    
    return render(request, 'depreciation_schedule/dashboard.html', context)


class DepreciationScheduleListView(LoginRequiredMixin, ListView):
    """List view for depreciation schedules"""
    model = DepreciationSchedule
    template_name = 'depreciation_schedule/schedule_list.html'
    context_object_name = 'schedules'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = DepreciationSchedule.objects.all()
        
        # Apply filters
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        start_date_from = self.request.GET.get('start_date_from')
        if start_date_from:
            queryset = queryset.filter(start_date__gte=start_date_from)
        
        start_date_to = self.request.GET.get('start_date_to')
        if start_date_to:
            queryset = queryset.filter(start_date__lte=start_date_to)
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(schedule_number__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = DepreciationScheduleFilterForm(self.request.GET)
        return context


class DepreciationScheduleCreateView(LoginRequiredMixin, AssetManagerRequiredMixin, CreateView):
    """Create view for depreciation schedules"""
    model = DepreciationSchedule
    form_class = DepreciationScheduleForm
    template_name = 'depreciation_schedule/schedule_form.html'
    success_url = reverse_lazy('depreciation_schedule:schedule_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f'Depreciation schedule "{form.instance.name}" created successfully.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['settings'] = DepreciationSettings.get_settings()
        return context


class DepreciationScheduleDetailView(LoginRequiredMixin, DetailView):
    """Detail view for depreciation schedules"""
    model = DepreciationSchedule
    template_name = 'depreciation_schedule/schedule_detail.html'
    context_object_name = 'schedule'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get depreciation entries for this schedule
        entries = self.object.depreciation_entries.all()
        
        # Apply filters
        asset_category = self.request.GET.get('asset_category')
        if asset_category:
            entries = entries.filter(asset__category_id=asset_category)
        
        asset_search = self.request.GET.get('asset_search')
        if asset_search:
            entries = entries.filter(
                Q(asset__asset_code__icontains=asset_search) |
                Q(asset__asset_name__icontains=asset_search)
            )
        
        period_from = self.request.GET.get('period_from')
        if period_from:
            entries = entries.filter(period__gte=period_from)
        
        period_to = self.request.GET.get('period_to')
        if period_to:
            entries = entries.filter(period__lte=period_to)
        
        # Paginate entries
        paginator = Paginator(entries, 50)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['entries'] = page_obj
        context['filter_form'] = DepreciationEntryFilterForm(self.request.GET)
        
        # Calculate totals
        context['total_depreciation'] = entries.aggregate(
            total=Coalesce(Sum('depreciation_amount'), Decimal('0.00'))
        )['total']
        
        context['total_assets'] = entries.values('asset').distinct().count()
        
        return context


class DepreciationScheduleUpdateView(LoginRequiredMixin, AssetManagerRequiredMixin, UpdateView):
    """Update view for depreciation schedules"""
    model = DepreciationSchedule
    form_class = DepreciationScheduleForm
    template_name = 'depreciation_schedule/schedule_form.html'
    success_url = reverse_lazy('depreciation_schedule:schedule_list')
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, f'Depreciation schedule "{form.instance.name}" updated successfully.')
        return super().form_valid(form)


class DepreciationScheduleDeleteView(LoginRequiredMixin, AssetManagerRequiredMixin, DeleteView):
    """Delete view for depreciation schedules"""
    model = DepreciationSchedule
    template_name = 'depreciation_schedule/schedule_confirm_delete.html'
    success_url = reverse_lazy('depreciation_schedule:schedule_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, f'Depreciation schedule "{self.get_object().name}" deleted successfully.')
        return super().delete(request, *args, **kwargs)


@login_required
def calculate_depreciation(request, pk):
    """Calculate depreciation for a schedule"""
    schedule = get_object_or_404(DepreciationSchedule, pk=pk)
    
    if request.method == 'POST':
        form = DepreciationCalculationForm(request.POST)
        if form.is_valid():
            try:
                # Calculate depreciation
                total_depreciation = schedule.calculate_depreciation()
                
                messages.success(
                    request, 
                    f'Depreciation calculated successfully. Total depreciation: {total_depreciation:,.2f}'
                )
                return redirect('depreciation_schedule:schedule_detail', pk=schedule.pk)
            except Exception as e:
                messages.error(request, f'Error calculating depreciation: {str(e)}')
    else:
        form = DepreciationCalculationForm()
    
    context = {
        'schedule': schedule,
        'form': form,
    }
    return render(request, 'depreciation_schedule/calculate_depreciation.html', context)


@login_required
def post_depreciation(request, pk):
    """Post depreciation to general ledger"""
    schedule = get_object_or_404(DepreciationSchedule, pk=pk)
    
    if request.method == 'POST':
        form = DepreciationPostingForm(request.POST)
        if form.is_valid():
            try:
                # Post to general ledger
                success, message = schedule.post_to_general_ledger(request.user)
                
                if success:
                    messages.success(request, message)
                else:
                    messages.error(request, message)
                
                return redirect('depreciation_schedule:schedule_detail', pk=schedule.pk)
            except Exception as e:
                messages.error(request, f'Error posting depreciation: {str(e)}')
    else:
        form = DepreciationPostingForm()
    
    context = {
        'schedule': schedule,
        'form': form,
    }
    return render(request, 'depreciation_schedule/post_depreciation.html', context)


@login_required
def depreciation_entries(request, pk):
    """View depreciation entries for a schedule"""
    schedule = get_object_or_404(DepreciationSchedule, pk=pk)
    entries = schedule.depreciation_entries.all()
    
    # Apply filters
    asset_category = request.GET.get('asset_category')
    if asset_category:
        entries = entries.filter(asset__category_id=asset_category)
    
    asset_search = request.GET.get('asset_search')
    if asset_search:
        entries = entries.filter(
            Q(asset__asset_code__icontains=asset_search) |
            Q(asset__asset_name__icontains=asset_search)
        )
    
    period_from = request.GET.get('period_from')
    if period_from:
        entries = entries.filter(period__gte=period_from)
    
    period_to = request.GET.get('period_to')
    if period_to:
        entries = entries.filter(period__lte=period_to)
    
    # Calculate total depreciation
    total_depreciation = entries.aggregate(
        total=Coalesce(Sum('depreciation_amount'), Decimal('0.00'))
    )['total']
    
    # Calculate average depreciation
    entry_count = entries.count()
    if entry_count > 0:
        average_depreciation = total_depreciation / entry_count
    else:
        average_depreciation = Decimal('0.00')
    
    # Paginate entries
    paginator = Paginator(entries, 100)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'schedule': schedule,
        'entries': page_obj,
        'filter_form': DepreciationEntryFilterForm(request.GET),
        'total_depreciation': total_depreciation,
        'average_depreciation': average_depreciation,
    }
    return render(request, 'depreciation_schedule/depreciation_entries.html', context)


@login_required
def export_depreciation(request, pk):
    """Export depreciation schedule"""
    schedule = get_object_or_404(DepreciationSchedule, pk=pk)
    
    if request.method == 'POST':
        form = DepreciationExportForm(request.POST)
        if form.is_valid():
            export_format = form.cleaned_data['export_format']
            include_details = form.cleaned_data['include_details']
            include_summary = form.cleaned_data['include_summary']
            include_charts = form.cleaned_data['include_charts']
            
            # Generate export (placeholder for now)
            if export_format == 'pdf':
                return generate_pdf_export(request, schedule, include_details, include_summary, include_charts)
            elif export_format == 'excel':
                return generate_excel_export(request, schedule, include_details, include_summary)
            elif export_format == 'csv':
                return generate_csv_export(request, schedule, include_details, include_summary)
    else:
        form = DepreciationExportForm()
    
    context = {
        'schedule': schedule,
        'form': form,
    }
    return render(request, 'depreciation_schedule/export_depreciation.html', context)


def generate_pdf_export(request, schedule, include_details, include_summary, include_charts):
    """Generate PDF export (placeholder)"""
    # This would typically use a library like ReportLab or WeasyPrint
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="depreciation_schedule_{schedule.schedule_number}.pdf"'
    
    # Placeholder content
    response.write(b'PDF export functionality would be implemented here')
    return response


def generate_excel_export(request, schedule, include_details, include_summary):
    """Generate Excel export (placeholder)"""
    # This would typically use a library like openpyxl or xlsxwriter
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="depreciation_schedule_{schedule.schedule_number}.xlsx"'
    
    # Placeholder content
    response.write(b'Excel export functionality would be implemented here')
    return response


def generate_csv_export(request, schedule, include_details, include_summary):
    """Generate CSV export (placeholder)"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="depreciation_schedule_{schedule.schedule_number}.csv"'
    
    # Placeholder content
    response.write('Period,Asset Code,Asset Name,Opening Value,Depreciation Amount,Accumulated Depreciation,Closing Value\n')
    return response


@login_required
def depreciation_settings(request):
    """Settings for depreciation module"""
    settings = DepreciationSettings.get_settings()
    
    if request.method == 'POST':
        form = DepreciationSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.instance.updated_by = request.user
            form.save()
            messages.success(request, 'Depreciation settings updated successfully.')
            return redirect('depreciation_schedule:settings')
    else:
        form = DepreciationSettingsForm(instance=settings)
    
    context = {
        'form': form,
        'settings': settings,
    }
    return render(request, 'depreciation_schedule/settings.html', context)


@login_required
def asset_depreciation_calculator(request):
    """Asset depreciation calculator"""
    if request.method == 'POST':
        form = AssetDepreciationForm(request.POST)
        if form.is_valid():
            assets = form.cleaned_data['assets']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            
            # Calculate depreciation for selected assets
            results = []
            for asset in assets:
                depreciation_amount = calculate_asset_depreciation_amount(asset, start_date, end_date)
                results.append({
                    'asset': asset,
                    'depreciation_amount': depreciation_amount,
                })
            
            context = {
                'form': form,
                'results': results,
                'start_date': start_date,
                'end_date': end_date,
            }
            return render(request, 'depreciation_schedule/asset_calculator.html', context)
    else:
        form = AssetDepreciationForm()
    
    context = {
        'form': form,
    }
    return render(request, 'depreciation_schedule/asset_calculator.html', context)


def calculate_asset_depreciation_amount(asset, start_date, end_date):
    """Calculate depreciation amount for an asset over a date range"""
    # This is a simplified calculation - in practice, you'd use the same logic as in the model
    if asset.depreciation_method.method == 'straight_line':
        depreciable_amount = asset.purchase_value - asset.salvage_value
        useful_life_months = asset.useful_life_years * 12
        
        if useful_life_months <= 0:
            return Decimal('0.00')
        
        monthly_depreciation = depreciable_amount / useful_life_months
        
        # Calculate number of months in the range
        months_diff = (end_date.year - start_date.year) * 12 + end_date.month - start_date.month
        
        total_depreciation = monthly_depreciation * months_diff
        
        # Ensure we don't exceed the remaining book value
        remaining_value = asset.book_value - asset.salvage_value
        if total_depreciation > remaining_value:
            total_depreciation = remaining_value
        
        return total_depreciation.quantize(Decimal('0.01'))
    else:
        return Decimal('0.00')


@login_required
def depreciation_api(request):
    """API endpoint for depreciation data"""
    if request.method == 'GET':
        action = request.GET.get('action')
        
        if action == 'get_asset_depreciation':
            asset_id = request.GET.get('asset_id')
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            
            try:
                asset = Asset.objects.get(id=asset_id)
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                
                depreciation_amount = calculate_asset_depreciation_amount(asset, start_date, end_date)
                
                return JsonResponse({
                    'success': True,
                    'depreciation_amount': float(depreciation_amount),
                    'asset_code': asset.asset_code,
                    'asset_name': asset.asset_name,
                })
            except (Asset.DoesNotExist, ValueError) as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                })
        
        elif action == 'get_schedule_summary':
            schedule_id = request.GET.get('schedule_id')
            
            try:
                schedule = DepreciationSchedule.objects.get(id=schedule_id)
                entries = schedule.depreciation_entries.all()
                
                summary = {
                    'total_depreciation': float(entries.aggregate(
                        total=Coalesce(Sum('depreciation_amount'), Decimal('0.00'))
                    )['total']),
                    'total_assets': entries.values('asset').distinct().count(),
                    'total_entries': entries.count(),
                }
                
                return JsonResponse({
                    'success': True,
                    'summary': summary
                })
            except DepreciationSchedule.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Schedule not found'
                })
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request'
    })
