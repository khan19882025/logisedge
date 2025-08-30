from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from django.utils import timezone
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from decimal import Decimal
from datetime import datetime, timedelta

from .models import (
    TaxJurisdiction, TaxType, TaxRate, ProductTaxCategory,
    CustomerTaxProfile, SupplierTaxProfile, TaxTransaction, 
    TaxSettingsAuditLog, VATReport
)
from .forms import (
    TaxJurisdictionForm, TaxTypeForm, TaxRateForm, ProductTaxCategoryForm,
    CustomerTaxProfileForm, SupplierTaxProfileForm, VATReportForm,
    TaxCalculationForm, TaxSettingsSearchForm, VATReportGenerationForm
)


@login_required
def tax_dashboard(request):
    """Tax Settings Dashboard"""
    # Get summary statistics
    total_jurisdictions = TaxJurisdiction.objects.filter(is_active=True).count()
    total_tax_types = TaxType.objects.filter(is_active=True).count()
    total_tax_rates = TaxRate.objects.filter(is_active=True).count()
    total_product_categories = ProductTaxCategory.objects.filter(is_active=True).count()
    total_customer_profiles = CustomerTaxProfile.objects.count()
    total_supplier_profiles = SupplierTaxProfile.objects.count()
    
    # Get current tax rates
    current_tax_rates = TaxRate.objects.filter(is_active=True).select_related('tax_type', 'jurisdiction')[:5]
    
    # Get recent transactions
    recent_transactions = TaxTransaction.objects.select_related('tax_rate', 'customer').order_by('-created_at')[:10]
    
    # Get VAT summary for current month
    current_month = timezone.now().replace(day=1)
    month_transactions = TaxTransaction.objects.filter(
        document_date__gte=current_month
    ).aggregate(
        total_sales=Sum('taxable_amount', filter=Q(transaction_type='sale')),
        total_purchases=Sum('taxable_amount', filter=Q(transaction_type='purchase')),
        total_sales_tax=Sum('tax_amount', filter=Q(transaction_type='sale')),
        total_purchase_tax=Sum('tax_amount', filter=Q(transaction_type='purchase'))
    )
    
    # Get recent audit logs
    recent_audit_logs = TaxSettingsAuditLog.objects.select_related('user').order_by('-timestamp')[:5]
    
    context = {
        'total_jurisdictions': total_jurisdictions,
        'total_tax_types': total_tax_types,
        'total_tax_rates': total_tax_rates,
        'total_product_categories': total_product_categories,
        'total_customer_profiles': total_customer_profiles,
        'total_supplier_profiles': total_supplier_profiles,
        'current_tax_rates': current_tax_rates,
        'recent_transactions': recent_transactions,
        'month_transactions': month_transactions,
        'recent_audit_logs': recent_audit_logs,
    }
    
    return render(request, 'tax_settings/dashboard.html', context)


# Tax Jurisdiction Views
class TaxJurisdictionListView(LoginRequiredMixin, ListView):
    model = TaxJurisdiction
    template_name = 'tax_settings/jurisdiction_list.html'
    context_object_name = 'jurisdictions'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = TaxJurisdiction.objects.select_related('parent_jurisdiction').all()
        
        # Apply search filters
        search = self.request.GET.get('search')
        jurisdiction_type = self.request.GET.get('jurisdiction_type')
        is_active = self.request.GET.get('is_active')
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(code__icontains=search)
            )
        
        if jurisdiction_type:
            queryset = queryset.filter(jurisdiction_type=jurisdiction_type)
        
        if is_active:
            queryset = queryset.filter(is_active=is_active == 'True')
        
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['jurisdiction_type'] = self.request.GET.get('jurisdiction_type', '')
        context['is_active'] = self.request.GET.get('is_active', '')
        return context


