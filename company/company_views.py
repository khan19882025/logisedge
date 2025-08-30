from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db import models
from company.company_model import Company
from company.company_form import CompanyForm

@login_required
def company_list(request):
    """Display list of companies with search and pagination"""
    companies = Company.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        companies = companies.filter(
            models.Q(name__icontains=search_query) |
            models.Q(code__icontains=search_query) |
            models.Q(email__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(companies, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'company/company_list.html', context)

@login_required
def company_create(request):
    """Create a new company"""
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Company created successfully!')
            return redirect('company:company_list')
    else:
        form = CompanyForm()
    
    context = {
        'form': form,
        'title': 'Create Company',
        'action': 'Create'
    }
    return render(request, 'company/company_form.html', context)

@login_required
def company_edit(request, pk):
    """Edit an existing company"""
    company = get_object_or_404(Company, pk=pk)
    
    if request.method == 'POST':
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, 'Company updated successfully!')
            return redirect('company:company_list')
    else:
        form = CompanyForm(instance=company)
    
    context = {
        'form': form,
        'company': company,
        'title': 'Edit Company',
        'action': 'Update'
    }
    return render(request, 'company/company_form.html', context)

@login_required
def company_delete(request, pk):
    """Delete a company"""
    company = get_object_or_404(Company, pk=pk)
    
    if request.method == 'POST':
        company.delete()
        messages.success(request, 'Company deleted successfully!')
        return redirect('company:company_list')
    
    context = {
        'company': company
    }
    return render(request, 'company/company_confirm_delete.html', context)

@login_required
def company_detail(request, pk):
    """Display company details"""
    company = get_object_or_404(Company, pk=pk)
    
    context = {
        'company': company
    }
    return render(request, 'company/company_detail.html', context) 