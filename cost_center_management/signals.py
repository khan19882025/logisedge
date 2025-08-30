from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from .models import (
    Department, CostCenter, CostCenterBudget, CostCenterTransaction,
    CostCenterReport, CostCenterAuditLog
)


@receiver(post_save, sender=Department)
def department_audit_log(sender, instance, created, **kwargs):
    """Log department changes"""
    if created:
        action = 'create'
        field_name = ''
        old_value = ''
        new_value = f"Department: {instance.name} ({instance.code})"
    else:
        action = 'update'
        field_name = 'general'
        old_value = 'Updated'
        new_value = f"Department: {instance.name} ({instance.code})"
    
    CostCenterAuditLog.objects.create(
        cost_center=None,  # Departments don't have cost centers
        action=action,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
        user=instance.created_by if created else instance.updated_by,
    )


@receiver(post_save, sender=CostCenter)
def cost_center_audit_log(sender, instance, created, **kwargs):
    """Log cost center changes"""
    if created:
        action = 'create'
        field_name = ''
        old_value = ''
        new_value = f"Cost Center: {instance.name} ({instance.code})"
    else:
        action = 'update'
        field_name = 'general'
        old_value = 'Updated'
        new_value = f"Cost Center: {instance.name} ({instance.code})"
    
    CostCenterAuditLog.objects.create(
        cost_center=instance,
        action=action,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
        user=instance.created_by if created else instance.updated_by,
    )


@receiver(post_delete, sender=CostCenter)
def cost_center_delete_log(sender, instance, **kwargs):
    """Log cost center deletions"""
    CostCenterAuditLog.objects.create(
        cost_center=None,  # Cost center is already deleted
        action='delete',
        field_name='',
        old_value=f"Cost Center: {instance.name} ({instance.code})",
        new_value='',
        user=instance.updated_by or instance.created_by,
    )


@receiver(post_save, sender=CostCenterBudget)
def cost_center_budget_audit_log(sender, instance, created, **kwargs):
    """Log cost center budget changes"""
    if created:
        action = 'create'
        field_name = ''
        old_value = ''
        new_value = f"Budget: {instance.budget_amount} {instance.currency} for {instance.cost_center.name}"
    else:
        action = 'update'
        field_name = 'general'
        old_value = 'Updated'
        new_value = f"Budget: {instance.budget_amount} {instance.currency} for {instance.cost_center.name}"
    
    CostCenterAuditLog.objects.create(
        cost_center=instance.cost_center,
        action=action,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
        user=instance.created_by if created else instance.updated_by,
    )


@receiver(post_save, sender=CostCenterTransaction)
def cost_center_transaction_audit_log(sender, instance, created, **kwargs):
    """Log cost center transaction changes"""
    if created:
        action = 'create'
        field_name = ''
        old_value = ''
        new_value = f"Transaction: {instance.amount} {instance.currency} - {instance.description}"
    else:
        action = 'update'
        field_name = 'general'
        old_value = 'Updated'
        new_value = f"Transaction: {instance.amount} {instance.currency} - {instance.description}"
    
    CostCenterAuditLog.objects.create(
        cost_center=instance.cost_center,
        action=action,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
        user=instance.created_by if created else instance.updated_by,
    )
