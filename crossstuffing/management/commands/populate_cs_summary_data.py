from django.core.management.base import BaseCommand
from crossstuffing.models import CrossStuffingSummary
from django.db import transaction


class Command(BaseCommand):
    help = 'Populate CS Summary items with sample data for new export fields'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if fields already have data',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        summary_items = CrossStuffingSummary.objects.all()
        
        if not summary_items.exists():
            self.stdout.write(
                self.style.WARNING('No CS Summary items found. Please create some summary items first.')
            )
            return
        
        self.stdout.write(f'Found {summary_items.count()} CS Summary items')
        
        updated_count = 0
        skipped_count = 0
        
        for item in summary_items:
            # Check if fields already have data
            has_data = any([
                item.exp_cntr,
                item.exp_size, 
                item.exp_seal
            ])
            
            if has_data and not force:
                self.stdout.write(
                    f'Skipping item {item.id} (already has data): '
                    f'exp_cntr="{item.exp_cntr}", exp_size="{item.exp_size}", exp_seal="{item.exp_seal}"'
                )
                skipped_count += 1
                continue
            
            # Generate sample data
            new_exp_cntr = f"EXP-{item.id:03d}"
            new_exp_size = "40ft" if item.id % 2 == 0 else "20ft"
            new_exp_seal = f"SEAL-{item.id:03d}"
            
            if dry_run:
                self.stdout.write(
                    f'Would update item {item.id}: '
                    f'exp_cntr="{new_exp_cntr}", exp_size="{new_exp_size}", exp_seal="{new_exp_seal}"'
                )
            else:
                # Update the fields
                item.exp_cntr = new_exp_cntr
                item.exp_size = new_exp_size
                item.exp_seal = new_exp_seal
                item.save()
                
                self.stdout.write(
                    f'Updated item {item.id}: '
                    f'exp_cntr="{new_exp_cntr}", exp_size="{new_exp_size}", exp_seal="{new_exp_seal}"'
                )
            
            updated_count += 1
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'DRY RUN: Would update {updated_count} items, skip {skipped_count} items'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully updated {updated_count} items, skipped {skipped_count} items'
                )
            )
            
            if updated_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        'New export fields have been populated with sample data. '
                        'Check your CS Summary table to see the new columns with data!'
                    )
                )
