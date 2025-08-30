from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from .models import (
    ApprovalRequest, WorkflowLevelApproval, ApprovalComment,
    ApprovalNotification, ApprovalAuditLog
)


@receiver(post_save, sender=ApprovalRequest)
def handle_approval_request_created(sender, instance, created, **kwargs):
    """Handle when a new approval request is created"""
    if created:
        # Create audit log entry
        ApprovalAuditLog.objects.create(
            approval_request=instance,
            user=instance.requester,
            action='created',
            description=f"Approval request {instance.request_id} created by {instance.requester.username}",
            ip_address='',  # Will be set in the view
            user_agent=''
        )
        
        # Send notification to approvers if request is submitted
        if instance.status in ['submitted', 'pending', 'in_progress']:
            send_approval_notifications(instance)


@receiver(pre_save, sender=ApprovalRequest)
def handle_approval_request_status_change(sender, instance, **kwargs):
    """Handle status changes in approval requests"""
    if instance.pk:  # Only for existing instances
        try:
            old_instance = ApprovalRequest.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                # Status has changed
                action = instance.status
                if action == 'approved':
                    instance.approved_at = timezone.now()
                elif action == 'rejected':
                    instance.rejected_at = timezone.now()
                
                # Create audit log entry
                ApprovalAuditLog.objects.create(
                    approval_request=instance,
                    user=instance.requester,  # Will be updated in the view
                    action=action,
                    description=f"Request {instance.request_id} status changed to {instance.get_status_display()}",
                    ip_address='',
                    user_agent=''
                )
                
                # Send notifications for status change
                send_status_change_notifications(instance, old_instance.status)
        except ApprovalRequest.DoesNotExist:
            pass


@receiver(post_save, sender=WorkflowLevelApproval)
def handle_workflow_level_approval(sender, instance, created, **kwargs):
    """Handle when a workflow level approval is created or updated"""
    if created:
        # Create audit log entry
        ApprovalAuditLog.objects.create(
            approval_request=instance.approval_request,
            user=instance.approver,
            action=instance.status,
            description=f"Level {instance.workflow_level.level_number} {instance.status} by {instance.approver.username}",
            ip_address='',
            user_agent=''
        )
        
        # Send notification to requester
        send_approval_status_notification(instance)
        
        # Check if all approvals are complete for this level
        check_level_completion(instance.workflow_level, instance.approval_request)


@receiver(post_save, sender=ApprovalComment)
def handle_approval_comment(sender, instance, created, **kwargs):
    """Handle when a comment is added to an approval request"""
    if created:
        # Create audit log entry
        ApprovalAuditLog.objects.create(
            approval_request=instance.approval_request,
            user=instance.user,
            action='commented',
            description=f"Comment added by {instance.user.username}",
            ip_address='',
            user_agent=''
        )
        
        # Send notification about the comment
        if not instance.is_internal:
            send_comment_notification(instance)


def send_approval_notifications(approval_request):
    """Send notifications to approvers when a new request needs approval"""
    if not approval_request.current_level or not approval_request.current_approvers.exists():
        return
    
    approvers = approval_request.current_approvers.all()
    for approver in approvers:
        # Create notification
        ApprovalNotification.objects.create(
            approval_request=approval_request,
            recipient=approver,
            notification_type='approval_required',
            notification_method='in_app',
            title=f'Approval Required: {approval_request.title}',
            message=f'You have a new approval request {approval_request.request_id} that requires your attention.',
        )
        
        # Send email notification if configured
        if settings.EMAIL_HOST_USER:
            try:
                context = {
                    'approval_request': approval_request,
                    'approver': approver,
                    'approval_url': f"{settings.SITE_URL}/approval-workflow/requests/{approval_request.pk}/approve/"
                }
                
                email_html = render_to_string('approval_workflow/email/approval_required.html', context)
                email_text = render_to_string('approval_workflow/email/approval_required.txt', context)
                
                send_mail(
                    subject=f'Approval Required: {approval_request.title}',
                    message=email_text,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[approver.email],
                    html_message=email_html,
                    fail_silently=True
                )
            except Exception as e:
                # Log the error but don't fail the request
                print(f"Failed to send email notification: {e}")


