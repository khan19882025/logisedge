from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail
from django.conf import settings
import json

from .models import (
    FreightBooking, Carrier, BookingCoordinator, BookingDocument,
    BookingCharge, BookingHistory
)
from .forms import (
    FreightBookingForm, CarrierForm, BookingCoordinatorForm,
    BookingDocumentForm, BookingChargeForm, BookingStatusForm,
    BookingSearchForm, BookingSummaryForm
)
from freight_quotation.models import Customer, FreightQuotation


# Carrier Views
class CarrierListView(LoginRequiredMixin, ListView):
    model = Carrier
    template_name = 'freight_booking/carrier_list.html'
    context_object_name = 'carriers'
    paginate_by = 20

    def get_queryset(self):
        queryset = Carrier.objects.all()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search) |
                Q(contact_person__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        return context


class CarrierCreateView(LoginRequiredMixin, CreateView):
    model = Carrier
    form_class = CarrierForm
    template_name = 'freight_booking/carrier_form.html'
    success_url = reverse_lazy('freight_booking:carrier_list')

    def form_valid(self, form):
        messages.success(self.request, 'Carrier created successfully!')
        return super().form_valid(form)


class CarrierUpdateView(LoginRequiredMixin, UpdateView):
    model = Carrier
    form_class = CarrierForm
    template_name = 'freight_booking/carrier_form.html'
    success_url = reverse_lazy('freight_booking:carrier_list')

    def form_valid(self, form):
        messages.success(self.request, 'Carrier updated successfully!')
        return super().form_valid(form)


class CarrierDeleteView(LoginRequiredMixin, DeleteView):
    model = Carrier
    template_name = 'freight_booking/carrier_confirm_delete.html'
    success_url = reverse_lazy('freight_booking:carrier_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Carrier deleted successfully!')
        return super().delete(request, *args, **kwargs)


# Booking Coordinator Views
class BookingCoordinatorListView(LoginRequiredMixin, ListView):
    model = BookingCoordinator
    template_name = 'freight_booking/coordinator_list.html'
    context_object_name = 'coordinators'
    paginate_by = 20

    def get_queryset(self):
        queryset = BookingCoordinator.objects.select_related('user')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(employee_id__icontains=search) |
                Q(department__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        return context


class BookingCoordinatorCreateView(LoginRequiredMixin, CreateView):
    model = BookingCoordinator
    form_class = BookingCoordinatorForm
    template_name = 'freight_booking/coordinator_form.html'
    success_url = reverse_lazy('freight_booking:coordinator_list')

    def form_valid(self, form):
        messages.success(self.request, 'Booking coordinator created successfully!')
        return super().form_valid(form)


class BookingCoordinatorUpdateView(LoginRequiredMixin, UpdateView):
    model = BookingCoordinator
    form_class = BookingCoordinatorForm
    template_name = 'freight_booking/coordinator_form.html'
    success_url = reverse_lazy('freight_booking:coordinator_list')

    def form_valid(self, form):
        messages.success(self.request, 'Booking coordinator updated successfully!')
        return super().form_valid(form)


class BookingCoordinatorDeleteView(LoginRequiredMixin, DeleteView):
    model = BookingCoordinator
    template_name = 'freight_booking/coordinator_confirm_delete.html'
    success_url = reverse_lazy('freight_booking:coordinator_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Booking coordinator deleted successfully!')
        return super().delete(request, *args, **kwargs)


# Freight Booking Views
class FreightBookingListView(LoginRequiredMixin, ListView):
    model = FreightBooking
    template_name = 'freight_booking/booking_list.html'
    context_object_name = 'bookings'
    paginate_by = 20

    def get_queryset(self):
        queryset = FreightBooking.objects.select_related(
            'customer', 'carrier', 'booking_coordinator', 'created_by'
        )
        
        # Apply filters
        form = BookingSearchForm(self.request.GET)
        if form.is_valid():
            data = form.cleaned_data
            
            if data.get('booking_reference'):
                queryset = queryset.filter(booking_reference__icontains=data['booking_reference'])
            
            if data.get('customer'):
                queryset = queryset.filter(customer=data['customer'])
            
            if data.get('status'):
                queryset = queryset.filter(status=data['status'])
            
            if data.get('shipment_type'):
                queryset = queryset.filter(shipment_type=data['shipment_type'])
            
            if data.get('carrier'):
                queryset = queryset.filter(carrier=data['carrier'])
            
            if data.get('date_from'):
                queryset = queryset.filter(booking_date__date__gte=data['date_from'])
            
            if data.get('date_to'):
                queryset = queryset.filter(booking_date__date__lte=data['date_to'])
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = BookingSearchForm(self.request.GET)
        return context


class FreightBookingCreateView(LoginRequiredMixin, CreateView):
    model = FreightBooking
    form_class = FreightBookingForm
    template_name = 'freight_booking/booking_form.html'
    success_url = reverse_lazy('freight_booking:booking_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        
        # Create history record
        BookingHistory.objects.create(
            booking=form.instance,
            action='created',
            user=self.request.user
        )
        
        messages.success(self.request, f'Booking created successfully! Reference: {form.instance.booking_reference}')
        return response


class FreightBookingUpdateView(LoginRequiredMixin, UpdateView):
    model = FreightBooking
    form_class = FreightBookingForm
    template_name = 'freight_booking/booking_form.html'
    success_url = reverse_lazy('freight_booking:booking_list')

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        
        # Create history record
        BookingHistory.objects.create(
            booking=form.instance,
            action='updated',
            user=self.request.user
        )
        
        messages.success(self.request, 'Booking updated successfully!')
        return response


class FreightBookingDetailView(LoginRequiredMixin, DetailView):
    model = FreightBooking
    template_name = 'freight_booking/booking_detail.html'
    context_object_name = 'booking'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['documents'] = self.object.documents.all()
        context['charges'] = self.object.charges.all()
        context['history'] = self.object.history.all()[:10]  # Last 10 history records
        context['status_form'] = BookingStatusForm(initial={'status': self.object.status})
        return context


class FreightBookingDeleteView(LoginRequiredMixin, DeleteView):
    model = FreightBooking
    template_name = 'freight_booking/booking_confirm_delete.html'
    success_url = reverse_lazy('freight_booking:booking_list')

    def delete(self, request, *args, **kwargs):
        booking = self.get_object()
        
        # Create history record before deletion
        BookingHistory.objects.create(
            booking=booking,
            action='cancelled',
            user=request.user,
            notes='Booking deleted'
        )
        
        messages.success(request, 'Booking deleted successfully!')
        return super().delete(request, *args, **kwargs)


# Booking Document Views
@login_required
def add_document(request, booking_id):
    booking = get_object_or_404(FreightBooking, id=booking_id)
    
    if request.method == 'POST':
        form = BookingDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.booking = booking
            document.uploaded_by = request.user
            document.filename = request.FILES['file'].name
            document.save()
            
            # Create history record
            BookingHistory.objects.create(
                booking=booking,
                action='document_added',
                user=request.user,
                notes=f'Document added: {document.get_document_type_display()}'
            )
            
            messages.success(request, 'Document uploaded successfully!')
            return redirect('freight_booking:booking_detail', pk=booking_id)
    else:
        form = BookingDocumentForm()
    
    return render(request, 'freight_booking/document_form.html', {
        'form': form,
        'booking': booking
    })


@login_required
@require_POST
def delete_document(request, document_id):
    document = get_object_or_404(BookingDocument, id=document_id)
    booking_id = document.booking.id
    
    # Create history record
    BookingHistory.objects.create(
        booking=document.booking,
        action='document_removed',
        user=request.user,
        notes=f'Document removed: {document.get_document_type_display()}'
    )
    
    document.delete()
    messages.success(request, 'Document deleted successfully!')
    return redirect('freight_booking:booking_detail', pk=booking_id)


# Booking Charge Views
@login_required
def add_charge(request, booking_id):
    booking = get_object_or_404(FreightBooking, id=booking_id)
    
    if request.method == 'POST':
        form = BookingChargeForm(request.POST)
        if form.is_valid():
            charge = form.save(commit=False)
            charge.booking = booking
            charge.save()
            
            # Update booking additional costs
            booking.additional_costs = booking.charges.aggregate(total=Sum('amount'))['total'] or 0
            booking.save()
            
            messages.success(request, 'Charge added successfully!')
            return redirect('freight_booking:booking_detail', pk=booking_id)
    else:
        form = BookingChargeForm()
    
    return render(request, 'freight_booking/charge_form.html', {
        'form': form,
        'booking': booking
    })


@login_required
def edit_charge(request, charge_id):
    charge = get_object_or_404(BookingCharge, id=charge_id)
    
    if request.method == 'POST':
        form = BookingChargeForm(request.POST, instance=charge)
        if form.is_valid():
            form.save()
            
            # Update booking additional costs
            charge.booking.additional_costs = charge.booking.charges.aggregate(total=Sum('amount'))['total'] or 0
            charge.booking.save()
            
            messages.success(request, 'Charge updated successfully!')
            return redirect('freight_booking:booking_detail', pk=charge.booking.id)
    else:
        form = BookingChargeForm(instance=charge)
    
    return render(request, 'freight_booking/charge_form.html', {
        'form': form,
        'booking': charge.booking,
        'charge': charge
    })


@login_required
@require_POST
def delete_charge(request, charge_id):
    charge = get_object_or_404(BookingCharge, id=charge_id)
    booking_id = charge.booking.id
    charge.delete()
    
    # Update booking additional costs
    charge.booking.additional_costs = charge.booking.charges.aggregate(total=Sum('amount'))['total'] or 0
    charge.booking.save()
    
    messages.success(request, 'Charge deleted successfully!')
    return redirect('freight_booking:booking_detail', pk=booking_id)


# Booking Status Management
@login_required
@require_POST
def change_status(request, booking_id):
    booking = get_object_or_404(FreightBooking, id=booking_id)
    form = BookingStatusForm(request.POST)
    
    if form.is_valid():
        new_status = form.cleaned_data['status']
        notes = form.cleaned_data.get('notes', '')
        
        # Update status and timestamps
        booking.status = new_status
        if new_status == 'confirmed' and not booking.confirmed_date:
            booking.confirmed_date = timezone.now()
        elif new_status == 'in_transit' and not booking.transit_start_date:
            booking.transit_start_date = timezone.now()
        elif new_status == 'delivered' and not booking.delivered_date:
            booking.delivered_date = timezone.now()
        
        booking.save()
        
        # Create history record
        BookingHistory.objects.create(
            booking=booking,
            action='status_changed',
            user=request.user,
            notes=f'Status changed to {new_status.title()}. {notes}'
        )
        
        messages.success(request, f'Booking status changed to {new_status.title()}')
    else:
        messages.error(request, 'Invalid status change request')
    
    return redirect('freight_booking:booking_detail', pk=booking_id)


# AJAX Views
@login_required
def get_quotation_details(request, quotation_id):
    """Get quotation details for AJAX requests"""
    quotation = get_object_or_404(FreightQuotation, id=quotation_id)
    return JsonResponse({
        'customer_id': quotation.customer.id,
        'customer_name': quotation.customer.name,
        'origin': quotation.origin,
        'destination': quotation.destination,
        'cargo_details': quotation.cargo_details,
        'weight': float(quotation.weight) if quotation.weight else 0,
        'volume': float(quotation.volume) if quotation.volume else 0,
        'packages': quotation.packages,
        'currency': quotation.currency,
        'total_amount': float(quotation.grand_total) if quotation.grand_total else 0,
    })


@login_required
def search_quotations(request):
    """Search quotations for AJAX requests"""
    query = request.GET.get('q', '')
    if query:
        quotations = FreightQuotation.objects.filter(
            quotation_number__icontains=query
        )[:10]
        results = [{'id': q.id, 'text': q.quotation_number} for q in quotations]
    else:
        results = []
    
    return JsonResponse({'results': results})


# Dashboard/Statistics Views
@login_required
def booking_statistics(request):
    """View for booking statistics and analytics"""
    # Get date range from request
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    queryset = FreightBooking.objects.all()
    
    if date_from:
        queryset = queryset.filter(booking_date__date__gte=date_from)
    if date_to:
        queryset = queryset.filter(booking_date__date__lte=date_to)
    
    # Calculate statistics
    total_bookings = queryset.count()
    total_value = queryset.aggregate(total=Sum('total_cost'))['total'] or 0
    
    # Calculate average value
    average_value = total_value / total_bookings if total_bookings > 0 else 0
    
    status_counts = queryset.values('status').annotate(count=Count('id'))
    shipment_type_counts = queryset.values('shipment_type').annotate(count=Count('id'))
    
    # Recent bookings
    recent_bookings = queryset.order_by('-created_at')[:10]
    
    context = {
        'total_bookings': total_bookings,
        'total_value': total_value,
        'average_value': average_value,
        'status_counts': status_counts,
        'shipment_type_counts': shipment_type_counts,
        'recent_bookings': recent_bookings,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'freight_booking/statistics.html', context)


# Booking Summary View
@login_required
def booking_summary(request, booking_id):
    """Show booking summary before confirmation"""
    booking = get_object_or_404(FreightBooking, id=booking_id)
    
    if request.method == 'POST':
        form = BookingSummaryForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['confirm_booking']:
                # Update status to booked
                booking.status = 'booked'
                booking.save()
                
                # Create history record
                BookingHistory.objects.create(
                    booking=booking,
                    action='status_changed',
                    user=request.user,
                    notes='Booking confirmed by user'
                )
                
                # Send notification email if requested
                if form.cleaned_data['send_notification']:
                    try:
                        send_booking_confirmation_email(booking)
                        messages.success(request, 'Booking confirmation email sent to customer.')
                    except Exception as e:
                        messages.warning(request, f'Booking confirmed but email notification failed: {str(e)}')
                
                messages.success(request, 'Booking confirmed successfully!')
                return redirect('freight_booking:booking_detail', pk=booking_id)
            else:
                messages.error(request, 'Please confirm the booking to proceed.')
    else:
        form = BookingSummaryForm()
    
    return render(request, 'freight_booking/booking_summary.html', {
        'booking': booking,
        'form': form
    })


def send_booking_confirmation_email(booking):
    """Send booking confirmation email to customer"""
    subject = f'Booking Confirmation - {booking.booking_reference}'
    
    context = {
        'booking': booking,
        'customer': booking.customer,
    }
    
    html_message = render_to_string('freight_booking/email/booking_confirmation.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[booking.customer.email],
        html_message=html_message,
        fail_silently=False,
    )
