from django.core.management.base import BaseCommand
from chart_of_accounts.models import ChartOfAccount, AccountType
from company.company_model import Company
from multi_currency.models import Currency


class Command(BaseCommand):
    help = 'Create Accounts Receivable account in chart of accounts'

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

            # Check if Accounts Receivable account already exists
            existing_account = ChartOfAccount.objects.filter(
                name__icontains='Accounts Receivable',
                company=company
            ).first()

            if existing_account:
                self.stdout.write(
                    self.style.WARNING(f'Accounts Receivable account already exists: {existing_account}')
                )
                return

            # Create Accounts Receivable account
            ar_account = ChartOfAccount.objects.create(
                account_code='1300',
                name='Accounts Receivable',
                description='Amounts owed by customers for goods or services',
                account_type=asset_account_type,
                account_nature='DEBIT',
                currency=currency,
                company=company,
                is_active=True
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created Accounts Receivable account: {ar_account}'
                )
            )
            self.stdout.write(
                f'Account Code: {ar_account.account_code}'
            )
            self.stdout.write(
                f'Account Name: {ar_account.name}'
            )
            self.stdout.write(
                f'Account Type: {ar_account.account_type.name}'
            )
            self.stdout.write(
                f'Account Nature: {ar_account.account_nature}'
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating Accounts Receivable account: {str(e)}')
            )
