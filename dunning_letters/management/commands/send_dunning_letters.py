from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import date, timedelta
from dunning_letters.models import DunningLetter

class Command(BaseCommand):
    help = 'Send dunning letters for overdue invoices based on escalation schedule'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending emails',
        )
        parser.add_argument(
            '--level',
            choices=['friendly', 'firm', 'final'],
            help='Send only letters of specific level',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        specific_level = options['level']
        
        self.stdout.write(
            self.style.SUCCESS('Starting dunning letter process...')
        )
        
        # Get overdue invoices that need dunning letters
        try:
            from invoice.models import Invoice
            overdue_invoices = Invoice.objects.filter(
                due_date__lt=date.today(),
                status__in=['sent', 'overdue']
            ).select_related('customer')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error getting overdue invoices: {e}')
            )
            return
        
        if not overdue_invoices.exists():
            self.stdout.write(
                self.style.WARNING('No overdue invoices found.')
            )
            return
        
        self.stdout.write(f'Found {overdue_invoices.count()} overdue invoices.')
        
        letters_sent = 0
        letters_created = 0
        
        for invoice in overdue_invoices:
            overdue_days = (date.today() - invoice.due_date).days
            
            # Determine which level of letter to send based on overdue days
            if overdue_days >= 90:  # 90+ days overdue - Final notice
                level = 'final'
            elif overdue_days >= 60:  # 60+ days overdue - Firm reminder
                level = 'firm'
            elif overdue_days >= 30:  # 30+ days overdue - Friendly reminder
                level = 'friendly'
            else:
                continue  # Skip if less than 30 days overdue
            
            # Skip if specific level requested and doesn't match
            if specific_level and level != specific_level:
                continue
            
            # Check if letter already exists for this level
            existing_letter = DunningLetter.objects.filter(
                customer=invoice.customer,
                invoice=invoice,
                level=level
            ).first()
            
            if existing_letter:
                # Check if it's time to send a follow-up (every 7 days)
                if (existing_letter.email_sent and 
                    existing_letter.days_since_sent and 
                    existing_letter.days_since_sent >= 7):
                    
                    if not dry_run:
                        try:
                            # Send follow-up email
                            send_mail(
                                subject=existing_letter.subject,
                                message=existing_letter.content,
                                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@logisedge.com'),
                                recipient_list=[existing_letter.email_recipient or invoice.customer.email],
                                fail_silently=False,
                            )
                            existing_letter.mark_as_sent(existing_letter.email_recipient or invoice.customer.email)
                            letters_sent += 1
                            self.stdout.write(
                                f'  ✓ Sent follow-up {level} letter to {invoice.customer.customer_name} for invoice {invoice.invoice_number}'
                            )
                        except Exception as e:
                            self.stdout.write(
                                self.style.ERROR(f'  ✗ Failed to send email to {invoice.customer.customer_name}: {e}')
                            )
                    else:
                        self.stdout.write(
                            f'  [DRY RUN] Would send follow-up {level} letter to {invoice.customer.customer_name} for invoice {invoice.invoice_number}'
                        )
                        letters_sent += 1
                else:
                    self.stdout.write(
                        f'  - Skipping {level} letter to {invoice.customer.customer_name} (already sent {existing_letter.days_since_sent or 0} days ago)'
                    )
            else:
                # Create new letter
                if not dry_run:
                    try:
                        letter = DunningLetter.objects.create(
                            customer=invoice.customer,
                            invoice=invoice,
                            level=level,
                            overdue_amount=invoice.total_amount,
                            overdue_days=overdue_days,
                            due_date=invoice.due_date,
                        )
                        
                        # Send email immediately
                        if invoice.customer.email:
                            send_mail(
                                subject=letter.subject,
                                message=letter.content,
                                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@logisedge.com'),
                                recipient_list=[invoice.customer.email],
                                fail_silently=False,
                            )
                            letter.mark_as_sent(invoice.customer.email)
                            letters_sent += 1
                            self.stdout.write(
                                f'  ✓ Created and sent {level} letter to {invoice.customer.customer_name} for invoice {invoice.invoice_number}'
                            )
                        else:
                            self.stdout.write(
                                self.style.WARNING(f'  ⚠ Created {level} letter for {invoice.customer.customer_name} but no email address available')
                            )
                        
                        letters_created += 1
                        
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'  ✗ Failed to create letter for {invoice.customer.customer_name}: {e}')
                        )
                else:
                    self.stdout.write(
                        f'  [DRY RUN] Would create and send {level} letter to {invoice.customer.customer_name} for invoice {invoice.invoice_number}'
                    )
                    letters_created += 1
                    letters_sent += 1
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write('SUMMARY:')
        self.stdout.write(f'  Letters created: {letters_created}')
        self.stdout.write(f'  Letters sent: {letters_sent}')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('\nThis was a dry run. No actual emails were sent.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('\nDunning letter process completed successfully!')
            ) 