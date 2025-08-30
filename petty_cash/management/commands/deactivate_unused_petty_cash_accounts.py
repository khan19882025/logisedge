from django.core.management.base import BaseCommand
from django.db import transaction
from chart_of_accounts.models import ChartOfAccount
from company.company_model import Company


class Command(BaseCommand):
    help = 'Deactivate unused petty cash accounts (1002, 1003, 1006) and keep only 1000'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company',
            type=str,
            help='Company name to deactivate accounts for (defaults to first active company)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deactivated without making changes'
        )

    def handle(self, *args, **options):
        self.stdout.write('Deactivating unused petty cash accounts...')
        
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
        
        # Account codes to deactivate
        accounts_to_deactivate = ['1002', '1003', '1006']
        
        with transaction.atomic():
            for account_code in accounts_to_deactivate:
                try:
                    account = ChartOfAccount.objects.get(
                        account_code=account_code,
                        company=company
                    )
                    
                    if options.get('dry_run'):
                        self.stdout.write(
                            f'Would deactivate: {account.account_code} - {account.name}'
                        )
                    else:
                        account.is_active = False
                        account.save()
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Deactivated: {account.account_code} - {account.name}'
                            )
                        )
                        
                except ChartOfAccount.DoesNotExist:
                    self.stdout.write(
                        f'Account {account_code} not found - skipping'
                    )
        
        # Verify main petty cash account (1000) is active
        try:
            main_account = ChartOfAccount.objects.get(
                account_code='1000',
                company=company
            )
            if not main_account.is_active:
                if options.get('dry_run'):
                    self.stdout.write(
                        f'Would activate main petty cash account: {main_account.account_code} - {main_account.name}'
                    )
                else:
                    main_account.is_active = True
                    main_account.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Activated main petty cash account: {main_account.account_code} - {main_account.name}'
                        )
                    )
            else:
                self.stdout.write(
                    f'Main petty cash account is already active: {main_account.account_code} - {main_account.name}'
                )
        except ChartOfAccount.DoesNotExist:
            self.stdout.write(
                self.style.WARNING('Main petty cash account (1000) not found')
            )
        
        if options.get('dry_run'):
            self.stdout.write(
                self.style.WARNING('Dry run completed - no changes made')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Petty cash account cleanup completed')
            )