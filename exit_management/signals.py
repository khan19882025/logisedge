from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import (
    ResignationRequest, ClearanceProcess, GratuityCalculation,
    FinalSettlement, ExitAuditLog
)
from django.utils import timezone


@receiver(post_save, sender=ResignationRequest)
def create_audit_log_on_resignation_save(sender, instance, created, **kwargs):
    """Create audit log when resignation request is saved"""
    if created:
        ExitAuditLog.objects.create(
            resignation=instance,
            action='resignation_submitted',
            details=f'Resignation request submitted for {instance.employee.full_name}'
        )
        
        # Send notification to manager
        if instance.manager:
            send_resignation_notification(instance, 'manager')
        
        # Send notification to HR
        send_resignation_notification(instance, 'hr')
    else:
        # Log status changes
        if instance.status == 'manager_review':
            ExitAuditLog.objects.create(
                resignation=instance,
                action='manager_approved',
                details=f'Resignation approved by manager: {instance.manager.get_full_name() if instance.manager else "Unknown"}'
            )
        elif instance.status == 'approved':
            ExitAuditLog.objects.create(
                resignation=instance,
                action='hr_approved',
                details=f'Resignation approved by HR: {instance.hr_manager.get_full_name() if instance.hr_manager else "Unknown"}'
            )


@receiver(post_save, sender=ClearanceProcess)
def create_clearance_audit_log(sender, instance, created, **kwargs):
    """Create audit log when clearance process is created"""
    if created:
        ExitAuditLog.objects.create(
            resignation=instance.resignation,
            action='clearance_started',
            details=f'Clearance process started for {instance.resignation.employee.full_name}'
        )


@receiver(post_save, sender=GratuityCalculation)
def create_gratuity_audit_log(sender, instance, created, **kwargs):
    """Create audit log when gratuity is calculated"""
    if created:
        ExitAuditLog.objects.create(
            resignation=instance.resignation,
            action='gratuity_calculated',
            details=f'Gratuity calculated: AED {instance.final_gratuity} for {instance.resignation.employee.full_name}'
        )


@receiver(post_save, sender=FinalSettlement)
def create_settlement_audit_log(sender, instance, created, **kwargs):
    """Create audit log when final settlement is created"""
    if created:
        ExitAuditLog.objects.create(
            resignation=instance.resignation,
            action='settlement_processed',
            details=f'Final settlement processed: AED {instance.net_settlement} for {instance.resignation.employee.full_name}'
        )


def send_resignation_notification(resignation, recipient_type):
    """Send email notification for resignation"""
    try:
        if recipient_type == 'manager' and resignation.manager:
            recipient_email = resignation.manager.email
            subject = f'Resignation Request - {resignation.employee.full_name}'
            template = 'exit_management/emails/manager_notification.html'
        elif recipient_type == 'hr':
            # Send to HR department email or default admin
            recipient_email = getattr(settings, 'HR_EMAIL', settings.ADMIN_EMAIL)
            subject = f'New Resignation Request - {resignation.employee.full_name}'
            template = 'exit_management/emails/hr_notification.html'
        else:
            return
        
        context = {
            'resignation': resignation,
            'employee': resignation.employee,
            'company_name': getattr(settings, 'COMPANY_NAME', 'LogisEdge')
        }
        
        html_message = render_to_string(template, context)
        plain_message = f"""
        Resignation Request
        
        Employee: {resignation.employee.full_name}
        Reference: {resignation.reference_number}
        Resignation Date: {resignation.resignation_date}
        Last Working Day: {resignation.last_working_day}
        Reason: {resignation.reason}
        
        Please review and take necessary action.
        """
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            html_message=html_message,
            fail_silently=True
        )
        
    except Exception as e:
        # Log error but don't fail the main operation
        print(f"Error sending resignation notification: {e}")


@receiver(post_save, sender=ResignationRequest)
def auto_assign_manager(sender, instance, created, **kwargs):
    """Auto-assign manager if not set"""
    if created and not instance.manager:
        # Try to get manager from employee's department or supervisor
        if instance.employee.department and instance.employee.department.manager:
            instance.manager = instance.employee.department.manager
            instance.save(update_fields=['manager'])


@receiver(post_save, sender=ClearanceProcess)
def auto_complete_clearance(sender, instance, **kwargs):
    """Auto-complete clearance if all items are cleared"""
    if not instance.is_completed:
        total_items = instance.clearance_items.count()
        if total_items > 0:
            cleared_items = instance.clearance_items.filter(status='cleared').count()
            if cleared_items == total_items:
                instance.is_completed = True
                instance.save(update_fields=['is_completed'])
                
                # Create audit log
                ExitAuditLog.objects.create(
                    resignation=instance.resignation,
                    action='clearance_completed',
                    details=f'Clearance process completed for {instance.resignation.employee.full_name}'
                )


@receiver(post_save, sender=ResignationRequest)
def update_employee_status(sender, instance, **kwargs):
    """Update employee status when exit is completed"""
    if instance.status == 'completed' and not instance.completed_at:
        # Update employee status to inactive
        employee = instance.employee
        employee.status = 'inactive'
        employee.save(update_fields=['status'])
        
        # Set completion date
        instance.completed_at = timezone.now()
        instance.save(update_fields=['completed_at'])
        
        # Create audit log
        ExitAuditLog.objects.create(
            resignation=instance,
            action='exit_completed',
            details=f'Exit process completed for {instance.employee.full_name}'
        ) 