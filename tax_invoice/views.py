from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json

from .models import TaxInvoice, TaxInvoiceItem, TaxInvoiceTemplate, TaxInvoiceSettings, TaxInvoiceExport
from .forms import (
    TaxInvoiceForm, TaxInvoiceItemForm, TaxInvoiceItemFormSet,
    TaxInvoiceTemplateForm, TaxInvoiceSettingsForm,
    TaxInvoiceSearchForm, TaxInvoiceExportForm, TaxInvoiceCalculatorForm
)


@login_required
def tax_invoice_dashboard(request):
    """Dashboard view for Tax Invoice module"""
    # Get summary statistics
    total_invoices = TaxInvoice.objects.count()
    total_amount = TaxInvoice.objects.aggregate(total=Sum('grand_total'))['total'] or Decimal('0.00')
    pending_invoices = TaxInvoice.objects.filter(status='sent').count()
    overdue_invoices = TaxInvoice.objects.filter(status='overdue').count()
    
    # Recent invoices
    recent_invoices = TaxInvoice.objects.order_by('-created_at')[:5]
    
    # Monthly summary (last 12 months)
    monthly_data = []
    for i in range(12):
        date = timezone.now().date() - timedelta(days=30*i)
        month_start = date.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        month_invoices = TaxInvoice.objects.filter(
            invoice_date__gte=month_start,
            invoice_date__lte=month_end
        )
        
        monthly_data.append({
            'month': month_start.strftime('%b %Y'),
            'count': month_invoices.count(),
            'amount': month_invoices.aggregate(total=Sum('grand_total'))['total'] or Decimal('0.00')
        })
    
    monthly_data.reverse()
    
    context = {
        'total_invoices': total_invoices,
        'total_amount': total_amount,
        'pending_invoices': pending_invoices,
        'overdue_invoices': overdue_invoices,
        'recent_invoices': recent_invoices,
        'monthly_data': monthly_data,
    }
    
    return render(request, 'tax_invoice/dashboard.html', context)


