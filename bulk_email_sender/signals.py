from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.core.cache import cache
from django.utils import timezone
from .models import (
    EmailTemplate, EmailCampaign, RecipientList, Recipient, 
    EmailTracking, EmailQueue, EmailSettings
)


@receiver(post_save, sender=EmailTemplate)
def email_template_post_save(sender, instance, created, **kwargs):
    """Handle post-save actions for email templates"""
    
    # Clear template cache
    cache.delete(f'template_{instance.id}')
    cache.delete('templates_list')
    
    # Update available placeholders
    if created or instance.html_content or instance.plain_text_content:
        import re
        html_placeholders = re.findall(r'\{\{(\w+)\}\}', instance.html_content or '')
        text_placeholders = re.findall(r'\{\{(\w+)\}\}', instance.plain_text_content or '')
        all_placeholders = list(set(html_placeholders + text_placeholders))
        
        if instance.available_placeholders != all_placeholders:
            instance.available_placeholders = all_placeholders
            # Save without triggering signals again
            EmailTemplate.objects.filter(id=instance.id).update(
                available_placeholders=all_placeholders
            )


@receiver(post_save, sender=EmailCampaign)
def email_campaign_post_save(sender, instance, created, **kwargs):
    """Handle post-save actions for email campaigns"""
    
    # Clear campaign cache
    cache.delete(f'campaign_{instance.id}')
    cache.delete('campaigns_list')
    
    # If campaign status changed to 'queued', create email queue
    if instance.status == 'queued' and instance.recipients.exists():
        # TODO: Implement Celery tasks
        # from .tasks import create_campaign_queue
        # create_campaign_queue.delay(instance.id)
        pass
    
    # If campaign status changed to 'sending', start sending process
    elif instance.status == 'sending':
        # TODO: Implement Celery tasks
        # from .tasks import start_campaign_sending
        # start_campaign_sending.delay(instance.id)
        pass


@receiver(post_save, sender=RecipientList)
def recipient_list_post_save(sender, instance, created, **kwargs):
    """Handle post-save actions for recipient lists"""
    
    # Clear recipient list cache
    cache.delete(f'recipient_list_{instance.id}')
    cache.delete('recipient_lists_list')
    
    # Process uploaded file if present
    if created and instance.source_file:
        # TODO: Implement Celery tasks
        # from .tasks import process_recipient_list_file
        # process_recipient_list_file.delay(instance.id)
        pass


@receiver(post_save, sender=Recipient)
def recipient_post_save(sender, instance, created, **kwargs):
    """Handle post-save actions for recipients"""
    
    # Clear recipient cache
    cache.delete(f'recipient_{instance.id}')
    
    # Update campaign statistics
    if instance.campaign:
        cache.delete(f'campaign_{instance.campaign.id}_stats')


@receiver(post_save, sender=EmailTracking)
def email_tracking_post_save(sender, instance, created, **kwargs):
    """Handle post-save actions for email tracking"""
    
    if created:
        # Update recipient status based on tracking type
        recipient = instance.recipient
        
        if instance.tracking_type == 'open' and recipient.status == 'delivered':
            recipient.status = 'opened'
            recipient.opened_at = timezone.now()
            recipient.save(update_fields=['status', 'opened_at'])
        
        elif instance.tracking_type == 'click' and recipient.status in ['delivered', 'opened']:
            recipient.status = 'clicked'
            recipient.clicked_at = timezone.now()
            recipient.save(update_fields=['status', 'clicked_at'])
        
        elif instance.tracking_type == 'bounce':
            recipient.status = 'bounced'
            recipient.save(update_fields=['status'])
        
        elif instance.tracking_type == 'unsubscribe':
            recipient.status = 'unsubscribed'
            recipient.is_unsubscribed = True
            recipient.unsubscribe_date = timezone.now()
            recipient.save(update_fields=['status', 'is_unsubscribed', 'unsubscribe_date'])
        
        # Clear tracking cache
        cache.delete(f'tracking_{instance.id}')
        cache.delete(f'campaign_{recipient.campaign.id}_tracking')


@receiver(post_save, sender=EmailQueue)
def email_queue_post_save(sender, instance, created, **kwargs):
    """Handle post-save actions for email queues"""
    
    # Clear queue cache
    cache.delete(f'queue_{instance.id}')
    
    if created:
        # Start processing queue if status is pending
        if instance.status == 'pending':
            # TODO: Implement Celery tasks
            # from .tasks import process_email_queue
            # process_email_queue.delay(instance.id)
            pass


