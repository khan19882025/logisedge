from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q
from django.urls import reverse
from django.http import JsonResponse
from datetime import date, timedelta
from .models import ActivityLog

# Import models for activity tracking
from invoice.models import Invoice
from quotation.models import Quotation
from grn.models import GRN
from job.models import Job
from customer.models import Customer
from items.models import Item
from ledger.models import Ledger
from general_journal.models import JournalEntry
from delivery_order.models import DeliveryOrder
from dispatchnote.models import DispatchNote
from crossstuffing.models import CrossStuffing
from documentation.models import Documentation
from putaways.models import Putaway
from facility.models import Facility, FacilityLocation
from chart_of_accounts.models import ChartOfAccount
from fiscal_year.models import FiscalYear, FiscalPeriod
from multi_currency.models import Currency, ExchangeRate
from salesman.models import Salesman
from service.models import Service
from port.models import Port
from credit_note.models import CreditNote
from debit_note.models import DebitNote
from customer_payments.models import CustomerPayment
from supplier_bills.models import SupplierBill
from supplier_payments.models import SupplierPayment
from dunning_letters.models import DunningLetter
# from accounts_receivable_aging.models import AccountsReceivableAging  # Model not implemented yet
# from rf_scanner.models import ScanRecord, ScanSession  # Models not implemented yet


@login_required
def dashboard(request):
    """Dashboard view with real daily activity data"""
    
    # Get selected date from request or default to today
    selected_date = request.GET.get('date', date.today().isoformat())
    try:
        selected_date = date.fromisoformat(selected_date)
    except ValueError:
        selected_date = date.today()
    
    # Get activities for the selected date
    activities = get_daily_activities(selected_date)
    
    # Get warehouse location statistics
    warehouse_stats = get_warehouse_stats()
    
    context = {
        'selected_date': selected_date,
        'activities': activities,
        'warehouse_stats': warehouse_stats,
        'total_activities': len(activities),
    }
    
    return render(request, 'dashboard/dashboard.html', context)


@login_required
def all_activities(request):
    """
    View to display all activities from various models with date filtering
    """
    activities = []
    
    # Get selected date from request, default to today
    selected_date_str = request.GET.get('date')
    if selected_date_str:
        try:
            selected_date = timezone.datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()
    
    # Define the date range for filtering
    start_datetime = timezone.make_aware(timezone.datetime.combine(selected_date, timezone.datetime.min.time()))
    end_datetime = timezone.make_aware(timezone.datetime.combine(selected_date, timezone.datetime.max.time()))
    
    # Define model configurations with their respective fields
    model_configs = [
        {
            'model': Invoice,
            'name': 'Invoice',
            'created_field': 'created_at',
            'updated_field': 'updated_at',
            'title_field': 'invoice_number',
            'url_name': 'invoice:invoice_detail',
            'url_param': 'invoice_id',
            'icon': 'bi-receipt',
            'color': 'primary'
        },
        {
            'model': Quotation,
            'name': 'Quotation', 
            'created_field': 'created_at',
            'updated_field': 'updated_at',
            'title_field': 'quotation_number',
            'url_name': 'quotation:quotation_detail',
            'url_param': 'quotation_id',
            'icon': 'bi-file-text',
            'color': 'info'
        },
        {
            'model': GRN,
            'name': 'GRN',
            'created_field': 'created_at', 
            'updated_field': 'updated_at',
            'title_field': 'grn_number',
            'url_name': 'grn:grn_detail',
            'url_param': 'grn_id',
            'icon': 'bi-box-seam',
            'color': 'success'
        }
    ]
    
    # Get pagination parameters
    page = request.GET.get('page', 1)
    per_page = 50
    
    for config in model_configs:
        model = config['model']
        name = config['name']
        created_field = config['created_field']
        updated_field = config['updated_field']
        title_field = config['title_field']
        url_name = config['url_name']
        url_param = config['url_param']
        icon = config['icon']
        color = config['color']
        
        try:
            # Get created records for the selected date
            created_records = model.objects.filter(
                **{f'{created_field}__gte': start_datetime, f'{created_field}__lte': end_datetime}
            ).select_related('created_by').order_by(f'-{created_field}')
            
            for record in created_records:
                activities.append({
                    'type': f'{name} Created',
                    'title': getattr(record, title_field, f'{name} #{record.pk}'),
                    'timestamp': getattr(record, created_field),
                    'user': getattr(record, 'created_by', None),
                    'url': reverse(url_name, kwargs={url_param: record.pk}) if hasattr(record, 'pk') else '#',
                    'icon': 'bi-plus-circle',
                    'color': 'success',
                    'model_icon': icon,
                    'model_color': color
                })
            
            # Get updated records for the selected date (excluding same-day creations)
            updated_records = model.objects.filter(
                **{f'{updated_field}__gte': start_datetime, f'{updated_field}__lte': end_datetime}
            ).exclude(
                **{f'{created_field}__gte': start_datetime, f'{created_field}__lte': end_datetime}
            ).select_related('updated_by').order_by(f'-{updated_field}')
            
            for record in updated_records:
                activities.append({
                    'type': f'{name} Updated',
                    'title': getattr(record, title_field, f'{name} #{record.pk}'),
                    'timestamp': getattr(record, updated_field),
                    'user': getattr(record, 'updated_by', None),
                    'url': reverse(url_name, kwargs={url_param: record.pk}) if hasattr(record, 'pk') else '#',
                    'icon': 'bi-pencil-square',
                    'color': 'warning',
                    'model_icon': icon,
                    'model_color': color
                })
                
        except Exception as e:
            # Log the error but continue processing other models
            print(f"Error processing {name}: {e}")
            continue
    
    # Sort activities by timestamp (most recent first)
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Implement pagination
    from django.core.paginator import Paginator
    paginator = Paginator(activities, per_page)
    
    try:
        activities_page = paginator.page(page)
    except:
        activities_page = paginator.page(1)
    
    context = {
        'activities': activities_page,
        'total_activities': len(activities),
        'page_title': 'All Activities',
        'selected_date': selected_date,
    }
    
    return render(request, 'dashboard/all_activities.html', context)


