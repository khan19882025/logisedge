from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date
from .models import (
    LeaveRequest, LeaveApproval, LeaveBalance, LeaveNotification,
    LeaveType, LeaveCalendar
)


@receiver(post_save, sender=LeaveRequest)
def create_leave_notifications(sender, instance, created, **kwargs):
    """Create notifications when a leave request is created or updated"""
    if created:
        # Notify approver about new leave request
        if instance.current_approver:
            LeaveNotification.objects.create(
                recipient=instance.current_approver,
                notification_type='approval_required',
                title=f'New Leave Request from {instance.employee.get_full_name()}',
                message=f'{instance.employee.get_full_name()} has submitted a leave request for {instance.leave_type.name} from {instance.start_date} to {instance.end_date}',
                related_leave_request=instance
            )
        
        # Create calendar entries for the leave period
        create_calendar_entries(instance)
    
    elif instance.status == 'approved':
        # Notify employee about approval
        LeaveNotification.objects.create(
            recipient=instance.employee,
            notification_type='request_approved',
            title='Leave Request Approved',
            message=f'Your leave request for {instance.leave_type.name} has been approved.',
            related_leave_request=instance
        )
        
        # Update leave balance
        update_leave_balance(instance)
        
    elif instance.status == 'rejected':
        # Notify employee about rejection
        LeaveNotification.objects.create(
            recipient=instance.employee,
            notification_type='request_rejected',
            title='Leave Request Rejected',
            message=f'Your leave request for {instance.leave_type.name} has been rejected.',
            related_leave_request=instance
        )


@receiver(post_save, sender=LeaveApproval)
def handle_approval_workflow(sender, instance, created, **kwargs):
    """Handle approval workflow when an approval is created"""
    if created:
        leave_request = instance.leave_request
        
        if instance.action == 'approve':
            leave_request.status = 'approved'
            leave_request.approved_by = instance.approver
            leave_request.approved_at = timezone.now()
            leave_request.approval_comments = instance.comments
            leave_request.save()
            
        elif instance.action == 'reject':
            leave_request.status = 'rejected'
            leave_request.approval_comments = instance.comments
            leave_request.save()


def create_calendar_entries(leave_request):
    """Create calendar entries for the leave period"""
    from datetime import timedelta
    
    current_date = leave_request.start_date
    end_date = leave_request.end_date
    
    while current_date <= end_date:
        # Skip weekends
        if current_date.weekday() < 5:  # Monday to Friday
            LeaveCalendar.objects.get_or_create(
                employee=leave_request.employee,
                date=current_date,
                defaults={
                    'leave_request': leave_request,
                    'is_half_day': leave_request.is_half_day,
                    'half_day_type': leave_request.half_day_type if leave_request.is_half_day else ''
                }
            )
        current_date += timedelta(days=1)


def update_leave_balance(leave_request):
    """Update leave balance when a request is approved"""
    balance, created = LeaveBalance.objects.get_or_create(
        employee=leave_request.employee,
        leave_type=leave_request.leave_type,
        year=date.today().year,
        defaults={
            'allocated_days': 0,
            'used_days': 0,
            'carried_forward_days': 0,
            'encashed_days': 0
        }
    )
    
    # Update used days
    balance.used_days += leave_request.total_days
    balance.save()


@receiver(pre_save, sender=LeaveBalance)
def calculate_balance_fields(sender, instance, **kwargs):
    """Calculate available days and total balance before saving"""
    instance.total_balance = instance.allocated_days + instance.carried_forward_days
    instance.available_days = instance.total_balance - instance.used_days - instance.encashed_days


@receiver(post_save, sender=User)
def create_default_leave_balances(sender, instance, created, **kwargs):
    """Create default leave balances for new users"""
    if created:
        current_year = date.today().year
        active_leave_types = LeaveType.objects.filter(is_active=True)
        
        for leave_type in active_leave_types:
            LeaveBalance.objects.get_or_create(
                employee=instance,
                leave_type=leave_type,
                year=current_year,
                defaults={
                    'allocated_days': leave_type.max_days_per_year,
                    'used_days': 0,
                    'carried_forward_days': 0,
                    'encashed_days': 0
                }
            )


@receiver(post_save, sender=LeaveType)
def update_existing_balances(sender, instance, created, **kwargs):
    """Update existing balances when leave type settings change"""
    if not created and instance.is_active:
        # Update balances for all users for the current year
        current_year = date.today().year
        balances = LeaveBalance.objects.filter(
            leave_type=instance,
            year=current_year
        )
        
        for balance in balances:
            # Only update if no days have been used yet
            if balance.used_days == 0:
                balance.allocated_days = instance.max_days_per_year
                balance.save()


# Signal to handle low balance notifications
def check_low_balance():
    """Check for employees with low leave balance and send notifications"""
    current_year = date.today().year
    low_balance_threshold = 5  # Days
    
    balances = LeaveBalance.objects.filter(
        year=current_year,
        available_days__lte=low_balance_threshold,
        available_days__gt=0
    ).select_related('employee', 'leave_type')
    
    for balance in balances:
        # Check if notification already exists
        existing_notification = LeaveNotification.objects.filter(
            recipient=balance.employee,
            notification_type='balance_low',
            related_leave_request__isnull=True,
            created_at__date=date.today()
        ).first()
        
        if not existing_notification:
            LeaveNotification.objects.create(
                recipient=balance.employee,
                notification_type='balance_low',
                title='Low Leave Balance Alert',
                message=f'You have only {balance.available_days} days remaining for {balance.leave_type.name}. Please plan your leaves accordingly.'
            )


# Signal to handle carry forward at year end
def process_carry_forward():
    """Process carry forward of unused leave at year end"""
    from datetime import date
    
    current_year = date.today().year
    previous_year = current_year - 1
    
    # Get all balances from previous year
    previous_balances = LeaveBalance.objects.filter(
        year=previous_year
    ).select_related('employee', 'leave_type')
    
    for balance in previous_balances:
        if balance.leave_type.can_carry_forward and balance.available_days > 0:
            # Calculate carry forward amount
            carry_forward_days = min(
                balance.available_days,
                balance.leave_type.max_carry_forward_days
            )
            
            if carry_forward_days > 0:
                # Create or update current year balance
                current_balance, created = LeaveBalance.objects.get_or_create(
                    employee=balance.employee,
                    leave_type=balance.leave_type,
                    year=current_year,
                    defaults={
                        'allocated_days': balance.leave_type.max_days_per_year,
                        'used_days': 0,
                        'carried_forward_days': carry_forward_days,
                        'encashed_days': 0
                    }
                )
                
                if not created:
                    current_balance.carried_forward_days = carry_forward_days
                    current_balance.save()
                
                # Create notification
                LeaveNotification.objects.create(
                    recipient=balance.employee,
                    notification_type='leave_reminder',
                    title='Leave Carry Forward',
                    message=f'{carry_forward_days} days of {balance.leave_type.name} have been carried forward from {previous_year} to {current_year}.'
                ) 