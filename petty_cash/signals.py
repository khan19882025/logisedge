from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from ledger.models import Ledger
from .models import PettyCashBalance
from chart_of_accounts.models import ChartOfAccount
from decimal import Decimal


@receiver(post_save, sender=Ledger)
def update_petty_cash_balance_on_ledger_save(sender, instance, created, **kwargs):
    """Update petty cash balance when a ledger entry affects petty cash account"""
    if instance.status == 'POSTED':
        # Check if this ledger entry is for a petty cash account
        petty_cash_account = is_petty_cash_account(instance.account)
        
        if petty_cash_account:
            update_petty_cash_balance_from_ledger()


@receiver(post_delete, sender=Ledger)
def update_petty_cash_balance_on_ledger_delete(sender, instance, **kwargs):
    """Update petty cash balance when a ledger entry is deleted"""
    if instance.status == 'POSTED':
        # Check if this ledger entry was for a petty cash account
        petty_cash_account = is_petty_cash_account(instance.account)
        
        if petty_cash_account:
            update_petty_cash_balance_from_ledger()


def is_petty_cash_account(account):
    """Check if an account is a petty cash account"""
    # Only use account 1000 as the main petty cash account
    return account.account_code == '1000'


def update_petty_cash_balance_from_ledger(account=None):
    """Update petty cash balance based on ledger entries for account 1000 only"""
    try:
        from django.db.models import Sum
        
        # Get only the main petty cash account (1000)
        try:
            petty_cash_account = ChartOfAccount.objects.get(account_code='1000')
            
            # Calculate balance for account 1000 only
            account_debit = Ledger.objects.filter(
                account=petty_cash_account,
                status='POSTED',
                entry_type='DR'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            account_credit = Ledger.objects.filter(
                account=petty_cash_account,
                status='POSTED',
                entry_type='CR'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            # For asset accounts like petty cash: Balance = Debits - Credits
            total_balance = account_debit - account_credit
            
        except ChartOfAccount.DoesNotExist:
            total_balance = Decimal('0.00')
        
        # Get or create petty cash balance record
        petty_cash_balance, created = PettyCashBalance.objects.get_or_create(
            location='Main Office',  # Default location
            defaults={
                'current_balance': total_balance,
                'currency_id': 3  # Default currency (AED)
            }
        )
        
        # Update the balance
        petty_cash_balance.current_balance = total_balance
        petty_cash_balance.save()
        
        print(f"Updated total petty cash balance to {total_balance} from all petty cash accounts")
        
    except Exception as e:
        print(f"Error updating petty cash balance: {str(e)}")