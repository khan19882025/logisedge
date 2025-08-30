from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Ledger, LedgerBatch
from chart_of_accounts.models import ChartOfAccount as Account
from decimal import Decimal
from django.db.models import Sum, Q


@receiver(post_save, sender=Ledger)
def update_account_balance(sender, instance, created, **kwargs):
    """Update account current balance when ledger entry is saved"""
    if instance.status == 'POSTED':
        account = instance.account
        
        # Calculate new balance for the account
        total_debit = Ledger.objects.filter(
            account=account,
            company=instance.company,
            fiscal_year=instance.fiscal_year,
            status='POSTED',
            entry_type='DR'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        total_credit = Ledger.objects.filter(
            account=account,
            company=instance.company,
            fiscal_year=instance.fiscal_year,
            status='POSTED',
            entry_type='CR'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Update account current balance
        account.current_balance = total_debit - total_credit
        account.save(update_fields=['current_balance'])


@receiver(post_delete, sender=Ledger)
def update_account_balance_on_delete(sender, instance, **kwargs):
    """Update account current balance when ledger entry is deleted"""
    if instance.status == 'POSTED':
        account = instance.account
        
        # Recalculate balance for the account
        total_debit = Ledger.objects.filter(
            account=account,
            company=instance.company,
            fiscal_year=instance.fiscal_year,
            status='POSTED',
            entry_type='DR'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        total_credit = Ledger.objects.filter(
            account=account,
            company=instance.company,
            fiscal_year=instance.fiscal_year,
            status='POSTED',
            entry_type='CR'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Update account current balance
        account.current_balance = total_debit - total_credit
        account.save(update_fields=['current_balance'])


@receiver(post_save, sender=LedgerBatch)
def update_batch_totals(sender, instance, created, **kwargs):
    """Update batch totals when ledger entries are added/removed"""
    # This signal can be used to recalculate batch totals
    # when ledger entries are associated with batches
    pass