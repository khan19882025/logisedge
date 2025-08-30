from django.core.management.base import BaseCommand
from django.utils import timezone
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json


class Command(BaseCommand):
    help = 'Set up periodic tasks for billing notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreate existing tasks',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        # Define the tasks to create
        tasks_to_create = [
            {
                'name': 'Daily Bill Reminder Notifications',
                'task': 'billing_payable_tracking.tasks.send_bill_reminder_notifications',
                'schedule': {'hour': 9, 'minute': 0},  # 9:00 AM daily
                'description': 'Send reminder notifications for due and overdue bills'
            },
            {
                'name': 'Mark Overdue Bills',
                'task': 'billing_payable_tracking.tasks.mark_overdue_bills',
                'schedule': {'hour': 1, 'minute': 0},  # 1:00 AM daily
                'description': 'Mark bills as overdue if past due date'
            },
            {
                'name': 'Daily Billing Summary Report',
                'task': 'billing_payable_tracking.tasks.send_daily_summary_report',
                'schedule': {'hour': 8, 'minute': 0},  # 8:00 AM daily
                'description': 'Send daily summary report to administrators'
            },
            {
                'name': 'Cleanup Old Bill Reminders',
                'task': 'billing_payable_tracking.tasks.cleanup_old_reminders',
                'schedule': {'hour': 3, 'minute': 0, 'day_of_week': 1},  # 3:00 AM every Monday
                'description': 'Clean up old bill reminder records (weekly)'
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for task_config in tasks_to_create:
            try:
                # Create or get the crontab schedule
                schedule_kwargs = task_config['schedule']
                crontab_schedule, created = CrontabSchedule.objects.get_or_create(
                    **schedule_kwargs
                )
                
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'Created crontab schedule: {crontab_schedule}')
                    )
                
                # Check if task already exists
                task_name = task_config['name']
                existing_task = PeriodicTask.objects.filter(name=task_name).first()
                
                if existing_task:
                    if force:
                        existing_task.delete()
                        self.stdout.write(
                            self.style.WARNING(f'Deleted existing task: {task_name}')
                        )
                    else:
                        # Update existing task
                        existing_task.crontab = crontab_schedule
                        existing_task.task = task_config['task']
                        existing_task.enabled = True
                        existing_task.save()
                        
                        updated_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'Updated existing task: {task_name}')
                        )
                        continue
                
                # Create new periodic task
                periodic_task = PeriodicTask.objects.create(
                    name=task_name,
                    task=task_config['task'],
                    crontab=crontab_schedule,
                    enabled=True,
                    description=task_config.get('description', ''),
                    kwargs=json.dumps({}),  # Empty kwargs
                )
                
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created periodic task: {task_name}')
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error creating task {task_config["name"]}: {str(e)}'
                    )
                )
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSetup completed:\n'
                f'- Created: {created_count} tasks\n'
                f'- Updated: {updated_count} tasks\n'
                f'- Total: {created_count + updated_count} tasks configured'
            )
        )
        
        # Additional instructions
        self.stdout.write(
            self.style.WARNING(
                '\nIMPORTANT: Make sure the following services are running:\n'
                '1. Redis server\n'
                '2. Celery worker: celery -A logisEdge worker --loglevel=info\n'
                '3. Celery beat: celery -A logisEdge beat --loglevel=info\n'
                '\nYou can check task status in Django Admin under PERIODIC TASKS > Periodic tasks'
            )
        )
        
        # Show next steps
        self.stdout.write(
            self.style.SUCCESS(
                '\nNext steps:\n'
                '1. Configure email settings in Django settings.py\n'
                '2. Set DEFAULT_FROM_EMAIL and SITE_URL in settings\n'
                '3. Test notifications with: python manage.py test_billing_notifications\n'
                '4. Monitor task execution in the admin interface'
            )
        )