from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import BudgetPlan, BudgetItem, BudgetApproval, BudgetAuditLog


@receiver(post_save, sender=BudgetPlan)
def budget_plan_audit_log(sender, instance, created, **kwargs):
    """Create audit log entry for budget plan changes"""
    if created:
        action = 'create'
    else:
        action = 'update'
    
    BudgetAuditLog.objects.create(
        budget_plan=instance,
        action=action,
        user=instance.created_by if created else instance.updated_by,
        field_name='',
        old_value='',
        new_value=f"Budget {instance.budget_code} - {instance.budget_name}"
    )


@receiver(post_delete, sender=BudgetPlan)
def budget_plan_delete_audit_log(sender, instance, **kwargs):
    """Create audit log entry for budget plan deletion"""
    BudgetAuditLog.objects.create(
        budget_plan=instance,
        action='delete',
        user=instance.created_by,
        field_name='',
        old_value=f"Budget {instance.budget_code} - {instance.budget_name}",
        new_value=''
    )


@receiver(post_save, sender=BudgetApproval)
def budget_approval_audit_log(sender, instance, created, **kwargs):
    """Create audit log entry for budget approvals"""
    if created:
        action = instance.approval_type
        BudgetAuditLog.objects.create(
            budget_plan=instance.budget_plan,
            action=action,
            user=instance.approved_by,
            field_name='status',
            old_value=instance.budget_plan.status,
            new_value=instance.budget_plan.status
        )
