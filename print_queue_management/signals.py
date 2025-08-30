from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth.models import User
from .models import (
    Printer, PrinterGroup, PrintTemplate, ERPEvent, 
    AutoPrintRule, PrintJob, BatchPrintJob, PrintJobLog
)


# Printer Signals
@receiver(post_save, sender=Printer)
def printer_post_save(sender, instance, created, **kwargs):
    """Handle printer post-save actions"""
    if created:
        # Log printer creation
        PrintJobLog.objects.create(
            print_job=None,  # No specific job for printer creation
            action='created',
            message=f'Printer "{instance.name}" created',
            user=instance.created_by,
            ip_address=getattr(instance, '_ip_address', ''),
            user_agent=getattr(instance, '_user_agent', ''),
            details={
                'printer_id': str(instance.id),
                'printer_type': instance.printer_type,
                'location': instance.location
            }
        )
    else:
        # Log printer updates
        PrintJobLog.objects.create(
            print_job=None,
            action='updated',
            message=f'Printer "{instance.name}" updated',
            user=instance.updated_by,
            ip_address=getattr(instance, '_ip_address', ''),
            user_agent=getattr(instance, '_user_agent', ''),
            details={
                'printer_id': str(instance.id),
                'changes': getattr(instance, '_changes', {})
            }
        )


@receiver(post_delete, sender=Printer)
def printer_post_delete(sender, instance, **kwargs):
    """Handle printer deletion"""
    PrintJobLog.objects.create(
        print_job=None,
        action='deleted',
        message=f'Printer "{instance.name}" deleted',
        user=getattr(instance, '_deleted_by', None),
        ip_address=getattr(instance, '_ip_address', ''),
        user_agent=getattr(instance, '_user_agent', ''),
        details={
            'printer_name': instance.name,
            'printer_type': instance.printer_type,
            'location': instance.location
        }
    )


# Print Template Signals
@receiver(post_save, sender=PrintTemplate)
def print_template_post_save(sender, instance, created, **kwargs):
    """Handle print template post-save actions"""
    if created:
        PrintJobLog.objects.create(
            print_job=None,
            action='created',
            message=f'Print template "{instance.name}" created',
            user=instance.created_by,
            ip_address=getattr(instance, '_ip_address', ''),
            user_agent=getattr(instance, '_user_agent', ''),
            details={
                'template_id': str(instance.id),
                'template_type': instance.template_type
            }
        )
    else:
        PrintJobLog.objects.create(
            print_job=None,
            action='updated',
            message=f'Print template "{instance.name}" updated',
            user=instance.updated_by,
            ip_address=getattr(instance, '_ip_address', ''),
            user_agent=getattr(instance, '_user_agent', ''),
            details={
                'template_id': str(instance.id),
                'changes': getattr(instance, '_changes', {})
            }
        )


# Auto-Print Rule Signals
@receiver(post_save, sender=AutoPrintRule)
def auto_print_rule_post_save(sender, instance, created, **kwargs):
    """Handle auto-print rule post-save actions"""
    if created:
        PrintJobLog.objects.create(
            print_job=None,
            action='created',
            message=f'Auto-print rule "{instance.name}" created',
            user=instance.created_by,
            ip_address=getattr(instance, '_ip_address', ''),
            user_agent=getattr(instance, '_user_agent', ''),
            details={
                'rule_id': str(instance.id),
                'erp_event': instance.erp_event.name,
                'template': instance.print_template.name,
                'priority': instance.priority
            }
        )
    else:
        PrintJobLog.objects.create(
            print_job=None,
            action='updated',
            message=f'Auto-print rule "{instance.name}" updated',
            user=instance.updated_by,
            ip_address=getattr(instance, '_ip_address', ''),
            user_agent=getattr(instance, '_user_agent', ''),
            details={
                'rule_id': str(instance.id),
                'changes': getattr(instance, '_changes', {})
            }
        )


# Print Job Signals
@receiver(post_save, sender=PrintJob)
def print_job_post_save(sender, instance, created, **kwargs):
    """Handle print job post-save actions"""
    if created:
        # Create initial log entry
        PrintJobLog.objects.create(
            print_job=instance,
            action='created',
            message=f'Print job "{instance.job_number}" created',
            user=instance.created_by,
            ip_address=getattr(instance, '_ip_address', ''),
            user_agent=getattr(instance, '_user_agent', ''),
            details={
                'template': instance.print_template.name,
                'printer': instance.printer.name if instance.printer else 'Group',
                'priority': instance.priority,
                'pages': instance.pages,
                'copies': instance.copies
            }
        )
        
        # Check if auto-print rule exists and auto_print is enabled
        if instance.auto_print_rule and instance.auto_print_rule.auto_print:
            # Trigger automatic printing
            trigger_auto_print(instance)
    else:
        # Log status changes
        old_status = getattr(instance, '_old_status', None)
        if old_status and old_status != instance.status:
            PrintJobLog.objects.create(
                print_job=instance,
                action='status_changed',
                message=f'Print job status changed from {old_status} to {instance.status}',
                user=instance.updated_by,
                ip_address=getattr(instance, '_ip_address', ''),
                user_agent=getattr(instance, '_user_agent', ''),
                details={
                    'old_status': old_status,
                    'new_status': instance.status,
                    'timestamp': timezone.now().isoformat()
                }
            )


