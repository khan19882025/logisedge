from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Salesman
from .forms import SalesmanForm

def salesman_list(request):
    """Display list of all salesmen with search and pagination"""
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    department_filter = request.GET.get('department', '')
    
    salesmen = Salesman.objects.all()
    
    # Apply filters
    if search_query:
        salesmen = salesmen.filter(
            Q(salesman_code__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    if status_filter:
        salesmen = salesmen.filter(status=status_filter)
    
    if department_filter:
        salesmen = salesmen.filter(department__icontains=department_filter)
    
    # Pagination
    paginator = Paginator(salesmen, 10)  # Show 10 salesmen per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'department_filter': department_filter,
        'status_choices': Salesman.STATUS_CHOICES,
    }
    
    return render(request, 'salesman/salesman_list.html', context)

def salesman_create(request):
    """Create a new salesman"""
    if request.method == 'POST':
        form = SalesmanForm(request.POST)
        if form.is_valid():
            salesman = form.save(commit=False)
            salesman.created_by = request.user
            salesman.save()
            messages.success(request, 'Salesman created successfully!')
            return redirect('salesman:salesman_list')
    else:
        form = SalesmanForm()
    
    context = {
        'form': form,
        'title': 'Add New Salesman'
    }
    return render(request, 'salesman/salesman_form.html', context)

def salesman_detail(request, pk):
    """Display salesman details"""
    salesman = get_object_or_404(Salesman, pk=pk)
    
    context = {
        'salesman': salesman
    }
    return render(request, 'salesman/salesman_detail.html', context)

def salesman_update(request, pk):
    """Update an existing salesman"""
    salesman = get_object_or_404(Salesman, pk=pk)
    
    if request.method == 'POST':
        form = SalesmanForm(request.POST, instance=salesman)
        if form.is_valid():
            salesman = form.save(commit=False)
            salesman.updated_by = request.user
            salesman.save()
            messages.success(request, 'Salesman updated successfully!')
            return redirect('salesman:salesman_list')
    else:
        form = SalesmanForm(instance=salesman)
    
    context = {
        'form': form,
        'salesman': salesman,
        'title': 'Edit Salesman'
    }
    return render(request, 'salesman/salesman_form.html', context)

def salesman_delete(request, pk):
    """Delete a salesman"""
    salesman = get_object_or_404(Salesman, pk=pk)
    
    if request.method == 'POST':
        salesman.delete()
        messages.success(request, 'Salesman deleted successfully!')
        return redirect('salesman:salesman_list')
    
    context = {
        'salesman': salesman
    }
    return render(request, 'salesman/salesman_confirm_delete.html', context)
