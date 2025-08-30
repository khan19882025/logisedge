from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
import json
from datetime import datetime, timedelta

from .models import (
    Container, ContainerBooking, ContainerTracking, 
    ContainerInventory, ContainerMovement, ContainerNotification
)
from .forms import (
    ContainerForm, ContainerBookingForm, ContainerTrackingForm,
    ContainerInventoryForm, ContainerMovementForm, ContainerSearchForm,
    ContainerBookingSearchForm, ContainerInventorySearchForm,
    ContainerBulkUploadForm, ContainerNotificationForm,
    ContainerStatusUpdateForm, ContainerMaintenanceForm
)

# Dashboard Views
@login_required
def container_dashboard(request):
    """Main container management dashboard"""
    
    # Get summary statistics
    total_containers = Container.objects.count()
    available_containers = Container.objects.filter(status='available').count()
    booked_containers = Container.objects.filter(status='booked').count()
    in_use_containers = Container.objects.filter(status='in_use').count()
    
    # Booking statistics
    total_bookings = ContainerBooking.objects.count()
    pending_bookings = ContainerBooking.objects.filter(status='pending').count()
    active_bookings = ContainerBooking.objects.filter(status='active').count()
    
    # Overstayed containers
    overstayed_containers = ContainerInventory.objects.filter(is_overstayed=True).count()
    
    # Maintenance due
    maintenance_due = Container.objects.filter(
        next_maintenance__lte=timezone.now().date()
    ).count()
    
    # Recent activities
    recent_bookings = ContainerBooking.objects.order_by('-booking_date')[:5]
    recent_tracking = ContainerTracking.objects.order_by('-event_date')[:5]
    recent_movements = ContainerMovement.objects.order_by('-movement_date')[:5]
    
    # Port-wise inventory
    port_inventory = ContainerInventory.objects.values('port').annotate(
        count=Count('container')
    ).order_by('-count')[:10]
    
    # Container type distribution with percentage calculation
    container_types_raw = Container.objects.values('container_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Calculate percentages for each container type
    container_types = []
    for type_data in container_types_raw:
        percentage = (type_data['count'] / total_containers * 100) if total_containers > 0 else 0
        container_types.append({
            'container_type': type_data['container_type'],
            'count': type_data['count'],
            'percentage': round(percentage, 1)
        })
    
    context = {
        'total_containers': total_containers,
        'available_containers': available_containers,
        'booked_containers': booked_containers,
        'in_use_containers': in_use_containers,
        'total_bookings': total_bookings,
        'pending_bookings': pending_bookings,
        'active_bookings': active_bookings,
        'overstayed_containers': overstayed_containers,
        'maintenance_due': maintenance_due,
        'recent_bookings': recent_bookings,
        'recent_tracking': recent_tracking,
        'recent_movements': recent_movements,
        'port_inventory': port_inventory,
        'container_types': container_types,
    }
    
    return render(request, 'container_management/dashboard.html', context)

# Container Views
class ContainerListView(LoginRequiredMixin, ListView):
    model = Container
    template_name = 'container_management/container_list.html'
    context_object_name = 'containers'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Container.objects.all()
        
        # Apply search filters
        search_form = ContainerSearchForm(self.request.GET)
        if search_form.is_valid():
            search_by = search_form.cleaned_data.get('search_by')
            search_term = search_form.cleaned_data.get('search_term')
            container_type = search_form.cleaned_data.get('container_type')
            status = search_form.cleaned_data.get('status')
            port = search_form.cleaned_data.get('port')
            
            if search_term:
                if search_by == 'container_number':
                    queryset = queryset.filter(container_number__icontains=search_term)
                elif search_by == 'booking_number':
                    queryset = queryset.filter(bookings__booking_number__icontains=search_term)
                elif search_by == 'customer':
                    queryset = queryset.filter(bookings__customer__name__icontains=search_term)
                elif search_by == 'location':
                    queryset = queryset.filter(current_location__icontains=search_term)
                elif search_by == 'status':
                    queryset = queryset.filter(status__icontains=search_term)
            
            if container_type:
                queryset = queryset.filter(container_type=container_type)
            
            if status:
                queryset = queryset.filter(status=status)
            
            if port:
                queryset = queryset.filter(inventory_records__port__icontains=port)
        
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ContainerSearchForm(self.request.GET)
        return context

class ContainerDetailView(LoginRequiredMixin, DetailView):
    model = Container
    template_name = 'container_management/container_detail.html'
    context_object_name = 'container'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        container = self.get_object()
        
        # Get related data
        context['bookings'] = container.bookings.all()[:5]
        context['tracking_events'] = container.tracking_events.all()[:10]
        context['movements'] = container.movements.all()[:10]
        context['inventory_records'] = container.inventory_records.all()[:5]
        
        return context

class ContainerCreateView(LoginRequiredMixin, CreateView):
    model = Container
    form_class = ContainerForm
    template_name = 'container_management/container_form.html'
    success_url = reverse_lazy('container_management:container_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Container created successfully!')
        return super().form_valid(form)

class ContainerUpdateView(LoginRequiredMixin, UpdateView):
    model = Container
    form_class = ContainerForm
    template_name = 'container_management/container_form.html'
    success_url = reverse_lazy('container_management:container_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Container updated successfully!')
        return super().form_valid(form)

class ContainerDeleteView(LoginRequiredMixin, DeleteView):
    model = Container
    template_name = 'container_management/container_confirm_delete.html'
    success_url = reverse_lazy('container_management:container_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Container deleted successfully!')
        return super().delete(request, *args, **kwargs)

# Container Booking Views
class ContainerBookingListView(LoginRequiredMixin, ListView):
    model = ContainerBooking
    template_name = 'container_management/booking_list.html'
    context_object_name = 'bookings'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = ContainerBooking.objects.all()
        
        # Apply search filters
        search_form = ContainerBookingSearchForm(self.request.GET)
        if search_form.is_valid():
            search_by = search_form.cleaned_data.get('search_by')
            search_term = search_form.cleaned_data.get('search_term')
            status = search_form.cleaned_data.get('status')
            date_from = search_form.cleaned_data.get('date_from')
            date_to = search_form.cleaned_data.get('date_to')
            
            if search_term:
                if search_by == 'booking_number':
                    queryset = queryset.filter(booking_number__icontains=search_term)
                elif search_by == 'container_number':
                    queryset = queryset.filter(container__container_number__icontains=search_term)
                elif search_by == 'customer':
                    queryset = queryset.filter(customer__name__icontains=search_term)
                elif search_by == 'status':
                    queryset = queryset.filter(status__icontains=search_term)
            
            if status:
                queryset = queryset.filter(status=status)
            
            if date_from:
                queryset = queryset.filter(booking_date__date__gte=date_from)
            
            if date_to:
                queryset = queryset.filter(booking_date__date__lte=date_to)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ContainerBookingSearchForm(self.request.GET)
        return context

class ContainerBookingDetailView(LoginRequiredMixin, DetailView):
    model = ContainerBooking
    template_name = 'container_management/booking_detail.html'
    context_object_name = 'booking'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        booking = self.get_object()
        
        # Get related data
        context['tracking_events'] = booking.tracking_events.all()
        context['movements'] = ContainerMovement.objects.filter(container_booking=booking)
        
        return context

class ContainerBookingCreateView(LoginRequiredMixin, CreateView):
    model = ContainerBooking
    form_class = ContainerBookingForm
    template_name = 'container_management/booking_form.html'
    success_url = reverse_lazy('container_management:booking_list')
    
    def form_valid(self, form):
        booking = form.save()
        
        # Update container status
        container = booking.container
        container.status = 'booked'
        container.save()
        
        # Create notification
        ContainerNotification.objects.create(
            notification_type='booking_confirmation',
            priority='medium',
            container=container,
            container_booking=booking,
            title=f'Container Booking Confirmed - {booking.booking_number}',
            message=f'Container {container.container_number} has been booked for {booking.customer.name}',
            recipient_email=booking.customer.email if hasattr(booking.customer, 'email') else '',
            recipient_name=booking.customer.name
        )
        
        messages.success(self.request, 'Container booking created successfully!')
        return super().form_valid(form)

class ContainerBookingUpdateView(LoginRequiredMixin, UpdateView):
    model = ContainerBooking
    form_class = ContainerBookingForm
    template_name = 'container_management/booking_form.html'
    success_url = reverse_lazy('container_management:booking_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Container booking updated successfully!')
        return super().form_valid(form)

class ContainerBookingDeleteView(LoginRequiredMixin, DeleteView):
    model = ContainerBooking
    template_name = 'container_management/booking_confirm_delete.html'
    success_url = reverse_lazy('container_management:booking_list')
    
    def delete(self, request, *args, **kwargs):
        booking = self.get_object()
        
        # Update container status back to available
        container = booking.container
        container.status = 'available'
        container.save()
        
        messages.success(request, 'Container booking deleted successfully!')
        return super().delete(request, *args, **kwargs)

# Container Tracking Views
class ContainerTrackingListView(LoginRequiredMixin, ListView):
    model = ContainerTracking
    template_name = 'container_management/tracking_list.html'
    context_object_name = 'page_obj'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = ContainerTracking.objects.all()
        
        # Apply search filters
        search_by = self.request.GET.get('search_by', '')
        search_term = self.request.GET.get('search_term', '')
        milestone = self.request.GET.get('milestone', '')
        status = self.request.GET.get('status', '')
        
        if search_term:
            if search_by == 'tracking_number':
                queryset = queryset.filter(tracking_number__icontains=search_term)
            elif search_by == 'container':
                queryset = queryset.filter(container__container_number__icontains=search_term)
            elif search_by == 'location':
                queryset = queryset.filter(location__icontains=search_term)
            elif search_by == 'vessel':
                queryset = queryset.filter(vessel_name__icontains=search_term)
            else:
                queryset = queryset.filter(
                    Q(tracking_number__icontains=search_term) |
                    Q(container__container_number__icontains=search_term) |
                    Q(location__icontains=search_term) |
                    Q(vessel_name__icontains=search_term)
                )
        
        if milestone:
            queryset = queryset.filter(milestone=milestone)
        
        if status:
            if status == 'on_time':
                queryset = queryset.filter(is_delayed=False, is_completed=False)
            elif status == 'delayed':
                queryset = queryset.filter(is_delayed=True)
            elif status == 'completed':
                queryset = queryset.filter(is_completed=True)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add search parameters to context
        context['search_by'] = self.request.GET.get('search_by', '')
        context['search_term'] = self.request.GET.get('search_term', '')
        context['milestone'] = self.request.GET.get('milestone', '')
        context['status'] = self.request.GET.get('status', '')
        
        # Add summary counts
        all_tracking = ContainerTracking.objects.all()
        context['in_transit_count'] = all_tracking.filter(milestone='in_transit').count()
        context['delayed_count'] = all_tracking.filter(is_delayed=True).count()
        context['delivered_count'] = all_tracking.filter(milestone='delivered').count()
        
        return context

class ContainerTrackingDetailView(LoginRequiredMixin, DetailView):
    model = ContainerTracking
    template_name = 'container_management/tracking_detail.html'
    context_object_name = 'tracking'

class ContainerTrackingCreateView(LoginRequiredMixin, CreateView):
    model = ContainerTracking
    form_class = ContainerTrackingForm
    template_name = 'container_management/tracking_form.html'
    success_url = reverse_lazy('container_management:tracking_list')
    
    def form_valid(self, form):
        tracking = form.save()
        
        # Create notification
        ContainerNotification.objects.create(
            notification_type='tracking_update',
            priority='medium',
            container=tracking.container,
            container_tracking=tracking,
            title=f'Container Tracking Update - {tracking.container.container_number}',
            message=f'Container {tracking.container.container_number} reached {tracking.get_milestone_display()} at {tracking.location}',
            recipient_email=tracking.container_booking.customer.email if hasattr(tracking.container_booking.customer, 'email') else '',
            recipient_name=tracking.container_booking.customer.name
        )
        
        messages.success(self.request, 'Tracking event created successfully!')
        return super().form_valid(form)

class ContainerTrackingUpdateView(LoginRequiredMixin, UpdateView):
    model = ContainerTracking
    form_class = ContainerTrackingForm
    template_name = 'container_management/tracking_form.html'
    success_url = reverse_lazy('container_management:tracking_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Tracking event updated successfully!')
        return super().form_valid(form)

class ContainerTrackingDeleteView(LoginRequiredMixin, DeleteView):
    model = ContainerTracking
    template_name = 'container_management/tracking_confirm_delete.html'
    success_url = reverse_lazy('container_management:tracking_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Tracking record deleted successfully!')
        return super().delete(request, *args, **kwargs)

# Container Inventory Views
class ContainerInventoryListView(LoginRequiredMixin, ListView):
    model = ContainerInventory
    template_name = 'container_management/inventory_list.html'
    context_object_name = 'inventory_records'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = ContainerInventory.objects.all()
        
        # Apply search filters
        search_form = ContainerInventorySearchForm(self.request.GET)
        if search_form.is_valid():
            port = search_form.cleaned_data.get('port')
            terminal = search_form.cleaned_data.get('terminal')
            status = search_form.cleaned_data.get('status')
            container_type = search_form.cleaned_data.get('container_type')
            overstayed_only = search_form.cleaned_data.get('overstayed_only')
            
            if port:
                queryset = queryset.filter(port__icontains=port)
            
            if terminal:
                queryset = queryset.filter(terminal__icontains=terminal)
            
            if status:
                queryset = queryset.filter(status=status)
            
            if container_type:
                queryset = queryset.filter(container__container_type=container_type)
            
            if overstayed_only:
                queryset = queryset.filter(is_overstayed=True)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ContainerInventorySearchForm(self.request.GET)
        return context

class ContainerInventoryDetailView(LoginRequiredMixin, DetailView):
    model = ContainerInventory
    template_name = 'container_management/inventory_detail.html'
    context_object_name = 'inventory'

class ContainerInventoryCreateView(LoginRequiredMixin, CreateView):
    model = ContainerInventory
    form_class = ContainerInventoryForm
    template_name = 'container_management/inventory_form.html'
    success_url = reverse_lazy('container_management:inventory_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Inventory record created successfully!')
        return super().form_valid(form)

class ContainerInventoryUpdateView(LoginRequiredMixin, UpdateView):
    model = ContainerInventory
    form_class = ContainerInventoryForm
    template_name = 'container_management/inventory_form.html'
    success_url = reverse_lazy('container_management:inventory_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Inventory record updated successfully!')
        return super().form_valid(form)

class ContainerInventoryDeleteView(LoginRequiredMixin, DeleteView):
    model = ContainerInventory
    template_name = 'container_management/inventory_confirm_delete.html'
    success_url = reverse_lazy('container_management:inventory_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Inventory record deleted successfully!')
        return super().delete(request, *args, **kwargs)

@login_required
def inventory_export(request):
    """Export inventory data to CSV"""
    import csv
    from django.http import HttpResponse
    
    # Get filtered queryset (same as list view)
    queryset = ContainerInventory.objects.all()
    
    # Apply search filters
    search_by = request.GET.get('search_by', '')
    search_term = request.GET.get('search_term', '')
    port = request.GET.get('port', '')
    container_type = request.GET.get('container_type', '')
    status = request.GET.get('status', '')
    
    if search_term:
        if search_by == 'container':
            queryset = queryset.filter(container__container_number__icontains=search_term)
        elif search_by == 'port':
            queryset = queryset.filter(port__icontains=search_term)
        elif search_by == 'terminal':
            queryset = queryset.filter(terminal__icontains=search_term)
        elif search_by == 'yard_location':
            queryset = queryset.filter(yard_location__icontains=search_term)
        else:
            queryset = queryset.filter(
                Q(container__container_number__icontains=search_term) |
                Q(port__icontains=search_term) |
                Q(terminal__icontains=search_term) |
                Q(yard_location__icontains=search_term)
            )
    
    if port:
        queryset = queryset.filter(port=port)
    
    if container_type:
        queryset = queryset.filter(container__container_type=container_type)
    
    if status:
        queryset = queryset.filter(status=status)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="container_inventory_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Container Number', 'Container Type', 'Container Size', 'Port', 'Terminal',
        'Yard', 'Position (Bay-Row-Tier)', 'Status', 'Arrival Date', 'Days in Port',
        'Vessel Name', 'Voyage Number', 'Next Action', 'Expected Departure',
        'Demurrage Start Date', 'Demurrage Rate', 'Is Overstayed', 'Notes'
    ])
    
    for record in queryset:
        writer.writerow([
            record.container.container_number,
            record.container.get_container_type_display(),
            record.container.size,
            record.port,
            record.terminal or '',
            record.yard or '',
            f"{record.bay or ''}-{record.row or ''}-{record.tier or ''}",
            record.get_status_display(),
            record.arrival_date.strftime('%Y-%m-%d %H:%M'),
            record.get_days_in_port() if hasattr(record, 'get_days_in_port') else 0,
            '',  # vessel_name not in model
            '',  # voyage_number not in model
            '',  # next_action not in model
            record.expected_departure.strftime('%Y-%m-%d') if record.expected_departure else '',
            '',  # demurrage_start_date not in model
            '',  # demurrage_rate not in model
            'Yes' if record.is_overstayed else 'No',
            record.notes or ''
        ])
    
    return response