@receiver(post_save, sender=EmailSettings)
def email_settings_post_save(sender, instance, created, **kwargs):
    """Handle post-save actions for email settings"""
    
    # Clear settings cache
    cache.delete(f'email_settings_{instance.id}')
    cache.delete('email_settings_list')
    
    # If this is the first active settings, set as default
    if instance.is_active and created:
        EmailSettings.objects.exclude(id=instance.id).update(is_active=False)


@receiver(post_delete, sender=EmailTemplate)
def email_template_post_delete(sender, instance, **kwargs):
    """Handle post-delete actions for email templates"""
    
    # Clear template cache
    cache.delete(f'template_{instance.id}')
    cache.delete('templates_list')
    
    # Check if any campaigns are using this template
    campaigns_using_template = EmailCampaign.objects.filter(template=instance)
    if campaigns_using_template.exists():
        # Update campaigns to use a default template or mark as inactive
        campaigns_using_template.update(status='draft')


@receiver(post_delete, sender=EmailCampaign)
def email_campaign_post_delete(sender, instance, **kwargs):
    """Handle post-delete actions for email campaigns"""
    
    # Clear campaign cache
    cache.delete(f'campaign_{instance.id}')
    cache.delete('campaigns_list')
    
    # Clean up related data
    # Note: Recipients and tracking data will be automatically deleted due to CASCADE


@receiver(post_delete, sender=RecipientList)
def recipient_list_post_delete(sender, instance, **kwargs):
    """Handle post-delete actions for recipient lists"""
    
    # Clear recipient list cache
    cache.delete(f'recipient_list_{instance.id}')
    cache.delete('recipient_lists_list')


@receiver(post_delete, sender=Recipient)
def recipient_post_delete(sender, instance, **kwargs):
    """Handle post-delete actions for recipients"""
    
    # Clear recipient cache
    cache.delete(f'recipient_{instance.id}')
    
    # Update campaign statistics
    if instance.campaign:
        cache.delete(f'campaign_{instance.campaign.id}_stats')


@receiver(post_delete, sender=EmailTracking)
def email_tracking_post_delete(sender, instance, **kwargs):
    """Handle post-delete actions for email tracking"""
    
    # Clear tracking cache
    cache.delete(f'tracking_{instance.id}')
    
    # Update recipient status if needed
    recipient = instance.recipient
    if recipient:
        cache.delete(f'campaign_{recipient.campaign.id}_tracking')


@receiver(post_delete, sender=EmailQueue)
def email_queue_post_delete(sender, instance, **kwargs):
    """Handle post-delete actions for email queues"""
    
    # Clear queue cache
    cache.delete(f'queue_{instance.id}')


@receiver(post_delete, sender=EmailSettings)
def email_settings_post_delete(sender, instance, **kwargs):
    """Handle post-delete actions for email settings"""
    
    # Clear settings cache
    cache.delete(f'email_settings_{instance.id}')
    cache.delete('email_settings_list')


@receiver(pre_save, sender=EmailCampaign)
def email_campaign_pre_save(sender, instance, **kwargs):
    """Handle pre-save actions for email campaigns"""
    
    if instance.pk:  # Existing instance
        try:
            old_instance = EmailCampaign.objects.get(pk=instance.pk)
            
            # If status changed to 'completed', set completed_at
            if old_instance.status != 'completed' and instance.status == 'completed':
                instance.completed_at = timezone.now()
            
            # If status changed to 'started', set started_at
            if old_instance.status != 'sending' and instance.status == 'sending':
                instance.started_at = timezone.now()
                
        except EmailCampaign.DoesNotExist:
            pass


@receiver(pre_save, sender=EmailQueue)
def email_queue_pre_save(sender, instance, **kwargs):
    """Handle pre-save actions for email queues"""
    
    if instance.pk:  # Existing instance
        try:
            old_instance = EmailQueue.objects.get(pk=instance.pk)
            
            # If status changed to 'processing', set started_at
            if old_instance.status != 'processing' and instance.status == 'processing':
                instance.started_at = timezone.now()
            
            # If status changed to 'completed', set completed_at
            if old_instance.status != 'completed' and instance.status == 'completed':
                instance.completed_at = timezone.now()
                
        except EmailQueue.DoesNotExist:
            pass


@receiver(pre_save, sender=Recipient)
def recipient_pre_save(sender, instance, **kwargs):
    """Handle pre-save actions for recipients"""
    
    if instance.pk:  # Existing instance
        try:
            old_instance = Recipient.objects.get(pk=instance.pk)
            
            # If status changed to 'sent', set sent_at
            if old_instance.status != 'sent' and instance.status == 'sent':
                instance.sent_at = timezone.now()
            
            # If status changed to 'delivered', set delivered_at
            if old_instance.status != 'delivered' and instance.status == 'delivered':
                instance.delivered_at = timezone.now()
                
        except Recipient.DoesNotExist:
            pass


