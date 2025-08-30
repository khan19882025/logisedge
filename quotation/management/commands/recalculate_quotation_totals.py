from django.core.management.base import BaseCommand
from quotation.models import Quotation


class Command(BaseCommand):
    help = 'Recalculate VAT and totals for all quotations'

    def handle(self, *args, **options):
        quotations = Quotation.objects.all()
        updated_count = 0
        
        for quotation in quotations:
            old_vat = quotation.vat_amount
            old_total = quotation.total_amount
            
            # Recalculate totals
            quotation.calculate_totals()
            quotation.save(update_fields=['subtotal', 'vat_amount', 'additional_tax_amount', 'total_amount', 'tax_amount'])
            
            if old_vat != quotation.vat_amount or old_total != quotation.total_amount:
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Updated {quotation.quotation_number}: '
                        f'VAT {old_vat} → {quotation.vat_amount}, '
                        f'Total {old_total} → {quotation.total_amount}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully recalculated {updated_count} quotations')
        ) 