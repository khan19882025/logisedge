from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from dispose_asset.models import DisposalType, ApprovalLevel
from decimal import Decimal


class Command(BaseCommand):
    help = 'Set up initial data for the Dispose Asset module'

    def handle(self, *args, **options):
        self.stdout.write('Setting up Dispose Asset module...')
        
        # Create disposal types
        disposal_types = [
            {
                'name': 'Sold',
                'description': 'Asset sold to another party for monetary value'
            },
            {
                'name': 'Scrapped',
                'description': 'Asset disposed of as scrap material'
            },
            {
                'name': 'Donated',
                'description': 'Asset donated to charity or organization'
            },
            {
                'name': 'Lost',
                'description': 'Asset lost or stolen'
            },
            {
                'name': 'Damaged',
                'description': 'Asset damaged beyond repair'
            },
            {
                'name': 'Obsolete',
                'description': 'Asset no longer useful due to technological advancement'
            }
        ]
        
        for disposal_type_data in disposal_types:
            disposal_type, created = DisposalType.objects.get_or_create(
                name=disposal_type_data['name'],
                defaults=disposal_type_data
            )
            if created:
                self.stdout.write(f'Created disposal type: {disposal_type.name}')
            else:
                self.stdout.write(f'Disposal type already exists: {disposal_type.name}')
        
        # Create approval levels
        approval_levels = [
            {
                'name': 'Asset Manager',
                'level': 1,
                'description': 'First level approval by asset manager',
                'required_role': 'asset_manager',
                'min_amount': Decimal('0.00'),
                'max_amount': Decimal('10000.00')
            },
            {
                'name': 'Finance Manager',
                'level': 2,
                'description': 'Second level approval by finance manager',
                'required_role': 'finance_manager',
                'min_amount': Decimal('10000.01'),
                'max_amount': Decimal('50000.00')
            },
            {
                'name': 'General Manager',
                'level': 3,
                'description': 'Final approval by general manager',
                'required_role': 'general_manager',
                'min_amount': Decimal('50000.01'),
                'max_amount': None
            }
        ]
        
        for approval_level_data in approval_levels:
            approval_level, created = ApprovalLevel.objects.get_or_create(
                level=approval_level_data['level'],
                defaults=approval_level_data
            )
            if created:
                self.stdout.write(f'Created approval level: {approval_level.name}')
            else:
                self.stdout.write(f'Approval level already exists: {approval_level.name}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up Dispose Asset module!')
        ) 