from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import (
    TransactionTagging, DefaultCostCenterMapping, TransactionTaggingRule,
    TransactionTaggingAuditLog, TransactionTaggingReport
)


@receiver(post_save, sender=TransactionTagging)
def create_transaction_tagging_audit_log(sender, instance, created, **kwargs):
    """Create audit log when transaction tagging is created or updated"""
    if created:
        TransactionTaggingAuditLog.objects.create(
            transaction_tagging=instance,
            action='create',
            user=instance.created_by
        )
    else:
        # For updates, we'll create a generic update log
        # In a real implementation, you might want to track specific field changes
        TransactionTaggingAuditLog.objects.create(
            transaction_tagging=instance,
            action='update',
            user=instance.updated_by
        )


@receiver(post_save, sender=DefaultCostCenterMapping)
def create_default_mapping_audit_log(sender, instance, created, **kwargs):
    """Create audit log when default cost center mapping is created or updated"""
    if created:
        # Log creation
        pass  # You can add specific logging here if needed
    else:
        # Log update
        pass  # You can add specific logging here if needed


@receiver(post_save, sender=TransactionTaggingRule)
def create_rule_audit_log(sender, instance, created, **kwargs):
    """Create audit log when transaction tagging rule is created or updated"""
    if created:
        # Log creation
        pass  # You can add specific logging here if needed
    else:
        # Log update
        pass  # You can add specific logging here if needed


@receiver(post_delete, sender=TransactionTagging)
def create_transaction_tagging_delete_log(sender, instance, **kwargs):
    """Create audit log when transaction tagging is deleted"""
    TransactionTaggingAuditLog.objects.create(
        transaction_tagging=instance,
        action='delete',
        user=instance.updated_by or instance.created_by
    )
