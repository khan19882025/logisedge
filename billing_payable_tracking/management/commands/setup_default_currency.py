from django.core.management.base import BaseCommand
from django.db import transaction
from multi_currency.models import Currency, CurrencySettings


class Command(BaseCommand):
    help = 'Set up default currency for billing system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--currency-code',
            type=str,
            default='USD',
            help='Currency code to set as default (default: USD)'
        )
        parser.add_argument(
            '--currency-name',
            type=str,
            default='US Dollar',
            help='Currency name (default: US Dollar)'
        )
        parser.add_argument(
            '--currency-symbol',
            type=str,
            default='$',
            help='Currency symbol (default: $)'
        )

    def handle(self, *args, **options):
        currency_code = options['currency_code']
        currency_name = options['currency_name']
        currency_symbol = options['currency_symbol']
        
        try:
            with transaction.atomic():
                # Create or get the currency
                currency, created = Currency.objects.get_or_create(
                    code=currency_code,
                    defaults={
                        'name': currency_name,
                        'symbol': currency_symbol,
                        'is_active': True,
                        'is_base_currency': True
                    }
                )
                
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Created currency: {currency_code} ({currency_name})'
                        )
                    )
                else:
                    # Update existing currency to be base currency if needed
                    if not currency.is_base_currency:
                        # Remove base currency flag from other currencies
                        Currency.objects.filter(is_base_currency=True).update(is_base_currency=False)
                        currency.is_base_currency = True
                        currency.save()
                        
                    self.stdout.write(
                        self.style.WARNING(
                            f'Currency {currency_code} already exists'
                        )
                    )
                
                # Create or update currency settings
                currency_settings, settings_created = CurrencySettings.objects.get_or_create(
                    defaults={'default_currency': currency}
                )
                
                if not settings_created:
                    currency_settings.default_currency = currency
                    currency_settings.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Updated default currency to: {currency_code}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Set default currency to: {currency_code}'
                        )
                    )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        'Default currency setup completed successfully!'
                    )
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Error setting up default currency: {str(e)}'
                )
            )
            raise