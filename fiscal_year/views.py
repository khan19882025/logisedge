from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import FiscalYear, FiscalPeriod, FiscalSettings
from .forms import (
    FiscalYearForm, FiscalPeriodForm, FiscalSettingsForm,
    FiscalYearSearchForm, FiscalPeriodSearchForm
)


@login_required
def dashboard(request):
    """Fiscal Year Settings Dashboard"""
    context = {
        'title': 'Fiscal Year Settings',
        'current_fiscal_year': FiscalYear.objects.filter(is_current=True).first(),
        'total_fiscal_years': FiscalYear.objects.count(),
        'total_periods': FiscalPeriod.objects.count(),
        'active_periods': FiscalPeriod.objects.filter(status='open').count(),
        'closed_periods': FiscalPeriod.objects.filter(status='closed').count(),
        'recent_fiscal_years': FiscalYear.objects.order_by('-created_at')[:5],
        'recent_periods': FiscalPeriod.objects.order_by('-created_at')[:5],
    }
    return render(request, 'fiscal_year/dashboard.html', context)


@login_required
def fiscal_year_list(request):
    """List all fiscal years"""
    search_form = FiscalYearSearchForm(request.GET)
    fiscal_years = FiscalYear.objects.all()
    
    if search_form.is_valid():
        search = search_form.cleaned_data.get('search')
        status = search_form.cleaned_data.get('status')
        is_current = search_form.cleaned_data.get('is_current')
        start_date_from = search_form.cleaned_data.get('start_date_from')
        start_date_to = search_form.cleaned_data.get('start_date_to')
        
        if search:
            fiscal_years = fiscal_years.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        
        if status:
            fiscal_years = fiscal_years.filter(status=status)
        
        if is_current:
            fiscal_years = fiscal_years.filter(is_current=True)
        
        if start_date_from:
            fiscal_years = fiscal_years.filter(start_date__gte=start_date_from)
        
        if start_date_to:
            fiscal_years = fiscal_years.filter(start_date__lte=start_date_to)
    
    # Pagination
    paginator = Paginator(fiscal_years, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'title': 'Fiscal Years',
        'page_obj': page_obj,
        'search_form': search_form,
        'total_fiscal_years': fiscal_years.count(),
    }
    return render(request, 'fiscal_year/fiscal_year_list.html', context)


@login_required
def fiscal_year_create(request):
    """Create a new fiscal year"""
    if request.method == 'POST':
        form = FiscalYearForm(request.POST)
        if form.is_valid():
            fiscal_year = form.save()
            messages.success(request, f'Fiscal year "{fiscal_year.name}" created successfully.')
            return redirect('fiscal_year:fiscal_year_detail', pk=fiscal_year.pk)
    else:
        form = FiscalYearForm()
    
    context = {
        'title': 'Create Fiscal Year',
        'form': form,
        'submit_text': 'Create Fiscal Year',
    }
    return render(request, 'fiscal_year/fiscal_year_form.html', context)


@login_required
def fiscal_year_detail(request, pk):
    """View fiscal year details"""
    fiscal_year = get_object_or_404(FiscalYear, pk=pk)
    periods = fiscal_year.periods.all()
    
    context = {
        'title': f'Fiscal Year: {fiscal_year.name}',
        'fiscal_year': fiscal_year,
        'periods': periods,
    }
    return render(request, 'fiscal_year/fiscal_year_detail.html', context)


@login_required
def fiscal_year_update(request, pk):
    """Update fiscal year"""
    fiscal_year = get_object_or_404(FiscalYear, pk=pk)
    
    if request.method == 'POST':
        form = FiscalYearForm(request.POST, instance=fiscal_year)
        if form.is_valid():
            form.save()
            messages.success(request, f'Fiscal year "{fiscal_year.name}" updated successfully.')
            return redirect('fiscal_year:fiscal_year_detail', pk=fiscal_year.pk)
    else:
        form = FiscalYearForm(instance=fiscal_year)
    
    context = {
        'title': f'Edit Fiscal Year: {fiscal_year.name}',
        'form': form,
        'fiscal_year': fiscal_year,
        'submit_text': 'Update Fiscal Year',
    }
    return render(request, 'fiscal_year/fiscal_year_form.html', context)


@login_required
def fiscal_year_delete(request, pk):
    """Delete fiscal year"""
    fiscal_year = get_object_or_404(FiscalYear, pk=pk)
    
    if request.method == 'POST':
        name = fiscal_year.name
        fiscal_year.delete()
        messages.success(request, f'Fiscal year "{name}" deleted successfully.')
        return redirect('fiscal_year:fiscal_year_list')
    
    context = {
        'title': f'Delete Fiscal Year: {fiscal_year.name}',
        'fiscal_year': fiscal_year,
    }
    return render(request, 'fiscal_year/fiscal_year_confirm_delete.html', context)


