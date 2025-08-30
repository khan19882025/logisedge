from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import ChequeRegister, ChequeStatusHistory, ChequeAlert


@receiver(post_save, sender=ChequeRegister)
def create_initial_status_history(sender, instance, created, **kwargs):
    """Create initial status history when cheque is created"""
    if created:
        ChequeStatusHistory.objects.create(
            cheque=instance,
            new_status=instance.status,
            changed_by=instance.created_by,
            remarks="Cheque created"
        )


@receiver(pre_save, sender=ChequeRegister)
def check_post_dated_cheques(sender, instance, **kwargs):
    """Check for post-dated cheques and create alerts"""
    if instance.cheque_date and instance.cheque_date > timezone.now().date():
        instance.is_post_dated = True
        
        # Create alert for post-dated cheques due soon (within 7 days)
        days_until_due = (instance.cheque_date - timezone.now().date()).days
        if days_until_due <= 7 and days_until_due > 0:
            ChequeAlert.objects.get_or_create(
                cheque=instance,
                alert_type='post_dated_due',
                defaults={
                    'message': f"Post-dated cheque {instance.cheque_number} is due in {days_until_due} days."
                }
            )


@receiver(pre_save, sender=ChequeRegister)
def check_overdue_cheques(sender, instance, **kwargs):
    """Check for overdue cheques and create alerts"""
    if (instance.status == 'pending' and 
        instance.cheque_date and 
        instance.cheque_date < timezone.now().date()):
        
        # Create alert for overdue cheques
        days_overdue = (timezone.now().date() - instance.cheque_date).days
        ChequeAlert.objects.get_or_create(
            cheque=instance,
            alert_type='overdue',
            defaults={
                'message': f"Cheque {instance.cheque_number} is overdue by {days_overdue} days."
            }
        )


@receiver(post_save, sender=ChequeStatusHistory)
def create_status_change_alerts(sender, instance, created, **kwargs):
    """Create alerts for status changes"""
    if created and instance.new_status in ['bounced', 'cleared']:
        alert_type = instance.new_status
        message = f"Cheque {instance.cheque.cheque_number} has been {instance.new_status}."
        
        ChequeAlert.objects.create(
            cheque=instance.cheque,
            alert_type=alert_type,
            message=message
        ) 