class TaxJurisdictionCreateView(LoginRequiredMixin, CreateView):
    model = TaxJurisdiction
    form_class = TaxJurisdictionForm
    template_name = 'tax_settings/jurisdiction_form.html'
    success_url = reverse_lazy('tax_settings:jurisdiction_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Tax jurisdiction created successfully.')
        return super().form_valid(form)


class TaxJurisdictionDetailView(LoginRequiredMixin, DetailView):
    model = TaxJurisdiction
    template_name = 'tax_settings/jurisdiction_detail.html'
    context_object_name = 'jurisdiction'


class TaxJurisdictionUpdateView(LoginRequiredMixin, UpdateView):
    model = TaxJurisdiction
    form_class = TaxJurisdictionForm
    template_name = 'tax_settings/jurisdiction_form.html'
    success_url = reverse_lazy('tax_settings:jurisdiction_list')
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Tax jurisdiction updated successfully.')
        return super().form_valid(form)


class TaxJurisdictionDeleteView(LoginRequiredMixin, DeleteView):
    model = TaxJurisdiction
    template_name = 'tax_settings/jurisdiction_confirm_delete.html'
    success_url = reverse_lazy('tax_settings:jurisdiction_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Tax jurisdiction deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Tax Type Views
class TaxTypeListView(LoginRequiredMixin, ListView):
    model = TaxType
    template_name = 'tax_settings/tax_type_list.html'
    context_object_name = 'tax_types'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = TaxType.objects.all()
        
        # Apply search filters
        search = self.request.GET.get('search')
        tax_type = self.request.GET.get('tax_type')
        is_active = self.request.GET.get('is_active')
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(code__icontains=search)
            )
        
        if tax_type:
            queryset = queryset.filter(tax_type=tax_type)
        
        if is_active:
            queryset = queryset.filter(is_active=is_active == 'True')
        
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['tax_type'] = self.request.GET.get('tax_type', '')
        context['is_active'] = self.request.GET.get('is_active', '')
        return context


class TaxTypeCreateView(LoginRequiredMixin, CreateView):
    model = TaxType
    form_class = TaxTypeForm
    template_name = 'tax_settings/tax_type_form.html'
    success_url = reverse_lazy('tax_settings:tax_type_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Tax type created successfully.')
        return super().form_valid(form)


class TaxTypeDetailView(LoginRequiredMixin, DetailView):
    model = TaxType
    template_name = 'tax_settings/tax_type_detail.html'
    context_object_name = 'tax_type'


class TaxTypeUpdateView(LoginRequiredMixin, UpdateView):
    model = TaxType
    form_class = TaxTypeForm
    template_name = 'tax_settings/tax_type_form.html'
    success_url = reverse_lazy('tax_settings:tax_type_list')
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Tax type updated successfully.')
        return super().form_valid(form)


