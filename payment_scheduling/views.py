from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum, F, Count
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.template.loader import render_to_string
from django.http import JsonResponse
from datetime import datetime, date, timedelta
from decimal import Decimal
from django.apps import apps
import json

# Get models dynamically
def get_payment_schedule_model():
    return apps.get_model('payment_scheduling', 'PaymentSchedule')

def get_payment_installment_model():
    return apps.get_model('payment_scheduling', 'PaymentInstallment')

def get_payment_reminder_model():
    return apps.get_model('payment_scheduling', 'PaymentReminder')

def get_payment_schedule_history_model():
    return apps.get_model('payment_scheduling', 'PaymentScheduleHistory')

def get_customer_model():
    return apps.get_model('customer', 'Customer')

# Removed get_supplier_model() as vendor is now CharField


@login_required
def dashboard(request):
    """Payment Scheduling Dashboard"""
    
    PaymentSchedule = get_payment_schedule_model()
    
    # Get summary statistics
    total_schedules = PaymentSchedule.objects.count()
    pending_schedules = PaymentSchedule.objects.filter(status='pending').count()
    overdue_schedules = PaymentSchedule.objects.filter(status='overdue').count()
    partially_paid_schedules = PaymentSchedule.objects.filter(status='partially_paid').count()
    
    # Calculate total outstanding amounts
    outstanding_amount = PaymentSchedule.objects.filter(
        status__in=['pending', 'partially_paid', 'overdue']
    ).aggregate(total=Sum('outstanding_amount'))['total'] or Decimal('0.00')
    
    # Get recent schedules
    recent_schedules = PaymentSchedule.objects.select_related(
        'customer'
    ).order_by('-created_at')[:10]
    
    # Get upcoming payments (next 7 days)
    upcoming_payments = PaymentSchedule.objects.filter(
        due_date__gte=date.today(),
        due_date__lte=date.today() + timedelta(days=7),
        status__in=['pending', 'partially_paid']
    ).order_by('due_date')[:5]
    
    # Get overdue payments
    overdue_payments = PaymentSchedule.objects.filter(
        status='overdue'
    ).order_by('due_date')[:5]
    
    # VAT summary
    vat_summary = PaymentSchedule.objects.filter(
        status__in=['pending', 'partially_paid', 'overdue']
    ).aggregate(
        total_vat_amount=Sum('vat_amount'),
        total_taxable_amount=Sum('total_amount')
    )
    
    context = {
        'total_schedules': total_schedules,
        'pending_schedules': pending_schedules,
        'overdue_schedules': overdue_schedules,
        'partially_paid_schedules': partially_paid_schedules,
        'outstanding_amount': outstanding_amount,
        'recent_schedules': recent_schedules,
        'upcoming_payments': upcoming_payments,
        'overdue_payments': overdue_payments,
        'vat_summary': vat_summary,
    }
    
    return render(request, 'payment_scheduling/dashboard.html', context)


