from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
from billing_payable_tracking.models import Bill, BillAlert


class Command(BaseCommand):
    help = 'Generate daily alerts for bill generation and due date reminders'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date to generate alerts for (YYYY-MM-DD format). Defaults to today.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what alerts would be generated without creating them',
        )

    def handle(self, *args, **options):
        # Parse the date or use today
        if options['date']:
            try:
                target_date = datetime.strptime(options['date'], '%Y-%m-%d').date()
            except ValueError:
                self.stdout.write(
                    self.style.ERROR('Invalid date format. Use YYYY-MM-DD')
                )
                return
        else:
            target_date = timezone.now().date()

        self.stdout.write(f'Generating alerts for {target_date}')
        
        dry_run = options['dry_run']
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No alerts will be created'))

        # Get all users for alert generation
        users = User.objects.filter(is_active=True)
        
        generated_alerts = 0
        due_soon_alerts = 0

        # Generate alerts for bill generation (recurring bills)
        self.stdout.write('\nChecking for bill generation alerts...')
        recurring_bills = Bill.objects.filter(
            is_recurring=True,
            generate_day=target_date.day
        )
        
        for bill in recurring_bills:
            for user in users:
                # Check if alert already exists for this date
                existing_alert = BillAlert.objects.filter(
                    bill=bill,
                    user=user,
                    alert_type='generated',
                    show_date=target_date
                ).exists()
                
                if not existing_alert:
                    if not dry_run:
                        BillAlert.objects.create(
                            bill=bill,
                            user=user,
                            alert_type='generated',
                            show_date=target_date
                        )
                    generated_alerts += 1
                    self.stdout.write(
                        f'  Created generation alert: {bill.bill_name} for {user.username}'
                    )

        # Generate alerts for bills due in 4 days
        self.stdout.write('\nChecking for due soon alerts...')
        due_date = target_date + timedelta(days=4)
        bills_due_soon = Bill.objects.filter(
            due_date=due_date,
            status='pending'  # Only for unpaid bills
        )
        
        for bill in bills_due_soon:
            for user in users:
                # Check if alert already exists for this date
                existing_alert = BillAlert.objects.filter(
                    bill=bill,
                    user=user,
                    alert_type='due_soon',
                    show_date=target_date
                ).exists()
                
                if not existing_alert:
                    if not dry_run:
                        BillAlert.objects.create(
                            bill=bill,
                            user=user,
                            alert_type='due_soon',
                            show_date=target_date
                        )
                    due_soon_alerts += 1
                    self.stdout.write(
                        f'  Created due soon alert: {bill.bill_name} for {user.username}'
                    )

        # Update next_generate_date for recurring bills
        if not dry_run:
            self.stdout.write('\nUpdating next generation dates for recurring bills...')
            for bill in recurring_bills:
                # Calculate next month's generation date
                next_month = target_date.replace(day=1) + timedelta(days=32)
                next_month = next_month.replace(day=1)  # First day of next month
                
                try:
                    # Try to set the generate_day in next month
                    next_generate_date = next_month.replace(day=bill.generate_day)
                except ValueError:
                    # Handle cases where generate_day doesn't exist in next month (e.g., Feb 30)
                    # Set to last day of the month
                    next_month_last_day = (next_month.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                    next_generate_date = next_month_last_day
                
                bill.next_generate_date = next_generate_date
                bill.save()
                self.stdout.write(
                    f'  Updated {bill.bill_name} next generation date to {next_generate_date}'
                )

        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(f'Alert generation summary for {target_date}:')
        self.stdout.write(f'  Bill generation alerts: {generated_alerts}')
        self.stdout.write(f'  Due soon alerts: {due_soon_alerts}')
        self.stdout.write(f'  Total alerts: {generated_alerts + due_soon_alerts}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nNo alerts were actually created (dry run mode)'))
        else:
            self.stdout.write(self.style.SUCCESS('\nAlert generation completed successfully!'))