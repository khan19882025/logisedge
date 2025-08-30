from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import ChartOfAccount, AccountType


@receiver(post_save, sender=ChartOfAccount)
def update_account_hierarchy(sender, instance, created, **kwargs):
    """Update account hierarchy when account is saved"""
    if created:
        # Auto-calculate level based on parent
        if instance.parent_account:
            instance.level = instance.parent_account.level + 1
        else:
            instance.level = 0
        
        # Auto-set is_group if has sub_accounts
        if instance.sub_accounts.exists():
            instance.is_group = True
        
        # Save without triggering signals again
        ChartOfAccount.objects.filter(pk=instance.pk).update(
            level=instance.level,
            is_group=instance.is_group
        )


@receiver(pre_save, sender=AccountType)
def validate_account_type(sender, instance, **kwargs):
    """Validate account type before saving"""
    # Ensure name is unique within the same category
    if AccountType.objects.filter(
        name=instance.name,
        category=instance.category
    ).exclude(pk=instance.pk if instance.pk else None).exists():
        from django.core.exceptions import ValidationError
        raise ValidationError(f"Account type '{instance.name}' already exists in category '{instance.get_category_display()}'") 