def send_status_change_notifications(approval_request, old_status):
    """Send notifications when approval request status changes"""
    # Notify requester
    ApprovalNotification.objects.create(
        approval_request=approval_request,
        recipient=approval_request.requester,
        notification_type=approval_request.status,
        notification_method='in_app',
        title=f'Request {approval_request.request_id} {approval_request.get_status_display()}',
        message=f'Your approval request "{approval_request.title}" has been {approval_request.get_status_display()}.',
    )
    
    # Send email to requester
    if settings.EMAIL_HOST_USER:
        try:
            context = {
                'approval_request': approval_request,
                'old_status': old_status,
                'new_status': approval_request.status,
                'request_url': f"{settings.SITE_URL}/approval-workflow/requests/{approval_request.pk}/"
            }
            
            email_html = render_to_string('approval_workflow/email/status_change.html', context)
            email_text = render_to_string('approval_workflow/email/status_change.txt', context)
            
            send_mail(
                subject=f'Request {approval_request.request_id} {approval_request.get_status_display()}',
                message=email_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[approval_request.requester.email],
                html_message=email_html,
                fail_silently=True
            )
        except Exception as e:
            print(f"Failed to send status change email: {e}")


def send_approval_status_notification(approval):
    """Send notification when an approval is made"""
    approval_request = approval.approval_request
    
    # Notify requester
    ApprovalNotification.objects.create(
        approval_request=approval_request,
        recipient=approval_request.requester,
        notification_type=approval.status,
        notification_method='in_app',
        title=f'Request {approval_request.request_id} {approval.get_status_display()}',
        message=f'Your request "{approval_request.title}" has been {approval.get_status_display()} by {approval.approver.get_full_name()}.',
    )


def send_comment_notification(comment):
    """Send notification when a comment is added"""
    approval_request = comment.approval_request
    
    # Notify relevant parties (requester and current approvers)
    recipients = [approval_request.requester]
    if approval_request.current_approvers.exists():
        recipients.extend(approval_request.current_approvers.all())
    
    for recipient in recipients:
        if recipient != comment.user:  # Don't notify the comment author
            ApprovalNotification.objects.create(
                approval_request=approval_request,
                recipient=recipient,
                notification_type='commented',
                notification_method='in_app',
                title=f'New Comment: {approval_request.title}',
                message=f'A new comment has been added to request {approval_request.request_id} by {comment.user.get_full_name()}.',
            )


def check_level_completion(workflow_level, approval_request):
    """Check if all required approvals for a level are complete"""
    if workflow_level.level_type == 'parallel':
        # For parallel approvals, check if minimum required approvals are met
        approved_count = WorkflowLevelApproval.objects.filter(
            approval_request=approval_request,
            workflow_level=workflow_level,
            status='approved'
        ).count()
        
        if approved_count >= workflow_level.min_approvals_required:
            # Level is complete, move to next level or complete request
            move_to_next_level(approval_request)
    
    elif workflow_level.level_type == 'sequential':
        # For sequential approvals, check if all approvers have approved
        total_approvers = workflow_level.approvers.count()
        approved_count = WorkflowLevelApproval.objects.filter(
            approval_request=approval_request,
            workflow_level=workflow_level,
            status='approved'
        ).count()
        
        if approved_count >= total_approvers:
            # Level is complete, move to next level or complete request
            move_to_next_level(approval_request)


def move_to_next_level(approval_request):
    """Move approval request to the next level or complete it"""
    workflow_definition = approval_request.workflow_definition
    current_level = approval_request.current_level
    
    if current_level:
        # Find the next level
        next_level = workflow_definition.levels.filter(
            level_number__gt=current_level.level_number,
            is_active=True
        ).first()
        
        if next_level:
            # Move to next level
            approval_request.current_level = next_level
            approval_request.status = 'in_progress'
            
            # Assign approvers for the next level
            next_level_approvers = list(next_level.approvers.all())
            
            # Add group members if any
            for group in next_level.approver_groups.all():
                next_level_approvers.extend(list(group.user_set.all()))
            
            approval_request.current_approvers.set(next_level_approvers)
            approval_request.save()
            
            # Send notifications to new approvers
            send_approval_notifications(approval_request)
            
        else:
            # No more levels, request is complete
            approval_request.status = 'approved'
            approval_request.approved_at = timezone.now()
            approval_request.save()
            
            # Send completion notification
            send_status_change_notifications(approval_request, 'in_progress')
    else:
        # No current level, this shouldn't happen but handle gracefully
        approval_request.status = 'approved'
        approval_request.save()


# Disconnect signals for testing purposes
def disconnect_signals():
    """Disconnect all signals - useful for testing"""
    post_save.disconnect(handle_approval_request_created, sender=ApprovalRequest)
    pre_save.disconnect(handle_approval_request_status_change, sender=ApprovalRequest)
    post_save.disconnect(handle_workflow_level_approval, sender=WorkflowLevelApproval)
    post_save.disconnect(handle_approval_comment, sender=ApprovalComment)
