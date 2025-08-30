from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta

class DunningLetter(models.Model):
    LEVEL_CHOICES = [
        ('friendly', 'Friendly Reminder'),
        ('firm', 'Firm Reminder'),
        ('final', 'Final Notice'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('viewed', 'Viewed'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Related fields
    customer = models.ForeignKey('customer.Customer', on_delete=models.CASCADE, related_name='dunning_letters')
    invoice = models.ForeignKey('invoice.Invoice', on_delete=models.CASCADE, related_name='dunning_letters')
    
    # Letter details
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='friendly')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    subject = models.CharField(max_length=255)
    content = models.TextField()
    
    # Tracking
    overdue_amount = models.DecimalField(max_digits=12, decimal_places=2)
    overdue_days = models.IntegerField()
    due_date = models.DateField()
    
    # Communication
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    email_recipient = models.EmailField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['customer', 'invoice', 'level']
    
    def __str__(self):
        return f"Dunning Letter {self.level.title()} - {self.customer.customer_name} - {self.invoice.invoice_number}"
    
    def save(self, *args, **kwargs):
        if not self.subject:
            self.subject = self.generate_subject()
        if not self.content:
            self.content = self.generate_content()
        super().save(*args, **kwargs)
    
    def generate_subject(self):
        """Generate email subject based on level"""
        subjects = {
            'friendly': f'Friendly Reminder: Invoice {self.invoice.invoice_number}',
            'firm': f'URGENT: Payment Required for Invoice {self.invoice.invoice_number}',
            'final': f'FINAL NOTICE: Immediate Payment Required for Invoice {self.invoice.invoice_number}',
        }
        return subjects.get(self.level, f'Payment Reminder: Invoice {self.invoice.invoice_number}')
    
    def generate_content(self):
        """Generate letter content based on level"""
        templates = {
            'friendly': self.get_friendly_template(),
            'firm': self.get_firm_template(),
            'final': self.get_final_template(),
        }
        return templates.get(self.level, self.get_friendly_template())
    
    def get_friendly_template(self):
        """Friendly reminder template"""
        return f"""Dear {self.customer.customer_name},

We hope this message finds you well. We wanted to bring to your attention that invoice {self.invoice.invoice_number} for AED {self.overdue_amount} is currently overdue by {self.overdue_days} days.

We understand that sometimes payments can be delayed due to various circumstances. If you have already made the payment, please disregard this message.

If you haven't made the payment yet, we would appreciate if you could process it at your earliest convenience. You can make the payment using the details provided on the invoice.

If you have any questions or need to discuss payment arrangements, please don't hesitate to contact us.

Thank you for your prompt attention to this matter.

Best regards,
{self.get_company_name()}

---
Invoice Details:
Invoice Number: {self.invoice.invoice_number}
Due Date: {self.due_date}
Amount Due: AED {self.overdue_amount}
Days Overdue: {self.overdue_days}"""
    
    def get_firm_template(self):
        """Firm reminder template"""
        return f"""Dear {self.customer.customer_name},

This is a formal reminder that invoice {self.invoice.invoice_number} for AED {self.overdue_amount} is now {self.overdue_days} days overdue.

We have previously sent you a friendly reminder, but we have not received your payment. This delay is causing us concern and may affect our ability to continue providing services to you.

Please arrange for immediate payment of the outstanding amount. If you are experiencing financial difficulties, we are willing to discuss payment arrangements, but we need to hear from you.

Failure to respond may result in:
- Suspension of services
- Legal action
- Additional late payment fees

Please contact us immediately to resolve this matter.

Sincerely,
{self.get_company_name()}

---
Invoice Details:
Invoice Number: {self.invoice.invoice_number}
Due Date: {self.due_date}
Amount Due: AED {self.overdue_amount}
Days Overdue: {self.overdue_days}"""
    
    def get_final_template(self):
        """Final notice template"""
        return f"""Dear {self.customer.customer_name},

This is our FINAL NOTICE regarding invoice {self.invoice.invoice_number} for AED {self.overdue_amount}, which is now {self.overdue_days} days overdue.

Despite our previous reminders, we have not received your payment or any communication from you regarding this matter.

This is your final opportunity to resolve this outstanding debt before we take further action, which may include:
- Immediate suspension of all services
- Legal proceedings
- Referral to a collection agency
- Reporting to credit agencies

To avoid these consequences, you must make full payment immediately or contact us within 48 hours to discuss payment arrangements.

This matter is now urgent and requires your immediate attention.

Sincerely,
{self.get_company_name()}

---
Invoice Details:
Invoice Number: {self.invoice.invoice_number}
Due Date: {self.due_date}
Amount Due: AED {self.overdue_amount}
Days Overdue: {self.overdue_days}"""
    
    def get_company_name(self):
        """Get company name from settings or default"""
        try:
            from company.company_model import Company
            company = Company.objects.first()
            return company.name if company else "LogisEdge"
        except:
            return "LogisEdge"
    
    @property
    def next_level(self):
        """Get the next escalation level"""
        levels = ['friendly', 'firm', 'final']
        try:
            current_index = levels.index(self.level)
            if current_index < len(levels) - 1:
                return levels[current_index + 1]
        except ValueError:
            pass
        return None
    
    @property
    def days_since_sent(self):
        """Calculate days since the letter was sent"""
        if self.email_sent_at:
            return (timezone.now() - self.email_sent_at).days
        return None
    
    def mark_as_sent(self, email_recipient=None):
        """Mark the letter as sent"""
        self.email_sent = True
        self.email_sent_at = timezone.now()
        self.status = 'sent'
        if email_recipient:
            self.email_recipient = email_recipient
        self.save()
    
    def mark_as_viewed(self):
        """Mark the letter as viewed"""
        self.status = 'viewed'
        self.save()
    
    def mark_as_paid(self):
        """Mark the letter as paid"""
        self.status = 'paid'
        self.save()
