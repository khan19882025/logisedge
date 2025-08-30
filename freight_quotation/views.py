from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
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
    Customer, CargoType, Incoterm, ChargeType, FreightQuotation,
    QuotationCharge, QuotationAttachment, QuotationHistory
)
from .forms import (
    CustomerForm, CargoTypeForm, IncotermForm, ChargeTypeForm,
    FreightQuotationForm, QuotationChargeForm, QuotationAttachmentForm,
    QuotationSearchForm, QuotationStatusForm
)


# Customer Views
class CustomerListView(LoginRequiredMixin, ListView):
    model = Customer
    template_name = 'freight_quotation/customer_list.html'
    context_object_name = 'customers'
    paginate_by = 20

    def get_queryset(self):
        queryset = Customer.objects.all()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(phone__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        return context


class CustomerCreateView(LoginRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'freight_quotation/customer_form.html'
    success_url = reverse_lazy('freight_quotation:customer_list')

    def form_valid(self, form):
        messages.success(self.request, 'Customer created successfully!')
        return super().form_valid(form)


class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'freight_quotation/customer_form.html'
    success_url = reverse_lazy('freight_quotation:customer_list')

    def form_valid(self, form):
        messages.success(self.request, 'Customer updated successfully!')
        return super().form_valid(form)


class CustomerDeleteView(LoginRequiredMixin, DeleteView):
    model = Customer
    template_name = 'freight_quotation/customer_confirm_delete.html'
    success_url = reverse_lazy('freight_quotation:customer_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Customer deleted successfully!')
        return super().delete(request, *args, **kwargs)


# Cargo Type Views
class CargoTypeListView(LoginRequiredMixin, ListView):
    model = CargoType
    template_name = 'freight_quotation/cargo_type_list.html'
    context_object_name = 'cargo_types'
    paginate_by = 20


class CargoTypeCreateView(LoginRequiredMixin, CreateView):
    model = CargoType
    form_class = CargoTypeForm
    template_name = 'freight_quotation/cargo_type_form.html'
    success_url = reverse_lazy('freight_quotation:cargo_type_list')

    def form_valid(self, form):
        messages.success(self.request, 'Cargo type created successfully!')
        return super().form_valid(form)


class CargoTypeUpdateView(LoginRequiredMixin, UpdateView):
    model = CargoType
    form_class = CargoTypeForm
    template_name = 'freight_quotation/cargo_type_form.html'
    success_url = reverse_lazy('freight_quotation:cargo_type_list')

    def form_valid(self, form):
        messages.success(self.request, 'Cargo type updated successfully!')
        return super().form_valid(form)


class CargoTypeDeleteView(LoginRequiredMixin, DeleteView):
    model = CargoType
    template_name = 'freight_quotation/cargo_type_confirm_delete.html'
    success_url = reverse_lazy('freight_quotation:cargo_type_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Cargo type deleted successfully!')
        return super().delete(request, *args, **kwargs)


# Incoterm Views
class IncotermListView(LoginRequiredMixin, ListView):
    model = Incoterm
    template_name = 'freight_quotation/incoterm_list.html'
    context_object_name = 'incoterms'
    paginate_by = 20


class IncotermCreateView(LoginRequiredMixin, CreateView):
    model = Incoterm
    form_class = IncotermForm
    template_name = 'freight_quotation/incoterm_form.html'
    success_url = reverse_lazy('freight_quotation:incoterm_list')

    def form_valid(self, form):
        messages.success(self.request, 'Incoterm created successfully!')
        return super().form_valid(form)


class IncotermUpdateView(LoginRequiredMixin, UpdateView):
    model = Incoterm
    form_class = IncotermForm
    template_name = 'freight_quotation/incoterm_form.html'
    success_url = reverse_lazy('freight_quotation:incoterm_list')

    def form_valid(self, form):
        messages.success(self.request, 'Incoterm updated successfully!')
        return super().form_valid(form)


class IncotermDeleteView(LoginRequiredMixin, DeleteView):
    model = Incoterm
    template_name = 'freight_quotation/incoterm_confirm_delete.html'
    success_url = reverse_lazy('freight_quotation:incoterm_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Incoterm deleted successfully!')
        return super().delete(request, *args, **kwargs)


# Charge Type Views
class ChargeTypeListView(LoginRequiredMixin, ListView):
    model = ChargeType
    template_name = 'freight_quotation/charge_type_list.html'
    context_object_name = 'charge_types'
    paginate_by = 20


class ChargeTypeCreateView(LoginRequiredMixin, CreateView):
    model = ChargeType
    form_class = ChargeTypeForm
    template_name = 'freight_quotation/charge_type_form.html'
    success_url = reverse_lazy('freight_quotation:charge_type_list')

    def form_valid(self, form):
        messages.success(self.request, 'Charge type created successfully!')
        return super().form_valid(form)


class ChargeTypeUpdateView(LoginRequiredMixin, UpdateView):
    model = ChargeType
    form_class = ChargeTypeForm
    template_name = 'freight_quotation/charge_type_form.html'
    success_url = reverse_lazy('freight_quotation:charge_type_list')

    def form_valid(self, form):
        messages.success(self.request, 'Charge type updated successfully!')
        return super().form_valid(form)


class ChargeTypeDeleteView(LoginRequiredMixin, DeleteView):
    model = ChargeType
    template_name = 'freight_quotation/charge_type_confirm_delete.html'
    success_url = reverse_lazy('freight_quotation:charge_type_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Charge type deleted successfully!')
        return super().delete(request, *args, **kwargs)


# Freight Quotation Views
class FreightQuotationListView(LoginRequiredMixin, ListView):
    model = FreightQuotation
    template_name = 'freight_quotation/quotation_list.html'
    context_object_name = 'quotations'
    paginate_by = 20

    def get_queryset(self):
        queryset = FreightQuotation.objects.select_related('customer', 'cargo_type', 'created_by')
        
        # Apply filters
        form = QuotationSearchForm(self.request.GET)
        if form.is_valid():
            data = form.cleaned_data
            
            if data.get('quotation_number'):
                queryset = queryset.filter(quotation_number__icontains=data['quotation_number'])
            
            if data.get('customer'):
                queryset = queryset.filter(customer=data['customer'])
            
            if data.get('status'):
                queryset = queryset.filter(status=data['status'])
            
            if data.get('mode_of_transport'):
                queryset = queryset.filter(mode_of_transport=data['mode_of_transport'])
            
            if data.get('date_from'):
                queryset = queryset.filter(quotation_date__gte=data['date_from'])
            
            if data.get('date_to'):
                queryset = queryset.filter(quotation_date__lte=data['date_to'])
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = QuotationSearchForm(self.request.GET)
        return context


class FreightQuotationCreateView(LoginRequiredMixin, CreateView):
    model = FreightQuotation
    form_class = FreightQuotationForm
    template_name = 'freight_quotation/quotation_form.html'
    success_url = reverse_lazy('freight_quotation:quotation_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        
        # Create history record
        QuotationHistory.objects.create(
            quotation=form.instance,
            action='created',
            user=self.request.user
        )
        
        messages.success(self.request, 'Quotation created successfully!')
        return response


class FreightQuotationUpdateView(LoginRequiredMixin, UpdateView):
    model = FreightQuotation
    form_class = FreightQuotationForm
    template_name = 'freight_quotation/quotation_form.html'
    success_url = reverse_lazy('freight_quotation:quotation_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Create history record
        QuotationHistory.objects.create(
            quotation=form.instance,
            action='updated',
            user=self.request.user
        )
        
        messages.success(self.request, 'Quotation updated successfully!')
        return response


class FreightQuotationDetailView(LoginRequiredMixin, DetailView):
    model = FreightQuotation
    template_name = 'freight_quotation/quotation_detail.html'
    context_object_name = 'quotation'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['charges'] = self.object.charges.all()
        context['attachments'] = self.object.attachments.all()
        context['history'] = self.object.history.all()[:10]  # Last 10 history records
        context['status_form'] = QuotationStatusForm(initial={'status': self.object.status})
        return context


class FreightQuotationDeleteView(LoginRequiredMixin, DeleteView):
    model = FreightQuotation
    template_name = 'freight_quotation/quotation_confirm_delete.html'
    success_url = reverse_lazy('freight_quotation:quotation_list')

    def delete(self, request, *args, **kwargs):
        # Create history record before deletion
        QuotationHistory.objects.create(
            quotation=self.get_object(),
            action='cancelled',
            user=request.user,
            notes='Quotation deleted'
        )
        
        messages.success(request, 'Quotation deleted successfully!')
        return super().delete(request, *args, **kwargs)


# Quotation Charge Views
@login_required
def add_charge(request, quotation_id):
    quotation = get_object_or_404(FreightQuotation, id=quotation_id)
    
    if request.method == 'POST':
        form = QuotationChargeForm(request.POST)
        if form.is_valid():
            charge = form.save(commit=False)
            charge.quotation = quotation
            charge.save()
            messages.success(request, 'Charge added successfully!')
            return redirect('freight_quotation:quotation_detail', pk=quotation_id)
    else:
        form = QuotationChargeForm()
    
    return render(request, 'freight_quotation/charge_form.html', {
        'form': form,
        'quotation': quotation
    })


@login_required
def edit_charge(request, charge_id):
    charge = get_object_or_404(QuotationCharge, id=charge_id)
    
    if request.method == 'POST':
        form = QuotationChargeForm(request.POST, instance=charge)
        if form.is_valid():
            form.save()
            messages.success(request, 'Charge updated successfully!')
            return redirect('freight_quotation:quotation_detail', pk=charge.quotation.id)
    else:
        form = QuotationChargeForm(instance=charge)
    
    return render(request, 'freight_quotation/charge_form.html', {
        'form': form,
        'quotation': charge.quotation,
        'charge': charge
    })


@login_required
@require_POST
def delete_charge(request, charge_id):
    charge = get_object_or_404(QuotationCharge, id=charge_id)
    quotation_id = charge.quotation.id
    charge.delete()
    messages.success(request, 'Charge deleted successfully!')
    return redirect('freight_quotation:quotation_detail', pk=quotation_id)


# Quotation Attachment Views
@login_required
def add_attachment(request, quotation_id):
    quotation = get_object_or_404(FreightQuotation, id=quotation_id)
    
    if request.method == 'POST':
        form = QuotationAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.quotation = quotation
            attachment.uploaded_by = request.user
            attachment.filename = request.FILES['file'].name
            attachment.save()
            messages.success(request, 'Attachment uploaded successfully!')
            return redirect('freight_quotation:quotation_detail', pk=quotation_id)
    else:
        form = QuotationAttachmentForm()
    
    return render(request, 'freight_quotation/attachment_form.html', {
        'form': form,
        'quotation': quotation
    })


@login_required
@require_POST
def delete_attachment(request, attachment_id):
    attachment = get_object_or_404(QuotationAttachment, id=attachment_id)
    quotation_id = attachment.quotation.id
    attachment.delete()
    messages.success(request, 'Attachment deleted successfully!')
    return redirect('freight_quotation:quotation_detail', pk=quotation_id)


# Quotation Status Management
@login_required
@require_POST
def change_status(request, quotation_id):
    quotation = get_object_or_404(FreightQuotation, id=quotation_id)
    form = QuotationStatusForm(request.POST)
    
    if form.is_valid():
        new_status = form.cleaned_data['status']
        notes = form.cleaned_data.get('notes', '')
        
        # Update status and timestamps
        quotation.status = new_status
        if new_status == 'sent' and not quotation.sent_at:
            quotation.sent_at = timezone.now()
        elif new_status == 'accepted' and not quotation.accepted_at:
            quotation.accepted_at = timezone.now()
        elif new_status == 'rejected' and not quotation.rejected_at:
            quotation.rejected_at = timezone.now()
        
        quotation.save()
        
        # Create history record
        QuotationHistory.objects.create(
            quotation=quotation,
            action=new_status,
            user=request.user,
            notes=notes
        )
        
        messages.success(request, f'Quotation status changed to {new_status.title()}')
    else:
        messages.error(request, 'Invalid status change request')
    
    return redirect('freight_quotation:quotation_detail', pk=quotation_id)


# AJAX Views
@login_required
def get_customer_details(request, customer_id):
    """Get customer details for AJAX requests"""
    customer = get_object_or_404(Customer, id=customer_id)
    return JsonResponse({
        'name': customer.name,
        'email': customer.email,
        'phone': customer.phone,
        'address': customer.address,
        'country': customer.country,
    })


@login_required
def clone_quotation(request, quotation_id):
    """Clone an existing quotation"""
    original = get_object_or_404(FreightQuotation, id=quotation_id)
    
    # Create new quotation with same data
    new_quotation = FreightQuotation.objects.create(
        customer=original.customer,
        mode_of_transport=original.mode_of_transport,
        origin=original.origin,
        destination=original.destination,
        transit_time_estimate=original.transit_time_estimate,
        cargo_type=original.cargo_type,
        cargo_details=original.cargo_details,
        weight=original.weight,
        volume=original.volume,
        packages=original.packages,
        incoterm=original.incoterm,
        remarks=original.remarks,
        internal_notes=f"Cloned from {original.quotation_number}",
        validity_date=original.validity_date,
        currency=original.currency,
        vat_percentage=original.vat_percentage,
        created_by=request.user,
        status='draft'
    )
    
    # Clone charges
    for charge in original.charges.all():
        QuotationCharge.objects.create(
            quotation=new_quotation,
            charge_type=charge.charge_type,
            description=charge.description,
            currency=charge.currency,
            rate=charge.rate,
            unit=charge.unit,
            quantity=charge.quantity
        )
    
    # Create history record
    QuotationHistory.objects.create(
        quotation=new_quotation,
        action='created',
        user=request.user,
        notes=f'Cloned from quotation {original.quotation_number}'
    )
    
    messages.success(request, f'Quotation cloned successfully! New quotation: {new_quotation.quotation_number}')
    return redirect('freight_quotation:quotation_detail', pk=new_quotation.id)


# Dashboard/Statistics Views
@login_required
def quotation_statistics(request):
    """View for quotation statistics and analytics"""
    # Get date range from request
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    queryset = FreightQuotation.objects.all()
    
    if date_from:
        queryset = queryset.filter(quotation_date__gte=date_from)
    if date_to:
        queryset = queryset.filter(quotation_date__lte=date_to)
    
    # Calculate statistics
    total_quotations = queryset.count()
    total_value = queryset.aggregate(total=Sum('grand_total'))['total'] or 0
    
    # Calculate average value
    average_value = total_value / total_quotations if total_quotations > 0 else 0
    
    status_counts = queryset.values('status').annotate(count=Count('id'))
    mode_counts = queryset.values('mode_of_transport').annotate(count=Count('id'))
    
    # Recent quotations
    recent_quotations = queryset.order_by('-created_at')[:10]
    
    context = {
        'total_quotations': total_quotations,
        'total_value': total_value,
        'average_value': average_value,
        'status_counts': status_counts,
        'mode_counts': mode_counts,
        'recent_quotations': recent_quotations,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'freight_quotation/statistics.html', context)
