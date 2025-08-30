"""
Django management command to set up default Chart of Accounts for payment sources.
This command creates the necessary accounts if they don't exist and links them to payment sources.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from chart_of_accounts.models import ChartOfAccount, AccountType
from company.company_model import Company
from multi_currency.models import Currency


class Command(BaseCommand):
    help = 'Set up default Chart of Accounts for payment sources'

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

    def handle(self, *args, **options):
        self.stdout.write('Setting up default Chart of Accounts for payment sources...')
        
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
        
        # Get or create account types
        asset_type, _ = AccountType.objects.get_or_create(
            name='Asset',
            category='ASSET',
            defaults={'description': 'Asset accounts'}
        )
        
        liability_type, _ = AccountType.objects.get_or_create(
            name='Liability',
            category='LIABILITY',
            defaults={'description': 'Liability accounts'}
        )
        
        self.stdout.write('Account types ready')
        
        # Define default accounts for payment sources
        default_accounts = [
            # Prepaid accounts (Assets)
            {
                'code': '1200',
                'name': 'DP World Prepaid Deposit',
                'description': 'Prepaid deposits with DP World',
                'account_type': asset_type,
                'payment_type': 'prepaid'
            },
            {
                'code': '1210',
                'name': 'CDR Prepaid Account',
                'description': 'Prepaid account for CDR services',
                'account_type': asset_type,
                'payment_type': 'prepaid'
            },
            {
                'code': '1220',
                'name': 'Other Prepaid Deposits',
                'description': 'Other prepaid deposits and advances',
                'account_type': asset_type,
                'payment_type': 'prepaid'
            },
            
            # Postpaid accounts (Liabilities)
            {
                'code': '2000',
                'name': 'Accounts Payable',
                'description': 'Amounts owed to vendors and suppliers',
                'account_type': liability_type,
                'payment_type': 'postpaid'
            },
            {
                'code': '2010',
                'name': 'Credit Card Payable',
                'description': 'Amounts owed on credit cards',
                'account_type': liability_type,
                'payment_type': 'postpaid'
            },
            {
                'code': '2020',
                'name': 'Late Manifest Payable',
                'description': 'Amounts owed for late manifest charges',
                'account_type': liability_type,
                'payment_type': 'postpaid'
            },
            
            # Cash/Bank accounts (Assets)
            {
                'code': '1000',
                'name': 'Petty Cash',
                'description': 'Petty cash fund',
                'account_type': asset_type,
                'payment_type': 'cash_bank'
            },
            {
                'code': '1010',
                'name': 'Main Bank Account',
                'description': 'Primary bank account for transactions',
                'account_type': asset_type,
                'payment_type': 'cash_bank'
            },
            {
                'code': '1020',
                'name': 'Secondary Bank Account',
                'description': 'Secondary bank account',
                'account_type': asset_type,
                'payment_type': 'cash_bank'
            }
        ]
        
        # Create or update accounts
        created_count = 0
        updated_count = 0
        
        with transaction.atomic():
            for account_data in default_accounts:
                account_code = account_data['code']
                account_name = account_data['name']
                
                # Check if account exists
                existing_account = ChartOfAccount.objects.filter(
                    account_code=account_code,
                    company=company
                ).first()
                
                if existing_account and not options['force']:
                    self.stdout.write(f'Account {account_code} - {account_name} already exists')
                    continue
                
                if existing_account and options['force']:
                    # Update existing account
                    existing_account.name = account_name
                    existing_account.description = account_data['description']
                    existing_account.account_type = account_data['account_type']
                    existing_account.currency = default_currency
                    existing_account.save()
                    updated_count += 1
                    self.stdout.write(f'Updated account: {account_code} - {account_name}')
                else:
                    # Create new account
                    ChartOfAccount.objects.create(
                        account_code=account_code,
                        name=account_name,
                        description=account_data['description'],
                        account_type=account_data['account_type'],
                        currency=default_currency,
                        company=company,
                        is_active=True
                    )
                    created_count += 1
                    self.stdout.write(f'Created account: {account_code} - {account_name}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully set up Chart of Accounts for payment sources!\n'
                f'Created: {created_count} accounts\n'
                f'Updated: {updated_count} accounts\n'
                f'Total accounts: {created_count + updated_count}'
            )
        )
        
        # Display summary
        self.stdout.write('\nAccount Summary:')
        self.stdout.write('=' * 50)
        
        for account_data in default_accounts:
            account = ChartOfAccount.objects.filter(
                account_code=account_data['code'],
                company=company
            ).first()
            
            if account:
                status = '✓' if account.is_active else '✗'
                self.stdout.write(
                    f'{status} {account.account_code} - {account.name} '
                    f'({account_data["payment_type"]})'
                )
        
        self.stdout.write('\nSetup complete! You can now create payment sources and link them to these accounts.')