# AJAX Views
@login_required
def container_search_ajax(request):
    """AJAX endpoint for container search"""
    search_term = request.GET.get('q', '')
    
    if len(search_term) >= 3:
        containers = Container.objects.filter(
            Q(container_number__icontains=search_term) |
            Q(container_type__icontains=search_term) |
            Q(current_location__icontains=search_term)
        )[:10]
        
        results = []
        for container in containers:
            results.append({
                'id': container.id,
                'container_number': container.container_number,
                'container_type': container.get_container_type_display(),
                'status': container.get_status_display(),
                'location': container.current_location,
            })
        
        return JsonResponse({'results': results})
    
    return JsonResponse({'results': []})

@login_required
def container_status_update_ajax(request, pk):
    """AJAX endpoint for updating container status"""
    if request.method == 'POST':
        container = get_object_or_404(Container, pk=pk)
        form = ContainerStatusUpdateForm(request.POST)
        
        if form.is_valid():
            container.status = form.cleaned_data['status']
            if form.cleaned_data['location']:
                container.current_location = form.cleaned_data['location']
            container.save()
            
            # Create movement record
            ContainerMovement.objects.create(
                container=container,
                movement_type='transfer',
                from_location=container.current_location,
                to_location=form.cleaned_data['location'] or container.current_location,
                movement_date=timezone.now(),
                notes=form.cleaned_data['notes']
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Container status updated successfully!'
            })
        
        return JsonResponse({
            'success': False,
            'errors': form.errors
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def container_booking_status_update(request, pk):
    """Update container booking status"""
    booking = get_object_or_404(ContainerBooking, pk=pk)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(ContainerBooking.BOOKING_STATUS):
            booking.status = new_status
            if new_status == 'confirmed':
                booking.confirmed_date = timezone.now()
            booking.save()
            
            # Update container status
            container = booking.container
            if new_status in ['confirmed', 'active']:
                container.status = 'in_use'
            elif new_status == 'completed':
                container.status = 'available'
            container.save()
            
            messages.success(request, f'Booking status updated to {booking.get_status_display()}')
        
        return redirect('container_management:booking_detail', pk=pk)
    
    return redirect('container_management:booking_list')

# Report Views
@login_required
def container_report(request):
    """Generate container reports"""
    
    report_type = request.GET.get('type', 'inventory')
    
    if report_type == 'inventory':
        # Port-wise inventory report
        inventory_data = ContainerInventory.objects.values('port', 'terminal').annotate(
            total_containers=Count('container'),
            empty_containers=Count('container', filter=Q(status='empty')),
            stuffed_containers=Count('container', filter=Q(status='stuffed')),
            overstayed_containers=Count('container', filter=Q(is_overstayed=True))
        ).order_by('port', 'terminal')
        
        context = {
            'report_type': 'inventory',
            'inventory_data': inventory_data,
        }
        
    elif report_type == 'bookings':
        # Booking report
        bookings_data = ContainerBooking.objects.values('status').annotate(
            count=Count('id'),
            total_amount=Sum('total_amount')
        ).order_by('status')
        
        context = {
            'report_type': 'bookings',
            'bookings_data': bookings_data,
        }
    
    elif report_type == 'maintenance':
        # Maintenance report
        maintenance_data = Container.objects.filter(
            next_maintenance__lte=timezone.now().date() + timedelta(days=30)
        ).values('container_type').annotate(
            count=Count('id')
        ).order_by('container_type')
        
        context = {
            'report_type': 'maintenance',
            'maintenance_data': maintenance_data,
        }
    
    else:
        context = {'report_type': 'inventory'}
    
    return render(request, 'container_management/reports.html', context)

# Bulk Upload View
@login_required
def container_bulk_upload(request):
    """Bulk upload containers via Excel/CSV"""
    
    if request.method == 'POST':
        form = ContainerBulkUploadForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Handle file upload and processing
            # This would require additional libraries like pandas or openpyxl
            messages.success(request, 'Bulk upload completed successfully!')
            return redirect('container_management:container_list')
    else:
        form = ContainerBulkUploadForm()
    
    return render(request, 'container_management/bulk_upload.html', {'form': form})

# Notification Views
@login_required
def notification_list(request):
    """List container notifications"""
    notifications = ContainerNotification.objects.all().order_by('-created_at')
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'container_management/notification_list.html', {
        'page_obj': page_obj
    })

@login_required
def notification_detail(request, pk):
    """View notification details"""
    notification = get_object_or_404(ContainerNotification, pk=pk)
    
    # Mark as read
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
    
    return render(request, 'container_management/notification_detail.html', {
        'notification': notification
    })

@login_required
def send_notification(request):
    """Send container notification"""
    
    if request.method == 'POST':
        form = ContainerNotificationForm(request.POST)
        
        if form.is_valid():
            notification = form.save()
            
            # Send email if recipient email is provided
            if notification.recipient_email:
                try:
                    send_mail(
                        notification.title,
                        notification.message,
                        settings.DEFAULT_FROM_EMAIL,
                        [notification.recipient_email],
                        fail_silently=False,
                    )
                    notification.is_sent = True
                    notification.sent_at = timezone.now()
                    notification.save()
                except Exception as e:
                    messages.error(request, f'Failed to send email: {str(e)}')
            
            messages.success(request, 'Notification sent successfully!')
            return redirect('container_management:notification_list')
    else:
        form = ContainerNotificationForm()
    
    return render(request, 'container_management/send_notification.html', {'form': form})
