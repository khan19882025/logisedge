from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.db import models
from .models import Customer
from .forms import CustomerForm, CustomerSearchForm

@login_required
def customer_list(request):
    """Display list of customers with search and pagination"""
    search_form = CustomerSearchForm(request.GET)
    customers = Customer.objects.all()
    
    # Apply search filters
    if search_form.is_valid():
        search = search_form.cleaned_data.get('search')
        customer_type = search_form.cleaned_data.get('customer_type')
        is_active = search_form.cleaned_data.get('is_active')
        
        if search:
            customers = customers.filter(
                Q(customer_code__icontains=search) |
                Q(customer_name__icontains=search) |
                Q(contact_person__icontains=search) |
                Q(email__icontains=search)
            )
        
        if customer_type:
            customers = customers.filter(customer_types=customer_type)
        
        if is_active:
            customers = customers.filter(is_active=(is_active == 'True'))
    
    # Pagination
    paginator = Paginator(customers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_customers': customers.count(),
    }
    return render(request, 'customer/customer_list.html', context)

@login_required
def customer_create(request):
    """Create a new customer"""
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.created_by = request.user
            customer.customer_code = None  # Ensure it's None initially
            
            # Save the customer first
            customer.save()
            
            # Now set the many-to-many relationships
            form.save_m2m()
            
            # Generate customer code after M2M relationships are saved
            if not customer.customer_code:
                customer.customer_code = customer.generate_customer_code()
                customer.save(update_fields=['customer_code'])
            
            messages.success(request, f'Customer "{customer.customer_name}" created successfully.')
            return redirect('customer:customer_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomerForm()
    
    context = {
        'form': form,
        'title': 'Create Customer',
        'action': 'Create',
    }
    return render(request, 'customer/customer_form.html', context)

@login_required
def customer_update(request, pk):
    """Update an existing customer"""
    customer = get_object_or_404(Customer, pk=pk)
    
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.updated_by = request.user
            
            # Save the customer first
            customer.save()
            
            # Now set the many-to-many relationships
            form.save_m2m()
            
            # Generate customer code if it doesn't exist
            if not customer.customer_code:
                customer.customer_code = customer.generate_customer_code()
                customer.save()
            
            messages.success(request, f'Customer "{customer.customer_name}" updated successfully.')
            return redirect('customer:customer_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomerForm(instance=customer)
    
    context = {
        'form': form,
        'customer': customer,
        'title': 'Update Customer',
        'action': 'Update',
    }
    return render(request, 'customer/customer_form.html', context)

@login_required
def customer_detail(request, pk):
    """Display customer details"""
    customer = get_object_or_404(Customer, pk=pk)
    
    context = {
        'customer': customer,
    }
    return render(request, 'customer/customer_detail.html', context)

@login_required
def customer_delete(request, pk):
    """Delete a customer"""
    customer = get_object_or_404(Customer, pk=pk)
    
    if request.method == 'POST':
        try:
            customer_name = customer.customer_name
            customer.delete()
            messages.success(request, f'Customer "{customer_name}" deleted successfully.')
            return redirect('customer:customer_list')
        except models.ProtectedError as e:
            # Handle case where customer cannot be deleted due to related records
            protected_objects = []
            for obj in e.protected_objects:
                if hasattr(obj, 'job_code'):
                    protected_objects.append(f"Job: {obj.job_code}")
                elif hasattr(obj, 'quotation_number'):
                    protected_objects.append(f"Quotation: {obj.quotation_number}")
                elif hasattr(obj, 'grn_number'):
                    protected_objects.append(f"GRN: {obj.grn_number}")
                elif hasattr(obj, 'documentation_number'):
                    protected_objects.append(f"Documentation: {obj.documentation_number}")
                elif hasattr(obj, 'delivery_order_number'):
                    protected_objects.append(f"Delivery Order: {obj.delivery_order_number}")
                elif hasattr(obj, 'cs_number'):
                    protected_objects.append(f"Crossstuffing: {obj.cs_number}")
                else:
                    protected_objects.append(f"{obj._meta.verbose_name}: {obj}")
            
            error_message = f'Cannot delete customer "{customer_name}" because it is referenced by the following records: {", ".join(protected_objects)}. Please delete or update these records first.'
            messages.error(request, error_message)
            return redirect('customer:customer_detail', pk=pk)
        except Exception as e:
            messages.error(request, f'An error occurred while deleting the customer: {str(e)}')
            return redirect('customer:customer_detail', pk=pk)
    
    context = {
        'customer': customer,
    }
    return render(request, 'customer/customer_confirm_delete.html', context)

@login_required
@require_POST
def generate_portal_credentials(request, pk):
    """Generate portal username and password for customer"""
    customer = get_object_or_404(Customer, pk=pk)
    
    import secrets
    import string
    
    # Generate username based on customer code
    username = f"cust_{customer.customer_code.lower()}"
    
    # Generate random password
    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for i in range(12))
    
    customer.portal_username = username
    customer.portal_password = password
    customer.portal_active = True
    customer.save()
    
    return JsonResponse({
        'success': True,
        'username': username,
        'password': password,
        'message': 'Portal credentials generated successfully.'
    })

@login_required
@require_POST
def toggle_portal_status(request, pk):
    """Toggle customer portal active status"""
    customer = get_object_or_404(Customer, pk=pk)
    customer.portal_active = not customer.portal_active
    customer.save()
    
    return JsonResponse({
        'success': True,
        'portal_active': customer.portal_active,
        'message': f'Portal {"activated" if customer.portal_active else "deactivated"} successfully.'
    })

@login_required
def get_customer_address(request, pk):
    """API endpoint to get customer address for dropdowns"""
    customer = get_object_or_404(Customer, pk=pk)
    
    # Get the best available address (shipping address preferred, fallback to billing)
    address = customer.shipping_address or customer.billing_address or ''
    
    return JsonResponse({
        'success': True,
        'address': address,
        'customer_name': customer.customer_name
    })
