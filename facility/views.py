from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Facility, FacilityLocation
from .forms import FacilityForm, FacilityLocationForm, FacilitySearchForm, FacilityLocationSearchForm


@login_required
def facility_list(request):
    """Display list of facilities with search and filtering"""
    facilities = Facility.objects.all()
    search_form = FacilitySearchForm(request.GET)
    
    if search_form.is_valid():
        search_term = search_form.cleaned_data.get('search_term')
        search_field = search_form.cleaned_data.get('search_field')
        facility_type = search_form.cleaned_data.get('facility_type')
        status = search_form.cleaned_data.get('status')
        city = search_form.cleaned_data.get('city')
        is_owned = search_form.cleaned_data.get('is_owned')
        
        # Apply search filters
        if search_term:
            if search_field == 'all':
                facilities = facilities.filter(
                    Q(facility_code__icontains=search_term) |
                    Q(facility_name__icontains=search_term) |
                    Q(city__icontains=search_term) |
                    Q(contact_person__icontains=search_term) |
                    Q(description__icontains=search_term)
                )
            elif search_field == 'facility_code':
                facilities = facilities.filter(facility_code__icontains=search_term)
            elif search_field == 'facility_name':
                facilities = facilities.filter(facility_name__icontains=search_term)
            elif search_field == 'city':
                facilities = facilities.filter(city__icontains=search_term)
            elif search_field == 'contact_person':
                facilities = facilities.filter(contact_person__icontains=search_term)
        
        # Apply filters
        if facility_type:
            facilities = facilities.filter(facility_type=facility_type)
        
        if status:
            facilities = facilities.filter(status=status)
        
        if city:
            facilities = facilities.filter(city__icontains=city)
        
        if is_owned:
            facilities = facilities.filter(is_owned=is_owned == 'True')
    
    # Pagination
    paginator = Paginator(facilities, 15)  # Show 15 facilities per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_facilities': facilities.count(),
        'active_facilities': facilities.filter(status='active').count(),
        'inactive_facilities': facilities.filter(status='inactive').count(),
        'owned_facilities': facilities.filter(is_owned=True).count(),
        'leased_facilities': facilities.filter(is_owned=False).count(),
    }
    
    return render(request, 'facility/facility_list.html', context)


