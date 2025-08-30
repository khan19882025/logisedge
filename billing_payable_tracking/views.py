from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models import Q, Sum, Count
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from datetime import datetime, timedelta
import json

from .models import Vendor, Bill, BillHistory, BillReminder
from .serializers import (
    VendorSerializer, BillSerializer, BillCreateSerializer, BillUpdateSerializer,
    BillActionSerializer, DashboardStatsSerializer, BillFilterSerializer,
    BillHistorySerializer, BillReminderSerializer
)
from .utils import BillProcessor, BillFilters, BillValidators


# REST API ViewSets
class VendorViewSet(viewsets.ModelViewSet):
    """ViewSet for Vendor CRUD operations"""
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter active vendors by default"""
        queryset = Vendor.objects.all()
        active_only = self.request.query_params.get('active_only', 'true')
        if active_only.lower() == 'true':
            queryset = queryset.filter(is_active=True)
        return queryset.order_by('name')


class BillViewSet(viewsets.ModelViewSet):
    """ViewSet for Bill CRUD operations"""
    queryset = Bill.objects.select_related('vendor', 'created_by').prefetch_related('history', 'reminders')
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return BillCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return BillUpdateSerializer
        return BillSerializer
    
    def get_queryset(self):
        """Filter bills based on query parameters"""
        queryset = self.queryset.all()
        
        # Apply filters
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        vendor_filter = self.request.query_params.get('vendor')
        if vendor_filter:
            queryset = queryset.filter(vendor_id=vendor_filter)
        
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(bill_no__icontains=search) |
                Q(vendor__name__icontains=search) |
                Q(notes__icontains=search)
            )
        
        confirmed = self.request.query_params.get('confirmed')
        if confirmed is not None:
            queryset = queryset.filter(confirmed=confirmed.lower() == 'true')
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """Set created_by to current user"""
        # Handle case when user is not authenticated (for testing)
        user = self.request.user if self.request.user.is_authenticated else None
        if user:
            bill = serializer.save(created_by=user)
            # Create history entry
            BillHistory.objects.create(
                bill=bill,
                action='created',
                user=user,
                description=f'Bill created with amount {bill.amount}'
            )
        else:
            # For testing without authentication, create a temporary user or skip history
            from django.contrib.auth.models import User
            temp_user = User.objects.first()  # Use first available user for testing
            bill = serializer.save(created_by=temp_user)
            if temp_user:
                BillHistory.objects.create(
                    bill=bill,
                    action='created',
                    user=temp_user,
                    description=f'Bill created with amount {bill.amount} (test mode)'
                )
    
    def perform_update(self, serializer):
        """Track changes in history and set updated_by"""
        old_bill = self.get_object()
        old_status = old_bill.status
        
        bill = serializer.save(updated_by=self.request.user)
        
        # Create history entry if status changed
        if old_status != bill.status:
            BillHistory.objects.create(
                bill=bill,
                action='updated',
                user=self.request.user,
                description=f'Status changed from {old_status} to {bill.status}',
                old_values={'status': old_status},
                new_values={'status': bill.status}
            )
    
    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """Mark bill as paid"""
        bill = self.get_object()
        serializer = BillActionSerializer(data=request.data)
        
        if serializer.is_valid():
            if bill.status == 'paid':
                return Response(
                    {'error': 'Bill is already marked as paid'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            processor = BillProcessor()
            success = processor.process_bill_payment(
                bill, 
                request.user, 
                serializer.validated_data.get('notes', '')
            )
            
            if success:
                return Response({'message': 'Bill marked as paid successfully'})
            else:
                return Response(
                    {'error': 'Failed to process payment'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm bill"""
        bill = self.get_object()
        serializer = BillActionSerializer(data=request.data)
        
        if serializer.is_valid():
            if bill.confirmed:
                return Response(
                    {'error': 'Bill is already confirmed'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            processor = BillProcessor()
            success = processor.confirm_bill(
                bill, 
                request.user, 
                serializer.validated_data.get('notes', '')
            )
            
            if success:
                return Response({'message': 'Bill confirmed successfully'})
            else:
                return Response(
                    {'error': 'Failed to confirm bill'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Get dashboard statistics"""
        processor = BillProcessor()
        stats = processor.get_dashboard_stats()
        serializer = DashboardStatsSerializer(stats)
        return Response(serializer.data)


# Regular Django Views
@login_required
def dashboard(request):
    """Dashboard view with statistics"""
    from .models import BillAlert
    from django.utils import timezone
    
    processor = BillProcessor()
    stats = processor.get_dashboard_stats()
    
    # Get undismissed alerts for the current user
    alerts = BillAlert.objects.filter(
        user=request.user,
        is_dismissed=False,
        show_date__lte=timezone.now().date()
    ).select_related('bill').order_by('-created_at')
    
    context = {
        'stats': stats,
        'alerts': alerts,
        'page_title': 'Billing & Payable Tracking Dashboard'
    }
    return render(request, 'billing_payable_tracking/dashboard.html', context)


@login_required
@require_http_methods(["POST"])
def dismiss_alert(request, alert_id):
    """AJAX endpoint to dismiss an alert"""
    from django.http import JsonResponse
    from .models import BillAlert
    
    try:
        alert = BillAlert.objects.get(
            id=alert_id,
            user=request.user,
            is_dismissed=False
        )
        alert.dismiss()
        return JsonResponse({
            'success': True,
            'message': 'Alert dismissed successfully'
        })
    except BillAlert.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Alert not found or already dismissed'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
def bill_list(request):
    """List all bills with filtering"""
    bills = Bill.objects.select_related('vendor', 'created_by').all()
    vendors = Vendor.objects.filter(is_active=True).order_by('name')
    
    # Apply filters
    status_filter = request.GET.get('status')
    if status_filter:
        bills = bills.filter(status=status_filter)
    
    vendor_filter = request.GET.get('vendor')
    if vendor_filter:
        bills = bills.filter(vendor_id=vendor_filter)
    
    search = request.GET.get('search')
    if search:
        bills = bills.filter(
            Q(bill_no__icontains=search) |
            Q(vendor__name__icontains=search)
        )
    
    bills = bills.order_by('-created_at')
    
    context = {
        'bills': bills,
        'vendors': vendors,
        'current_filters': {
            'status': status_filter,
            'vendor': vendor_filter,
            'search': search
        },
        'page_title': 'Bills Management'
    }
    return render(request, 'billing_payable_tracking/bill_list.html', context)


@login_required
def bill_create(request):
    """Create new bill"""
    if request.method == 'POST':
        # Handle form submission
        data = {
            'vendor': request.POST.get('vendor'),
            'bill_no': request.POST.get('bill_no'),
            'bill_date': request.POST.get('bill_date'),
            'due_date': request.POST.get('due_date'),
            'amount': request.POST.get('amount'),
            'notes': request.POST.get('notes', '')
        }
        
        validator = BillValidators()
        is_valid, errors = validator.validate_bill_data(data)
        
        if is_valid:
            try:
                vendor = Vendor.objects.get(id=data['vendor'])
                bill = Bill.objects.create(
                    vendor=vendor,
                    bill_no=data['bill_no'],
                    bill_date=datetime.strptime(data['bill_date'], '%Y-%m-%d').date(),
                    due_date=datetime.strptime(data['due_date'], '%Y-%m-%d').date(),
                    amount=data['amount'],
                    notes=data['notes'],
                    created_by=request.user
                )
                
                # Create history entry
                BillHistory.objects.create(
                    bill=bill,
                    action='created',
                    user=request.user,
                    description=f'Bill created with amount {bill.amount}'
                )
                
                messages.success(request, 'Bill created successfully!')
                return redirect('billing_payable_tracking:bill_list')
            except Exception as e:
                messages.error(request, f'Error creating bill: {str(e)}')
        else:
            for field, error_list in errors.items():
                for error in error_list:
                    messages.error(request, f'{field}: {error}')
    
    vendors = Vendor.objects.filter(is_active=True).order_by('name')
    context = {
        'vendors': vendors,
        'page_title': 'Create New Bill'
    }
    return render(request, 'billing_payable_tracking/bill_create.html', context)


@login_required
def bill_detail(request, pk):
    """Bill detail view"""
    bill = get_object_or_404(Bill.objects.select_related('vendor', 'created_by'), pk=pk)
    history = bill.history.select_related('user').order_by('-timestamp')
    reminders = bill.reminders.order_by('-sent_date')
    
    context = {
        'bill': bill,
        'history': history,
        'reminders': reminders,
        'page_title': f'Bill {bill.bill_no}'
    }
    return render(request, 'billing_payable_tracking/bill_detail.html', context)


@login_required
def bill_edit(request, pk):
    """Edit bill"""
    bill = get_object_or_404(Bill, pk=pk)
    
    if request.method == 'POST':
        # Handle form submission
        old_status = bill.status
        
        bill.vendor_id = request.POST.get('vendor')
        bill.bill_no = request.POST.get('bill_no')
        bill.bill_date = datetime.strptime(request.POST.get('bill_date'), '%Y-%m-%d').date()
        bill.due_date = datetime.strptime(request.POST.get('due_date'), '%Y-%m-%d').date()
        bill.amount = request.POST.get('amount')
        bill.notes = request.POST.get('notes', '')
        bill.confirmed = request.POST.get('confirmed') == 'on'
        
        try:
            bill.save()
            
            # Create history entry if status changed
            if old_status != bill.status:
                BillHistory.objects.create(
                    bill=bill,
                    action='updated',
                    user=request.user,
                    description='Bill updated',
                    old_values={'status': old_status},
                    new_values={'status': bill.status}
                )
            
            messages.success(request, 'Bill updated successfully!')
            return redirect('billing_payable_tracking:bill_detail', pk=bill.pk)
        except Exception as e:
            messages.error(request, f'Error updating bill: {str(e)}')
    
    vendors = Vendor.objects.filter(is_active=True).order_by('name')
    context = {
        'bill': bill,
        'vendors': vendors,
        'page_title': f'Edit Bill {bill.bill_no}'
    }
    return render(request, 'billing_payable_tracking/bill_form.html', context)


@login_required
def bill_delete(request, pk):
    """Delete bill"""
    bill = get_object_or_404(Bill, pk=pk)
    
    if request.method == 'POST':
        bill_no = bill.bill_no
        bill.delete()
        messages.success(request, f'Bill {bill_no} deleted successfully!')
        return redirect('billing_payable_tracking:bill_list')
    
    context = {
        'bill': bill,
        'page_title': f'Delete Bill {bill.bill_no}'
    }
    return render(request, 'billing_payable_tracking/bill_confirm_delete.html', context)


# AJAX Views
@login_required
@require_http_methods(["POST"])
def mark_bill_paid(request, bill_id):
    """AJAX endpoint to mark bill as paid"""
    try:
        bill = get_object_or_404(Bill, pk=bill_id)
        
        if bill.status == 'paid':
            return JsonResponse({
                'success': False,
                'message': 'Bill is already marked as paid'
            })
        
        data = json.loads(request.body) if request.body else {}
        notes = data.get('notes', '')
        
        processor = BillProcessor()
        success = processor.process_bill_payment(bill, request.user, notes)
        
        if success:
            return JsonResponse({
                'success': True,
                'message': 'Bill marked as paid successfully',
                'new_status': bill.status
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to process payment'
            })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def confirm_bill(request, bill_id):
    """AJAX endpoint to confirm bill"""
    try:
        bill = get_object_or_404(Bill, pk=bill_id)
        
        if bill.confirmed:
            return JsonResponse({
                'success': False,
                'message': 'Bill is already confirmed'
            })
        
        data = json.loads(request.body) if request.body else {}
        notes = data.get('notes', '')
        
        processor = BillProcessor()
        success = processor.confirm_bill(bill, request.user, notes)
        
        if success:
            return JsonResponse({
                'success': True,
                'message': 'Bill confirmed successfully',
                'confirmed': bill.confirmed
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to confirm bill'
            })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        })


@login_required
def get_dashboard_stats(request):
    """AJAX endpoint for dashboard statistics"""
    try:
        processor = BillProcessor()
        stats = processor.get_dashboard_stats()
        return JsonResponse({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        })


@login_required
def filter_bills(request):
    """AJAX endpoint for filtering bills"""
    try:
        filters = BillFilters()
        bills_queryset = filters.filter_bills(request.GET)
        
        bills_data = []
        for bill in bills_queryset:
            bills_data.append({
                'id': bill.id,
                'vendor_name': bill.vendor.name,
                'bill_no': bill.bill_no,
                'bill_date': bill.bill_date.strftime('%Y-%m-%d'),
                'due_date': bill.due_date.strftime('%Y-%m-%d'),
                'amount': str(bill.amount),
                'status': bill.status,
                'confirmed': bill.confirmed,
                'created_at': bill.created_at.strftime('%Y-%m-%d %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'data': bills_data,
            'count': len(bills_data)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        })


# Vendor Views
@login_required
def vendor_list(request):
    """List all vendors"""
    vendors = Vendor.objects.all().order_by('name')
    
    search = request.GET.get('search')
    if search:
        vendors = vendors.filter(
            Q(name__icontains=search) |
            Q(email__icontains=search) |
            Q(contact_person__icontains=search)
        )
    
    context = {
        'vendors': vendors,
        'search': search,
        'page_title': 'Vendors Management'
    }
    return render(request, 'billing_payable_tracking/vendor_list.html', context)


@login_required
def vendor_create(request):
    """Create new vendor"""
    if request.method == 'POST':
        try:
            vendor = Vendor.objects.create(
                name=request.POST.get('name'),
                email=request.POST.get('email', ''),
                phone=request.POST.get('phone', ''),
                address=request.POST.get('address', ''),
                contact_person=request.POST.get('contact_person', ''),
                payment_terms=int(request.POST.get('payment_terms', 30))
            )
            messages.success(request, 'Vendor created successfully!')
            return redirect('billing_payable_tracking:vendor_list')
        except Exception as e:
            messages.error(request, f'Error creating vendor: {str(e)}')
    
    context = {
        'page_title': 'Create New Vendor'
    }
    return render(request, 'billing_payable_tracking/vendor_create.html', context)


@login_required
def vendor_detail(request, pk):
    """Vendor detail view"""
    vendor = get_object_or_404(Vendor, pk=pk)
    bills = vendor.bills.all().order_by('-created_at')[:10]  # Recent 10 bills
    
    context = {
        'vendor': vendor,
        'bills': bills,
        'page_title': f'Vendor: {vendor.name}'
    }
    return render(request, 'billing_payable_tracking/vendor_detail.html', context)


@login_required
def vendor_edit(request, pk):
    """Edit vendor"""
    vendor = get_object_or_404(Vendor, pk=pk)
    
    if request.method == 'POST':
        try:
            vendor.name = request.POST.get('name')
            vendor.email = request.POST.get('email', '')
            vendor.phone = request.POST.get('phone', '')
            vendor.address = request.POST.get('address', '')
            vendor.contact_person = request.POST.get('contact_person', '')
            vendor.payment_terms = int(request.POST.get('payment_terms', 30))
            vendor.is_active = request.POST.get('is_active') == 'on'
            vendor.save()
            
            messages.success(request, 'Vendor updated successfully!')
            return redirect('billing_payable_tracking:vendor_detail', pk=vendor.pk)
        except Exception as e:
            messages.error(request, f'Error updating vendor: {str(e)}')
    
    context = {
        'vendor': vendor,
        'page_title': f'Edit Vendor: {vendor.name}'
    }
    return render(request, 'billing_payable_tracking/vendor_form.html', context)


@login_required
def vendor_delete(request, pk):
    """Delete vendor"""
    vendor = get_object_or_404(Vendor, pk=pk)
    
    if request.method == 'POST':
        vendor_name = vendor.name
        vendor.delete()
        messages.success(request, f'Vendor {vendor_name} deleted successfully!')
        return redirect('billing_payable_tracking:vendor_list')
    
    context = {
        'vendor': vendor,
        'page_title': f'Delete Vendor: {vendor.name}'
    }
    return render(request, 'billing_payable_tracking/vendor_confirm_delete.html', context)


@login_required
def reports(request):
    """Reports view"""
    context = {
        'page_title': 'Billing & Payable Reports'
    }
    return render(request, 'billing_payable_tracking/reports.html', context)
