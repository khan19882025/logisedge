from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from .models import Service
from .forms import ServiceForm, ServiceSearchForm

# Create your views here.

@login_required
def service_list(request):
    """Display list of services with search and pagination"""
    search_form = ServiceSearchForm(request.GET)
    services = Service.objects.all()
    
    # Apply search filters
    if search_form.is_valid():
        search = search_form.cleaned_data.get('search')
        service_type = search_form.cleaned_data.get('service_type')
        status = search_form.cleaned_data.get('status')
        is_featured = search_form.cleaned_data.get('is_featured')
        
        if search:
            services = services.filter(
                Q(service_code__icontains=search) |
                Q(service_name__icontains=search) |
                Q(description__icontains=search) |
                Q(short_description__icontains=search)
            )
        
        if service_type:
            services = services.filter(service_type=service_type)
        
        if status:
            services = services.filter(status=status)
        
        if is_featured:
            services = services.filter(is_featured=(is_featured == 'True'))
    
    # Pagination
    paginator = Paginator(services, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_services': services.count(),
    }
    return render(request, 'service/service_list.html', context)

@login_required
def service_create(request):
    """Create a new service"""
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.created_by = request.user
            service.save()
            messages.success(request, f'Service "{service.service_name}" created successfully.')
            return redirect('service:service_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ServiceForm()
    
    context = {
        'form': form,
        'title': 'Create Service',
        'action': 'Create',
    }
    return render(request, 'service/service_form.html', context)

@login_required
def service_update(request, pk):
    """Update an existing service"""
    service = get_object_or_404(Service, pk=pk)
    
    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            service = form.save(commit=False)
            service.updated_by = request.user
            service.save()
            messages.success(request, f'Service "{service.service_name}" updated successfully.')
            return redirect('service:service_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ServiceForm(instance=service)
    
    context = {
        'form': form,
        'service': service,
        'title': 'Update Service',
        'action': 'Update',
    }
    return render(request, 'service/service_form.html', context)

@login_required
def service_detail(request, pk):
    """Display service details"""
    service = get_object_or_404(Service, pk=pk)
    
    context = {
        'service': service,
    }
    return render(request, 'service/service_detail.html', context)

@login_required
def service_delete(request, pk):
    """Delete a service"""
    service = get_object_or_404(Service, pk=pk)
    
    if request.method == 'POST':
        service_name = service.service_name
        service.delete()
        messages.success(request, f'Service "{service_name}" deleted successfully.')
        return redirect('service:service_list')
    
    context = {
        'service': service,
    }
    return render(request, 'service/service_confirm_delete.html', context)

@login_required
def service_price_ajax(request, pk):
    """Return service price data via AJAX"""
    try:
        service = get_object_or_404(Service, pk=pk)
        return JsonResponse({
            'success': True,
            'sale_price': str(service.sale_price),
            'base_price': str(service.base_price),
            'cost_price': str(service.cost_price),
            'currency': service.currency,
            'has_vat': service.has_vat,
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