@login_required
def schedule_list(request):
    """List view for payment schedules"""
    
    PaymentSchedule = get_payment_schedule_model()
    
    # Get filter parameters
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    payment_type = request.GET.get('payment_type', '')
    currency = request.GET.get('currency', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    overdue_only = request.GET.get('overdue_only', False)
    
    # Start with all schedules
    schedules = PaymentSchedule.objects.select_related(
        'customer'
    ).prefetch_related('installments')
    
    # Apply filters
    if search:
        schedules = schedules.filter(
            Q(schedule_number__icontains=search) |
            Q(customer__customer_name__icontains=search) |
            Q(vendor__icontains=search) |
            Q(invoice_reference__icontains=search) |
            Q(po_reference__icontains=search)
        )
    
    if status:
        schedules = schedules.filter(status=status)
    
    if payment_type:
        schedules = schedules.filter(payment_type=payment_type)
    
    if currency:
        schedules = schedules.filter(currency=currency)
    
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            schedules = schedules.filter(due_date__gte=date_from)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            schedules = schedules.filter(due_date__lte=date_to)
        except ValueError:
            pass
    
    if overdue_only:
        schedules = schedules.filter(status='overdue')
    
    # Pagination
    paginator = Paginator(schedules, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Search form
    from .forms import PaymentScheduleFilterForm
    filter_form = PaymentScheduleFilterForm(request.GET)
    
    context = {
        'schedules': page_obj,
        'filter_form': filter_form,
    }
    
    return render(request, 'payment_scheduling/schedule_list.html', context)


@login_required
def schedule_detail(request, schedule_id):
    """Detail view for payment schedule"""
    
    PaymentSchedule = get_payment_schedule_model()
    PaymentInstallment = get_payment_installment_model()
    PaymentReminder = get_payment_reminder_model()
    PaymentScheduleHistory = get_payment_schedule_history_model()
    
    schedule = get_object_or_404(
        PaymentSchedule.objects.select_related('customer'),
        id=schedule_id
    )
    
    installments = schedule.installments.all().order_by('installment_number')
    reminders = schedule.reminders.all().order_by('-scheduled_date')
    history = schedule.history.all().order_by('-timestamp')
    
    context = {
        'schedule': schedule,
        'installments': installments,
        'reminders': reminders,
        'history': history,
    }
    
    return render(request, 'payment_scheduling/schedule_detail.html', context)


@login_required
def schedule_create(request):
    """Create new payment schedule"""
    
    PaymentSchedule = get_payment_schedule_model()
    PaymentInstallment = get_payment_installment_model()
    PaymentScheduleHistory = get_payment_schedule_history_model()
    
    if request.method == 'POST':
        from .forms import PaymentScheduleForm
        form = PaymentScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.created_by = request.user
            schedule.save()
            
            # Create installments
            installment_count = form.cleaned_data['installment_count']
            installment_amount = schedule.total_amount / Decimal(installment_count)
            
            for i in range(1, installment_count + 1):
                PaymentInstallment.objects.create(
                    payment_schedule=schedule,
                    installment_number=i,
                    amount=installment_amount,
                    due_date=schedule.due_date
                )
            
            # Create history entry
            PaymentScheduleHistory.objects.create(
                payment_schedule=schedule,
                action='created',
                user=request.user,
                description=f'Payment schedule created with {installment_count} installments'
            )
            
            messages.success(request, f'Payment schedule {schedule.schedule_number} created successfully.')
            return redirect('payment_scheduling:schedule_detail', schedule_id=schedule.id)
    else:
        from .forms import PaymentScheduleForm
        form = PaymentScheduleForm()
    
    context = {
        'form': form,
        'mode': 'create',
    }
    
    return render(request, 'payment_scheduling/schedule_form.html', context)


@login_required
def schedule_update(request, schedule_id):
    """Update payment schedule"""
    
    PaymentSchedule = get_payment_schedule_model()
    PaymentScheduleHistory = get_payment_schedule_history_model()
    
    schedule = get_object_or_404(PaymentSchedule, id=schedule_id)
    
    if request.method == 'POST':
        from .forms import PaymentScheduleForm
        form = PaymentScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            old_status = schedule.status
            schedule = form.save(commit=False)
            schedule.updated_by = request.user
            schedule.save()
            
            # Create history entry
            if old_status != schedule.status:
                PaymentScheduleHistory.objects.create(
                    payment_schedule=schedule,
                    action='status_changed',
                    user=request.user,
                    description=f'Status changed from {old_status} to {schedule.status}',
                    old_values={'status': old_status},
                    new_values={'status': schedule.status}
                )
            
            messages.success(request, f'Payment schedule {schedule.schedule_number} updated successfully.')
            return redirect('payment_scheduling:schedule_detail', schedule_id=schedule.id)
    else:
        from .forms import PaymentScheduleForm
        form = PaymentScheduleForm(instance=schedule)
    
    context = {
        'form': form,
        'schedule': schedule,
        'mode': 'update',
    }
    
    return render(request, 'payment_scheduling/schedule_form.html', context)


@login_required
def schedule_delete(request, schedule_id):
    """Delete payment schedule"""
    
    PaymentSchedule = get_payment_schedule_model()
    schedule = get_object_or_404(PaymentSchedule, id=schedule_id)
    
    if request.method == 'POST':
        schedule_number = schedule.schedule_number
        schedule.delete()
        messages.success(request, f'Payment schedule {schedule_number} deleted successfully.')
        return redirect('payment_scheduling:schedule_list')
    
    context = {
        'schedule': schedule,
    }
    
    return render(request, 'payment_scheduling/schedule_confirm_delete.html', context)


@login_required
@require_POST
def schedule_status_change(request, schedule_id):
    """Change payment schedule status via AJAX"""
    
    PaymentSchedule = get_payment_schedule_model()
    PaymentScheduleHistory = get_payment_schedule_history_model()
    
    try:
        schedule = get_object_or_404(PaymentSchedule, id=schedule_id)
        new_status = request.POST.get('status')
        
        if new_status in dict(PaymentSchedule.STATUS_CHOICES):
            old_status = schedule.status
            schedule.status = new_status
            schedule.save()
            
            # Create history entry
            PaymentScheduleHistory.objects.create(
                payment_schedule=schedule,
                action='status_changed',
                user=request.user,
                description=f'Status changed from {old_status} to {new_status}',
                old_values={'status': old_status},
                new_values={'status': new_status}
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Status changed to {new_status} successfully.'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid status.'
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
def calendar_view(request):
    """Calendar view for payment schedules"""
    
    PaymentSchedule = get_payment_schedule_model()
    
    # Get date range
    year = int(request.GET.get('year', date.today().year))
    month = int(request.GET.get('month', date.today().month))
    
    # Get schedules for the month
    schedules = PaymentSchedule.objects.filter(
        due_date__year=year,
        due_date__month=month
    ).select_related('customer')
    
    # Group schedules by date
    calendar_data = {}
    for schedule in schedules:
        due_date = schedule.due_date.strftime('%Y-%m-%d')
        if due_date not in calendar_data:
            calendar_data[due_date] = []
        calendar_data[due_date].append(schedule)
    
    context = {
        'calendar_data': calendar_data,
        'year': year,
        'month': month,
    }
    
    return render(request, 'payment_scheduling/calendar_view.html', context)


@login_required
def reminder_create(request, schedule_id):
    """Create payment reminder"""
    
    PaymentSchedule = get_payment_schedule_model()
    PaymentReminder = get_payment_reminder_model()
    
    schedule = get_object_or_404(PaymentSchedule, id=schedule_id)
    
    if request.method == 'POST':
        from .forms import PaymentReminderForm
        form = PaymentReminderForm(request.POST)
        if form.is_valid():
            reminder = form.save(commit=False)
            reminder.payment_schedule = schedule
            reminder.save()
            
            messages.success(request, 'Reminder created successfully.')
            return redirect('payment_scheduling:schedule_detail', schedule_id=schedule.id)
    else:
        from .forms import PaymentReminderForm
        form = PaymentReminderForm()
    
    context = {
        'form': form,
        'schedule': schedule,
    }
    
    return render(request, 'payment_scheduling/reminder_form.html', context)


@login_required
def report_list(request):
    """Payment scheduling reports"""
    
    PaymentSchedule = get_payment_schedule_model()
    PaymentInstallment = get_payment_installment_model()
    
    # Get filter parameters
    report_type = request.GET.get('type', 'summary')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    status = request.GET.get('status', '')
    payment_type = request.GET.get('payment_type', '')
    
    schedules = PaymentSchedule.objects.all()
    
    # Apply date filters
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            schedules = schedules.filter(due_date__gte=date_from)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            schedules = schedules.filter(due_date__lte=date_to)
        except ValueError:
            pass
    
    if status:
        schedules = schedules.filter(status=status)
    
    if payment_type:
        schedules = schedules.filter(payment_type=payment_type)
    
    # Generate report data based on type
    if report_type == 'summary':
        report_data = schedules.aggregate(
            total_schedules=Count('id'),
            total_amount=Sum('total_amount'),
            total_vat=Sum('vat_amount'),
            outstanding_amount=Sum('outstanding_amount')
        )
    elif report_type == 'vat_summary':
        report_data = schedules.values('currency').annotate(
            total_taxable=Sum('total_amount'),
            total_vat=Sum('vat_amount'),
            schedule_count=Count('id')
        )
    elif report_type == 'overdue':
        report_data = schedules.filter(status='overdue').values(
            'customer__customer_name'
        ).annotate(
            total_overdue=Sum('outstanding_amount'),
            count=Count('id')
        )
    
    context = {
        'report_type': report_type,
        'report_data': report_data,
        'schedules': schedules,
    }
    
    return render(request, 'payment_scheduling/reports.html', context)


@login_required
@csrf_exempt
def api_schedule_data(request):
    """API endpoint for schedule data (for AJAX requests)"""
    
    PaymentSchedule = get_payment_schedule_model()
    
    if request.method == 'GET':
        schedules = PaymentSchedule.objects.filter(
            status__in=['pending', 'partially_paid', 'overdue']
        ).values(
            'id', 'schedule_number', 'total_amount', 'outstanding_amount', 
            'due_date', 'status', 'currency'
        )
        
        return JsonResponse({'schedules': list(schedules)})
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)


@login_required
def bulk_update(request):
    """Bulk update payment schedules"""
    
    PaymentSchedule = get_payment_schedule_model()
    
    if request.method == 'POST':
        from .forms import PaymentScheduleBulkUpdateForm
        form = PaymentScheduleBulkUpdateForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            schedule_ids = form.cleaned_data['schedule_ids'].split(',')
            
            schedules = PaymentSchedule.objects.filter(id__in=schedule_ids)
            
            if action == 'status':
                new_status = form.cleaned_data['new_status']
                schedules.update(status=new_status)
                messages.success(request, f'Status updated for {schedules.count()} schedules.')
            
            elif action == 'export':
                # Handle export logic
                pass
            
            elif action == 'delete':
                schedules.delete()
                messages.success(request, f'{schedules.count()} schedules deleted successfully.')
            
            return redirect('payment_scheduling:schedule_list')
    else:
        from .forms import PaymentScheduleBulkUpdateForm
        form = PaymentScheduleBulkUpdateForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'payment_scheduling/bulk_update.html', context)
