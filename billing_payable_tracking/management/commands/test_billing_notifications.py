from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta

from billing_payable_tracking.models import Vendor, Bill
from billing_payable_tracking.tasks import (
    send_bill_reminder_notifications,
    mark_overdue_bills,
    send_daily_summary_report,
    cleanup_old_reminders
)


class Command(BaseCommand):
    help = 'Test billing notification system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-test-data',
            action='store_true',
            help='Create test bills for notification testing',
        )
        parser.add_argument(
            '--test-reminders',
            action='store_true',
            help='Test bill reminder notifications',
        )
        parser.add_argument(
            '--test-overdue',
            action='store_true',
            help='Test overdue bill marking',
        )
        parser.add_argument(
            '--test-summary',
            action='store_true',
            help='Test daily summary report',
        )
        parser.add_argument(
            '--test-cleanup',
            action='store_true',
            help='Test cleanup old reminders',
        )
        parser.add_argument(
            '--test-all',
            action='store_true',
            help='Run all tests',
        )

    def handle(self, *args, **options):
        if options['test_all']:
            options.update({
                'create_test_data': True,
                'test_reminders': True,
                'test_overdue': True,
                'test_summary': True,
                'test_cleanup': True
            })
        
        if options['create_test_data']:
            self.create_test_data()
        
        if options['test_reminders']:
            self.test_reminders()
        
        if options['test_overdue']:
            self.test_overdue()
        
        if options['test_summary']:
            self.test_summary()
        
        if options['test_cleanup']:
            self.test_cleanup()
        
        if not any(options.values()):
            self.stdout.write(
                self.style.WARNING(
                    'No test specified. Use --help to see available options.'
                )
            )

    def create_test_data(self):
        """Create test data for notification testing"""
        self.stdout.write('Creating test data...')
        
        try:
            # Get or create a test user
            user, created = User.objects.get_or_create(
                username='test_billing_user',
                defaults={
                    'email': 'test@example.com',
                    'first_name': 'Test',
                    'last_name': 'User',
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(f'Created test user: {user.username}')
            
            # Create test vendor
            vendor, created = Vendor.objects.get_or_create(
                name='Test Vendor Corp',
                defaults={
                    'email': 'vendor@testcorp.com',
                    'phone': '+1-555-0123',
                    'address': '123 Test Street, Test City, TC 12345',
                    'payment_terms': 30,
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(f'Created test vendor: {vendor.name}')
            
            today = timezone.now().date()
            
            # Create test bills with different statuses and due dates
            test_bills = [
                {
                    'bill_no': 'TEST-OVERDUE-001',
                    'amount': 1500.00,
                    'due_date': today - timedelta(days=5),  # 5 days overdue
                    'status': 'pending',
                    'description': 'Test overdue bill'
                },
                {
                    'bill_no': 'TEST-DUE-TODAY-001',
                    'amount': 2500.00,
                    'due_date': today,  # Due today
                    'status': 'confirmed',
                    'description': 'Test bill due today'
                },
                {
                    'bill_no': 'TEST-UPCOMING-001',
                    'amount': 3500.00,
                    'due_date': today + timedelta(days=3),  # Due in 3 days
                    'status': 'pending',
                    'description': 'Test upcoming bill'
                },
                {
                    'bill_no': 'TEST-FUTURE-001',
                    'amount': 1000.00,
                    'due_date': today + timedelta(days=10),  # Due in 10 days
                    'status': 'pending',
                    'description': 'Test future bill'
                }
            ]
            
            created_bills = 0
            for bill_data in test_bills:
                bill, created = Bill.objects.get_or_create(
                    bill_no=bill_data['bill_no'],
                    defaults={
                        'vendor': vendor,
                        'amount': bill_data['amount'],
                        'due_date': bill_data['due_date'],
                        'status': bill_data['status'],
                        'description': bill_data['description'],
                        'payment_terms': 30,
                        'created_by': user
                    }
                )
                
                if created:
                    created_bills += 1
                    self.stdout.write(f'Created test bill: {bill.bill_no}')
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Test data creation completed. Created {created_bills} new bills.'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating test data: {str(e)}')
            )

    def test_reminders(self):
        """Test bill reminder notifications"""
        self.stdout.write('Testing bill reminder notifications...')
        
        try:
            result = send_bill_reminder_notifications.delay()
            self.stdout.write(f'Task ID: {result.id}')
            
            # Wait for result (with timeout)
            try:
                task_result = result.get(timeout=30)
                self.stdout.write(
                    self.style.SUCCESS(f'Reminder notifications result: {task_result}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f'Task queued but result not available: {str(e)}'
                    )
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error testing reminders: {str(e)}')
            )

    def test_overdue(self):
        """Test overdue bill marking"""
        self.stdout.write('Testing overdue bill marking...')
        
        try:
            result = mark_overdue_bills.delay()
            self.stdout.write(f'Task ID: {result.id}')
            
            try:
                task_result = result.get(timeout=30)
                self.stdout.write(
                    self.style.SUCCESS(f'Overdue marking result: {task_result}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f'Task queued but result not available: {str(e)}'
                    )
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error testing overdue marking: {str(e)}')
            )

    def test_summary(self):
        """Test daily summary report"""
        self.stdout.write('Testing daily summary report...')
        
        try:
            result = send_daily_summary_report.delay()
            self.stdout.write(f'Task ID: {result.id}')
            
            try:
                task_result = result.get(timeout=30)
                self.stdout.write(
                    self.style.SUCCESS(f'Daily summary result: {task_result}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f'Task queued but result not available: {str(e)}'
                    )
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error testing daily summary: {str(e)}')
            )

    def test_cleanup(self):
        """Test cleanup old reminders"""
        self.stdout.write('Testing cleanup old reminders...')
        
        try:
            result = cleanup_old_reminders.delay()
            self.stdout.write(f'Task ID: {result.id}')
            
            try:
                task_result = result.get(timeout=30)
                self.stdout.write(
                    self.style.SUCCESS(f'Cleanup result: {task_result}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f'Task queued but result not available: {str(e)}'
                    )
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error testing cleanup: {str(e)}')
            )

    def show_system_status(self):
        """Show system status for debugging"""
        self.stdout.write('\nSystem Status:')
        
        # Check if Celery is available
        try:
            from celery import current_app
            inspect = current_app.control.inspect()
            
            # Check active tasks
            active_tasks = inspect.active()
            if active_tasks:
                self.stdout.write(f'Active Celery tasks: {len(active_tasks)}')
            else:
                self.stdout.write('No active Celery tasks')
                
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Celery not available: {str(e)}')
            )
        
        # Check database
        try:
            bill_count = Bill.objects.count()
            vendor_count = Vendor.objects.count()
            self.stdout.write(f'Database: {bill_count} bills, {vendor_count} vendors')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Database error: {str(e)}')
            )