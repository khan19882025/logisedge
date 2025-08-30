from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import PaymentSchedule, PaymentInstallment, PaymentReminder
from django.db.models import Sum


@receiver(post_save, sender=PaymentSchedule)
def create_payment_installments(sender, instance, created, **kwargs):
    """Create installments when a payment schedule is created"""
    if created and instance.installment_count > 1:
        # Calculate installment amounts
        installment_amount = instance.total_amount / instance.installment_count
        due_date = instance.due_date
        
        for i in range(1, instance.installment_count + 1):
            PaymentInstallment.objects.create(
                payment_schedule=instance,
                installment_number=i,
                amount=installment_amount,
                due_date=due_date
            )


@receiver(pre_save, sender=PaymentSchedule)
def update_schedule_status(sender, instance, **kwargs):
    """Update schedule status based on payments"""
    if instance.pk:  # Only for existing instances
        old_instance = PaymentSchedule.objects.get(pk=instance.pk)
        
        # Check if status needs to be updated
        if instance.paid_amount >= instance.total_with_vat:
            instance.status = 'paid'
        elif instance.paid_amount > 0:
            instance.status = 'partially_paid'
        elif instance.due_date < timezone.now().date():
            instance.status = 'overdue'


@receiver(post_save, sender=PaymentInstallment)
def update_schedule_payments(sender, instance, **kwargs):
    """Update schedule payment amounts when installments are updated"""
    schedule = instance.payment_schedule
    
    # Recalculate total paid amount
    total_paid = schedule.installments.aggregate(
        total_paid=Sum('paid_amount')
    )['total_paid'] or 0
    
    schedule.paid_amount = total_paid
    schedule.outstanding_amount = schedule.total_with_vat - total_paid
    
    # Update status
    if total_paid >= schedule.total_with_vat:
        schedule.status = 'paid'
    elif total_paid > 0:
        schedule.status = 'partially_paid'
    elif schedule.due_date < timezone.now().date():
        schedule.status = 'overdue'
    
    schedule.save(update_fields=['paid_amount', 'outstanding_amount', 'status'])
