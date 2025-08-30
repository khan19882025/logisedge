from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import transaction
import pandas as pd
import json
from datetime import datetime, timedelta

from .models import (
    Shipment, StatusUpdate, ShipmentAttachment, NotificationLog, 
    BulkUpdateLog, ShipmentSearch
)
from .forms import (
    ShipmentForm, StatusUpdateForm, ShipmentSearchForm, ShipmentAttachmentForm,
    BulkUpdateForm, NotificationForm, ShipmentFilterForm, QuickStatusUpdateForm,
    ShipmentImportForm
)

class StaffRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure only staff can access certain views"""
    
    def test_func(self):
        return self.request.user.is_staff

class ShipmentListView(LoginRequiredMixin, ListView):
    """View for listing all shipments with search and filtering"""
    
    model = Shipment
    template_name = 'shipment_tracking/shipment_list.html'
    context_object_name = 'shipments'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Shipment.objects.filter(is_active=True)
        
        # Apply filters
        status = self.request.GET.get('status')
        origin_port = self.request.GET.get('origin_port')
        destination_port = self.request.GET.get('destination_port')
        customer = self.request.GET.get('customer')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        is_tracking_enabled = self.request.GET.get('is_tracking_enabled')
        
        if status:
            queryset = queryset.filter(current_status=status)
        if origin_port:
            queryset = queryset.filter(origin_port__icontains=origin_port)
        if destination_port:
            queryset = queryset.filter(destination_port__icontains=destination_port)
        if customer:
            queryset = queryset.filter(customer_id=customer)
        if date_from:
            queryset = queryset.filter(booking_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(booking_date__lte=date_to)
        if is_tracking_enabled:
            queryset = queryset.filter(is_tracking_enabled=True)
        
        # If user is not staff, only show their shipments
        # if not self.request.user.is_staff:
        #     queryset = queryset.filter(customer__user=self.request.user)
        
        return queryset.select_related('customer').prefetch_related('status_updates')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = ShipmentFilterForm(self.request.GET)
        context['search_form'] = ShipmentSearchForm()
        
        # Add statistics
        context['total_shipments'] = Shipment.objects.filter(is_active=True).count()
        context['delivered_shipments'] = Shipment.objects.filter(
            is_active=True, current_status='delivered'
        ).count()
        context['in_transit_shipments'] = Shipment.objects.filter(
            is_active=True, current_status__in=['sailing', 'arrived_destination', 'customs_cleared']
        ).count()
        
        return context

class ShipmentDetailView(LoginRequiredMixin, DetailView):
    """View for displaying shipment details with status timeline"""
    
    model = Shipment
    template_name = 'shipment_tracking/shipment_detail.html'
    context_object_name = 'shipment'
    
    def get_queryset(self):
        queryset = Shipment.objects.select_related('customer').prefetch_related(
            'status_updates', 'attachments', 'notifications'
        )
        
        # If user is not staff, only show their shipments
        # if not self.request.user.is_staff:
        #     queryset = queryset.filter(customer__user=self.request.user)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_form'] = StatusUpdateForm(shipment=self.object)
        context['attachment_form'] = ShipmentAttachmentForm()
        context['notification_form'] = NotificationForm()
        context['quick_update_form'] = QuickStatusUpdateForm()
        
        # Get status timeline
        context['status_timeline'] = self.object.status_updates.all()
        
        # Get recent attachments
        context['recent_attachments'] = self.object.attachments.all()[:5]
        
        # Get recent notifications
        context['recent_notifications'] = self.object.notifications.all()[:5]
        
        return context

class ShipmentCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    """View for creating new shipments"""
    
    model = Shipment
    form_class = ShipmentForm
    template_name = 'shipment_tracking/shipment_form.html'
    success_url = reverse_lazy('shipment_tracking:shipment_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Shipment created successfully!')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New Shipment'
        context['button_text'] = 'Create Shipment'
        return context

class ShipmentUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    """View for updating shipments"""
    
    model = Shipment
    form_class = ShipmentForm
    template_name = 'shipment_tracking/shipment_form.html'
    
    def get_success_url(self):
        return reverse('shipment_tracking:shipment_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Shipment updated successfully!')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Shipment'
        context['button_text'] = 'Update Shipment'
        return context

class ShipmentDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    """View for deleting shipments"""
    
    model = Shipment
    template_name = 'shipment_tracking/shipment_confirm_delete.html'
    success_url = reverse_lazy('shipment_tracking:shipment_list')
    
    def delete(self, request, *args, **kwargs):
        shipment = self.get_object()
        shipment.is_active = False
        shipment.save()
        messages.success(request, 'Shipment deleted successfully!')
        return redirect(self.success_url)

@login_required
def shipment_search(request):
    """View for searching shipments"""
    
    if request.method == 'GET':
        form = ShipmentSearchForm(request.GET)
        if form.is_valid():
            search_type = form.cleaned_data['search_type']
            search_query = form.cleaned_data['search_query']
            status_filter = form.cleaned_data['status_filter']
            date_from = form.cleaned_data['date_from']
            date_to = form.cleaned_data['date_to']
            
            queryset = Shipment.objects.filter(is_active=True)
            
            # Apply search filters
            if search_query:
                if search_type == 'container':
                    queryset = queryset.filter(container_number__icontains=search_query)
                elif search_type == 'booking':
                    queryset = queryset.filter(booking_id__icontains=search_query)
                elif search_type == 'hbl':
                    queryset = queryset.filter(hbl_number__icontains=search_query)
                elif search_type == 'customer_ref':
                    queryset = queryset.filter(customer_reference__icontains=search_query)
                elif search_type == 'customer_name':
                    queryset = queryset.filter(customer_name__icontains=search_query)
                else:  # all
                    queryset = queryset.filter(
                        Q(container_number__icontains=search_query) |
                        Q(booking_id__icontains=search_query) |
                        Q(hbl_number__icontains=search_query) |
                        Q(customer_reference__icontains=search_query) |
                        Q(customer_name__icontains=search_query)
                    )
            
            if status_filter:
                queryset = queryset.filter(current_status=status_filter)
            
            if date_from:
                queryset = queryset.filter(booking_date__gte=date_from)
            
            if date_to:
                queryset = queryset.filter(booking_date__lte=date_to)
            
            # If user is not staff, only show their shipments
            # if not request.user.is_staff:
            #     queryset = queryset.filter(customer__user=request.user)
            
            # Log search
            if search_query:
                ShipmentSearch.objects.create(
                    user=request.user,
                    search_query=search_query,
                    search_type=search_type,
                    search_results_count=queryset.count()
                )
            
            # Paginate results
            paginator = Paginator(queryset, 20)
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            
            return render(request, 'shipment_tracking/shipment_search_results.html', {
                'form': form,
                'page_obj': page_obj,
                'search_query': search_query,
                'results_count': queryset.count()
            })
    
    else:
        form = ShipmentSearchForm()
    
    return render(request, 'shipment_tracking/shipment_search.html', {
        'form': form
    })

@login_required
def add_status_update(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Access denied. Staff privileges required.')
        return redirect('shipment_tracking:shipment_list')
    """View for adding status updates to shipments"""
    
    shipment = get_object_or_404(Shipment, pk=pk)
    
    if request.method == 'POST':
        form = StatusUpdateForm(request.POST, shipment=shipment)
        if form.is_valid():
            status_update = form.save(commit=False)
            status_update.shipment = shipment
            status_update.updated_by = request.user
            status_update.save()
            
            messages.success(request, 'Status updated successfully!')
            return redirect('shipment_tracking:shipment_detail', pk=shipment.pk)
    else:
        form = StatusUpdateForm(shipment=shipment)
    
    return render(request, 'shipment_tracking/status_update_form.html', {
        'form': form,
        'shipment': shipment
    })

@login_required
def quick_status_update(request, pk):
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Access denied. Staff privileges required.'})
    """View for quick status updates via AJAX"""
    
    if request.method == 'POST' and request.is_ajax():
        shipment = get_object_or_404(Shipment, pk=pk)
        form = QuickStatusUpdateForm(request.POST)
        
        if form.is_valid():
            with transaction.atomic():
                # Create status update
                status_update = StatusUpdate.objects.create(
                    shipment=shipment,
                    status=form.cleaned_data['status'],
                    location=form.cleaned_data['location'],
                    description=form.cleaned_data['description'],
                    updated_by=request.user
                )
                
                # Send notification if requested
                if form.cleaned_data.get('send_notification') and shipment.customer_email:
                    # Here you would implement actual notification logic
                    NotificationLog.objects.create(
                        shipment=shipment,
                        status_update=status_update,
                        notification_type='email',
                        recipient=shipment.customer_email,
                        subject=f'Status Update: {shipment.shipment_id}',
                        message=f'Your shipment {shipment.shipment_id} status has been updated to {status_update.get_status_display()}',
                        sent_by=request.user,
                        is_sent=True
                    )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Status updated successfully!',
                    'new_status': status_update.get_status_display(),
                    'location': status_update.location,
                    'timestamp': status_update.timestamp.strftime('%Y-%m-%d %H:%M')
                })
        
        return JsonResponse({
            'success': False,
            'errors': form.errors
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
def upload_attachment(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Access denied. Staff privileges required.')
        return redirect('shipment_tracking:shipment_list')
    """View for uploading attachments to shipments"""
    
    shipment = get_object_or_404(Shipment, pk=pk)
    
    if request.method == 'POST':
        form = ShipmentAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.shipment = shipment
            attachment.uploaded_by = request.user
            attachment.save()
            
            messages.success(request, 'Attachment uploaded successfully!')
            return redirect('shipment_tracking:shipment_detail', pk=shipment.pk)
    else:
        form = ShipmentAttachmentForm()
    
    return render(request, 'shipment_tracking/attachment_form.html', {
        'form': form,
        'shipment': shipment
    })

@login_required
def bulk_update_view(request):
    if not request.user.is_staff:
        messages.error(request, 'Access denied. Staff privileges required.')
        return redirect('shipment_tracking:shipment_list')
    """View for bulk updating shipments via Excel"""
    
    if request.method == 'POST':
        form = BulkUpdateForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                file = form.cleaned_data['excel_file']
                df = pd.read_excel(file)
                
                successful_updates = 0
                failed_updates = 0
                success_details = []
                error_details = []
                
                for index, row in df.iterrows():
                    try:
                        shipment = Shipment.objects.get(
                            shipment_id=row['shipment_id'],
                            is_active=True
                        )
                        
                        # Create status update
                        StatusUpdate.objects.create(
                            shipment=shipment,
                            status=row['status'],
                            location=row['location'],
                            description=row.get('description', ''),
                            updated_by=request.user
                        )
                        
                        successful_updates += 1
                        success_details.append({
                            'shipment_id': row['shipment_id'],
                            'status': row['status']
                        })
                        
                    except Shipment.DoesNotExist:
                        failed_updates += 1
                        error_details.append({
                            'shipment_id': row['shipment_id'],
                            'error': 'Shipment not found'
                        })
                    except Exception as e:
                        failed_updates += 1
                        error_details.append({
                            'shipment_id': row.get('shipment_id', 'Unknown'),
                            'error': str(e)
                        })
                
                # Log bulk update
                BulkUpdateLog.objects.create(
                    update_type='excel_upload',
                    file_uploaded=file,
                    total_records=len(df),
                    successful_updates=successful_updates,
                    failed_updates=failed_updates,
                    processed_by=request.user,
                    success_details=success_details,
                    error_details=error_details
                )
                
                messages.success(
                    request, 
                    f'Bulk update completed! {successful_updates} successful, {failed_updates} failed.'
                )
                
            except Exception as e:
                messages.error(request, f'Error processing file: {str(e)}')
    else:
        form = BulkUpdateForm()
    
    return render(request, 'shipment_tracking/bulk_update.html', {
        'form': form
    })

@login_required
def shipment_import_view(request):
    if not request.user.is_staff:
        messages.error(request, 'Access denied. Staff privileges required.')
        return redirect('shipment_tracking:shipment_list')
    """View for importing shipments from Excel"""
    
    if request.method == 'POST':
        form = ShipmentImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                file = form.cleaned_data['excel_file']
                df = pd.read_excel(file)
                
                successful_imports = 0
                failed_imports = 0
                
                for index, row in df.iterrows():
                    try:
                        # Create shipment
                        Shipment.objects.create(
                            container_number=row['container_number'],
                            customer_name=row['customer_name'],
                            origin_port=row['origin_port'],
                            destination_port=row['destination_port'],
                            origin_country=row.get('origin_country', ''),
                            destination_country=row.get('destination_country', ''),
                            booking_date=row['booking_date'],
                            booking_id=row.get('booking_id', ''),
                            hbl_number=row.get('hbl_number', ''),
                            customer_reference=row.get('customer_reference', ''),
                            created_by=request.user
                        )
                        successful_imports += 1
                        
                    except Exception as e:
                        failed_imports += 1
                
                messages.success(
                    request, 
                    f'Import completed! {successful_imports} imported, {failed_imports} failed.'
                )
                
            except Exception as e:
                messages.error(request, f'Error processing file: {str(e)}')
    else:
        form = ShipmentImportForm()
    
    return render(request, 'shipment_tracking/shipment_import.html', {
        'form': form
    })

@login_required
def dashboard_view(request):
    """Dashboard view for shipment tracking overview"""
    
    # Get statistics
    total_shipments = Shipment.objects.filter(is_active=True).count()
    delivered_shipments = Shipment.objects.filter(
        is_active=True, current_status='delivered'
    ).count()
    in_transit_shipments = Shipment.objects.filter(
        is_active=True, current_status__in=['sailing', 'arrived_destination', 'customs_cleared']
    ).count()
    on_hold_shipments = Shipment.objects.filter(
        is_active=True, current_status='on_hold'
    ).count()
    
    # Get recent shipments
    recent_shipments = Shipment.objects.filter(is_active=True).order_by('-created_at')[:10]
    
    # Get recent status updates
    recent_updates = StatusUpdate.objects.select_related('shipment').order_by('-timestamp')[:10]
    
    # Get status distribution
    status_distribution = Shipment.objects.filter(is_active=True).values('current_status').annotate(
        count=Count('current_status')
    )
    
    context = {
        'total_shipments': total_shipments,
        'delivered_shipments': delivered_shipments,
        'in_transit_shipments': in_transit_shipments,
        'on_hold_shipments': on_hold_shipments,
        'recent_shipments': recent_shipments,
        'recent_updates': recent_updates,
        'status_distribution': status_distribution,
    }
    
    return render(request, 'shipment_tracking/dashboard.html', context)

@login_required
def api_shipment_status(request, pk):
    """API endpoint for getting shipment status (for external integrations)"""
    
    shipment = get_object_or_404(Shipment, pk=pk, is_active=True)
    
    data = {
        'shipment_id': shipment.shipment_id,
        'container_number': shipment.container_number,
        'current_status': shipment.current_status,
        'status_display': shipment.get_current_status_display(),
        'current_location': shipment.current_location,
        'last_updated': shipment.last_updated.isoformat(),
        'expected_arrival': shipment.expected_arrival.isoformat() if shipment.expected_arrival else None,
        'is_delivered': shipment.is_delivered,
        'is_delayed': shipment.is_delayed,
    }
    
    return JsonResponse(data)

@login_required
def export_shipments(request):
    """Export shipments to Excel"""
    
    queryset = Shipment.objects.filter(is_active=True)
    
    # Apply filters if any
    status = request.GET.get('status')
    if status:
        queryset = queryset.filter(current_status=status)
    
    # If user is not staff, only export their shipments
    # if not request.user.is_staff:
    #     queryset = queryset.filter(customer__user=request.user)
    
    # Create DataFrame
    data = []
    for shipment in queryset:
        data.append({
            'Shipment ID': shipment.shipment_id,
            'Container Number': shipment.container_number,
            'Booking ID': shipment.booking_id,
            'HBL Number': shipment.hbl_number,
            'Customer Name': shipment.customer_name,
            'Origin Port': shipment.origin_port,
            'Destination Port': shipment.destination_port,
            'Current Status': shipment.get_current_status_display(),
            'Current Location': shipment.current_location,
            'Booking Date': shipment.booking_date,
            'Expected Arrival': shipment.expected_arrival,
            'Last Updated': shipment.last_updated,
        })
    
    df = pd.DataFrame(data)
    
    # Create response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=shipments_export.xlsx'
    
    df.to_excel(response, index=False)
    return response