class TaxInvoiceListView(LoginRequiredMixin, ListView):
    """List view for TaxInvoice objects"""
    model = TaxInvoice
    template_name = 'tax_invoice/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = TaxInvoice.objects.all()
        
        # Apply search filters
        search = self.request.GET.get('search')
        status = self.request.GET.get('status')
        currency = self.request.GET.get('currency')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        customer_name = self.request.GET.get('customer_name')
        
        if search:
            queryset = queryset.filter(
                Q(invoice_number__icontains=search) |
                Q(customer_name__icontains=search) |
                Q(company_name__icontains=search)
            )
        
        if status:
            queryset = queryset.filter(status=status)
        
        if currency:
            queryset = queryset.filter(currency=currency)
        
        if date_from:
            queryset = queryset.filter(invoice_date__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(invoice_date__lte=date_to)
        
        if customer_name:
            queryset = queryset.filter(customer_name__icontains=customer_name)
        
        return queryset.order_by('-invoice_date', '-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = TaxInvoiceSearchForm(self.request.GET)
        return context


class TaxInvoiceCreateView(LoginRequiredMixin, CreateView):
    """Create view for TaxInvoice objects"""
    model = TaxInvoice
    form_class = TaxInvoiceForm
    template_name = 'tax_invoice/invoice_form.html'
    success_url = reverse_lazy('tax_invoice:invoice_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['item_formset'] = TaxInvoiceItemFormSet(self.request.POST, instance=self.object)
        else:
            context['item_formset'] = TaxInvoiceItemFormSet(instance=self.object)
        
        # Get default settings
        try:
            settings = TaxInvoiceSettings.get_settings()
            context['default_settings'] = settings
        except:
            context['default_settings'] = None
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        item_formset = context['item_formset']
        
        if form.is_valid() and item_formset.is_valid():
            self.object = form.save(commit=False)
            self.object.created_by = self.request.user
            self.object.save()
            
            # Save the formset
            item_formset.instance = self.object
            item_formset.save()
            
            messages.success(self.request, f'Tax Invoice "{self.object.invoice_number}" created successfully.')
            return redirect('tax_invoice:invoice_detail', pk=self.object.pk)
        
        return self.render_to_response(self.get_context_data(form=form))


class TaxInvoiceDetailView(LoginRequiredMixin, DetailView):
    """Detail view for TaxInvoice objects"""
    model = TaxInvoice
    template_name = 'tax_invoice/invoice_detail.html'
    context_object_name = 'invoice'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all()
        context['exports'] = self.object.exports.all()[:5]
        return context


class TaxInvoiceUpdateView(LoginRequiredMixin, UpdateView):
    """Update view for TaxInvoice objects"""
    model = TaxInvoice
    form_class = TaxInvoiceForm
    template_name = 'tax_invoice/invoice_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['item_formset'] = TaxInvoiceItemFormSet(self.request.POST, instance=self.object)
        else:
            context['item_formset'] = TaxInvoiceItemFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        item_formset = context['item_formset']
        
        if form.is_valid() and item_formset.is_valid():
            self.object = form.save(commit=False)
            self.object.updated_by = self.request.user
            self.object.save()
            
            # Save the formset
            item_formset.instance = self.object
            item_formset.save()
            
            messages.success(self.request, f'Tax Invoice "{self.object.invoice_number}" updated successfully.')
            return redirect('tax_invoice:invoice_detail', pk=self.object.pk)
        
        return self.render_to_response(self.get_context_data(form=form))


class TaxInvoiceDeleteView(LoginRequiredMixin, DeleteView):
    """Delete view for TaxInvoice objects"""
    model = TaxInvoice
    template_name = 'tax_invoice/invoice_confirm_delete.html'
    success_url = reverse_lazy('tax_invoice:invoice_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, f'Tax Invoice "{self.get_object().invoice_number}" deleted successfully.')
        return super().delete(request, *args, **kwargs)


@login_required
def tax_invoice_calculator(request):
    """Tax calculation view"""
    if request.method == 'POST':
        form = TaxInvoiceCalculatorForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            vat_rate = form.cleaned_data['vat_rate']
            calculation_type = form.cleaned_data['calculation_type']
            
            if calculation_type == 'exclusive':
                # Add VAT to amount
                vat_amount = amount * (vat_rate / Decimal('100'))
                total_amount = amount + vat_amount
                result = {
                    'original_amount': amount,
                    'vat_rate': vat_rate,
                    'vat_amount': vat_amount,
                    'total_amount': total_amount,
                    'calculation_type': 'VAT Exclusive'
                }
            else:
                # Extract VAT from amount
                vat_amount = amount * (vat_rate / (Decimal('100') + vat_rate))
                taxable_amount = amount - vat_amount
                result = {
                    'original_amount': amount,
                    'vat_rate': vat_rate,
                    'vat_amount': vat_amount,
                    'taxable_amount': taxable_amount,
                    'calculation_type': 'VAT Inclusive'
                }
            
            return JsonResponse(result)
    else:
        form = TaxInvoiceCalculatorForm()
    
    return render(request, 'tax_invoice/calculator.html', {'form': form})


@login_required
def export_tax_invoice(request, pk):
    """Export tax invoice as PDF or Excel"""
    invoice = get_object_or_404(TaxInvoice, pk=pk)
    
    if request.method == 'POST':
        form = TaxInvoiceExportForm(request.POST)
        if form.is_valid():
            export_format = form.cleaned_data['export_format']
            
            # Create export record
            export = TaxInvoiceExport.objects.create(
                invoice=invoice,
                export_format=export_format,
                exported_by=request.user
            )
            
            if export_format == 'pdf':
                # TODO: Implement PDF generation
                messages.success(request, f'PDF export for invoice {invoice.invoice_number} has been queued.')
            elif export_format == 'excel':
                # TODO: Implement Excel generation
                messages.success(request, f'Excel export for invoice {invoice.invoice_number} has been queued.')
            elif export_format == 'email':
                email_to = form.cleaned_data['email_to']
                # TODO: Implement email sending
                messages.success(request, f'Invoice {invoice.invoice_number} has been sent to {email_to}.')
            
            return redirect('tax_invoice:invoice_detail', pk=invoice.pk)
    else:
        form = TaxInvoiceExportForm()
    
    return render(request, 'tax_invoice/export_invoice.html', {
        'invoice': invoice,
        'form': form
    })


@login_required
def tax_invoice_api(request):
    """API endpoint for AJAX requests"""
    if request.method == 'GET':
        action = request.GET.get('action')
        
        if action == 'calculate_tax':
            try:
                amount = Decimal(request.GET.get('amount', '0'))
                vat_rate = Decimal(request.GET.get('vat_rate', '0'))
                calculation_type = request.GET.get('calculation_type', 'exclusive')
                
                if calculation_type == 'exclusive':
                    vat_amount = amount * (vat_rate / Decimal('100'))
                    total_amount = amount + vat_amount
                    result = {
                        'vat_amount': float(vat_amount),
                        'total_amount': float(total_amount)
                    }
                else:
                    vat_amount = amount * (vat_rate / (Decimal('100') + vat_rate))
                    taxable_amount = amount - vat_amount
                    result = {
                        'vat_amount': float(vat_amount),
                        'taxable_amount': float(taxable_amount)
                    }
                
                return JsonResponse(result)
            except (ValueError, TypeError):
                return JsonResponse({'error': 'Invalid input'}, status=400)
        
        elif action == 'get_customer_details':
            # TODO: Implement customer lookup
            return JsonResponse({'error': 'Not implemented'}, status=501)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


# Template views
class TaxInvoiceTemplateListView(LoginRequiredMixin, ListView):
    """List view for TaxInvoiceTemplate objects"""
    model = TaxInvoiceTemplate
    template_name = 'tax_invoice/template_list.html'
    context_object_name = 'templates'
    paginate_by = 20


class TaxInvoiceTemplateCreateView(LoginRequiredMixin, CreateView):
    """Create view for TaxInvoiceTemplate objects"""
    model = TaxInvoiceTemplate
    form_class = TaxInvoiceTemplateForm
    template_name = 'tax_invoice/template_form.html'
    success_url = reverse_lazy('tax_invoice:template_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f'Template "{form.instance.name}" created successfully.')
        return super().form_valid(form)


class TaxInvoiceTemplateDetailView(LoginRequiredMixin, DetailView):
    """Detail view for TaxInvoiceTemplate objects"""
    model = TaxInvoiceTemplate
    template_name = 'tax_invoice/template_detail.html'
    context_object_name = 'template'


class TaxInvoiceTemplateUpdateView(LoginRequiredMixin, UpdateView):
    """Update view for TaxInvoiceTemplate objects"""
    model = TaxInvoiceTemplate
    form_class = TaxInvoiceTemplateForm
    template_name = 'tax_invoice/template_form.html'
    success_url = reverse_lazy('tax_invoice:template_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Template "{form.instance.name}" updated successfully.')
        return super().form_valid(form)


class TaxInvoiceTemplateDeleteView(LoginRequiredMixin, DeleteView):
    """Delete view for TaxInvoiceTemplate objects"""
    model = TaxInvoiceTemplate
    template_name = 'tax_invoice/template_confirm_delete.html'
    success_url = reverse_lazy('tax_invoice:template_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, f'Template "{self.get_object().name}" deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Settings views
@login_required
def tax_invoice_settings(request):
    """Settings view for TaxInvoice module"""
    settings = TaxInvoiceSettings.get_settings()
    
    if request.method == 'POST':
        form = TaxInvoiceSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.instance.updated_by = request.user
            form.save()
            messages.success(request, 'Tax Invoice settings updated successfully.')
            return redirect('tax_invoice:settings')
    else:
        form = TaxInvoiceSettingsForm(instance=settings)
    
    return render(request, 'tax_invoice/settings.html', {
        'form': form,
        'settings': settings
    })