@receiver(pre_save, sender=PrintJob)
def print_job_pre_save(sender, instance, **kwargs):
    """Capture old values before saving print job"""
    if instance.pk:
        try:
            old_instance = PrintJob.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except PrintJob.DoesNotExist:
            pass


# Batch Print Job Signals
@receiver(post_save, sender=BatchPrintJob)
def batch_print_job_post_save(sender, instance, created, **kwargs):
    """Handle batch print job post-save actions"""
    if created:
        PrintJobLog.objects.create(
            print_job=None,
            action='created',
            message=f'Batch print job "{instance.name}" scheduled',
            user=instance.created_by,
            ip_address=getattr(instance, '_ip_address', ''),
            user_agent=getattr(instance, '_user_agent', ''),
            details={
                'batch_job_id': str(instance.id),
                'scheduled_at': instance.scheduled_at.isoformat(),
                'rule': instance.auto_print_rule.name
            }
        )
    else:
        # Log status changes
        old_status = getattr(instance, '_old_status', None)
        if old_status and old_status != instance.status:
            PrintJobLog.objects.create(
                print_job=None,
                action='status_changed',
                message=f'Batch job status changed from {old_status} to {instance.status}',
                user=instance.updated_by,
                ip_address=getattr(instance, '_ip_address', ''),
                user_agent=getattr(instance, '_user_agent', ''),
                details={
                    'batch_job_id': str(instance.id),
                    'old_status': old_status,
                    'new_status': instance.status,
                    'timestamp': timezone.now().isoformat()
                }
            )


@receiver(pre_save, sender=BatchPrintJob)
def batch_print_job_pre_save(sender, instance, **kwargs):
    """Capture old values before saving batch print job"""
    if instance.pk:
        try:
            old_instance = BatchPrintJob.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except BatchPrintJob.DoesNotExist:
            pass


# ERP Event Signals
@receiver(post_save, sender=ERPEvent)
def erp_event_post_save(sender, instance, created, **kwargs):
    """Handle ERP event post-save actions"""
    if created:
        PrintJobLog.objects.create(
            print_job=None,
            action='created',
            message=f'ERP event "{instance.name}" created',
            user=instance.created_by,
            ip_address=getattr(instance, '_ip_address', ''),
            user_agent=getattr(instance, '_user_agent', ''),
            details={
                'event_id': str(instance.id),
                'event_type': instance.event_type,
                'event_code': instance.event_code
            }
        )


# Custom signal for ERP event triggers
from django.dispatch import Signal

# Signal emitted when an ERP event occurs
erp_event_triggered = Signal()

@receiver(erp_event_triggered)
def handle_erp_event(sender, event_code, data, user, **kwargs):
    """Handle ERP events and trigger automatic printing"""
    try:
        # Find active auto-print rules for this event
        rules = AutoPrintRule.objects.filter(
            erp_event__event_code=event_code,
            is_active=True
        )
        
        for rule in rules:
            # Check conditions if specified
            if rule.conditions and not check_conditions(rule.conditions, data):
                continue
            
            # Create print job
            create_auto_print_job(rule, data, user)
            
    except Exception as e:
        # Log error
        PrintJobLog.objects.create(
            print_job=None,
            action='error',
            message=f'Error processing ERP event {event_code}: {str(e)}',
            user=user,
            ip_address=getattr(data, 'ip_address', ''),
            user_agent=getattr(data, 'user_agent', ''),
            details={
                'event_code': event_code,
                'error': str(e),
                'data': data
            }
        )


def check_conditions(conditions, data):
    """Check if data meets the specified conditions"""
    try:
        for key, value in conditions.items():
            if key not in data or data[key] != value:
                return False
        return True
    except Exception:
        return False


