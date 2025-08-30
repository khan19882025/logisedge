import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.utils import timezone
import json

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import PaymentSource
from .forms import PaymentSourceForm
from .serializers import (
    PaymentSourceSerializer, PaymentSourceCreateSerializer,
    PaymentSourceUpdateSerializer, PaymentSourceListSerializer,
    PaymentSourceDropdownSerializer
)

logger = logging.getLogger(__name__)


# API Viewsets
class PaymentSourceViewSet(viewsets.ModelViewSet):
    """ViewSet for PaymentSource API endpoints"""
    
    permission_classes = [IsAuthenticated]
    queryset = PaymentSource.objects.all()
    
    def get_queryset(self):
        """Filter queryset based on request parameters"""
        queryset = PaymentSource.objects.all()
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active', None)
        active = self.request.query_params.get('active', None)
        
        if is_active is not None:
            if is_active.lower() == 'true':
                queryset = queryset.filter(is_active=True)
            elif is_active.lower() == 'false':
                queryset = queryset.filter(is_active=False)
        elif active is not None:
            if active.lower() == 'true':
                queryset = queryset.filter(active=True)
            elif active.lower() == 'false':
                queryset = queryset.filter(active=False)
        
        # Filter by payment type
        payment_type = self.request.query_params.get('payment_type', None)
        if payment_type:
            queryset = queryset.filter(payment_type=payment_type)
        
        # Filter by source type
        source_type = self.request.query_params.get('source_type', None)
        if source_type:
            queryset = queryset.filter(source_type=source_type)
        
        # Filter by category
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by currency
        currency = self.request.query_params.get('currency', None)
        if currency:
            queryset = queryset.filter(currency_id=currency)
        
        # Filter by linked ledger
        linked_ledger = self.request.query_params.get('linked_ledger', None)
        if linked_ledger:
            queryset = queryset.filter(linked_ledger_id=linked_ledger)
        
        # Filter by linked account (backward compatibility)
        linked_account = self.request.query_params.get('linked_account', None)
        if linked_account:
            queryset = queryset.filter(linked_account_id=linked_account)
        
        # Search by name, code, description, or linked account
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(code__icontains=search) |
                Q(description__icontains=search) |
                Q(linked_ledger__name__icontains=search) |
                Q(linked_ledger__account_code__icontains=search) |
                Q(linked_account__name__icontains=search) |
                Q(linked_account__account_code__icontains=search)
            )
        
        return queryset.order_by('name')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return PaymentSourceCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PaymentSourceUpdateSerializer
        elif self.action == 'list':
            return PaymentSourceListSerializer
        elif self.action == 'dropdown':
            return PaymentSourceDropdownSerializer
        return PaymentSourceSerializer
    
    def perform_create(self, serializer):
        """Set the user when creating"""
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )
    
    def perform_update(self, serializer):
        """Set the user when updating"""
        serializer.save(updated_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get only active payment sources"""
        queryset = self.get_queryset().filter(active=True)
        serializer = PaymentSourceDropdownSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def dropdown(self, request):
        """Get payment sources for dropdown (active only)"""
        queryset = self.get_queryset().filter(active=True)
        serializer = PaymentSourceDropdownSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_payment_type(self, request):
        """Get payment sources filtered by payment type"""
        payment_type = request.query_params.get('type', None)
        if not payment_type:
            return Response(
                {'error': 'Payment type parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(
            payment_type=payment_type,
            active=True
        )
        serializer = PaymentSourceDropdownSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_source_type(self, request):
        """Get payment sources filtered by source type"""
        source_type = request.query_params.get('type', None)
        if not source_type:
            return Response(
                {'error': 'Source type parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(
            source_type=source_type,
            active=True
        )
        serializer = PaymentSourceDropdownSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get payment sources filtered by category"""
        category = request.query_params.get('category', None)
        if not category:
            return Response(
                {'error': 'Category parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(
            category=category,
            active=True
        )
        serializer = PaymentSourceDropdownSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete instead of hard delete"""
        instance = self.get_object()
        instance.soft_delete(user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


# Frontend Template Views
@login_required
def payment_source_list(request):
    """List view for payment sources"""
    payment_sources = PaymentSource.objects.all().order_by('name')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        payment_sources = payment_sources.filter(
            Q(name__icontains=search_query) | 
            Q(code__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(linked_ledger__name__icontains=search_query) |
            Q(linked_account__name__icontains=search_query)
        )
    
    # Filter by payment type
    payment_type_filter = request.GET.get('payment_type', '')
    if payment_type_filter:
        payment_sources = payment_sources.filter(payment_type=payment_type_filter)
    
    # Filter by source type
    source_type_filter = request.GET.get('source_type', '')
    if source_type_filter:
        payment_sources = payment_sources.filter(source_type=source_type_filter)
    
    # Filter by category
    category_filter = request.GET.get('category', '')
    if category_filter:
        payment_sources = payment_sources.filter(category=category_filter)
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        payment_sources = payment_sources.filter(active=True)
    elif status_filter == 'inactive':
        payment_sources = payment_sources.filter(active=False)
    
    context = {
        'payment_sources': payment_sources,
        'search_query': search_query,
        'payment_type_filter': payment_type_filter,
        'source_type_filter': source_type_filter,
        'category_filter': category_filter,
        'status_filter': status_filter,
        'payment_type_choices': PaymentSource.PAYMENT_TYPE_CHOICES,
        'source_type_choices': PaymentSource.SOURCE_TYPE_CHOICES,
        'category_choices': PaymentSource.CATEGORY_CHOICES,
    }
    
    return render(request, 'payment_source/payment_source_list.html', context)


@login_required
def payment_source_create(request):
    """Create new payment source"""
    if request.method == 'POST':
        form = PaymentSourceForm(request.POST)
        if form.is_valid():
            payment_source = form.save(commit=False)
            payment_source.created_by = request.user
            payment_source.updated_by = request.user
            payment_source.save()
            
            messages.success(request, f'Payment source "{payment_source.name}" created successfully!')
            return redirect('payment_source:payment_source_detail', pk=payment_source.pk)
    else:
        form = PaymentSourceForm()
    
    # Get context data for form fields
    try:
        from multi_currency.models import Currency
        currencies = Currency.objects.filter(is_active=True).order_by('code')
    except:
        currencies = []
    
    try:
        from chart_of_accounts.models import ChartOfAccount
        chart_accounts = ChartOfAccount.objects.filter(is_active=True).order_by('account_code', 'name')
    except:
        chart_accounts = []
    
    try:
        from chart_of_accounts.models import ChartOfAccount
        expense_accounts = ChartOfAccount.objects.filter(
            is_active=True,
            account_type__category='EXPENSE'
        ).order_by('account_code', 'name')
    except:
        expense_accounts = []
    
    try:
        from customer.models import Customer, CustomerType
        vendor_type = CustomerType.objects.filter(code='VEN').first()
        if vendor_type:
            vendors = Customer.objects.filter(
                customer_types=vendor_type,
                is_active=True
            ).order_by('customer_name')
        else:
            vendors = []
    except:
        vendors = []
    
    context = {
        'form': form,
        'title': 'Create New Payment Source',
        'is_edit': False,
        'payment_type_choices': PaymentSource.PAYMENT_TYPE_CHOICES,
        'source_type_choices': PaymentSource.SOURCE_TYPE_CHOICES,
        'category_choices': PaymentSource.CATEGORY_CHOICES,
        'currencies': currencies,
        'chart_accounts': chart_accounts,
        'expense_accounts': expense_accounts,
        'vendors': vendors,
    }
    
    return render(request, 'payment_source/payment_source_form.html', context)


@login_required
def payment_source_detail(request, pk):
    """Detail view for payment source"""
    payment_source = get_object_or_404(PaymentSource, pk=pk)
    
    context = {
        'payment_source': payment_source,
    }
    
    return render(request, 'payment_source/payment_source_detail.html', context)


@login_required
def payment_source_update(request, pk):
    """Update payment source"""
    payment_source = get_object_or_404(PaymentSource, pk=pk)
    
    if request.method == 'POST':
        form = PaymentSourceForm(request.POST, instance=payment_source)
        if form.is_valid():
            payment_source = form.save(commit=False)
            payment_source.updated_by = request.user
            payment_source.save()
            
            messages.success(request, f'Payment source "{payment_source.name}" updated successfully!')
            return redirect('payment_source:payment_source_detail', pk=payment_source.pk)
    else:
        form = PaymentSourceForm(instance=payment_source)
    
    # Get context data for form fields
    try:
        from multi_currency.models import Currency
        currencies = Currency.objects.filter(is_active=True).order_by('code')
    except:
        currencies = []
    
    try:
        from chart_of_accounts.models import ChartOfAccount
        chart_accounts = ChartOfAccount.objects.filter(is_active=True).order_by('account_code', 'name')
    except:
        chart_accounts = []
    
    try:
        from chart_of_accounts.models import ChartOfAccount
        expense_accounts = ChartOfAccount.objects.filter(
            is_active=True,
            account_type__category='EXPENSE'
        ).order_by('account_code', 'name')
    except:
        expense_accounts = []
    
    try:
        from customer.models import Customer, CustomerType
        vendor_type = CustomerType.objects.filter(code='VEN').first()
        if vendor_type:
            vendors = Customer.objects.filter(
                customer_types=vendor_type,
                is_active=True
            ).order_by('customer_name')
        else:
            vendors = []
    except:
        vendors = []
    
    context = {
        'form': form,
        'payment_source': payment_source,
        'title': f'Edit Payment Source: {payment_source.name}',
        'is_edit': True,
        'payment_type_choices': PaymentSource.PAYMENT_TYPE_CHOICES,
        'source_type_choices': PaymentSource.SOURCE_TYPE_CHOICES,
        'category_choices': PaymentSource.CATEGORY_CHOICES,
        'currencies': currencies,
        'chart_accounts': chart_accounts,
        'expense_accounts': expense_accounts,
        'vendors': vendors,
    }
    
    return render(request, 'payment_source/payment_source_form.html', context)


@login_required
def payment_source_delete(request, pk):
    """Soft delete payment source"""
    payment_source = get_object_or_404(PaymentSource, pk=pk)
    
    if request.method == 'POST':
        payment_source.soft_delete(user=request.user)
        messages.success(request, f'Payment source "{payment_source.name}" deactivated successfully!')
        return redirect('payment_source:payment_source_list')
    
    context = {
        'payment_source': payment_source,
    }
    
    return render(request, 'payment_source/payment_source_confirm_delete.html', context)


@login_required
def payment_source_restore(request, pk):
    """Restore deactivated payment source"""
    payment_source = get_object_or_404(PaymentSource, pk=pk)
    
    if request.method == 'POST':
        payment_source.restore(user=request.user)
        messages.success(request, f'Payment source "{payment_source.name}" restored successfully!')
        return redirect('payment_source:payment_source_detail', pk=payment_source.pk)
    
    context = {
        'payment_source': payment_source,
    }
    
    return render(request, 'payment_source/payment_source_confirm_restore.html', context)


# AJAX endpoints
@login_required
@require_http_methods(['GET'])
def get_payment_sources_ajax(request):
    """AJAX endpoint to get payment sources for dropdown"""
    payment_type = request.GET.get('payment_type', '')
    source_type = request.GET.get('source_type', '')
    category = request.GET.get('category', '')
    is_active = request.GET.get('is_active', 'true')
    active = request.GET.get('active', 'true')
    
    queryset = PaymentSource.objects.all()
    
    if payment_type:
        queryset = queryset.filter(payment_type=payment_type)
    
    if source_type:
        queryset = queryset.filter(source_type=source_type)
    
    if category:
        queryset = queryset.filter(category=category)
    
    # Use active field if available, fallback to is_active for backward compatibility
    if active.lower() == 'true':
        queryset = queryset.filter(active=True)
    elif is_active.lower() == 'true':
        queryset = queryset.filter(is_active=True)
    
    queryset = queryset.order_by('name')
    
    data = [{
        'id': ps.id,
        'name': ps.name,
        'code': ps.code,
        'payment_type': ps.payment_type,
        'payment_type_display': ps.get_payment_type_display(),
        'source_type': ps.source_type,
        'source_type_display': ps.get_source_type_display(),
        'category': ps.category,
        'category_display': ps.get_category_display(),
        'linked_account_display': ps.linked_account_display
    } for ps in queryset]
    
    return JsonResponse({'results': data})


@login_required
@require_http_methods(['POST'])
@csrf_exempt
def update_payment_source_status_ajax(request):
    """AJAX endpoint to update payment source status"""
    try:
        data = json.loads(request.body)
        payment_source_id = data.get('id')
        new_status = data.get('active') or data.get('is_active')  # Support both fields
        
        if payment_source_id is None or new_status is None:
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        payment_source = get_object_or_404(PaymentSource, pk=payment_source_id)
        payment_source.active = new_status
        payment_source.is_active = new_status  # Keep legacy field in sync
        payment_source.updated_by = request.user
        payment_source.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Payment source status updated successfully!',
            'new_status': payment_source.active
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