def get_daily_activities(selected_date):
    """Get activities for the selected date from various models"""
    activities = []
    
    # Define the date range for the selected date only
    start_datetime = timezone.make_aware(timezone.datetime.combine(selected_date, timezone.datetime.min.time()))
    end_datetime = timezone.make_aware(timezone.datetime.combine(selected_date, timezone.datetime.max.time()))
    
    # Model configurations for activity tracking
    model_configs = [
        {
            'model': Invoice,
            'name': 'Invoice',
            'badge_class': 'bg-success',
            'created_field': 'created_at',
            'updated_field': 'updated_at',
            'number_field': 'invoice_number',
            'title_field': 'invoice_number',
        },
        {
            'model': Quotation,
            'name': 'Quotation',
            'badge_class': 'bg-primary',
            'created_field': 'created_at',
            'updated_field': 'updated_at',
            'number_field': 'quotation_number',
            'title_field': 'quotation_number',
        },
        {
            'model': GRN,
            'name': 'GRN',
            'badge_class': 'bg-info',
            'created_field': 'created_at',
            'updated_field': 'updated_at',
            'number_field': 'grn_number',
            'title_field': 'grn_number',
        },
        {
            'model': Job,
            'name': 'Job',
            'badge_class': 'bg-warning',
            'created_field': 'created_at',
            'updated_field': 'updated_at',
            'number_field': 'job_number',
            'title_field': 'job_number',
        },
        {
            'model': Customer,
            'name': 'Customer',
            'badge_class': 'bg-secondary',
            'created_field': 'created_at',
            'updated_field': 'updated_at',
            'number_field': 'customer_code',
            'title_field': 'customer_name',
        },
        {
            'model': Item,
            'name': 'Item',
            'badge_class': 'bg-dark',
            'created_field': 'created_at',
            'updated_field': 'updated_at',
            'number_field': 'item_code',
            'title_field': 'item_name',
        },
        {
            'model': Ledger,
            'name': 'Ledger',
            'badge_class': 'bg-success',
            'created_field': 'created_at',
            'updated_field': 'updated_at',
            'number_field': 'ledger_number',
            'title_field': 'ledger_number',
        },
        {
            'model': JournalEntry,
            'name': 'Journal Entry',
            'badge_class': 'bg-primary',
            'created_field': 'created_at',
            'updated_field': 'updated_at',
            'number_field': 'journal_number',
            'title_field': 'journal_number',
        },
        {
            'model': DeliveryOrder,
            'name': 'Delivery Order',
            'badge_class': 'bg-info',
            'created_field': 'created_at',
            'updated_field': 'updated_at',
            'number_field': 'do_number',
            'title_field': 'do_number',
        },
        {
            'model': DispatchNote,
            'name': 'Dispatch Note',
            'badge_class': 'bg-warning',
            'created_field': 'created_at',
            'updated_field': 'updated_at',
            'number_field': 'gdn_number',
            'title_field': 'gdn_number',
        },
        {
            'model': CrossStuffing,
            'name': 'Cross Stuffing',
            'badge_class': 'bg-secondary',
            'created_field': 'created_at',
            'updated_field': 'updated_at',
            'number_field': 'cs_number',
            'title_field': 'cs_number',
        },
        {
            'model': Documentation,
            'name': 'Documentation',
            'badge_class': 'bg-dark',
            'created_field': 'created_at',
            'updated_field': 'updated_at',
            'number_field': 'doc_number',
            'title_field': 'doc_number',
        },
        {
            'model': Putaway,
            'name': 'Putaway',
            'badge_class': 'bg-success',
            'created_field': 'created_at',
            'updated_field': 'updated_at',
            'number_field': 'putaway_number',
            'title_field': 'putaway_number',
        },
        {
            'model': Facility,
            'name': 'Facility',
            'badge_class': 'bg-primary',
            'created_field': 'created_at',
            'updated_field': 'updated_at',
            'number_field': 'facility_code',
            'title_field': 'facility_name',
        },
        {
            'model': ChartOfAccount,
            'name': 'Chart of Account',
            'badge_class': 'bg-info',
            'created_field': 'created_at',
            'updated_field': 'updated_at',
            'number_field': 'account_code',
            'title_field': 'name',
        },
        {
            'model': CreditNote,
            'name': 'Credit Note',
            'badge_class': 'bg-success',
            'created_field': 'created_at',
            'updated_field': 'updated_at',
            'number_field': 'credit_note_number',
            'title_field': 'credit_note_number',
        },
        {
            'model': DebitNote,
            'name': 'Debit Note',
            'badge_class': 'bg-danger',
            'created_field': 'created_at',
            'updated_field': 'updated_at',
            'number_field': 'debit_note_number',
            'title_field': 'debit_note_number',
        },
        {
            'model': CustomerPayment,
            'name': 'Customer Payment',
            'badge_class': 'bg-success',
            'created_field': 'created_at',
            'updated_field': 'updated_at',
            'number_field': 'payment_number',
            'title_field': 'payment_number',
        },
        {
            'model': SupplierBill,
            'name': 'Supplier Bill',
            'badge_class': 'bg-warning',
            'created_field': 'created_at',
            'updated_field': 'updated_at',
            'number_field': 'bill_number',
            'title_field': 'bill_number',
        },
        {
            'model': SupplierPayment,
            'name': 'Supplier Payment',
            'badge_class': 'bg-info',
            'created_field': 'created_at',
            'updated_field': 'updated_at',
            'number_field': 'payment_number',
            'title_field': 'payment_number',
        },
        {
            'model': DunningLetter,
            'name': 'Dunning Letter',
            'badge_class': 'bg-danger',
            'created_field': 'created_at',
            'updated_field': 'updated_at',
            'number_field': 'id',
            'title_field': 'id',
        },
    ]
    
    # Collect activities from all models
    for config in model_configs:
        model = config['model']
        model_name = config['name']
        badge_class = config['badge_class']
        created_field = config['created_field']
        updated_field = config['updated_field']
        number_field = config['number_field']
        title_field = config['title_field']
        
        try:
            # Get created records for the selected date only
            created_records = model.objects.filter(
                **{f"{created_field}__gte": start_datetime, f"{created_field}__lte": end_datetime}
            ).select_related('created_by').order_by(f'-{created_field}')[:25]  # Limit to 25 most recent per model
            
            for record in created_records:
                title = getattr(record, title_field, str(record))
                activities.append({
                    'date': record.created_at.date(),
                    'type': model_name,
                    'badge_class': badge_class,
                    'description': f"Created new {model_name.lower()} {title}",
                    'user': record.created_by.get_full_name() if record.created_by and record.created_by.get_full_name() else (record.created_by.username if record.created_by else 'System'),
                    'time': record.created_at.time(),
                    'timestamp': record.created_at,
                })
            
            # Get updated records for the selected date only (excluding same-day creations)
            updated_records = model.objects.filter(
                **{f"{updated_field}__gte": start_datetime, f"{updated_field}__lte": end_datetime}
            ).exclude(
                **{f"{created_field}__date": selected_date}
            ).select_related('updated_by').order_by(f'-{updated_field}')[:25]  # Limit to 25 most recent per model
            
            for record in updated_records:
                title = getattr(record, title_field, str(record))
                activities.append({
                    'date': record.updated_at.date(),
                    'type': model_name,
                    'badge_class': badge_class,
                    'description': f"Updated {model_name.lower()} {title}",
                    'user': record.updated_by.get_full_name() if record.updated_by and record.updated_by.get_full_name() else (record.updated_by.username if record.updated_by else 'System'),
                    'time': record.updated_at.time(),
                    'timestamp': record.updated_at,
                })
                
        except Exception as e:
            # Skip models that don't exist or have issues
            continue
    
    # Sort activities by timestamp (most recent first)
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return activities[:100]  # Limit to 100 most recent activities


def get_warehouse_stats():
    """Get warehouse location statistics"""
    try:
        total_locations = FacilityLocation.objects.count()
        occupied_locations = FacilityLocation.objects.filter(current_utilization__gt=0).count()
        free_locations = total_locations - occupied_locations
        
        return {
            'total_racks': total_locations,
            'occupied': occupied_locations,
            'free': free_locations,
        }
    except:
        return {
            'total_racks': 0,
            'occupied': 0,
            'free': 0,
        }


def health_check(request):
    """Simple health check endpoint for deployment platforms"""
    return JsonResponse({'status': 'healthy', 'timestamp': timezone.now().isoformat()})
