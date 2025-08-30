from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import DepositSlip, DepositSlipItem, DepositSlipAudit

# This file can be used for any signal handling in the future
# For example, automatic audit trail creation, notifications, etc.

@receiver(post_save, sender=DepositSlip)
def create_deposit_slip_audit(sender, instance, created, **kwargs):
    """Create audit trail entry when deposit slip is saved"""
    if created:
        # This is handled in the view for better control
        pass

@receiver(post_delete, sender=DepositSlipItem)
def update_deposit_slip_total_on_delete(sender, instance, **kwargs):
    """Update deposit slip total when item is deleted"""
    try:
        deposit_slip = instance.deposit_slip
        deposit_slip.save()  # This will recalculate the total
    except:
        pass  # Handle case where deposit slip is already deleted 