@login_required
def fiscal_period_list(request):
    """List all fiscal periods"""
    search_form = FiscalPeriodSearchForm(request.GET)
    periods = FiscalPeriod.objects.select_related('fiscal_year').all()
    
    if search_form.is_valid():
        search = search_form.cleaned_data.get('search')
        fiscal_year = search_form.cleaned_data.get('fiscal_year')
        period_type = search_form.cleaned_data.get('period_type')
        status = search_form.cleaned_data.get('status')
        is_current = search_form.cleaned_data.get('is_current')
        
        if search:
            periods = periods.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        
        if fiscal_year:
            periods = periods.filter(fiscal_year=fiscal_year)
        
        if period_type:
            periods = periods.filter(period_type=period_type)
        
        if status:
            periods = periods.filter(status=status)
        
        if is_current:
            periods = periods.filter(is_current=True)
    
    # Pagination
    paginator = Paginator(periods, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'title': 'Fiscal Periods',
        'page_obj': page_obj,
        'search_form': search_form,
        'total_periods': periods.count(),
    }
    return render(request, 'fiscal_year/fiscal_period_list.html', context)


@login_required
def fiscal_period_create(request):
    """Create a new fiscal period"""
    if request.method == 'POST':
        form = FiscalPeriodForm(request.POST)
        if form.is_valid():
            period = form.save()
            messages.success(request, f'Fiscal period "{period.name}" created successfully.')
            return redirect('fiscal_year:fiscal_period_detail', pk=period.pk)
    else:
        form = FiscalPeriodForm()
    
    context = {
        'title': 'Create Fiscal Period',
        'form': form,
        'submit_text': 'Create Fiscal Period',
    }
    return render(request, 'fiscal_year/fiscal_period_form.html', context)


@login_required
def fiscal_period_detail(request, pk):
    """View fiscal period details"""
    period = get_object_or_404(FiscalPeriod, pk=pk)
    
    context = {
        'title': f'Fiscal Period: {period.name}',
        'period': period,
    }
    return render(request, 'fiscal_year/fiscal_period_detail.html', context)


@login_required
def fiscal_period_update(request, pk):
    """Update fiscal period"""
    period = get_object_or_404(FiscalPeriod, pk=pk)
    
    if request.method == 'POST':
        form = FiscalPeriodForm(request.POST, instance=period)
        if form.is_valid():
            form.save()
            messages.success(request, f'Fiscal period "{period.name}" updated successfully.')
            return redirect('fiscal_year:fiscal_period_detail', pk=period.pk)
    else:
        form = FiscalPeriodForm(instance=period)
    
    context = {
        'title': f'Edit Fiscal Period: {period.name}',
        'form': form,
        'period': period,
        'submit_text': 'Update Fiscal Period',
    }
    return render(request, 'fiscal_year/fiscal_period_form.html', context)


@login_required
def fiscal_period_delete(request, pk):
    """Delete fiscal period"""
    period = get_object_or_404(FiscalPeriod, pk=pk)
    
    if request.method == 'POST':
        name = period.name
        period.delete()
        messages.success(request, f'Fiscal period "{name}" deleted successfully.')
        return redirect('fiscal_year:fiscal_period_list')
    
    context = {
        'title': f'Delete Fiscal Period: {period.name}',
        'period': period,
    }
    return render(request, 'fiscal_year/fiscal_period_confirm_delete.html', context)


@login_required
def settings_view(request):
    """View and edit fiscal year settings"""
    settings = FiscalSettings.get_settings()
    
    if request.method == 'POST':
        form = FiscalSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fiscal year settings updated successfully.')
            return redirect('fiscal_year:settings')
    else:
        form = FiscalSettingsForm(instance=settings)
    
    context = {
        'title': 'Fiscal Year Settings',
        'form': form,
        'settings': settings,
    }
    return render(request, 'fiscal_year/settings.html', context)


@login_required
@require_POST
def toggle_fiscal_year_status(request, pk):
    """Toggle fiscal year current status"""
    fiscal_year = get_object_or_404(FiscalYear, pk=pk)
    fiscal_year.is_current = not fiscal_year.is_current
    fiscal_year.save()
    
    return JsonResponse({
        'success': True,
        'is_current': fiscal_year.is_current,
        'message': f'Fiscal year "{fiscal_year.name}" {"set as current" if fiscal_year.is_current else "unset as current"}'
    })


@login_required
@require_POST
def toggle_period_status(request, pk):
    """Toggle fiscal period current status"""
    period = get_object_or_404(FiscalPeriod, pk=pk)
    period.is_current = not period.is_current
    period.save()
    
    return JsonResponse({
        'success': True,
        'is_current': period.is_current,
        'message': f'Period "{period.name}" {"set as current" if period.is_current else "unset as current"}'
    })
