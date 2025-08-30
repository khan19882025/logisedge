from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from recurring_journal_entry.models import RecurringEntry
from datetime import date
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Generate journal entries for active recurring templates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be generated without actually creating entries',
        )
        parser.add_argument(
            '--template-id',
            type=int,
            help='Generate entries for a specific template ID only',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='User ID to use for generating entries (defaults to first superuser)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        template_id = options.get('template_id')
        user_id = options.get('user_id')
        
        # Get user
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User with ID {user_id} does not exist')
                )
                return
        else:
            # Get first superuser
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                self.stdout.write(
                    self.style.ERROR('No superuser found. Please specify a user with --user-id')
                )
                return
        
        # Get recurring entries
        if template_id:
            try:
                recurring_entries = [RecurringEntry.objects.get(id=template_id)]
            except RecurringEntry.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Recurring entry with ID {template_id} does not exist')
                )
                return
        else:
            recurring_entries = RecurringEntry.objects.filter(status='ACTIVE')
        
        if not recurring_entries:
            self.stdout.write(
                self.style.WARNING('No active recurring entries found')
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS(f'Processing {len(recurring_entries)} recurring entry(ies)')
        )
        
        total_generated = 0
        total_errors = 0
        
        for recurring_entry in recurring_entries:
            try:
                generated_count = self.process_recurring_entry(
                    recurring_entry, user, dry_run
                )
                total_generated += generated_count
                
                if generated_count > 0:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Generated {generated_count} entry(ies) for template "{recurring_entry.template_name}"'
                        )
                    )
                else:
                    self.stdout.write(
                        f'No entries generated for template "{recurring_entry.template_name}"'
                    )
                    
            except Exception as e:
                total_errors += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'Error processing template "{recurring_entry.template_name}": {str(e)}'
                    )
                )
                logger.error(f'Error processing recurring entry {recurring_entry.id}: {str(e)}')
        
        # Summary
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'DRY RUN: Would generate {total_generated} entries total'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully generated {total_generated} entries total'
                )
            )
        
        if total_errors > 0:
            self.stdout.write(
                self.style.ERROR(f'Encountered {total_errors} error(s)')
            )

    def process_recurring_entry(self, recurring_entry, user, dry_run=False):
        """Process a single recurring entry and generate due entries"""
        generated_count = 0
        today = date.today()
        
        # Check if entry is balanced
        if not recurring_entry.is_balanced:
            raise ValueError("Recurring entry is not balanced")
        
        # Get next posting date
        next_date = recurring_entry.get_next_posting_date()
        
        # Generate entries for all due dates
        while next_date and next_date <= today:
            # Check if entry already exists for this date
            if recurring_entry.generated_entries.filter(posting_date=next_date).exists():
                self.stdout.write(
                    f'  Entry for {next_date} already exists, skipping'
                )
                next_date = recurring_entry.get_next_posting_date(next_date)
                continue
            
            if dry_run:
                self.stdout.write(
                    f'  Would generate entry for {next_date}'
                )
                generated_count += 1
            else:
                try:
                    # Generate the journal entry
                    journal_entry = recurring_entry.generate_journal_entry(next_date, user)
                    
                    self.stdout.write(
                        f'  Generated entry {journal_entry.voucher_number} for {next_date}'
                    )
                    generated_count += 1
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'  Failed to generate entry for {next_date}: {str(e)}')
                    )
                    raise
            
            # Get next date
            next_date = recurring_entry.get_next_posting_date(next_date)
        
        return generated_count 