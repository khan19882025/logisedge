from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import JournalEntry
from ledger.models import Ledger
from django.utils import timezone


@receiver(post_save, sender=JournalEntry)
def create_ledger_entries_from_journal(sender, instance, created, **kwargs):
    """
    Create ledger entries when a journal entry is posted
    """
    # Only create ledger entries when the journal entry is posted
    if instance.status == 'posted' and not created:
        # Check if ledger entries already exist for this journal entry
        existing_ledgers = Ledger.objects.filter(
            reference=instance.journal_number
        ).exists()
        
        if not existing_ledgers:
            # Create ledger entries for each journal entry line
            for line in instance.lines.all():
                # Create debit entry
                if line.debit_amount > 0:
                    Ledger.objects.create(
                        account=line.account,
                        entry_date=instance.date,
                        reference=instance.journal_number,
                        description=line.description or instance.description,
                        amount=line.debit_amount,
                        entry_type='DR',
                        status='POSTED',
                        company=instance.company,
                        fiscal_year=instance.fiscal_year,
                        created_by=instance.posted_by or instance.created_by,
                        created_at=timezone.now()
                    )
                
                # Create credit entry
                if line.credit_amount > 0:
                    Ledger.objects.create(
                        account=line.account,
                        entry_date=instance.date,
                        reference=instance.journal_number,
                        description=line.description or instance.description,
                        amount=line.credit_amount,
                        entry_type='CR',
                        status='POSTED',
                        company=instance.company,
                        fiscal_year=instance.fiscal_year,
                        created_by=instance.posted_by or instance.created_by,
                        created_at=timezone.now()
                    )