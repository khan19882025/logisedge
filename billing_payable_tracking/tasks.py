import logging
from datetime import datetime, timedelta
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.urls import reverse

from .models import Bill, Vendor, BillReminder

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_bill_reminder_notifications(self):
    """
    Send reminder notifications for bills that are due soon or overdue
    This task should be scheduled to run daily
    """
    try:
        today = timezone.now().date()
        
        # Get bills that are due today or overdue
        due_bills = Bill.objects.filter(
            status__in=['pending', 'confirmed'],
            due_date__lte=today
        ).select_related('vendor', 'created_by')
        
        # Get bills due in the next 3 days (upcoming reminders)
        upcoming_bills = Bill.objects.filter(
            status__in=['pending', 'confirmed'],
            due_date__gt=today,
            due_date__lte=today + timedelta(days=3)
        ).select_related('vendor', 'created_by')
        
        notifications_sent = 0
        
        # Process overdue and due today bills
        for bill in due_bills:
            days_overdue = (today - bill.due_date).days
            
            # Check if we should send a reminder based on frequency
            should_send = False
            
            if days_overdue == 0:  # Due today
                should_send = True
                reminder_type = 'due_today'
            elif days_overdue > 0:  # Overdue
                # Send reminders every 3 days for overdue bills
                if days_overdue % 3 == 0:
                    should_send = True
                reminder_type = 'overdue'
            
            if should_send:
                # Check if we already sent a reminder today
                existing_reminder = BillReminder.objects.filter(
                    bill=bill,
                    reminder_date=today,
                    reminder_type=reminder_type
                ).exists()
                
                if not existing_reminder:
                    success = send_bill_reminder_email(bill, reminder_type, days_overdue)
                    if success:
                        # Create reminder record
                        BillReminder.objects.create(
                            bill=bill,
                            reminder_type=reminder_type,
                            reminder_date=today,
                            sent_to=bill.created_by.email if bill.created_by else '',
                            status='sent'
                        )
                        notifications_sent += 1
        
        # Process upcoming bills (3-day advance notice)
        for bill in upcoming_bills:
            days_until_due = (bill.due_date - today).days
            
            # Send 3-day advance notice
            if days_until_due == 3:
                existing_reminder = BillReminder.objects.filter(
                    bill=bill,
                    reminder_date=today,
                    reminder_type='upcoming'
                ).exists()
                
                if not existing_reminder:
                    success = send_bill_reminder_email(bill, 'upcoming', days_until_due)
                    if success:
                        BillReminder.objects.create(
                            bill=bill,
                            reminder_type='upcoming',
                            reminder_date=today,
                            sent_to=bill.created_by.email if bill.created_by else '',
                            status='sent'
                        )
                        notifications_sent += 1
        
        logger.info(f"Bill reminder notifications completed. Sent {notifications_sent} notifications.")
        return f"Successfully sent {notifications_sent} bill reminder notifications"
        
    except Exception as e:
        logger.error(f"Error in send_bill_reminder_notifications: {str(e)}")
        # Retry the task
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def mark_overdue_bills(self):
    """
    Mark bills as overdue if they are past their due date
    This task should be scheduled to run daily
    """
    try:
        today = timezone.now().date()
        
        # Find bills that are past due date and not yet marked as overdue
        overdue_bills = Bill.objects.filter(
            status__in=['pending', 'confirmed'],
            due_date__lt=today
        )
        
        updated_count = 0
        for bill in overdue_bills:
            bill.status = 'overdue'
            bill.save(update_fields=['status'])
            updated_count += 1
            
            logger.info(f"Marked bill {bill.bill_no} as overdue (due: {bill.due_date})")
        
        logger.info(f"Marked {updated_count} bills as overdue")
        return f"Successfully marked {updated_count} bills as overdue"
        
    except Exception as e:
        logger.error(f"Error in mark_overdue_bills: {str(e)}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_daily_summary_report(self):
    """
    Send daily summary report to administrators
    This task should be scheduled to run daily in the morning
    """
    try:
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        # Gather statistics
        stats = {
            'total_bills': Bill.objects.count(),
            'pending_bills': Bill.objects.filter(status='pending').count(),
            'overdue_bills': Bill.objects.filter(status='overdue').count(),
            'due_today': Bill.objects.filter(due_date=today, status__in=['pending', 'confirmed']).count(),
            'due_this_week': Bill.objects.filter(
                due_date__range=[today, today + timedelta(days=7)],
                status__in=['pending', 'confirmed']
            ).count(),
            'bills_created_yesterday': Bill.objects.filter(created_at__date=yesterday).count(),
            'bills_paid_yesterday': Bill.objects.filter(
                status='paid',
                updated_at__date=yesterday
            ).count(),
        }
        
        # Get recent bills for the report
        recent_overdue = Bill.objects.filter(status='overdue').order_by('due_date')[:10]
        due_today = Bill.objects.filter(
            due_date=today,
            status__in=['pending', 'confirmed']
        ).order_by('amount')[:10]
        
        # Get admin users to send the report to
        admin_users = User.objects.filter(
            is_staff=True,
            is_active=True,
            email__isnull=False
        ).exclude(email='')
        
        if not admin_users.exists():
            logger.warning("No admin users found to send daily summary report")
            return "No admin users found to send report"
        
        # Send email to each admin
        emails_sent = 0
        for admin in admin_users:
            try:
                subject = f"Daily Billing Summary - {today.strftime('%B %d, %Y')}"
                
                # Render email template
                html_content = render_to_string('billing_payable_tracking/emails/daily_summary.html', {
                    'admin': admin,
                    'stats': stats,
                    'recent_overdue': recent_overdue,
                    'due_today': due_today,
                    'date': today,
                })
                
                # Send email
                send_mail(
                    subject=subject,
                    message='',  # Plain text version
                    html_message=html_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[admin.email],
                    fail_silently=False
                )
                
                emails_sent += 1
                logger.info(f"Sent daily summary report to {admin.email}")
                
            except Exception as e:
                logger.error(f"Failed to send daily summary to {admin.email}: {str(e)}")
                continue
        
        return f"Successfully sent daily summary report to {emails_sent} administrators"
        
    except Exception as e:
        logger.error(f"Error in send_daily_summary_report: {str(e)}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def cleanup_old_reminders(self):
    """
    Clean up old bill reminders (older than 90 days)
    This task should be scheduled to run weekly
    """
    try:
        cutoff_date = timezone.now().date() - timedelta(days=90)
        
        deleted_count, _ = BillReminder.objects.filter(
            reminder_date__lt=cutoff_date
        ).delete()
        
        logger.info(f"Cleaned up {deleted_count} old bill reminders")
        return f"Successfully cleaned up {deleted_count} old bill reminders"
        
    except Exception as e:
        logger.error(f"Error in cleanup_old_reminders: {str(e)}")
        raise self.retry(exc=e)


def send_bill_reminder_email(bill, reminder_type, days_info):
    """
    Helper function to send bill reminder email
    """
    try:
        if not bill.created_by or not bill.created_by.email:
            logger.warning(f"No email address for bill {bill.bill_no} creator")
            return False
        
        # Determine subject and template based on reminder type
        if reminder_type == 'overdue':
            subject = f"OVERDUE: Bill {bill.bill_no} - {days_info} days overdue"
            template = 'billing_payable_tracking/emails/overdue_reminder.html'
        elif reminder_type == 'due_today':
            subject = f"DUE TODAY: Bill {bill.bill_no} - Payment Required"
            template = 'billing_payable_tracking/emails/due_today_reminder.html'
        elif reminder_type == 'upcoming':
            subject = f"UPCOMING: Bill {bill.bill_no} - Due in {days_info} days"
            template = 'billing_payable_tracking/emails/upcoming_reminder.html'
        else:
            logger.error(f"Unknown reminder type: {reminder_type}")
            return False
        
        # Render email content
        html_content = render_to_string(template, {
            'bill': bill,
            'user': bill.created_by,
            'days_info': days_info,
            'bill_url': f"{settings.SITE_URL}/accounting/billing-payable-tracking/bills/{bill.id}/",
        })
        
        # Send email
        send_mail(
            subject=subject,
            message='',  # Plain text version
            html_message=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[bill.created_by.email],
            fail_silently=False
        )
        
        logger.info(f"Sent {reminder_type} reminder for bill {bill.bill_no} to {bill.created_by.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send reminder email for bill {bill.bill_no}: {str(e)}")
        return False


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def generate_vendor_payment_summary(self, vendor_id=None):
    """
    Generate payment summary report for vendors
    Can be run for a specific vendor or all vendors
    """
    try:
        if vendor_id:
            vendors = Vendor.objects.filter(id=vendor_id, is_active=True)
        else:
            vendors = Vendor.objects.filter(is_active=True)
        
        summaries_generated = 0
        
        for vendor in vendors:
            # Get vendor's bills summary
            bills = Bill.objects.filter(vendor=vendor)
            
            summary = {
                'vendor': vendor.name,
                'total_bills': bills.count(),
                'pending_bills': bills.filter(status='pending').count(),
                'overdue_bills': bills.filter(status='overdue').count(),
                'paid_bills': bills.filter(status='paid').count(),
                'total_amount': sum(bill.amount for bill in bills),
                'pending_amount': sum(bill.amount for bill in bills.filter(status__in=['pending', 'confirmed', 'overdue'])),
                'paid_amount': sum(bill.amount for bill in bills.filter(status='paid')),
            }
            
            # Log the summary (could be extended to save to database or send email)
            logger.info(f"Vendor Payment Summary for {vendor.name}: {summary}")
            summaries_generated += 1
        
        return f"Successfully generated payment summaries for {summaries_generated} vendors"
        
    except Exception as e:
        logger.error(f"Error in generate_vendor_payment_summary: {str(e)}")
        raise self.retry(exc=e)