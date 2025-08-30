from django.core.management.base import BaseCommand
from django.db import transaction
from chart_of_accounts.models import ChartOfAccount, AccountType
from company.company_model import Company
from multi_currency.models import Currency


class Command(BaseCommand):
    help = 'Set up default Chart of Accounts with parent accounts and ledger accounts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company',
            type=str,
            help='Company name to set up accounts for (defaults to first active company)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of existing accounts'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear all existing accounts before creating new ones'
        )

    def handle(self, *args, **options):
        self.stdout.write('Setting up default Chart of Accounts...')
        
        # Get company
        company_name = options.get('company')
        if company_name:
            try:
                company = Company.objects.get(name=company_name, is_active=True)
            except Company.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Company "{company_name}" not found or not active')
                )
                return
        else:
            company = Company.objects.filter(is_active=True).first()
            if not company:
                self.stdout.write(
                    self.style.ERROR('No active company found')
                )
                return
        
        self.stdout.write(f'Using company: {company.name}')
        
        # Get default currency (AED)
        try:
            default_currency = Currency.objects.get(code='AED')
        except Currency.DoesNotExist:
            default_currency = Currency.objects.first()
            if not default_currency:
                self.stdout.write(
                    self.style.ERROR('No currency found')
                )
                return
        
        # Clear existing accounts if requested
        if options.get('clear_existing'):
            existing_count = ChartOfAccount.objects.filter(company=company).count()
            ChartOfAccount.objects.filter(company=company).delete()
            self.stdout.write(
                self.style.WARNING(f'Cleared {existing_count} existing accounts')
            )
        
        # Ensure account types exist
        self._ensure_account_types()
        
        # Define parent accounts and their ledger accounts
        accounts_structure = [
            # ASSETS
            {
                'parent': {'name': 'Petty Cash', 'type': 'Current Assets', 'code': '1000'},
                'ledgers': [
                    # Only using 1000 as main petty cash account - no sub-ledgers needed
                ]
            },
            {
                'parent': {'name': 'Bank Accounts', 'type': 'Current Assets', 'code': '1100'},
                'ledgers': [
                    {'name': 'Bank A', 'code': '1101'},
                    {'name': 'Bank B', 'code': '1102'},
                ]
            },
            {
                'parent': {'name': 'Accounts Receivable', 'type': 'Current Assets', 'code': '1200'},
                'ledgers': [
                    {'name': 'Accounts Receivable A', 'code': '1201'},
                    {'name': 'Accounts Receivable B', 'code': '1202'},
                ]
            },
            {
                'parent': {'name': 'Inventory / Stock', 'type': 'Current Assets', 'code': '1300'},
                'ledgers': [
                    {'name': 'Raw Materials', 'code': '1301'},
                    {'name': 'Work-in-Progress', 'code': '1302'},
                    {'name': 'Finished Goods', 'code': '1303'},
                ]
            },
            {
                'parent': {'name': 'Prepaid Expenses', 'type': 'Current Assets', 'code': '1400'},
                'ledgers': [
                    {'name': 'Prepaid Rent', 'code': '1401'},
                    {'name': 'Prepaid Insurance', 'code': '1402'},
                ]
            },
            {
                'parent': {'name': 'Fixed Assets', 'type': 'Fixed Assets', 'code': '1500'},
                'ledgers': [
                    {'name': 'Land', 'code': '1501'},
                    {'name': 'Building', 'code': '1502'},
                    {'name': 'Vehicles', 'code': '1503'},
                    {'name': 'Machinery', 'code': '1504'},
                ]
            },
            {
                'parent': {'name': 'Intangible Assets', 'type': 'Intangible Assets', 'code': '1600'},
                'ledgers': [
                    {'name': 'Goodwill', 'code': '1601'},
                    {'name': 'Patents', 'code': '1602'},
                ]
            },
            {
                'parent': {'name': 'Long-term Investments', 'type': 'Investments', 'code': '1700'},
                'ledgers': [
                    {'name': 'Long-term Investment A', 'code': '1701'},
                    {'name': 'Long-term Investment B', 'code': '1702'},
                ]
            },
            
            # LIABILITIES
            {
                'parent': {'name': 'Current Liabilities', 'type': 'Current Liabilities', 'code': '2000'},
                'ledgers': [
                    {'name': 'Vendor A Payable', 'code': '2001'},
                    {'name': 'Vendor B Payable', 'code': '2002'},
                    {'name': 'Short-term Loan A', 'code': '2003'},
                ]
            },
            {
                'parent': {'name': 'Non-Current Liabilities', 'type': 'Long-term Liabilities', 'code': '2100'},
                'ledgers': [
                    {'name': 'Bank Loan B', 'code': '2101'},
                ]
            },
            
            # EQUITY
            {
                'parent': {'name': 'Owner\'s Equity / Capital', 'type': 'Owner\'s Equity', 'code': '3000'},
                'ledgers': [
                    {'name': 'Owner\'s Capital A', 'code': '3001'},
                ]
            },
            {
                'parent': {'name': 'Retained Earnings / Reserves', 'type': 'Retained Earnings', 'code': '3100'},
                'ledgers': [
                    {'name': 'Retained Earnings', 'code': '3101'},
                ]
            },
            
            # REVENUE
            {
                'parent': {'name': 'Sales Revenue', 'type': 'Operating Revenue', 'code': '4000'},
                'ledgers': [
                    {'name': 'Local Sales', 'code': '4001'},
                    {'name': 'Export Sales', 'code': '4002'},
                ]
            },
            {
                'parent': {'name': 'Other Income', 'type': 'Other Revenue', 'code': '4100'},
                'ledgers': [
                    {'name': 'Service Income', 'code': '4101'},
                ]
            },
            
            # EXPENSES
            {
                'parent': {'name': 'Cost of Goods Sold (COGS)', 'type': 'Operating Expenses', 'code': '5000'},
                'ledgers': [
                    {'name': 'Material Cost', 'code': '5001'},
                    {'name': 'Direct Labor', 'code': '5002'},
                    {'name': 'Manufacturing Overhead', 'code': '5003'},
                ]
            },
            {
                'parent': {'name': 'Administrative Expenses', 'type': 'Administrative Expenses', 'code': '5100'},
                'ledgers': [
                    {'name': 'Salaries', 'code': '5101'},
                    {'name': 'Rent', 'code': '5102'},
                    {'name': 'Utilities', 'code': '5103'},
                    {'name': 'Office Supplies', 'code': '5104'},
                ]
            },
            {
                'parent': {'name': 'Selling & Distribution Expenses', 'type': 'Selling Expenses', 'code': '5200'},
                'ledgers': [
                    {'name': 'Marketing', 'code': '5201'},
                    {'name': 'Freight', 'code': '5202'},
                    {'name': 'Delivery Charges', 'code': '5203'},
                ]
            },
            {
                'parent': {'name': 'Financial Expenses', 'type': 'Financial Expenses', 'code': '5300'},
                'ledgers': [
                    {'name': 'Bank Charges', 'code': '5301'},
                    {'name': 'Interest Paid', 'code': '5302'},
                ]
            },
            {
                'parent': {'name': 'Depreciation & Amortization', 'type': 'Depreciation', 'code': '5400'},
                'ledgers': [
                    {'name': 'Depreciation', 'code': '5401'},
                    {'name': 'Amortization', 'code': '5402'},
                ]
            },
            {
                'parent': {'name': 'Other Expenses', 'type': 'Operating Expenses', 'code': '5500'},
                'ledgers': [
                    {'name': 'Miscellaneous Expense', 'code': '5501'},
                ]
            },
        ]
        
        created_parents = 0
        created_ledgers = 0
        updated_parents = 0
        updated_ledgers = 0
        
        with transaction.atomic():
            for group in accounts_structure:
                parent_data = group['parent']
                ledgers_data = group['ledgers']
                
                # Get account type for parent
                try:
                    account_type = AccountType.objects.get(name=parent_data['type'])
                except AccountType.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f'Account type "{parent_data["type"]}" not found')
                    )
                    continue
                
                # Create or update parent account
                parent_account, parent_created = ChartOfAccount.objects.get_or_create(
                    account_code=parent_data['code'],
                    company=company,
                    defaults={
                        'name': parent_data['name'],
                        'description': f'Parent account for {parent_data["name"]}',
                        'account_type': account_type,
                        'currency': default_currency,
                        'is_group': True,
                        'level': 0,
                        'is_active': True,
                    }
                )
                
                if parent_created:
                    created_parents += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Created parent: {parent_account.account_code} - {parent_account.name}')
                    )
                elif options.get('force'):
                    parent_account.name = parent_data['name']
                    parent_account.description = f'Parent account for {parent_data["name"]}'
                    parent_account.account_type = account_type
                    parent_account.save()
                    updated_parents += 1
                    self.stdout.write(
                        self.style.WARNING(f'↻ Updated parent: {parent_account.account_code} - {parent_account.name}')
                    )
                
                # Create or update ledger accounts
                for ledger_data in ledgers_data:
                    ledger_account, ledger_created = ChartOfAccount.objects.get_or_create(
                        account_code=ledger_data['code'],
                        company=company,
                        defaults={
                            'name': ledger_data['name'],
                            'description': f'Ledger account for {ledger_data["name"]}',
                            'account_type': account_type,
                            'parent_account': parent_account,
                            'currency': default_currency,
                            'is_group': False,
                            'level': 1,
                            'is_active': True,
                        }
                    )
                    
                    if ledger_created:
                        created_ledgers += 1
                        self.stdout.write(
                            f'  ✓ Created ledger: {ledger_account.account_code} - {ledger_account.name}'
                        )
                    elif options.get('force'):
                        ledger_account.name = ledger_data['name']
                        ledger_account.description = f'Ledger account for {ledger_data["name"]}'
                        ledger_account.account_type = account_type
                        ledger_account.parent_account = parent_account
                        ledger_account.save()
                        updated_ledgers += 1
                        self.stdout.write(
                            f'  ↻ Updated ledger: {ledger_account.account_code} - {ledger_account.name}'
                        )
        
        # Display summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS(
                f'Chart of Accounts Setup Complete!\n'
                f'• Created Parent Accounts: {created_parents}\n'
                f'• Created Ledger Accounts: {created_ledgers}\n'
                f'• Updated Parent Accounts: {updated_parents}\n'
                f'• Updated Ledger Accounts: {updated_ledgers}\n'
                f'• Total Accounts: {created_parents + created_ledgers + updated_parents + updated_ledgers}'
            )
        )
        
        # Display account summary by category
        self.stdout.write('\nAccounts by Category:')
        for category_code, category_name in AccountType.ACCOUNT_CATEGORIES:
            parent_count = ChartOfAccount.objects.filter(
                company=company,
                account_type__category=category_code,
                is_group=True
            ).count()
            ledger_count = ChartOfAccount.objects.filter(
                company=company,
                account_type__category=category_code,
                is_group=False
            ).count()
            self.stdout.write(f'• {category_name}: {parent_count} parent(s), {ledger_count} ledger(s)')
        
        self.stdout.write('\nSetup complete! You can now use these accounts in your transactions.')
    
    def _ensure_account_types(self):
        """Ensure all required account types exist"""
        required_types = [
            {'name': 'Current Assets', 'category': 'ASSET'},
            {'name': 'Fixed Assets', 'category': 'ASSET'},
            {'name': 'Intangible Assets', 'category': 'ASSET'},
            {'name': 'Investments', 'category': 'ASSET'},
            {'name': 'Current Liabilities', 'category': 'LIABILITY'},
            {'name': 'Long-term Liabilities', 'category': 'LIABILITY'},
            {'name': 'Owner\'s Equity', 'category': 'EQUITY'},
            {'name': 'Retained Earnings', 'category': 'EQUITY'},
            {'name': 'Operating Revenue', 'category': 'REVENUE'},
            {'name': 'Other Revenue', 'category': 'REVENUE'},
            {'name': 'Operating Expenses', 'category': 'EXPENSE'},
            {'name': 'Administrative Expenses', 'category': 'EXPENSE'},
            {'name': 'Selling Expenses', 'category': 'EXPENSE'},
            {'name': 'Financial Expenses', 'category': 'EXPENSE'},
            {'name': 'Depreciation', 'category': 'EXPENSE'},
        ]
        
        for type_data in required_types:
            AccountType.objects.get_or_create(
                name=type_data['name'],
                defaults={
                    'category': type_data['category'],
                    'description': f'{type_data["name"]} account type',
                    'is_active': True
                }
            )