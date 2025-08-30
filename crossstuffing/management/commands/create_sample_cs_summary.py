from django.core.management.base import BaseCommand
from crossstuffing.models import CrossStuffing, CrossStuffingSummary
from django.db import transaction


class Command(BaseCommand):
    help = 'Create sample CS Summary items for testing the new export fields'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Check if we have any cross stuffing records
        crossstuffings = CrossStuffing.objects.all()
        
        if not crossstuffings.exists():
            self.stdout.write(
                self.style.WARNING('No Cross Stuffing records found. Please create some cross stuffing records first.')
            )
            return
        
        # Check if we already have summary items
        existing_summary = CrossStuffingSummary.objects.all()
        
        if existing_summary.exists():
            self.stdout.write(
                self.style.WARNING(
                    f'Found {existing_summary.count()} existing CS Summary items. '
                    'Use the populate_cs_summary_data command to add data to existing items.'
                )
            )
            return
        
        # Create sample summary items
        sample_data = [
            {
                'job_no': 'JOB-001',
                'items': 'Electronics, Clothing',
                'qty': 100,
                'imp_cntr': 'IMP-001',
                'size': '40ft',
                'seal': 'SEAL-001',
                'exp_cntr': 'EXP-001',
                'exp_size': '40ft',
                'exp_seal': 'SEAL-EXP-001',
                'remarks': 'Sample import/export data'
            },
            {
                'job_no': 'JOB-002',
                'items': 'Machinery Parts',
                'qty': 50,
                'imp_cntr': 'IMP-002',
                'size': '20ft',
                'seal': 'SEAL-002',
                'exp_cntr': 'EXP-002',
                'exp_size': '20ft',
                'exp_seal': 'SEAL-EXP-002',
                'remarks': 'Heavy machinery components'
            },
            {
                'job_no': 'JOB-003',
                'items': 'Textiles, Furniture',
                'qty': 200,
                'imp_cntr': 'IMP-003',
                'size': '40ft',
                'seal': 'SEAL-003',
                'exp_cntr': 'EXP-003',
                'exp_size': '40ft',
                'exp_seal': 'SEAL-EXP-003',
                'remarks': 'Mixed consumer goods'
            }
        ]
        
        if dry_run:
            self.stdout.write('DRY RUN: Would create the following sample CS Summary items:')
            for i, data in enumerate(sample_data, 1):
                self.stdout.write(f'  {i}. {data}')
        else:
            with transaction.atomic():
                created_items = []
                for data in sample_data:
                    # Use the first available cross stuffing record
                    crossstuffing = crossstuffings.first()
                    
                    summary_item = CrossStuffingSummary(
                        crossstuffing=crossstuffing,
                        **data
                    )
                    summary_item.save()
                    created_items.append(summary_item)
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully created {len(created_items)} sample CS Summary items!'
                    )
                )
                
                for item in created_items:
                    self.stdout.write(
                        f'  - {item.job_no}: {item.items} (Qty: {item.qty})'
                    )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        'Now you can see the new export fields (Exp CNTR, Size, Seal) '
                        'populated with sample data in your CS Summary table!'
                    )
                )
