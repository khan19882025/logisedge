from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Item
from .forms import ItemForm, ItemSearchForm


@login_required
def item_list(request):
    """Display list of items with search and filtering"""
    items = Item.objects.all()
    search_form = ItemSearchForm(request.GET)
    
    if search_form.is_valid():
        search_term = search_form.cleaned_data.get('search_term')
        search_field = search_form.cleaned_data.get('search_field')
        item_category = search_form.cleaned_data.get('item_category')
        status = search_form.cleaned_data.get('status')
        min_price = search_form.cleaned_data.get('min_price')
        max_price = search_form.cleaned_data.get('max_price')
        
        # Apply search filters
        if search_term:
            if search_field == 'all':
                items = items.filter(
                    Q(item_code__icontains=search_term) |
                    Q(item_name__icontains=search_term) |
                    Q(brand__icontains=search_term) |
                    Q(supplier__icontains=search_term) |
                    Q(barcode__icontains=search_term) |
                    Q(description__icontains=search_term)
                )
            elif search_field == 'item_code':
                items = items.filter(item_code__icontains=search_term)
            elif search_field == 'item_name':
                items = items.filter(item_name__icontains=search_term)
            elif search_field == 'brand':
                items = items.filter(brand__icontains=search_term)
            elif search_field == 'supplier':
                items = items.filter(supplier__icontains=search_term)
            elif search_field == 'barcode':
                items = items.filter(barcode__icontains=search_term)
        
        # Apply filters
        if item_category:
            items = items.filter(item_category=item_category)
        
        if status:
            items = items.filter(status=status)
        
        if min_price is not None:
            items = items.filter(selling_price__gte=min_price)
        
        if max_price is not None:
            items = items.filter(selling_price__lte=max_price)
    
    # Pagination
    paginator = Paginator(items, 20)  # Show 20 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_items': items.count(),
        'active_items': items.filter(status='active').count(),
        'inactive_items': items.filter(status='inactive').count(),
    }
    
    return render(request, 'items/item_list.html', context)


@login_required
def item_create(request):
    """Create a new item"""
    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.created_by = request.user
            item.updated_by = request.user
            item.save()
            messages.success(request, f'Item "{item.item_name}" created successfully.')
            return redirect('items:item_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ItemForm()
    
    context = {
        'form': form,
        'title': 'Create New Item',
        'submit_text': 'Create Item'
    }
    
    return render(request, 'items/item_form.html', context)


@login_required
def item_update(request, pk):
    """Update an existing item"""
    item = get_object_or_404(Item, pk=pk)
    
    if request.method == 'POST':
        form = ItemForm(request.POST, instance=item)
        if form.is_valid():
            item = form.save(commit=False)
            item.updated_by = request.user
            item.save()
            messages.success(request, f'Item "{item.item_name}" updated successfully.')
            return redirect('items:item_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ItemForm(instance=item)
    
    context = {
        'form': form,
        'item': item,
        'title': f'Edit Item: {item.item_name}',
        'submit_text': 'Update Item'
    }
    
    return render(request, 'items/item_form.html', context)


@login_required
def item_detail(request, pk):
    """Display item details"""
    item = get_object_or_404(Item, pk=pk)
    
    context = {
        'item': item,
        'specifications': item.get_full_specifications(),
    }
    
    return render(request, 'items/item_detail.html', context)


@login_required
def item_delete(request, pk):
    """Delete an item"""
    item = get_object_or_404(Item, pk=pk)
    
    if request.method == 'POST':
        item_name = item.item_name
        item.delete()
        messages.success(request, f'Item "{item_name}" deleted successfully.')
        return redirect('items:item_list')
    
    context = {
        'item': item
    }
    
    return render(request, 'items/item_confirm_delete.html', context)


@login_required
def item_quick_view(request, pk):
    """Quick view modal for item details"""
    item = get_object_or_404(Item, pk=pk)
    
    context = {
        'item': item,
        'specifications': item.get_full_specifications(),
    }
    
    return render(request, 'items/item_quick_view.html', context)


@csrf_exempt
@require_POST
def item_status_toggle(request, pk):
    """Toggle item status via AJAX"""
    try:
        item = get_object_or_404(Item, pk=pk)
        if item.status == 'active':
            item.status = 'inactive'
        else:
            item.status = 'active'
        item.save()
        
        return JsonResponse({
            'success': True,
            'status': item.status,
            'message': f'Item status changed to {item.status}'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
def item_export(request):
    """Export items to CSV"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="items_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Item Code', 'Item Name', 'Category', 'Status', 'Brand', 'Model',
        'Unit', 'Cost Price', 'Selling Price', 'Currency', 'Supplier',
        'Barcode', 'Created Date'
    ])
    
    items = Item.objects.all()
    for item in items:
        writer.writerow([
            item.item_code, item.item_name, item.get_item_category_display(), item.status,
            item.brand, item.model, item.unit_of_measure, item.cost_price,
            item.selling_price, item.currency, item.supplier, item.barcode,
            item.created_at.strftime('%Y-%m-%d')
        ])
    
    return response


# Class-based views for additional functionality
class ItemListView(LoginRequiredMixin, ListView):
    """Class-based view for item list"""
    model = Item
    template_name = 'items/item_list.html'
    context_object_name = 'items'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search_form = ItemSearchForm(self.request.GET)
        
        if search_form.is_valid():
            search_term = search_form.cleaned_data.get('search_term')
            if search_term:
                queryset = queryset.filter(
                    Q(item_code__icontains=search_term) |
                    Q(item_name__icontains=search_term) |
                    Q(brand__icontains=search_term)
                )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ItemSearchForm(self.request.GET)
        return context


class ItemDetailView(LoginRequiredMixin, DetailView):
    """Class-based view for item detail"""
    model = Item
    template_name = 'items/item_detail.html'
    context_object_name = 'item'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['specifications'] = self.object.get_full_specifications()
        return context


class ItemCreateView(LoginRequiredMixin, CreateView):
    """Class-based view for item creation"""
    model = Item
    form_class = ItemForm
    template_name = 'items/item_form.html'
    success_url = reverse_lazy('items:item_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, f'Item "{form.instance.item_name}" created successfully.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New Item'
        context['submit_text'] = 'Create Item'
        return context


class ItemUpdateView(LoginRequiredMixin, UpdateView):
    """Class-based view for item update"""
    model = Item
    form_class = ItemForm
    template_name = 'items/item_form.html'
    success_url = reverse_lazy('items:item_list')
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, f'Item "{form.instance.item_name}" updated successfully.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit Item: {self.object.item_name}'
        context['submit_text'] = 'Update Item'
        return context


class ItemDeleteView(LoginRequiredMixin, DeleteView):
    """Class-based view for item deletion"""
    model = Item
    template_name = 'items/item_confirm_delete.html'
    success_url = reverse_lazy('items:item_list')
    
    def delete(self, request, *args, **kwargs):
        item_name = self.get_object().item_name
        messages.success(request, f'Item "{item_name}" deleted successfully.')
        return super().delete(request, *args, **kwargs)
