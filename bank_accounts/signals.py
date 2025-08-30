from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import BankAccount, BankAccountTransaction


@receiver(pre_save, sender=BankAccount)
def bank_account_pre_save(sender, instance, **kwargs):
    """Handle pre-save operations for bank accounts"""
    
    # Set current balance to opening balance for new accounts
    if not instance.pk:  # New account
        instance.current_balance = instance.opening_balance
    
    # Ensure only one default account for payments/receipts
    if instance.is_default_for_payments:
        BankAccount.objects.filter(
            company=instance.company,
            is_default_for_payments=True
        ).exclude(pk=instance.pk).update(is_default_for_payments=False)
    
    if instance.is_default_for_receipts:
        BankAccount.objects.filter(
            company=instance.company,
            is_default_for_receipts=True
        ).exclude(pk=instance.pk).update(is_default_for_receipts=False)


@receiver(post_save, sender=BankAccountTransaction)
def transaction_post_save(sender, instance, created, **kwargs):
    """Handle post-save operations for transactions"""
    
    if created:
        # Update bank account balance
        bank_account = instance.bank_account
        if instance.transaction_type == 'credit':
            bank_account.current_balance += instance.amount
        else:  # debit
            bank_account.current_balance -= instance.amount
        
        bank_account.save(update_fields=['current_balance'])


@receiver(pre_delete, sender=BankAccount)
def bank_account_pre_delete(sender, instance, **kwargs):
    """Handle pre-delete operations for bank accounts"""
    
    # Check if account can be deleted
    if not instance.can_be_deleted():
        raise Exception("Cannot delete account with balance or transactions")


@receiver(pre_delete, sender=BankAccountTransaction)
def transaction_pre_delete(sender, instance, **kwargs):
    """Handle pre-delete operations for transactions"""
    
    # Reverse the transaction effect on bank account balance
    bank_account = instance.bank_account
    if instance.transaction_type == 'credit':
        bank_account.current_balance -= instance.amount
    else:  # debit
        bank_account.current_balance += instance.amount
    
    bank_account.save(update_fields=['current_balance']) 