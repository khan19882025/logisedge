from django.core.management.base import BaseCommand
from django.db import transaction
from customer_payments.models import CustomerPaymentInvoice
from invoice.models import Invoice
from decimal import Decimal


class Command(BaseCommand):
    help = 'Fix invoice statuses to match actual payment records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        self.stdout.write('🔍 Checking invoice statuses...')
        
        invoices_checked = 0
        invoices_updated = 0
        
        try:
            with transaction.atomic():
                # Get all invoices
                all_invoices = Invoice.objects.all()
                
                for invoice in all_invoices:
                    invoices_checked += 1
                    
                    # Get all payments for this invoice
                    payment_invoices = CustomerPaymentInvoice.objects.filter(invoice=invoice)
                    total_paid = sum(pi.amount_received for pi in payment_invoices)
                    
                    # Determine correct status
                    if total_paid >= invoice.total_sale:
                        correct_status = 'paid'
                    elif total_paid > 0:
                        correct_status = 'partial'
                    else:
                        correct_status = 'sent'
                    
                    # Check if status needs updating
                    if invoice.status != correct_status:
                        self.stdout.write(
                            f'🔄 Invoice {invoice.invoice_number}: '
                            f'Status "{invoice.status}" → "{correct_status}" '
                            f'(Paid: {total_paid}, Total: {invoice.total_sale})'
                        )
                        
                        if not dry_run:
                            invoice.status = correct_status
                            invoice.save(update_fields=['status'])
                        
                        invoices_updated += 1
                    else:
                        self.stdout.write(
                            f'✅ Invoice {invoice.invoice_number}: '
                            f'Status "{invoice.status}" is correct '
                            f'(Paid: {total_paid}, Total: {invoice.total_sale})'
                        )
                
                if dry_run:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'\n📊 DRY RUN SUMMARY:\n'
                            f'  • Invoices checked: {invoices_checked}\n'
                            f'  • Invoices that would be updated: {invoices_updated}\n'
                            f'  • Run without --dry-run to apply changes'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'\n✅ COMPLETED:\n'
                            f'  • Invoices checked: {invoices_checked}\n'
                            f'  • Invoices updated: {invoices_updated}\n'
                            f'  • All invoice statuses are now in sync with payment records'
                        )
                    )
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error: {str(e)}')
            )
            if not dry_run:
                self.stdout.write(
                    self.style.WARNING('⚠️ Changes were rolled back due to error')
                )
