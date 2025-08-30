from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import date
from .models import Currency, ExchangeRate, CurrencySettings
from .forms import (
    CurrencyForm, ExchangeRateForm, CurrencySettingsForm,
    CurrencySearchForm, ExchangeRateSearchForm
)


@login_required
def currency_dashboard(request):
    """Dashboard view for multi-currency management"""
    context = {
        'total_currencies': Currency.objects.count(),
        'active_currencies': Currency.objects.filter(is_active=True).count(),
        'base_currency': Currency.objects.filter(is_base_currency=True).first(),
        'total_exchange_rates': ExchangeRate.objects.count(),
        'active_exchange_rates': ExchangeRate.objects.filter(is_active=True).count(),
        'recent_currencies': Currency.objects.order_by('-created_at')[:5],
        'recent_exchange_rates': ExchangeRate.objects.order_by('-created_at')[:5],
        'settings': CurrencySettings.objects.first(),
    }
    return render(request, 'multi_currency/dashboard.html', context)


@login_required
def currency_list(request):
    """List view for currencies"""
    search_form = CurrencySearchForm(request.GET)
    currencies = Currency.objects.all()
    
    if search_form.is_valid():
        search = search_form.cleaned_data.get('search')
        status = search_form.cleaned_data.get('status')
        is_base_currency = search_form.cleaned_data.get('is_base_currency')
        
        if search:
            currencies = currencies.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(symbol__icontains=search)
            )
        
        if status:
            if status == 'active':
                currencies = currencies.filter(is_active=True)
            elif status == 'inactive':
                currencies = currencies.filter(is_active=False)
        
        if is_base_currency:
            currencies = currencies.filter(is_base_currency=True)
    
    # Pagination
    paginator = Paginator(currencies, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_currencies': currencies.count(),
    }
    return render(request, 'multi_currency/currency_list.html', context)


@login_required
def currency_create(request):
    """Create new currency"""
    if request.method == 'POST':
        form = CurrencyForm(request.POST)
        if form.is_valid():
            currency = form.save()
            messages.success(request, f'Currency "{currency.code}" created successfully.')
            return redirect('multi_currency:currency_list')
    else:
        form = CurrencyForm()
    
    context = {
        'form': form,
        'title': 'Add New Currency',
        'submit_text': 'Create Currency',
    }
    return render(request, 'multi_currency/currency_form.html', context)


@login_required
def currency_update(request, pk):
    """Update existing currency"""
    currency = get_object_or_404(Currency, pk=pk)
    
    if request.method == 'POST':
        form = CurrencyForm(request.POST, instance=currency)
        if form.is_valid():
            currency = form.save()
            messages.success(request, f'Currency "{currency.code}" updated successfully.')
            return redirect('multi_currency:currency_list')
    else:
        form = CurrencyForm(instance=currency)
    
    context = {
        'form': form,
        'currency': currency,
        'title': f'Edit Currency: {currency.code}',
        'submit_text': 'Update Currency',
    }
    return render(request, 'multi_currency/currency_form.html', context)


@login_required
def currency_detail(request, pk):
    """Detail view for currency"""
    currency = get_object_or_404(Currency, pk=pk)
    exchange_rates = ExchangeRate.objects.filter(
        Q(from_currency=currency) | Q(to_currency=currency)
    ).order_by('-effective_date')[:10]
    
    context = {
        'currency': currency,
        'exchange_rates': exchange_rates,
    }
    return render(request, 'multi_currency/currency_detail.html', context)


@login_required
def currency_delete(request, pk):
    """Delete currency"""
    currency = get_object_or_404(Currency, pk=pk)
    
    if request.method == 'POST':
        currency_name = currency.code
        currency.delete()
        messages.success(request, f'Currency "{currency_name}" deleted successfully.')
        return redirect('multi_currency:currency_list')
    
    context = {
        'currency': currency,
    }
    return render(request, 'multi_currency/currency_confirm_delete.html', context)


