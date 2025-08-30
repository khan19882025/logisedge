from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum
from django.utils import timezone
from .models import (
    BankReconciliationSession, ERPTransaction, BankStatementEntry, 
    MatchedEntry
)


@receiver(post_save, sender=ERPTransaction)
def update_session_erp_totals(sender, instance, created, **kwargs):
    """Update session totals when ERP transaction is saved"""
    if created or instance.reconciliation_session:
        session = instance.reconciliation_session
        
        # Recalculate ERP totals
        erp_credits = ERPTransaction.objects.filter(
            reconciliation_session=session,
            credit_amount__gt=0
        ).aggregate(total=Sum('credit_amount'))['total'] or 0
        
        erp_debits = ERPTransaction.objects.filter(
            reconciliation_session=session,
            debit_amount__gt=0
        ).aggregate(total=Sum('debit_amount'))['total'] or 0
        
        # Update session
        session.total_erp_credits = erp_credits
        session.total_erp_debits = erp_debits
        session.save(update_fields=['total_erp_credits', 'total_erp_debits'])


@receiver(post_save, sender=BankStatementEntry)
def update_session_bank_totals(sender, instance, created, **kwargs):
    """Update session totals when bank statement entry is saved"""
    if created or instance.reconciliation_session:
        session = instance.reconciliation_session
        
        # Recalculate bank totals
        bank_credits = BankStatementEntry.objects.filter(
            reconciliation_session=session,
            credit_amount__gt=0
        ).aggregate(total=Sum('credit_amount'))['total'] or 0
        
        bank_debits = BankStatementEntry.objects.filter(
            reconciliation_session=session,
            debit_amount__gt=0
        ).aggregate(total=Sum('debit_amount'))['total'] or 0
        
        # Update session
        session.total_bank_credits = bank_credits
        session.total_bank_debits = bank_debits
        session.save(update_fields=['total_bank_credits', 'total_bank_debits'])


@receiver(post_delete, sender=ERPTransaction)
def update_session_erp_totals_on_delete(sender, instance, **kwargs):
    """Update session totals when ERP transaction is deleted"""
    if instance.reconciliation_session:
        session = instance.reconciliation_session
        
        # Recalculate ERP totals
        erp_credits = ERPTransaction.objects.filter(
            reconciliation_session=session,
            credit_amount__gt=0
        ).aggregate(total=Sum('credit_amount'))['total'] or 0
        
        erp_debits = ERPTransaction.objects.filter(
            reconciliation_session=session,
            debit_amount__gt=0
        ).aggregate(total=Sum('debit_amount'))['total'] or 0
        
        # Update session
        session.total_erp_credits = erp_credits
        session.total_erp_debits = erp_debits
        session.save(update_fields=['total_erp_credits', 'total_erp_debits'])


@receiver(post_delete, sender=BankStatementEntry)
def update_session_bank_totals_on_delete(sender, instance, **kwargs):
    """Update session totals when bank statement entry is deleted"""
    if instance.reconciliation_session:
        session = instance.reconciliation_session
        
        # Recalculate bank totals
        bank_credits = BankStatementEntry.objects.filter(
            reconciliation_session=session,
            credit_amount__gt=0
        ).aggregate(total=Sum('credit_amount'))['total'] or 0
        
        bank_debits = BankStatementEntry.objects.filter(
            reconciliation_session=session,
            debit_amount__gt=0
        ).aggregate(total=Sum('debit_amount'))['total'] or 0
        
        # Update session
        session.total_bank_credits = bank_credits
        session.total_bank_debits = bank_debits
        session.save(update_fields=['total_bank_credits', 'total_bank_debits'])


@receiver(post_save, sender=MatchedEntry)
def update_matched_entries_count(sender, instance, created, **kwargs):
    """Update session matched entries count"""
    if created:
        session = instance.reconciliation_session
        
        # Update matched entries count in session
        matched_count = MatchedEntry.objects.filter(
            reconciliation_session=session
        ).count()
        
        # This could be stored in the session model if needed
        # For now, we'll just ensure the match is properly recorded


@receiver(post_delete, sender=MatchedEntry)
def update_matched_entries_count_on_delete(sender, instance, **kwargs):
    """Update session matched entries count when match is deleted"""
    session = instance.reconciliation_session
    
    # Update matched entries count in session
    matched_count = MatchedEntry.objects.filter(
        reconciliation_session=session
    ).count()
    
    # This could be stored in the session model if needed


@receiver(post_save, sender=BankReconciliationSession)
def update_session_balances(sender, instance, created, **kwargs):
    """Update session closing balances when status changes to completed"""
    if instance.status == 'completed' and not instance.completed_at:
        # Calculate closing balances
        erp_net = instance.total_erp_credits - instance.total_erp_debits
        bank_net = instance.total_bank_credits - instance.total_bank_debits
        
        instance.closing_balance_erp = instance.opening_balance_erp + erp_net
        instance.closing_balance_bank = instance.opening_balance_bank + bank_net
        instance.completed_at = timezone.now()
        instance.save(update_fields=[
            'closing_balance_erp', 'closing_balance_bank', 'completed_at'
        ]) 