class TaxTypeDeleteView(LoginRequiredMixin, DeleteView):
    model = TaxType
    template_name = 'tax_settings/tax_type_confirm_delete.html'
    success_url = reverse_lazy('tax_settings:tax_type_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Tax type deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Tax Rate Views
class TaxRateListView(LoginRequiredMixin, ListView):
    model = TaxRate
    template_name = 'tax_settings/tax_rate_list.html'
    context_object_name = 'tax_rates'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = TaxRate.objects.select_related('tax_type', 'jurisdiction').all()
        
        # Apply search filters
        search = self.request.GET.get('search')
        tax_type = self.request.GET.get('tax_type')
        jurisdiction = self.request.GET.get('jurisdiction')
        is_active = self.request.GET.get('is_active')
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(tax_type__name__icontains=search) |
                Q(jurisdiction__name__icontains=search)
            )
        
        if tax_type:
            queryset = queryset.filter(tax_type_id=tax_type)
        
        if jurisdiction:
            queryset = queryset.filter(jurisdiction_id=jurisdiction)
        
        if is_active:
            queryset = queryset.filter(is_active=is_active == 'True')
        
        return queryset.order_by('-effective_from', 'name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['tax_type'] = self.request.GET.get('tax_type', '')
        context['jurisdiction'] = self.request.GET.get('jurisdiction', '')
        context['is_active'] = self.request.GET.get('is_active', '')
        context['tax_types'] = TaxType.objects.filter(is_active=True)
        context['jurisdictions'] = TaxJurisdiction.objects.filter(is_active=True)
        return context


class TaxRateCreateView(LoginRequiredMixin, CreateView):
    model = TaxRate
    form_class = TaxRateForm
    template_name = 'tax_settings/tax_rate_form.html'
    success_url = reverse_lazy('tax_settings:tax_rate_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Tax rate created successfully.')
        return super().form_valid(form)


class TaxRateDetailView(LoginRequiredMixin, DetailView):
    model = TaxRate
    template_name = 'tax_settings/tax_rate_detail.html'
    context_object_name = 'tax_rate'


class TaxRateUpdateView(LoginRequiredMixin, UpdateView):
    model = TaxRate
    form_class = TaxRateForm
    template_name = 'tax_settings/tax_rate_form.html'
    success_url = reverse_lazy('tax_settings:tax_rate_list')
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Tax rate updated successfully.')
        return super().form_valid(form)


class TaxRateDeleteView(LoginRequiredMixin, DeleteView):
    model = TaxRate
    template_name = 'tax_settings/tax_rate_confirm_delete.html'
    success_url = reverse_lazy('tax_settings:tax_rate_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Tax rate deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Product Tax Category Views
class ProductTaxCategoryListView(LoginRequiredMixin, ListView):
    model = ProductTaxCategory
    template_name = 'tax_settings/product_category_list.html'
    context_object_name = 'categories'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = ProductTaxCategory.objects.select_related('default_tax_rate').all()
        
        # Apply search filters
        search = self.request.GET.get('search')
        is_active = self.request.GET.get('is_active')
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(code__icontains=search)
            )
        
        if is_active:
            queryset = queryset.filter(is_active=is_active == 'True')
        
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['is_active'] = self.request.GET.get('is_active', '')
        return context


class ProductTaxCategoryCreateView(LoginRequiredMixin, CreateView):
    model = ProductTaxCategory
    form_class = ProductTaxCategoryForm
    template_name = 'tax_settings/product_category_form.html'
    success_url = reverse_lazy('tax_settings:product_category_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Product tax category created successfully.')
        return super().form_valid(form)


class ProductTaxCategoryDetailView(LoginRequiredMixin, DetailView):
    model = ProductTaxCategory
    template_name = 'tax_settings/product_category_detail.html'
    context_object_name = 'category'


class ProductTaxCategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = ProductTaxCategory
    form_class = ProductTaxCategoryForm
    template_name = 'tax_settings/product_category_form.html'
    success_url = reverse_lazy('tax_settings:product_category_list')
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Product tax category updated successfully.')
        return super().form_valid(form)


class ProductTaxCategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = ProductTaxCategory
    template_name = 'tax_settings/product_category_confirm_delete.html'
    success_url = reverse_lazy('tax_settings:product_category_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Product tax category deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Customer Tax Profile Views
class CustomerTaxProfileListView(LoginRequiredMixin, ListView):
    model = CustomerTaxProfile
    template_name = 'tax_settings/customer_profile_list.html'
    context_object_name = 'profiles'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = CustomerTaxProfile.objects.select_related('customer', 'default_tax_rate').all()
        
        # Apply search filters
        search = self.request.GET.get('search')
        is_tax_exempt = self.request.GET.get('is_tax_exempt')
        
        if search:
            queryset = queryset.filter(
                Q(customer__name__icontains=search) |
                Q(tax_registration_number__icontains=search) |
                Q(tax_exemption_number__icontains=search)
            )
        
        if is_tax_exempt:
            queryset = queryset.filter(is_tax_exempt=is_tax_exempt == 'True')
        
        return queryset.order_by('customer__name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['is_tax_exempt'] = self.request.GET.get('is_tax_exempt', '')
        return context


class CustomerTaxProfileCreateView(LoginRequiredMixin, CreateView):
    model = CustomerTaxProfile
    form_class = CustomerTaxProfileForm
    template_name = 'tax_settings/customer_profile_form.html'
    success_url = reverse_lazy('tax_settings:customer_profile_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Customer tax profile created successfully.')
        return super().form_valid(form)


class CustomerTaxProfileDetailView(LoginRequiredMixin, DetailView):
    model = CustomerTaxProfile
    template_name = 'tax_settings/customer_profile_detail.html'
    context_object_name = 'profile'


class CustomerTaxProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = CustomerTaxProfile
    form_class = CustomerTaxProfileForm
    template_name = 'tax_settings/customer_profile_form.html'
    success_url = reverse_lazy('tax_settings:customer_profile_list')
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Customer tax profile updated successfully.')
        return super().form_valid(form)


class CustomerTaxProfileDeleteView(LoginRequiredMixin, DeleteView):
    model = CustomerTaxProfile
    template_name = 'tax_settings/customer_profile_confirm_delete.html'
    success_url = reverse_lazy('tax_settings:customer_profile_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Customer tax profile deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Supplier Tax Profile Views
class SupplierTaxProfileListView(LoginRequiredMixin, ListView):
    model = SupplierTaxProfile
    template_name = 'tax_settings/supplier_profile_list.html'
    context_object_name = 'profiles'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = SupplierTaxProfile.objects.select_related('default_tax_rate').all()
        
        # Apply search filters
        search = self.request.GET.get('search')
        is_tax_exempt = self.request.GET.get('is_tax_exempt')
        
        if search:
            queryset = queryset.filter(
                Q(supplier_name__icontains=search) |
                Q(supplier_code__icontains=search) |
                Q(tax_registration_number__icontains=search) |
                Q(tax_exemption_number__icontains=search)
            )
        
        if is_tax_exempt:
            queryset = queryset.filter(is_tax_exempt=is_tax_exempt == 'True')
        
        return queryset.order_by('supplier_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['is_tax_exempt'] = self.request.GET.get('is_tax_exempt', '')
        return context


class SupplierTaxProfileCreateView(LoginRequiredMixin, CreateView):
    model = SupplierTaxProfile
    form_class = SupplierTaxProfileForm
    template_name = 'tax_settings/supplier_profile_form.html'
    success_url = reverse_lazy('tax_settings:supplier_profile_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Supplier tax profile created successfully.')
        return super().form_valid(form)


class SupplierTaxProfileDetailView(LoginRequiredMixin, DetailView):
    model = SupplierTaxProfile
    template_name = 'tax_settings/supplier_profile_detail.html'
    context_object_name = 'profile'


class SupplierTaxProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = SupplierTaxProfile
    form_class = SupplierTaxProfileForm
    template_name = 'tax_settings/supplier_profile_form.html'
    success_url = reverse_lazy('tax_settings:supplier_profile_list')
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Supplier tax profile updated successfully.')
        return super().form_valid(form)


class SupplierTaxProfileDeleteView(LoginRequiredMixin, DeleteView):
    model = SupplierTaxProfile
    template_name = 'tax_settings/supplier_profile_confirm_delete.html'
    success_url = reverse_lazy('tax_settings:supplier_profile_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Supplier tax profile deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Tax Calculation View
@login_required
def tax_calculator(request):
    """Tax Calculator View"""
    if request.method == 'POST':
        form = TaxCalculationForm(request.POST)
        if form.is_valid():
            calculation_result = form.calculate_tax()
            return render(request, 'tax_settings/tax_calculator.html', {
                'form': form,
                'calculation_result': calculation_result
            })
    else:
        form = TaxCalculationForm()
    
    return render(request, 'tax_settings/tax_calculator.html', {'form': form})


# VAT Report Views
class VATReportListView(LoginRequiredMixin, ListView):
    model = VATReport
    template_name = 'tax_settings/vat_report_list.html'
    context_object_name = 'reports'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = VATReport.objects.select_related('created_by', 'filed_by').all()
        
        search = self.request.GET.get('search')
        report_period = self.request.GET.get('report_period')
        is_filed = self.request.GET.get('is_filed')
        
        if search:
            queryset = queryset.filter(report_name__icontains=search)
        
        if report_period:
            queryset = queryset.filter(report_period=report_period)
        
        if is_filed:
            queryset = queryset.filter(is_filed=is_filed == 'True')
        
        return queryset.order_by('-start_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = TaxSettingsSearchForm(self.request.GET)
        return context


class VATReportCreateView(LoginRequiredMixin, CreateView):
    model = VATReport
    form_class = VATReportForm
    template_name = 'tax_settings/vat_report_form.html'
    success_url = reverse_lazy('tax_settings:vat_report_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'VAT report created successfully.')
        return super().form_valid(form)


class VATReportUpdateView(LoginRequiredMixin, UpdateView):
    model = VATReport
    form_class = VATReportForm
    template_name = 'tax_settings/vat_report_form.html'
    success_url = reverse_lazy('tax_settings:vat_report_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'VAT report updated successfully.')
        return super().form_valid(form)


class VATReportDeleteView(LoginRequiredMixin, DeleteView):
    model = VATReport
    template_name = 'tax_settings/vat_report_confirm_delete.html'
    success_url = reverse_lazy('tax_settings:vat_report_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'VAT report deleted successfully.')
        return super().delete(request, *args, **kwargs)


@login_required
def generate_vat_report(request):
    """Generate VAT Report View"""
    if request.method == 'POST':
        form = VATReportGenerationForm(request.POST)
        if form.is_valid():
            # Generate VAT report based on form data
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            currency = form.cleaned_data['currency']
            
            # Get transactions for the period
            transactions = TaxTransaction.objects.filter(
                document_date__gte=start_date,
                document_date__lte=end_date,
                currency=currency
            )
            
            # Calculate totals
            sales_transactions = transactions.filter(transaction_type='sale')
            purchase_transactions = transactions.filter(transaction_type='purchase')
            
            total_sales = sales_transactions.aggregate(total=Sum('taxable_amount'))['total'] or 0
            total_purchases = purchase_transactions.aggregate(total=Sum('taxable_amount'))['total'] or 0
            total_sales_tax = sales_transactions.aggregate(total=Sum('tax_amount'))['total'] or 0
            total_purchase_tax = purchase_transactions.aggregate(total=Sum('tax_amount'))['total'] or 0
            
            net_vat_payable = total_sales_tax - total_purchase_tax
            
            # Create VAT report
            report_name = f"VAT Report - {start_date} to {end_date}"
            vat_report = VATReport.objects.create(
                report_name=report_name,
                report_period=form.cleaned_data['report_period'],
                start_date=start_date,
                end_date=end_date,
                total_sales=total_sales,
                total_purchases=total_purchases,
                total_sales_tax=total_sales_tax,
                total_purchase_tax=total_purchase_tax,
                net_vat_payable=net_vat_payable,
                currency=currency,
                created_by=request.user
            )
            
            messages.success(request, f'VAT report "{report_name}" generated successfully.')
            return redirect('tax_settings:vat_report_detail', pk=vat_report.pk)
    else:
        form = VATReportGenerationForm()
    
    return render(request, 'tax_settings/generate_vat_report.html', {'form': form})


class VATReportDetailView(LoginRequiredMixin, DetailView):
    model = VATReport
    template_name = 'tax_settings/vat_report_detail.html'
    context_object_name = 'report'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get detailed transactions for this report
        transactions = TaxTransaction.objects.filter(
            document_date__gte=self.object.start_date,
            document_date__lte=self.object.end_date,
            currency=self.object.currency
        ).select_related('tax_rate', 'customer', 'supplier').order_by('document_date')
        
        context['transactions'] = transactions
        return context


# Audit Log Views
class AuditLogListView(LoginRequiredMixin, ListView):
    model = TaxSettingsAuditLog
    template_name = 'tax_settings/audit_log_list.html'
    context_object_name = 'audit_logs'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = TaxSettingsAuditLog.objects.select_related('user').all()
        
        search = self.request.GET.get('search')
        action = self.request.GET.get('action')
        model_name = self.request.GET.get('model_name')
        
        if search:
            queryset = queryset.filter(
                Q(model_name__icontains=search) |
                Q(field_name__icontains=search) |
                Q(user__username__icontains=search)
            )
        
        if action:
            queryset = queryset.filter(action=action)
        
        if model_name:
            queryset = queryset.filter(model_name=model_name)
        
        return queryset.order_by('-timestamp')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = TaxSettingsSearchForm(self.request.GET)
        return context


# API Views for AJAX
@login_required
@csrf_exempt
def get_tax_rates_by_jurisdiction(request):
    """Get tax rates for a specific jurisdiction"""
    jurisdiction_id = request.GET.get('jurisdiction_id')
    if jurisdiction_id:
        tax_rates = TaxRate.objects.filter(
            jurisdiction_id=jurisdiction_id,
            is_active=True
        ).select_related('tax_type')
        
        data = [{
            'id': str(rate.id),
            'name': rate.name,
            'rate_percentage': float(rate.rate_percentage),
            'tax_type': rate.tax_type.name,
            'rounding_method': rate.rounding_method
        } for rate in tax_rates]
        
        return JsonResponse({'tax_rates': data})
    
    return JsonResponse({'tax_rates': []})


@login_required
@csrf_exempt
def calculate_tax_ajax(request):
    """Calculate tax amount via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            taxable_amount = Decimal(data.get('taxable_amount', 0))
            tax_rate_id = data.get('tax_rate_id')
            
            if tax_rate_id:
                tax_rate = TaxRate.objects.get(id=tax_rate_id)
                tax_amount = (taxable_amount * tax_rate.rate_percentage) / 100
                
                # Apply rounding
                if tax_rate.rounding_method == 'nearest_001':
                    tax_amount = round(tax_amount, 2)
                elif tax_rate.rounding_method == 'nearest_005':
                    tax_amount = round(tax_amount * 20) / 20
                elif tax_rate.rounding_method == 'nearest_010':
                    tax_amount = round(tax_amount * 10) / 10
                elif tax_rate.rounding_method == 'round_up':
                    tax_amount = (tax_amount * 100).__ceil__() / 100
                elif tax_rate.rounding_method == 'round_down':
                    tax_amount = (tax_amount * 100).__floor__() / 100
                
                total_amount = taxable_amount + tax_amount
                
                return JsonResponse({
                    'success': True,
                    'tax_amount': float(tax_amount),
                    'total_amount': float(total_amount),
                    'tax_rate_name': tax_rate.name
                })
        
        except (json.JSONDecodeError, TaxRate.DoesNotExist, ValueError) as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
def export_tax_data(request):
    """Export tax data to CSV"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="tax_data.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Tax Rate Name', 'Rate %', 'Tax Type', 'Jurisdiction', 'Effective From', 'Effective To', 'Status'])
    
    tax_rates = TaxRate.objects.select_related('tax_type', 'jurisdiction').all()
    for rate in tax_rates:
        writer.writerow([
            rate.name,
            rate.rate_percentage,
            rate.tax_type.name,
            rate.jurisdiction.name,
            rate.effective_from,
            rate.effective_to or 'No end date',
            'Active' if rate.is_active else 'Inactive'
        ])
    
    return response
