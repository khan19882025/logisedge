from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
import logging

from billing_payable_tracking.models import Bill, BillHistory, BillReminder

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process bills: mark overdue bills and send reminders'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--send-reminders',
            action='store_true',
            help='Send email reminders for due and overdue bills',
        )
        parser.add_argument(
            '--mark-overdue',
            action='store_true',
            help='Mark bills as overdue if past due date',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Run all processes (mark overdue + send reminders)',
        )
    
    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.verbosity = options['verbosity']
        
        if options['all']:
            options['mark_overdue'] = True
            options['send_reminders'] = True
        
        if not any([options['mark_overdue'], options['send_reminders']]):
            self.stdout.write(
                self.style.WARNING(
                    'No action specified. Use --mark-overdue, --send-reminders, or --all'
                )
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Starting bill processing... (DRY RUN: {self.dry_run})'
            )
        )
        
        try:
            if options['mark_overdue']:
                self.mark_overdue_bills()
            
            if options['send_reminders']:
                self.send_bill_reminders()
            
            self.stdout.write(
                self.style.SUCCESS('Bill processing completed successfully!')
            )
            
        except Exception as e:
            logger.error(f'Error processing bills: {str(e)}')
            self.stdout.write(
                self.style.ERROR(f'Error processing bills: {str(e)}')
            )
            raise
    
    def mark_overdue_bills(self):
        """Mark bills as overdue if they are past due date"""
        self.stdout.write('\n=== Marking Overdue Bills ===')
        
        # Get bills that should be marked as overdue
        today = timezone.now().date()
        overdue_bills = Bill.objects.filter(
            status='pending',
            due_date__lt=today
        ).select_related('vendor', 'created_by')
        
        if not overdue_bills.exists():
            self.stdout.write('No bills to mark as overdue.')
            return
        
        self.stdout.write(f'Found {overdue_bills.count()} bills to mark as overdue:')
        
        # Get system user for automated actions
        system_user = self.get_system_user()
        
        marked_count = 0
        
        with transaction.atomic():
            for bill in overdue_bills:
                days_overdue = (today - bill.due_date).days
                
                if self.verbosity >= 2:
                    self.stdout.write(
                        f'  - {bill.bill_no} ({bill.vendor.name}): '
                        f'{days_overdue} days overdue'
                    )
                
                if not self.dry_run:
                    # Mark as overdue
                    bill.mark_as_overdue(user=system_user)
                    
                    # Create history entry
                    BillHistory.objects.create(
                        bill=bill,
                        action='overdue',
                        user=system_user,
                        description=f'Automatically marked as overdue ({days_overdue} days past due)'
                    )
                
                marked_count += 1
        
        if self.dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would mark {marked_count} bills as overdue'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully marked {marked_count} bills as overdue'
                )
            )
    
    def send_bill_reminders(self):
        """Send email reminders for bills"""
        self.stdout.write('\n=== Sending Bill Reminders ===')
        
        today = timezone.now().date()
        
        # Bills due today
        due_today = Bill.objects.filter(
            status='pending',
            due_date=today
        ).select_related('vendor')
        
        # Bills due in 3 days (early warning)
        due_soon = Bill.objects.filter(
            status='pending',
            due_date=today + timedelta(days=3)
        ).select_related('vendor')
        
        # Overdue bills
        overdue_bills = Bill.objects.filter(
            status='overdue'
        ).select_related('vendor')
        
        # Send reminders
        self.send_reminder_batch(due_today, 'due_today', 'Bills Due Today')
        self.send_reminder_batch(due_soon, 'due_soon', 'Bills Due Soon (3 days)')
        self.send_reminder_batch(overdue_bills, 'overdue', 'Overdue Bills')
    
    def send_reminder_batch(self, bills, reminder_type, description):
        """Send reminders for a batch of bills"""
        if not bills.exists():
            self.stdout.write(f'No {description.lower()} to remind about.')
            return
        
        self.stdout.write(f'\nSending reminders for {bills.count()} {description.lower()}:')
        
        sent_count = 0
        failed_count = 0
        
        for bill in bills:
            try:
                # Check if reminder already sent today
                today = timezone.now().date()
                existing_reminder = BillReminder.objects.filter(
                    bill=bill,
                    reminder_type=reminder_type,
                    sent_date__date=today
                ).exists()
                
                if existing_reminder:
                    if self.verbosity >= 2:
                        self.stdout.write(
                            f'  - {bill.bill_no}: Reminder already sent today'
                        )
                    continue
                
                if self.verbosity >= 2:
                    self.stdout.write(
                        f'  - {bill.bill_no} ({bill.vendor.name}): '
                        f'${bill.amount} due {bill.due_date}'
                    )
                
                if not self.dry_run:
                    success = self.send_bill_reminder_email(bill, reminder_type)
                    
                    # Create reminder record
                    BillReminder.objects.create(
                        bill=bill,
                        reminder_type=reminder_type,
                        recipient_email=bill.vendor.email,
                        sent_successfully=success,
                        error_message='' if success else 'Email sending failed'
                    )
                    
                    if success:
                        sent_count += 1
                    else:
                        failed_count += 1
                else:
                    sent_count += 1
            
            except Exception as e:
                logger.error(f'Error sending reminder for bill {bill.bill_no}: {str(e)}')
                failed_count += 1
                
                if not self.dry_run:
                    BillReminder.objects.create(
                        bill=bill,
                        reminder_type=reminder_type,
                        recipient_email=bill.vendor.email or 'unknown@example.com',
                        sent_successfully=False,
                        error_message=str(e)
                    )
        
        if self.dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would send {sent_count} {description.lower()} reminders'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Sent {sent_count} {description.lower()} reminders '
                    f'({failed_count} failed)'
                )
            )
    
    def send_bill_reminder_email(self, bill, reminder_type):
        """Send email reminder for a specific bill"""
        try:
            # Email configuration
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@company.com')
            recipient_email = bill.vendor.email
            
            if not recipient_email:
                logger.warning(f'No email address for vendor {bill.vendor.name}')
                return False
            
            # Email content based on reminder type
            subject_templates = {
                'due_today': f'Bill Due Today - {bill.bill_no}',
                'due_soon': f'Bill Due Soon - {bill.bill_no}',
                'overdue': f'OVERDUE Bill - {bill.bill_no}'
            }
            
            message_templates = {
                'due_today': f'''
Dear {bill.vendor.name},

This is a reminder that the following bill is due TODAY:

Bill No: {bill.bill_no}
Amount: ${bill.amount:,.2f}
Due Date: {bill.due_date}

Please ensure payment is processed today to avoid any late fees.

Thank you for your business.

Best regards,
Accounts Payable Team
''',
                'due_soon': f'''
Dear {bill.vendor.name},

This is a reminder that the following bill is due in 3 days:

Bill No: {bill.bill_no}
Amount: ${bill.amount:,.2f}
Due Date: {bill.due_date}

Please prepare for payment to ensure timely processing.

Thank you for your business.

Best regards,
Accounts Payable Team
''',
                'overdue': f'''
Dear {bill.vendor.name},

IMPORTANT: The following bill is now OVERDUE:

Bill No: {bill.bill_no}
Amount: ${bill.amount:,.2f}
Due Date: {bill.due_date}
Days Overdue: {(timezone.now().date() - bill.due_date).days}

Please process payment immediately to avoid additional charges.

If payment has already been made, please contact us with payment details.

Thank you for your immediate attention.

Best regards,
Accounts Payable Team
'''
            }
            
            subject = subject_templates.get(reminder_type, f'Bill Reminder - {bill.bill_no}')
            message = message_templates.get(reminder_type, f'Reminder for bill {bill.bill_no}')
            
            # Send email
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[recipient_email],
                fail_silently=False
            )
            
            return True
            
        except Exception as e:
            logger.error(f'Failed to send email for bill {bill.bill_no}: {str(e)}')
            return False
    
    def get_system_user(self):
        """Get or create system user for automated actions"""
        try:
            # Try to get existing system user
            system_user = User.objects.get(username='system')
        except User.DoesNotExist:
            # Create system user if it doesn't exist
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