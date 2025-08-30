from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import HBL, HBLHistory


@receiver(pre_save, sender=HBL)
def generate_hbl_number(sender, instance, **kwargs):
    """Generate HBL number if not provided"""
    if not instance.hbl_number:
        # Get the current year
        current_year = timezone.now().year
        
        # Get the count of HBLs for this year
        hbl_count = HBL.objects.filter(
            created_at__year=current_year
        ).count()
        
        # Generate HBL number: HBL-YYYY-XXXX (e.g., HBL-2024-0001)
        instance.hbl_number = f"HBL-{current_year}-{hbl_count + 1:04d}"


@receiver(post_save, sender=HBL)
def create_hbl_history(sender, instance, created, **kwargs):
    """Create history entry when HBL is created or updated"""
    if created:
        HBLHistory.objects.create(
            hbl=instance,
            action='created',
            description=f'HBL {instance.hbl_number} created',
            user=instance.created_by
        )
    else:
        # For updates, just create a general update entry
        HBLHistory.objects.create(
            hbl=instance,
            action='updated',
            description=f'HBL {instance.hbl_number} updated',
            user=instance.updated_by
        )
