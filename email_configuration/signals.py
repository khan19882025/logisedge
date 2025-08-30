from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from .models import EmailConfiguration, EmailTestResult, EmailNotification


@receiver(post_save, sender=EmailConfiguration)
def email_configuration_saved(sender, instance, created, **kwargs):
    """Signal handler for when email configuration is saved"""
    if created:
        # Log the creation of new email configuration
        print(f"New email configuration created: {instance.name} ({instance.protocol})")
        
        # Send notification to administrators if configured
        if hasattr(settings, 'EMAIL_CONFIGURATION_NOTIFICATIONS') and settings.EMAIL_CONFIGURATION_NOTIFICATIONS:
            try:
                admin_users = User.objects.filter(is_staff=True, is_active=True)
                admin_emails = [user.email for user in admin_users if user.email]
                
                if admin_emails:
                    send_mail(
                        subject=f'New Email Configuration Created: {instance.name}',
                        message=f'''
                        A new email configuration has been created:
                        
                        Name: {instance.name}
                        Protocol: {instance.protocol.upper()}
                        Host: {instance.host}
                        Port: {instance.port}
                        Encryption: {instance.encryption}
                        Created by: {instance.created_by.username}
                        Created at: {instance.created_at}
                        
                        Please review and test this configuration.
                        ''',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=admin_emails,
                        fail_silently=True,
                    )
            except Exception as e:
                print(f"Failed to send email configuration notification: {e}")
    
    else:
        # Configuration was updated
        print(f"Email configuration updated: {instance.name} ({instance.protocol})")


@receiver(post_save, sender=EmailTestResult)
def email_test_result_saved(sender, instance, created, **kwargs):
    """Signal handler for when email test result is saved"""
    if created:
        print(f"New email test result: {instance.configuration.name} - {instance.test_type} ({instance.status})")
        
        # Update configuration test status
        if instance.status in ['success', 'failed', 'partial']:
            instance.configuration.last_test_status = instance.status
            instance.configuration.last_test_message = instance.test_message
            instance.configuration.last_tested = instance.started_at
            instance.configuration.save(update_fields=['last_test_status', 'last_test_message', 'last_tested'])
        
        # Send notification for failed tests
        if instance.status == 'failed' and hasattr(settings, 'EMAIL_TEST_FAILURE_NOTIFICATIONS') and settings.EMAIL_TEST_FAILURE_NOTIFICATIONS:
            try:
                admin_users = User.objects.filter(is_staff=True, is_active=True)
                admin_emails = [user.email for user in admin_users if user.email]
                
                if admin_emails:
                    send_mail(
                        subject=f'Email Configuration Test Failed: {instance.configuration.name}',
                        message=f'''
                        An email configuration test has failed:
                        
                        Configuration: {instance.configuration.name}
                        Test Type: {instance.test_type}
                        Status: {instance.status}
                        Error Details: {instance.error_details or 'No details provided'}
                        Tested by: {instance.tested_by.username}
                        Started at: {instance.started_at}
                        
                        Please investigate and fix the configuration issues.
                        ''',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=admin_emails,
                        fail_silently=True,
                    )
            except Exception as e:
                print(f"Failed to send test failure notification: {e}")


@receiver(post_save, sender=EmailNotification)
def email_notification_saved(sender, instance, created, **kwargs):
    """Signal handler for when email notification is saved"""
    if created:
        print(f"New email notification created: {instance.subject} ({instance.type})")
        
        # If notification is scheduled for immediate sending, queue it
        if not instance.scheduled_at or instance.scheduled_at <= timezone.now():
            # This would typically trigger a background task to send the email
            print(f"Notification '{instance.subject}' queued for immediate sending")
        else:
            print(f"Notification '{instance.subject}' scheduled for {instance.scheduled_at}")


@receiver(post_delete, sender=EmailConfiguration)
def email_configuration_deleted(sender, instance, **kwargs):
    """Signal handler for when email configuration is deleted"""
    print(f"Email configuration deleted: {instance.name} ({instance.protocol})")
    
    # Send notification to administrators
    if hasattr(settings, 'EMAIL_CONFIGURATION_NOTIFICATIONS') and settings.EMAIL_CONFIGURATION_NOTIFICATIONS:
        try:
            admin_users = User.objects.filter(is_staff=True, is_active=True)
            admin_emails = [user.email for user in admin_users if user.email]
            
            if admin_emails:
                send_mail(
                    subject=f'Email Configuration Deleted: {instance.name}',
                    message=f'''
                    An email configuration has been deleted:
                    
                    Name: {instance.name}
                    Protocol: {instance.protocol.upper()}
                    Host: {instance.host}
                    Port: {instance.port}
                    Deleted by: {getattr(instance, 'deleted_by', 'Unknown')}
                    
                    Please ensure this configuration is no longer needed.
                    ''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=admin_emails,
                    fail_silently=True,
                )
        except Exception as e:
            print(f"Failed to send configuration deletion notification: {e}")


# Import timezone for scheduled notifications
from django.utils import timezone
