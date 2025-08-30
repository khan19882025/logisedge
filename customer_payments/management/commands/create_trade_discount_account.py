from django.core.management.base import BaseCommand
from chart_of_accounts.models import ChartOfAccount, AccountType
from company.company_model import Company
from multi_currency.models import Currency


class Command(BaseCommand):
    help = 'Create Trade Discount account in chart of accounts'

    def handle(self, *args, **options):
        try:
            # Get or create company
            company = Company.objects.filter(is_active=True).first()
            if not company:
                self.stdout.write(
                    self.style.ERROR('No active company found. Please create a company first.')
                )
                return

            # Get or create Expense account type
            expense_account_type, created = AccountType.objects.get_or_create(
                name='Expense',
                defaults={
                    'category': 'EXPENSE',
                    'description': 'Expense accounts for business operations'
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created Expense account type: {expense_account_type.name}')
                )

            # Get default currency (AED)
            currency = Currency.objects.filter(code='AED').first()
            if not currency:
                currency = Currency.objects.first()

            # Check if Trade Discount account already exists
            existing_account = ChartOfAccount.objects.filter(
                name__icontains='Trade Discount',
                company=company
            ).first()

            if existing_account:
                self.stdout.write(
                    self.style.WARNING(f'Trade Discount account already exists: {existing_account}')
                )
                return

            # Create Trade Discount account
            trade_discount_account = ChartOfAccount.objects.create(
                account_code='5001',
                name='Trade Discount',
                description='Trade discounts given to customers',
                account_type=expense_account_type,
                account_nature='DEBIT',
                currency=currency,
                company=company,
                is_active=True
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created Trade Discount account: {trade_discount_account}'
                )
            )
            self.stdout.write(
                f'Account Code: {trade_discount_account.account_code}'
            )
            self.stdout.write(
                f'Account Name: {trade_discount_account.name}'
            )
            self.stdout.write(
                f'Account Type: {trade_discount_account.account_type.name}'
            )
            self.stdout.write(
                f'Account Nature: {trade_discount_account.account_nature}'
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating Trade Discount account: {str(e)}')
            )
