from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import StatusUpdate, NotificationLog

@receiver(post_save, sender=StatusUpdate)
def send_status_notification(sender, instance, created, **kwargs):
    """Send notification when a status update is created"""
    if created and instance.shipment.customer_email:
        try:
            # Create notification log
            notification = NotificationLog.objects.create(
                shipment=instance.shipment,
                status_update=instance,
                notification_type='email',
                recipient=instance.shipment.customer_email,
                subject=f'Shipment Status Update: {instance.shipment.shipment_id}',
                message=f'''
                Dear {instance.shipment.customer_name},
                
                Your shipment {instance.shipment.shipment_id} has been updated.
                
                New Status: {instance.get_status_display()}
                Location: {instance.location}
                Time: {instance.timestamp.strftime('%Y-%m-%d %H:%M')}
                
                {f'Description: {instance.description}' if instance.description else ''}
                
                Track your shipment at: {settings.SITE_URL}/shipment-tracking/{instance.shipment.pk}/
                
                Best regards,
                {settings.COMPANY_NAME}
                ''',
                sent_by=instance.updated_by,
                is_sent=True
            )
            
            # Send actual email if configured
            if hasattr(settings, 'EMAIL_HOST') and settings.EMAIL_HOST:
                send_mail(
                    subject=notification.subject,
                    message=notification.message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[notification.recipient],
                    fail_silently=True
                )
                notification.is_delivered = True
                notification.save()
                
        except Exception as e:
            # Log error but don't break the status update
            if 'notification' in locals():
                notification.error_message = str(e)
                notification.save()
