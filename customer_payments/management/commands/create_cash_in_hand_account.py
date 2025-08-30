from django.core.management.base import BaseCommand
from chart_of_accounts.models import ChartOfAccount, AccountType
from company.company_model import Company
from multi_currency.models import Currency


class Command(BaseCommand):
    help = 'Create Cash in Hand account in chart of accounts'

    def handle(self, *args, **options):
        try:
            # Get or create company
            company = Company.objects.filter(is_active=True).first()
            if not company:
                self.stdout.write(
                    self.style.ERROR('No active company found. Please create a company first.')
                )
                return

            # Get or create Asset account type
            asset_account_type, created = AccountType.objects.get_or_create(
                name='Asset',
                defaults={
                    'category': 'ASSET',
                    'description': 'Asset accounts for business resources'
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created Asset account type: {asset_account_type.name}')
                )

            # Get default currency (AED)
            currency = Currency.objects.filter(code='AED').first()
            if not currency:
                currency = Currency.objects.first()

            # Check if Cash in Hand account already exists
            existing_account = ChartOfAccount.objects.filter(
                name__icontains='Cash in Hand',
                company=company
            ).first()

            if existing_account:
                self.stdout.write(
                    self.style.WARNING(f'Cash in Hand account already exists: {existing_account}')
                )
                return

            # Create Cash in Hand account
            cash_account = ChartOfAccount.objects.create(
                account_code='1000',
                name='Cash in Hand',
                description='Physical cash available for transactions',
                account_type=asset_account_type,
                account_nature='DEBIT',
                currency=currency,
                company=company,
                is_active=True
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created Cash in Hand account: {cash_account}'
                )
            )
            self.stdout.write(
                f'Account Code: {cash_account.account_code}'
            )
            self.stdout.write(
                f'Account Name: {cash_account.name}'
            )
            self.stdout.write(
                f'Account Type: {cash_account.account_type.name}'
            )
            self.stdout.write(
                f'Account Nature: {cash_account.account_nature}'
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating Cash in Hand account: {str(e)}')
            )
