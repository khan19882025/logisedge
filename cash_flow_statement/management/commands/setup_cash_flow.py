from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection


class Command(BaseCommand):
    help = 'Set up cash flow statement tables and initial data'

    def handle(self, *args, **options):
        self.stdout.write('Setting up Cash Flow Statement tables...')
        
        try:
            # Run migrations
            call_command('migrate', 'cash_flow_statement', verbosity=1)
            self.stdout.write(self.style.SUCCESS('✓ Migrations applied successfully'))
            
            # Create initial data
            self.create_initial_data()
            self.stdout.write(self.style.SUCCESS('✓ Initial data created successfully'))
            
            self.stdout.write(self.style.SUCCESS('Cash Flow Statement setup completed successfully!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during setup: {e}'))
    
    def create_initial_data(self):
        """Create initial categories and items"""
        from cash_flow_statement.models import CashFlowCategory, CashFlowItem
        
        # Create Operating Activities categories
        operating_categories = [
            ('Net Income', 'OPERATING', 1),
            ('Depreciation & Amortization', 'OPERATING', 2),
            ('Changes in Working Capital', 'OPERATING', 3),
            ('Other Operating Activities', 'OPERATING', 4),
        ]
        
        # Create Investing Activities categories
        investing_categories = [
            ('Capital Expenditures', 'INVESTING', 1),
            ('Investments', 'INVESTING', 2),
            ('Asset Sales', 'INVESTING', 3),
            ('Other Investing Activities', 'INVESTING', 4),
        ]
        
        # Create Financing Activities categories
        financing_categories = [
            ('Debt Issuance', 'FINANCING', 1),
            ('Debt Repayment', 'FINANCING', 2),
            ('Equity Issuance', 'FINANCING', 3),
            ('Dividends', 'FINANCING', 4),
            ('Other Financing Activities', 'FINANCING', 5),
        ]
        
        all_categories = operating_categories + investing_categories + financing_categories
        
        for name, category_type, order in all_categories:
            category, created = CashFlowCategory.objects.get_or_create(
                name=name,
                category_type=category_type,
                defaults={
                    'display_order': order,
                    'description': f'Standard {name.lower()} category for cash flow statements'
                }
            )
            
            if created:
                self.stdout.write(f'  Created category: {name}')
        
        self.stdout.write('  Initial categories created successfully') 