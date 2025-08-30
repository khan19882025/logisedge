from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class BillProcessor:
    """Utility class for processing bills and handling overdue logic"""
    
    @staticmethod
    def get_system_user():
        """Get or create system user for automated actions"""
        try:
            system_user = User.objects.get(username='system')
        except User.DoesNotExist:
            system_user = User.objects.create_user(
                username='system',
                email='system@company.com',
                first_name='System',
                last_name='Automated',
                is_active=True,
                is_staff=False
            )
            logger.info('Created system user for automated actions')
        return system_user
    
    @staticmethod
    def mark_overdue_bills(dry_run=False):
        """Mark bills as overdue if they are past due date"""
        from .models import Bill, BillHistory
        
        today = timezone.now().date()
        overdue_bills = Bill.objects.filter(
            status='pending',
            due_date__lt=today
        ).select_related('vendor', 'created_by')
        
        if not overdue_bills.exists():
            return {'marked': 0, 'bills': []}
        
        system_user = BillProcessor.get_system_user()
        marked_bills = []
        
        with transaction.atomic():
            for bill in overdue_bills:
                days_overdue = (today - bill.due_date).days
                
                if not dry_run:
                    # Mark as overdue
                    bill.mark_as_overdue(user=system_user)
                    
                    # Create history entry
                    BillHistory.objects.create(
                        bill=bill,
                        action='overdue',
                        user=system_user,
                        description=f'Automatically marked as overdue ({days_overdue} days past due)'
                    )
                
                marked_bills.append({
                    'bill': bill,
                    'days_overdue': days_overdue
                })
        
        return {
            'marked': len(marked_bills),
            'bills': marked_bills
        }
    
    @staticmethod
    def get_bills_by_status():
        """Get bills categorized by their status for dashboard"""
        from .models import Bill
        
        today = timezone.now().date()
        
        # Bills due today
        due_today = Bill.objects.filter(
            status='pending',
            due_date=today
        ).select_related('vendor')
        
        # Bills due in next 7 days
        upcoming = Bill.objects.filter(
            status='pending',
            due_date__gt=today,
            due_date__lte=today + timedelta(days=7)
        ).select_related('vendor')
        
        # Overdue bills
        overdue = Bill.objects.filter(
            status='overdue'
        ).select_related('vendor')
        
        # All pending bills
        pending = Bill.objects.filter(
            status='pending'
        ).select_related('vendor')
        
        # Paid bills (recent)
        paid_recent = Bill.objects.filter(
            status='paid',
            paid_date__gte=today - timedelta(days=30)
        ).select_related('vendor')
        
        return {
            'due_today': {
                'count': due_today.count(),
                'total_amount': sum(bill.amount for bill in due_today),
                'bills': due_today
            },
            'upcoming': {
                'count': upcoming.count(),
                'total_amount': sum(bill.amount for bill in upcoming),
                'bills': upcoming
            },
            'overdue': {
                'count': overdue.count(),
                'total_amount': sum(bill.amount for bill in overdue),
                'bills': overdue
            },
            'pending': {
                'count': pending.count(),
                'total_amount': sum(bill.amount for bill in pending),
                'bills': pending
            },
            'paid_recent': {
                'count': paid_recent.count(),
                'total_amount': sum(bill.amount for bill in paid_recent),
                'bills': paid_recent
            }
        }
    
    @staticmethod
    def get_dashboard_stats():
        """Get statistics for dashboard display"""
        from multi_currency.models import CurrencySettings
        
        bills_data = BillProcessor.get_bills_by_status()
        
        # Get default currency information
        currency_settings = CurrencySettings.objects.first()
        default_currency = currency_settings.default_currency if currency_settings else None
        
        stats = {
            'today_due_count': bills_data['due_today']['count'],
            'today_due_amount': bills_data['due_today']['total_amount'],
            'overdue_count': bills_data['overdue']['count'],
            'overdue_amount': bills_data['overdue']['total_amount'],
            'upcoming_count': bills_data['upcoming']['count'],
            'upcoming_amount': bills_data['upcoming']['total_amount'],
            'total_pending_count': bills_data['pending']['count'],
            'total_pending_amount': bills_data['pending']['total_amount'],
            'paid_this_month_count': bills_data['paid_recent']['count'],
            'paid_this_month_amount': bills_data['paid_recent']['total_amount']
        }
        
        # Add currency information if available
        if default_currency:
            stats.update({
                'default_currency_code': default_currency.code,
                'default_currency_symbol': default_currency.symbol,
                'default_currency_name': default_currency.name
            })
        
        return stats
    
    @staticmethod
    def process_bill_payment(bill, user, paid_amount=None, paid_date=None):
        """Process bill payment with history tracking"""
        from .models import BillHistory
        
        if paid_amount is None:
            paid_amount = bill.amount
        
        if paid_date is None:
            paid_date = timezone.now().date()
        
        # Mark as paid
        bill.mark_as_paid(user=user, paid_amount=paid_amount, paid_date=paid_date)
        
        # Create history entry
        BillHistory.objects.create(
            bill=bill,
            action='paid',
            user=user,
            description=f'Payment processed: ${paid_amount:,.2f} on {paid_date}'
        )
        
        return bill
    
    @staticmethod
    def confirm_bill(bill, user):
        """Confirm bill with history tracking"""
        from .models import BillHistory
        
        # Confirm bill
        bill.confirm_bill(user=user)
        
        # Create history entry
        BillHistory.objects.create(
            bill=bill,
            action='confirmed',
            user=user,
            description='Bill confirmed'
        )
        
        return bill