@login_required
def exchange_rate_list(request):
    """List view for exchange rates"""
    search_form = ExchangeRateSearchForm(request.GET)
    exchange_rates = ExchangeRate.objects.all()
    
    if search_form.is_valid():
        from_currency = search_form.cleaned_data.get('from_currency')
        to_currency = search_form.cleaned_data.get('to_currency')
        rate_type = search_form.cleaned_data.get('rate_type')
        effective_date_from = search_form.cleaned_data.get('effective_date_from')
        effective_date_to = search_form.cleaned_data.get('effective_date_to')
        is_active = search_form.cleaned_data.get('is_active')
        
        if from_currency:
            exchange_rates = exchange_rates.filter(from_currency=from_currency)
        
        if to_currency:
            exchange_rates = exchange_rates.filter(to_currency=to_currency)
        
        if rate_type:
            exchange_rates = exchange_rates.filter(rate_type=rate_type)
        
        if effective_date_from:
            exchange_rates = exchange_rates.filter(effective_date__gte=effective_date_from)
        
        if effective_date_to:
            exchange_rates = exchange_rates.filter(effective_date__lte=effective_date_to)
        
        if is_active:
            exchange_rates = exchange_rates.filter(is_active=True)
    
    # Pagination
    paginator = Paginator(exchange_rates, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_rates': exchange_rates.count(),
    }
    return render(request, 'multi_currency/exchange_rate_list.html', context)


@login_required
def exchange_rate_create(request):
    """Create new exchange rate"""
    if request.method == 'POST':
        form = ExchangeRateForm(request.POST)
        if form.is_valid():
            exchange_rate = form.save()
            messages.success(request, f'Exchange rate created successfully.')
            return redirect('multi_currency:exchange_rate_list')
    else:
        form = ExchangeRateForm()
        # Set default effective date to today
        form.fields['effective_date'].initial = date.today()
    
    context = {
        'form': form,
        'title': 'Add New Exchange Rate',
        'submit_text': 'Create Exchange Rate',
    }
    return render(request, 'multi_currency/exchange_rate_form.html', context)


@login_required
def exchange_rate_update(request, pk):
    """Update existing exchange rate"""
    exchange_rate = get_object_or_404(ExchangeRate, pk=pk)
    
    if request.method == 'POST':
        form = ExchangeRateForm(request.POST, instance=exchange_rate)
        if form.is_valid():
            exchange_rate = form.save()
            messages.success(request, 'Exchange rate updated successfully.')
            return redirect('multi_currency:exchange_rate_list')
    else:
        form = ExchangeRateForm(instance=exchange_rate)
    
    context = {
        'form': form,
        'exchange_rate': exchange_rate,
        'title': 'Edit Exchange Rate',
        'submit_text': 'Update Exchange Rate',
    }
    return render(request, 'multi_currency/exchange_rate_form.html', context)


@login_required
def exchange_rate_detail(request, pk):
    """Detail view for exchange rate"""
    exchange_rate = get_object_or_404(ExchangeRate, pk=pk)
    
    context = {
        'exchange_rate': exchange_rate,
    }
    return render(request, 'multi_currency/exchange_rate_detail.html', context)


@login_required
def exchange_rate_delete(request, pk):
    """Delete exchange rate"""
    exchange_rate = get_object_or_404(ExchangeRate, pk=pk)
    
    if request.method == 'POST':
        exchange_rate.delete()
        messages.success(request, 'Exchange rate deleted successfully.')
        return redirect('multi_currency:exchange_rate_list')
    
    context = {
        'exchange_rate': exchange_rate,
    }
    return render(request, 'multi_currency/exchange_rate_confirm_delete.html', context)


@login_required
def currency_settings(request):
    """Currency settings view"""
    settings, created = CurrencySettings.objects.get_or_create()
    
    if request.method == 'POST':
        form = CurrencySettingsForm(request.POST, instance=settings)
        if form.is_valid():
            settings = form.save()
            messages.success(request, 'Currency settings updated successfully.')
            return redirect('multi_currency:currency_settings')
    else:
        form = CurrencySettingsForm(instance=settings)
    
    context = {
        'form': form,
        'settings': settings,
    }
    return render(request, 'multi_currency/currency_settings.html', context)


@login_required
@require_http_methods(["POST"])
def toggle_currency_status(request, pk):
    """Toggle currency active status via AJAX"""
    try:
        currency = get_object_or_404(Currency, pk=pk)
        currency.is_active = not currency.is_active
        currency.save()
        
        return JsonResponse({
            'success': True,
            'is_active': currency.is_active,
            'message': f'Currency "{currency.code}" {"activated" if currency.is_active else "deactivated"} successfully.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def toggle_exchange_rate_status(request, pk):
    """Toggle exchange rate active status via AJAX"""
    try:
        exchange_rate = get_object_or_404(ExchangeRate, pk=pk)
        exchange_rate.is_active = not exchange_rate.is_active
        exchange_rate.save()
        
        return JsonResponse({
            'success': True,
            'is_active': exchange_rate.is_active,
            'message': 'Exchange rate status updated successfully.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400) 