def create_auto_print_job(rule, data, user):
    """Create a print job based on auto-print rule"""
    try:
        # Determine printer
        printer = rule.printer
        if not printer and rule.printer_group:
            printer = rule.printer_group.get_available_printer()
        
        if not printer:
            raise ValueError("No available printer found")
        
        # Create print job
        job = PrintJob.objects.create(
            auto_print_rule=rule,
            print_template=rule.print_template,
            printer=printer,
            printer_group=rule.printer_group if not printer else None,
            priority=rule.priority,
            data=data,
            preview_required=rule.preview_required,
            created_by=user,
            updated_by=user
        )
        
        # Log job creation
        PrintJobLog.objects.create(
            print_job=job,
            action='auto_created',
            message=f'Print job automatically created from rule "{rule.name}"',
            user=user,
            ip_address=getattr(data, 'ip_address', ''),
            user_agent=getattr(data, 'user_agent', ''),
            details={
                'rule_id': str(rule.id),
                'erp_event': rule.erp_event.name,
                'template': rule.print_template.name
            }
        )
        
        return job
        
    except Exception as e:
        # Log error
        PrintJobLog.objects.create(
            print_job=None,
            action='error',
            message=f'Error creating auto-print job for rule "{rule.name}": {str(e)}',
            user=user,
            ip_address=getattr(data, 'ip_address', ''),
            user_agent=getattr(data, 'user_agent', ''),
            details={
                'rule_id': str(rule.id),
                'error': str(e),
                'data': data
            }
        )
        raise


def trigger_auto_print(print_job):
    """Trigger automatic printing for a print job"""
    try:
        # Update job status to processing
        print_job.status = 'processing'
        print_job.started_at = timezone.now()
        print_job.save()
        
        # Log processing start
        PrintJobLog.objects.create(
            print_job=print_job,
            action='processing_started',
            message=f'Print job processing started',
            user=print_job.created_by,
            ip_address='',
            user_agent='',
            details={
                'started_at': print_job.started_at.isoformat()
            }
        )
        
        # Here you would implement the actual printing logic
        # For now, we'll simulate it
        simulate_printing(print_job)
        
    except Exception as e:
        # Log error and mark job as failed
        print_job.status = 'failed'
        print_job.error_message = str(e)
        print_job.save()
        
        PrintJobLog.objects.create(
            print_job=print_job,
            action='failed',
            message=f'Print job failed: {str(e)}',
            user=print_job.created_by,
            ip_address='',
            user_agent='',
            details={
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }
        )


def simulate_printing(print_job):
    """Simulate the printing process"""
    import threading
    import time
    
    def print_worker():
        try:
            # Simulate printing time
            time.sleep(2)
            
            # Update job status
            print_job.status = 'printing'
            print_job.save()
            
            # Log printing start
            PrintJobLog.objects.create(
                print_job=print_job,
                action='printing_started',
                message=f'Print job printing started',
                user=print_job.created_by,
                ip_address='',
                user_agent='',
                details={
                    'timestamp': timezone.now().isoformat()
                }
            )
            
            # Simulate completion
            time.sleep(3)
            
            print_job.status = 'completed'
            print_job.completed_at = timezone.now()
            print_job.save()
            
            # Log completion
            PrintJobLog.objects.create(
                print_job=print_job,
                action='completed',
                message=f'Print job completed successfully',
                user=print_job.created_by,
                ip_address='',
                user_agent='',
                details={
                    'completed_at': print_job.completed_at.isoformat()
                }
            )
            
        except Exception as e:
            print_job.status = 'failed'
            print_job.error_message = str(e)
            print_job.save()
            
            PrintJobLog.objects.create(
                print_job=print_job,
                action='failed',
                message=f'Print job failed during execution: {str(e)}',
                user=print_job.created_by,
                ip_address='',
                user_agent='',
                details={
                    'error': str(e),
                    'timestamp': timezone.now().isoformat()
                }
            )
    
    # Start printing in background thread
    thread = threading.Thread(target=print_worker)
    thread.daemon = True
    thread.start()


# Utility function to emit ERP events
def emit_erp_event(event_code, data, user):
    """Emit an ERP event signal"""
    erp_event_triggered.send(
        sender=None,
        event_code=event_code,
        data=data,
        user=user
    )


# Example usage functions
def trigger_sales_order_approved(order_data, user):
    """Trigger automatic printing when sales order is approved"""
    emit_erp_event('sales_order_approved', order_data, user)


def trigger_delivery_order_dispatched(delivery_data, user):
    """Trigger automatic printing when delivery order is dispatched"""
    emit_erp_event('delivery_order_dispatched', delivery_data, user)


def trigger_goods_received(goods_data, user):
    """Trigger automatic printing when goods are received"""
    emit_erp_event('goods_received', goods_data, user)


def trigger_invoice_generated(invoice_data, user):
    """Trigger automatic printing when invoice is generated"""
    emit_erp_event('invoice_generated', invoice_data, user)