class BillFilters:
    """Utility class for filtering and searching bills"""
    
    @staticmethod
    def filter_bills(queryset, filters):
        """Apply filters to bill queryset"""
        # Status filter
        if filters.get('status'):
            queryset = queryset.filter(status=filters['status'])
        
        # Confirmed filter
        if filters.get('confirmed') is not None:
            queryset = queryset.filter(confirmed=filters['confirmed'])
        
        # Vendor filter
        if filters.get('vendor'):
            queryset = queryset.filter(vendor__id=filters['vendor'])
        
        # Date range filters
        if filters.get('bill_date_from'):
            queryset = queryset.filter(bill_date__gte=filters['bill_date_from'])
        
        if filters.get('bill_date_to'):
            queryset = queryset.filter(bill_date__lte=filters['bill_date_to'])
        
        if filters.get('due_date_from'):
            queryset = queryset.filter(due_date__gte=filters['due_date_from'])
        
        if filters.get('due_date_to'):
            queryset = queryset.filter(due_date__lte=filters['due_date_to'])
        
        # Amount range filters
        if filters.get('amount_min'):
            queryset = queryset.filter(amount__gte=filters['amount_min'])
        
        if filters.get('amount_max'):
            queryset = queryset.filter(amount__lte=filters['amount_max'])
        
        return queryset
    
    @staticmethod
    def search_bills(queryset, search_term):
        """Search bills by various fields"""
        if not search_term:
            return queryset
        
        from django.db.models import Q
        
        return queryset.filter(
            Q(bill_no__icontains=search_term) |
            Q(vendor__name__icontains=search_term) |
            Q(notes__icontains=search_term)
        )
    
    @staticmethod
    def get_filter_options():
        """Get available filter options"""
        from .models import Bill, Vendor
        
        return {
            'statuses': Bill.STATUS_CHOICES,
            'vendors': Vendor.objects.filter(is_active=True).values('id', 'name'),
            'confirmed_options': [
                (True, 'Confirmed'),
                (False, 'Unconfirmed')
            ]
        }


class BillValidators:
    """Utility class for bill validation"""
    
    @staticmethod
    def validate_bill_data(data):
        """Validate bill data before creation/update"""
        errors = []
        
        # Required fields
        required_fields = ['vendor', 'bill_no', 'bill_date', 'due_date', 'amount']
        for field in required_fields:
            if not data.get(field):
                errors.append(f'{field.replace("_", " ").title()} is required')
        
        # Date validation
        if data.get('bill_date') and data.get('due_date'):
            if data['due_date'] < data['bill_date']:
                errors.append('Due date cannot be before bill date')
        
        # Amount validation
        if data.get('amount'):
            try:
                amount = float(data['amount'])
                if amount <= 0:
                    errors.append('Amount must be greater than zero')
            except (ValueError, TypeError):
                errors.append('Amount must be a valid number')
        
        # Bill number uniqueness (would need to be checked in view/serializer)
        # This is just a format check
        if data.get('bill_no'):
            bill_no = str(data['bill_no']).strip()
            if len(bill_no) < 3:
                errors.append('Bill number must be at least 3 characters long')
        
        return errors
    
    @staticmethod
    def validate_payment_data(data, bill):
        """Validate payment data"""
        errors = []
        
        # Check if bill can be paid
        if bill.status == 'paid':
            errors.append('Bill is already paid')
        
        # Validate paid amount
        if data.get('paid_amount'):
            try:
                paid_amount = float(data['paid_amount'])
                if paid_amount <= 0:
                    errors.append('Paid amount must be greater than zero')
                if paid_amount > bill.amount:
                    errors.append('Paid amount cannot exceed bill amount')
            except (ValueError, TypeError):
                errors.append('Paid amount must be a valid number')
        
        # Validate paid date
        if data.get('paid_date'):
            paid_date = data['paid_date']
            if hasattr(paid_date, 'date'):
                paid_date = paid_date.date()
            
            if paid_date < bill.bill_date:
                errors.append('Paid date cannot be before bill date')
        
        return errors