@login_required
def facility_create(request):
    """Create a new facility"""
    if request.method == 'POST':
        form = FacilityForm(request.POST)
        if form.is_valid():
            facility = form.save(commit=False)
            facility.created_by = request.user
            facility.updated_by = request.user
            facility.save()
            messages.success(request, f'Facility "{facility.facility_name}" created successfully.')
            return redirect('facility:facility_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = FacilityForm()
    
    context = {
        'form': form,
        'title': 'Create New Facility',
        'submit_text': 'Create Facility'
    }
    
    return render(request, 'facility/facility_form.html', context)


@login_required
def facility_update(request, pk):
    """Update an existing facility"""
    facility = get_object_or_404(Facility, pk=pk)
    
    if request.method == 'POST':
        form = FacilityForm(request.POST, instance=facility)
        if form.is_valid():
            facility = form.save(commit=False)
            facility.updated_by = request.user
            facility.save()
            messages.success(request, f'Facility "{facility.facility_name}" updated successfully.')
            return redirect('facility:facility_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = FacilityForm(instance=facility)
    
    context = {
        'form': form,
        'facility': facility,
        'title': f'Edit Facility: {facility.facility_name}',
        'submit_text': 'Update Facility'
    }
    
    return render(request, 'facility/facility_form.html', context)


@login_required
def facility_detail(request, pk):
    """Display facility details"""
    facility = get_object_or_404(Facility, pk=pk)
    
    # Get locations for this facility
    locations = facility.locations.all()
    
    context = {
        'facility': facility,
        'locations': locations,
        'features': facility.get_facility_features(),
    }
    
    return render(request, 'facility/facility_detail.html', context)


@login_required
def facility_delete(request, pk):
    """Delete a facility"""
    facility = get_object_or_404(Facility, pk=pk)
    
    if request.method == 'POST':
        facility_name = facility.facility_name
        facility.delete()
        messages.success(request, f'Facility "{facility_name}" deleted successfully.')
        return redirect('facility:facility_list')
    
    context = {
        'facility': facility
    }
    
    return render(request, 'facility/facility_confirm_delete.html', context)


@login_required
def facility_quick_view(request, pk):
    """Quick view modal for facility details"""
    facility = get_object_or_404(Facility, pk=pk)
    
    context = {
        'facility': facility,
        'features': facility.get_facility_features(),
    }
    
    return render(request, 'facility/facility_quick_view.html', context)


@csrf_exempt
@require_POST
def facility_status_toggle(request, pk):
    """Toggle facility status via AJAX"""
    try:
        facility = get_object_or_404(Facility, pk=pk)
        if facility.status == 'active':
            facility.status = 'inactive'
        else:
            facility.status = 'active'
        facility.save()
        
        return JsonResponse({
            'success': True,
            'status': facility.status,
            'message': f'Facility status changed to {facility.status}'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
def facility_export(request):
    """Export facilities to CSV"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="facilities_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Facility Code', 'Facility Name', 'Type', 'Status', 'City', 'State',
        'Contact Person', 'Phone', 'Total Area', 'Monthly Rent', 'Currency',
        'Owner', 'Lease Status', 'Created Date'
    ])
    
    facilities = Facility.objects.all()
    for facility in facilities:
        writer.writerow([
            facility.facility_code, facility.facility_name, facility.get_facility_type_display(), 
            facility.status, facility.city, facility.state, facility.contact_person,
            facility.phone, facility.total_area, facility.monthly_rent, facility.currency,
            facility.owner, facility.lease_status, facility.created_at.strftime('%Y-%m-%d')
        ])
    
    return response


# Facility Location Views
@login_required
def location_list(request):
    """Display list of facility locations with search and filtering"""
    locations = FacilityLocation.objects.select_related('facility').all()
    search_form = FacilityLocationSearchForm(request.GET)
    
    if search_form.is_valid():
        search_term = search_form.cleaned_data.get('search_term')
        search_field = search_form.cleaned_data.get('search_field')
        facility = search_form.cleaned_data.get('facility')
        location_type = search_form.cleaned_data.get('location_type')
        status = search_form.cleaned_data.get('status')
        availability = search_form.cleaned_data.get('availability')
        
        # Apply search filters
        if search_term:
            if search_field == 'all':
                locations = locations.filter(
                    Q(location_code__icontains=search_term) |
                    Q(location_name__icontains=search_term) |
                    Q(facility__facility_name__icontains=search_term) |
                    Q(description__icontains=search_term)
                )
            elif search_field == 'location_code':
                locations = locations.filter(location_code__icontains=search_term)
            elif search_field == 'location_name':
                locations = locations.filter(location_name__icontains=search_term)
            elif search_field == 'facility':
                locations = locations.filter(facility__facility_name__icontains=search_term)
        
        # Apply filters
        if facility:
            locations = locations.filter(facility=facility)
        
        if location_type:
            locations = locations.filter(location_type=location_type)
        
        if status:
            locations = locations.filter(status=status)
        
        if availability:
            if availability == 'available':
                locations = locations.filter(status='active', current_utilization__lt=100)
            elif availability == 'full':
                locations = locations.filter(current_utilization__gte=100)
            elif availability == 'reserved':
                locations = locations.filter(status='reserved')
    
    # Pagination
    paginator = Paginator(locations, 20)  # Show 20 locations per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_locations': locations.count(),
        'active_locations': locations.filter(status='active').count(),
        'available_locations': locations.filter(status='active', current_utilization__lt=100).count(),
        'full_locations': locations.filter(current_utilization__gte=100).count(),
    }
    
    return render(request, 'facility/location_list.html', context)


@login_required
def location_create(request):
    """Create a new facility location"""
    if request.method == 'POST':
        form = FacilityLocationForm(request.POST)
        if form.is_valid():
            location = form.save(commit=False)
            location.created_by = request.user
            location.updated_by = request.user
            location.save()
            messages.success(request, f'Location "{location.location_name}" created successfully.')
            return redirect('facility:location_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = FacilityLocationForm()
    
    context = {
        'form': form,
        'title': 'Create New Location',
        'submit_text': 'Create Location'
    }
    
    return render(request, 'facility/location_form.html', context)


@login_required
def location_update(request, pk):
    """Update an existing facility location"""
    location = get_object_or_404(FacilityLocation, pk=pk)
    
    if request.method == 'POST':
        form = FacilityLocationForm(request.POST, instance=location)
        if form.is_valid():
            location = form.save(commit=False)
            location.updated_by = request.user
            location.save()
            messages.success(request, f'Location "{location.location_name}" updated successfully.')
            return redirect('facility:location_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = FacilityLocationForm(instance=location)
    
    context = {
        'form': form,
        'location': location,
        'title': f'Edit Location: {location.location_name}',
        'submit_text': 'Update Location'
    }
    
    return render(request, 'facility/location_form.html', context)


@login_required
def location_detail(request, pk):
    """Display facility location details"""
    location = get_object_or_404(FacilityLocation, pk=pk)
    
    context = {
        'location': location,
        'features': location.get_location_features(),
    }
    
    return render(request, 'facility/location_detail.html', context)


@login_required
def location_delete(request, pk):
    """Delete a facility location"""
    location = get_object_or_404(FacilityLocation, pk=pk)
    
    if request.method == 'POST':
        location_name = location.location_name
        location.delete()
        messages.success(request, f'Location "{location_name}" deleted successfully.')
        return redirect('facility:location_list')
    
    context = {
        'location': location
    }
    
    return render(request, 'facility/location_confirm_delete.html', context)


@login_required
def location_quick_view(request, pk):
    """Quick view modal for facility location details"""
    location = get_object_or_404(FacilityLocation, pk=pk)
    
    context = {
        'location': location,
        'features': location.get_location_features(),
    }
    
    return render(request, 'facility/location_quick_view.html', context)


@login_required
def facility_locations(request, facility_pk):
    """Display locations for a specific facility"""
    facility = get_object_or_404(Facility, pk=facility_pk)
    locations = facility.locations.all()
    
    context = {
        'facility': facility,
        'locations': locations,
    }
    
    return render(request, 'facility/facility_locations.html', context)


# Class-based views for additional functionality
class FacilityListView(LoginRequiredMixin, ListView):
    """Class-based view for facility list"""
    model = Facility
    template_name = 'facility/facility_list.html'
    context_object_name = 'facilities'
    paginate_by = 15
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search_form = FacilitySearchForm(self.request.GET)
        
        if search_form.is_valid():
            search_term = search_form.cleaned_data.get('search_term')
            if search_term:
                queryset = queryset.filter(
                    Q(facility_code__icontains=search_term) |
                    Q(facility_name__icontains=search_term) |
                    Q(city__icontains=search_term)
                )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = FacilitySearchForm(self.request.GET)
        return context


class FacilityDetailView(LoginRequiredMixin, DetailView):
    """Class-based view for facility detail"""
    model = Facility
    template_name = 'facility/facility_detail.html'
    context_object_name = 'facility'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['features'] = self.object.get_facility_features()
        context['locations'] = self.object.locations.all()
        return context


class FacilityCreateView(LoginRequiredMixin, CreateView):
    """Class-based view for facility creation"""
    model = Facility
    form_class = FacilityForm
    template_name = 'facility/facility_form.html'
    success_url = reverse_lazy('facility:facility_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, f'Facility "{form.instance.facility_name}" created successfully.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New Facility'
        context['submit_text'] = 'Create Facility'
        return context


class FacilityUpdateView(LoginRequiredMixin, UpdateView):
    """Class-based view for facility update"""
    model = Facility
    form_class = FacilityForm
    template_name = 'facility/facility_form.html'
    success_url = reverse_lazy('facility:facility_list')
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, f'Facility "{form.instance.facility_name}" updated successfully.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit Facility: {self.object.facility_name}'
        context['submit_text'] = 'Update Facility'
        return context


class FacilityDeleteView(LoginRequiredMixin, DeleteView):
    """Class-based view for facility deletion"""
    model = Facility
    template_name = 'facility/facility_confirm_delete.html'
    success_url = reverse_lazy('facility:facility_list')
    
    def delete(self, request, *args, **kwargs):
        facility_name = self.get_object().facility_name
        messages.success(request, f'Facility "{facility_name}" deleted successfully.')
        return super().delete(request, *args, **kwargs)
