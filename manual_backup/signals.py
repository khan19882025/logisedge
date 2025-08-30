from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import logging

from .models import BackupSession, BackupAuditLog, BackupConfiguration

logger = logging.getLogger(__name__)


@receiver(post_save, sender=BackupSession)
def backup_session_post_save(sender, instance, created, **kwargs):
    """Handle post-save events for backup sessions"""
    if created:
        # Log the creation of a new backup session
        BackupAuditLog.objects.create(
            backup_session=instance,
            level='info',
            message=f'Backup session "{instance.name}" created',
            details={
                'backup_id': str(instance.backup_id),
                'reason': instance.reason,
                'priority': instance.priority,
                'configuration': instance.configuration.name if instance.configuration else None
            }
        )
        
        # Send notification if emails are configured
        if instance.notify_emails and not instance.notification_sent:
            try:
                send_backup_notification(instance, 'created')
                instance.notification_sent = True
                instance.save(update_fields=['notification_sent'])
            except Exception as e:
                logger.error(f"Failed to send backup creation notification: {e}")
    
    elif instance.status in ['completed', 'failed']:
        # Log completion or failure
        level = 'info' if instance.status == 'completed' else 'error'
        message = f'Backup session "{instance.name}" {instance.status}'
        
        BackupAuditLog.objects.create(
            backup_session=instance,
            level=level,
            message=message,
            details={
                'status': instance.status,
                'duration': instance.duration_seconds,
                'file_size': instance.file_size_bytes,
                'progress': instance.progress_percentage
            }
        )
        
        # Send completion/failure notification
        if instance.notify_emails and not instance.notification_sent:
            try:
                send_backup_notification(instance, instance.status)
                instance.notification_sent = True
                instance.save(update_fields=['notification_sent'])
            except Exception as e:
                logger.error(f"Failed to send backup completion notification: {e}")


@receiver(post_save, sender=BackupConfiguration)
def backup_configuration_post_save(sender, instance, created, **kwargs):
    """Handle post-save events for backup configurations"""
    if created:
        BackupAuditLog.objects.create(
            level='info',
            message=f'Backup configuration "{instance.name}" created',
            details={
                'backup_type': instance.backup_type,
                'compression_level': instance.compression_level,
                'encryption_type': instance.encryption_type,
                'retention_days': instance.retention_days
            }
        )
    else:
        BackupAuditLog.objects.create(
            level='info',
            message=f'Backup configuration "{instance.name}" updated',
            details={
                'backup_type': instance.backup_type,
                'compression_level': instance.compression_level,
                'encryption_type': instance.encryption_type,
                'retention_days': instance.retention_days,
                'is_active': instance.is_active
            }
        )


@receiver(post_delete, sender=BackupConfiguration)
def backup_configuration_post_delete(sender, instance, **kwargs):
    """Handle post-delete events for backup configurations"""
    BackupAuditLog.objects.create(
        level='warning',
        message=f'Backup configuration "{instance.name}" deleted',
        details={
            'backup_type': instance.backup_type,
            'compression_level': instance.compression_level,
            'encryption_type': instance.encryption_type
        }
    )


@receiver(pre_save, sender=BackupSession)
def backup_session_pre_save(sender, instance, **kwargs):
    """Handle pre-save events for backup sessions"""
    if instance.pk:  # Only for existing instances
        try:
            old_instance = BackupSession.objects.get(pk=instance.pk)
            
            # Check if status changed
            if old_instance.status != instance.status:
                BackupAuditLog.objects.create(
                    backup_session=instance,
                    level='info',
                    message=f'Backup status changed from {old_instance.status} to {instance.status}',
                    details={
                        'old_status': old_instance.status,
                        'new_status': instance.status,
                        'timestamp': timezone.now().isoformat()
                    }
                )
            
            # Check if progress changed significantly
            if abs(old_instance.progress_percentage - instance.progress_percentage) >= 10:
                BackupAuditLog.objects.create(
                    backup_session=instance,
                    level='info',
                    message=f'Backup progress updated to {instance.progress_percentage}%',
                    details={
                        'old_progress': old_instance.progress_percentage,
                        'new_progress': instance.progress_percentage,
                        'current_step': instance.current_step
                    }
                )
                
        except BackupSession.DoesNotExist:
            pass


def send_backup_notification(backup_session, event_type):
    """Send email notification for backup events"""
    if not hasattr(settings, 'EMAIL_HOST') or not settings.EMAIL_HOST:
        logger.warning("Email settings not configured, skipping notification")
        return
    
    subject_map = {
        'created': f'Backup Session Created: {backup_session.name}',
        'completed': f'Backup Completed: {backup_session.name}',
        'failed': f'Backup Failed: {backup_session.name}',
        'cancelled': f'Backup Cancelled: {backup_session.name}'
    }
    
    subject = subject_map.get(event_type, f'Backup Update: {backup_session.name}')
    
    message = f"""
Backup Session: {backup_session.name}
Event: {event_type.title()}
Status: {backup_session.status}
Priority: {backup_session.priority}
Reason: {backup_session.reason}
Created: {backup_session.created_at}
"""
    
    if event_type == 'completed':
        message += f"""
Duration: {backup_session.duration_formatted}
File Size: {backup_session.file_size_formatted}
File Path: {backup_session.file_path}
"""
    elif event_type == 'failed':
        message += f"""
Error Details: Check the audit log for more information
Current Step: {backup_session.current_step}
"""
    
    # Send to configured email addresses
    email_list = [email.strip() for email in backup_session.notify_emails.split(',') if email.strip()]
    
    if email_list:
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=email_list,
                fail_silently=False
            )
            logger.info(f"Backup notification sent for session {backup_session.backup_id}")
        except Exception as e:
            logger.error(f"Failed to send backup notification: {e}")
            raise