# Custom signals for business logic
from django.dispatch import Signal

# Signal emitted when a campaign is started
campaign_started = Signal()

# Signal emitted when a campaign is completed
campaign_completed = Signal()

# Signal emitted when an email is sent
email_sent = Signal()

# Signal emitted when an email is opened
email_opened = Signal()

# Signal emitted when an email is clicked
email_clicked = Signal()

# Signal emitted when an email bounces
email_bounced = Signal()

# Signal emitted when someone unsubscribes
email_unsubscribed = Signal()

# Signal emitted when a recipient list is processed
recipient_list_processed = Signal()

# Signal emitted when email settings are updated
email_settings_updated = Signal()


# Signal handlers for custom signals
@receiver(campaign_started)
def handle_campaign_started(sender, campaign, **kwargs):
    """Handle campaign started signal"""
    
    # Log campaign start
    # TODO: Implement SystemLog model
    # from .models import SystemLog
    # SystemLog.objects.create(
    #     action='campaign_started',
    #     details=f'Campaign "{campaign.name}" started',
    #     related_object_id=campaign.id,
    #     related_object_type='EmailCampaign'
    # )
    
    # Send notifications if configured
    # TODO: Implement notification system


@receiver(campaign_completed)
def handle_campaign_completed(sender, campaign, **kwargs):
    """Handle campaign completed signal"""
    
    # Log campaign completion
    # TODO: Implement SystemLog model
    # from .models import SystemLog
    # SystemLog.objects.create(
    #     action='campaign_completed',
    #     details=f'Campaign "{campaign.name}" completed',
    #     related_object_id=campaign.id,
    #     related_object_type='EmailCampaign'
    # )
    
    # Generate campaign report
    # TODO: Implement report generation
    
    # Send completion notifications
    # TODO: Implement notification system


@receiver(email_sent)
def handle_email_sent(sender, recipient, **kwargs):
    """Handle email sent signal"""
    
    # Update campaign statistics
    if recipient.campaign:
        cache.delete(f'campaign_{recipient.campaign.id}_stats')
    
    # Log email sent
    # TODO: Implement logging system


@receiver(email_opened)
def handle_email_opened(sender, recipient, **kwargs):
    """Handle email opened signal"""
    
    # Update campaign statistics
    if recipient.campaign:
        cache.delete(f'campaign_{recipient.campaign.id}_stats')
    
    # Log email opened
    # TODO: Implement logging system


@receiver(email_clicked)
def handle_email_clicked(sender, recipient, **kwargs):
    """Handle email clicked signal"""
    
    # Update campaign statistics
    if recipient.campaign:
        cache.delete(f'campaign_{recipient.campaign.id}_stats')
    
    # Log email clicked
    # TODO: Implement logging system


@receiver(email_bounced)
def handle_email_bounced(sender, recipient, **kwargs):
    """Handle email bounced signal"""
    
    # Update campaign statistics
    if recipient.campaign:
        cache.delete(f'campaign_{recipient.campaign.id}_stats')
    
    # Log email bounced
    # TODO: Implement logging system
    
    # Check if this is a hard bounce and should be removed from future campaigns
    # TODO: Implement bounce handling logic


@receiver(email_unsubscribed)
def handle_email_unsubscribed(sender, recipient, **kwargs):
    """Handle email unsubscribed signal"""
    
    # Update campaign statistics
    if recipient.campaign:
        cache.delete(f'campaign_{recipient.campaign.id}_stats')
    
    # Log email unsubscribed
    # TODO: Implement logging system
    
    # Add to global unsubscribe list
    # TODO: Implement global unsubscribe list


@receiver(recipient_list_processed)
def handle_recipient_list_processed(sender, recipient_list, **kwargs):
    """Handle recipient list processed signal"""
    
    # Log recipient list processing
    # TODO: Implement SystemLog model
    # from .models import SystemLog
    # SystemLog.objects.create(
    #     action='recipient_list_processed',
    #     details=f'Recipient list "{recipient_list.name}" processed',
    #     related_object_id=recipient_list.id,
    #     related_object_type='RecipientList'
    # )
    
    # Send processing completion notification
    # TODO: Implement notification system


@receiver(email_settings_updated)
def handle_email_settings_updated(sender, settings, **kwargs):
    """Handle email settings updated signal"""
    
    # Log settings update
    # TODO: Implement SystemLog model
    # from .models import SystemLog
    # SystemLog.objects.create(
    #     action='email_settings_updated',
    #     details=f'Email settings "{settings.name}" updated',
    #     related_object_id=settings.id,
    #     related_object_type='EmailSettings'
    # )
    
    # Test email configuration
    # TODO: Implement configuration testing
    
    # Send settings update notification
    # TODO: Implement notification system
