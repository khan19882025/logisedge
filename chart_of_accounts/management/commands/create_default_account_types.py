from django.core.management.base import BaseCommand
from chart_of_accounts.models import AccountType


class Command(BaseCommand):
    help = 'Create default account types for Chart of Accounts'

    def handle(self, *args, **options):
        # Define standard account types
        account_types = [
            # Assets
            {'name': 'Current Assets', 'category': 'ASSET', 'description': 'Assets that can be converted to cash within one year'},
            {'name': 'Fixed Assets', 'category': 'ASSET', 'description': 'Long-term assets used in business operations'},
            {'name': 'Cash and Cash Equivalents', 'category': 'ASSET', 'description': 'Cash on hand and in bank accounts'},
            {'name': 'Accounts Receivable', 'category': 'ASSET', 'description': 'Amounts owed by customers for goods/services'},
            {'name': 'Inventory', 'category': 'ASSET', 'description': 'Goods held for sale or in production'},
            {'name': 'Prepaid Expenses', 'category': 'ASSET', 'description': 'Expenses paid in advance'},
            {'name': 'Investments', 'category': 'ASSET', 'description': 'Short-term and long-term investments'},
            
            # Liabilities
            {'name': 'Current Liabilities', 'category': 'LIABILITY', 'description': 'Obligations due within one year'},
            {'name': 'Long-term Liabilities', 'category': 'LIABILITY', 'description': 'Obligations due after one year'},
            {'name': 'Accounts Payable', 'category': 'LIABILITY', 'description': 'Amounts owed to suppliers and vendors'},
            {'name': 'Accrued Expenses', 'category': 'LIABILITY', 'description': 'Expenses incurred but not yet paid'},
            {'name': 'Bank Loans', 'category': 'LIABILITY', 'description': 'Loans from financial institutions'},
            {'name': 'Taxes Payable', 'category': 'LIABILITY', 'description': 'Taxes owed to government authorities'},
            {'name': 'Deferred Revenue', 'category': 'LIABILITY', 'description': 'Revenue received but not yet earned'},
            
            # Equity
            {'name': 'Owner\'s Equity', 'category': 'EQUITY', 'description': 'Owner\'s investment in the business'},
            {'name': 'Retained Earnings', 'category': 'EQUITY', 'description': 'Accumulated profits not distributed'},
            {'name': 'Common Stock', 'category': 'EQUITY', 'description': 'Capital stock issued to shareholders'},
            {'name': 'Additional Paid-in Capital', 'category': 'EQUITY', 'description': 'Excess amount paid over par value'},
            {'name': 'Treasury Stock', 'category': 'EQUITY', 'description': 'Company\'s own stock repurchased'},
            
            # Revenue
            {'name': 'Operating Revenue', 'category': 'REVENUE', 'description': 'Revenue from primary business activities'},
            {'name': 'Freight Income', 'category': 'REVENUE', 'description': 'Revenue from freight and transportation services'},
            {'name': 'Warehousing Revenue', 'category': 'REVENUE', 'description': 'Revenue from storage and warehousing services'},
            {'name': 'Custom Clearance Fees', 'category': 'REVENUE', 'description': 'Revenue from customs clearance services'},
            {'name': 'Service Revenue', 'category': 'REVENUE', 'description': 'Revenue from various services provided'},
            {'name': 'Other Revenue', 'category': 'REVENUE', 'description': 'Revenue from non-operating activities'},
            {'name': 'Interest Income', 'category': 'REVENUE', 'description': 'Income from interest on investments'},
            
            # Expenses
            {'name': 'Operating Expenses', 'category': 'EXPENSE', 'description': 'Expenses related to business operations'},
            {'name': 'Fuel Expense', 'category': 'EXPENSE', 'description': 'Cost of fuel for vehicles and equipment'},
            {'name': 'Transport Vehicle Maintenance', 'category': 'EXPENSE', 'description': 'Maintenance costs for transport vehicles'},
            {'name': 'Salaries and Wages', 'category': 'EXPENSE', 'description': 'Employee compensation and benefits'},
            {'name': 'Rent Expense', 'category': 'EXPENSE', 'description': 'Cost of renting facilities and equipment'},
            {'name': 'Utilities Expense', 'category': 'EXPENSE', 'description': 'Cost of electricity, water, gas, etc.'},
            {'name': 'Office Supplies', 'category': 'EXPENSE', 'description': 'Cost of office materials and supplies'},
            {'name': 'Insurance Expense', 'category': 'EXPENSE', 'description': 'Cost of business insurance policies'},
            {'name': 'Depreciation Expense', 'category': 'EXPENSE', 'description': 'Depreciation of fixed assets'},
            {'name': 'Interest Expense', 'category': 'EXPENSE', 'description': 'Interest paid on loans and borrowings'},
            {'name': 'Tax Expense', 'category': 'EXPENSE', 'description': 'Taxes paid to government authorities'},
        ]

        created_count = 0
        updated_count = 0

        for account_type_data in account_types:
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
                    self.style.SUCCESS(f'Created account type: {account_type.name}')
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
                        self.style.WARNING(f'Updated account type: {account_type.name}')
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed account types. '
                f'Created: {created_count}, Updated: {updated_count}'
            )
        ) 