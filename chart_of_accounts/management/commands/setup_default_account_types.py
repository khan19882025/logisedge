from django.core.management.base import BaseCommand
from chart_of_accounts.models import AccountType


class Command(BaseCommand):
    help = 'Set up default account types and categories'

    def handle(self, *args, **options):
        self.stdout.write('Setting up default account types...')
        
        # Default account types for each category
        default_account_types = [
            # Assets
            {'name': 'Current Assets', 'category': 'ASSET', 'description': 'Assets that can be converted to cash within one year'},
            {'name': 'Fixed Assets', 'category': 'ASSET', 'description': 'Long-term assets used in business operations'},
            {'name': 'Intangible Assets', 'category': 'ASSET', 'description': 'Non-physical assets with value'},
            {'name': 'Investments', 'category': 'ASSET', 'description': 'Long-term investments and securities'},
            
            # Liabilities
            {'name': 'Current Liabilities', 'category': 'LIABILITY', 'description': 'Obligations due within one year'},
            {'name': 'Long-term Liabilities', 'category': 'LIABILITY', 'description': 'Obligations due after one year'},
            {'name': 'Provisions', 'category': 'LIABILITY', 'description': 'Estimated liabilities and provisions'},
            
            # Equity
            {'name': 'Owner\'s Equity', 'category': 'EQUITY', 'description': 'Owner\'s investment and retained earnings'},
            {'name': 'Share Capital', 'category': 'EQUITY', 'description': 'Capital contributed by shareholders'},
            {'name': 'Retained Earnings', 'category': 'EQUITY', 'description': 'Accumulated profits and losses'},
            {'name': 'Reserves', 'category': 'EQUITY', 'description': 'Various reserves and appropriations'},
            
            # Revenue
            {'name': 'Operating Revenue', 'category': 'REVENUE', 'description': 'Revenue from primary business activities'},
            {'name': 'Other Revenue', 'category': 'REVENUE', 'description': 'Revenue from secondary activities'},
            {'name': 'Interest Income', 'category': 'REVENUE', 'description': 'Income from interest and investments'},
            {'name': 'Gain on Sale', 'category': 'REVENUE', 'description': 'Gains from sale of assets'},
            
            # Expenses
            {'name': 'Operating Expenses', 'category': 'EXPENSE', 'description': 'Expenses related to business operations'},
            {'name': 'Administrative Expenses', 'category': 'EXPENSE', 'description': 'General administrative costs'},
            {'name': 'Selling Expenses', 'category': 'EXPENSE', 'description': 'Costs related to sales and marketing'},
            {'name': 'Financial Expenses', 'category': 'EXPENSE', 'description': 'Interest and financial charges'},
            {'name': 'Depreciation', 'category': 'EXPENSE', 'description': 'Depreciation and amortization expenses'},
            {'name': 'Tax Expenses', 'category': 'EXPENSE', 'description': 'Income tax and other taxes'},
        ]
        
        created_count = 0
        updated_count = 0
        
        for account_type_data in default_account_types:
            account_type, created = AccountType.objects.get_or_create(
                name=account_type_data['name'],
                defaults={
                    'category': account_type_data['category'],
                    'description': account_type_data['description'],
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created: {account_type.get_category_display()} - {account_type.name}')
                )
            else:
                # Update existing account type if needed
                if (account_type.category != account_type_data['category'] or 
                    account_type.description != account_type_data['description']):
                    account_type.category = account_type_data['category']
                    account_type.description = account_type_data['description']
                    account_type.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'↻ Updated: {account_type.get_category_display()} - {account_type.name}')
                    )
        
        total_account_types = AccountType.objects.count()
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(
                f'Account Types Setup Complete!\n'
                f'• Created: {created_count}\n'
                f'• Updated: {updated_count}\n'
                f'• Total Account Types: {total_account_types}'
            )
        )
        
        # Display summary by category
        self.stdout.write('\nAccount Types by Category:')
        for category_code, category_name in AccountType.ACCOUNT_CATEGORIES:
            count = AccountType.objects.filter(category=category_code).count()
            self.stdout.write(f'• {category_name}: {count}') 