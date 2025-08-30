from django.db import models
from django.contrib.auth.models import User
from customer.models import Customer
from job.models import Job
from delivery_order.models import DeliveryOrder
from decimal import Decimal

class Invoice(models.Model):
    """Invoice Model"""
    
    # Basic Information
    invoice_number = models.CharField(max_length=20, unique=True, blank=True)
    invoice_date = models.DateField()
    due_date = models.DateField(null=True, blank=True, verbose_name="Due Date")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="Customer")
    jobs = models.ManyToManyField(Job, verbose_name="Jobs", blank=True)
    delivery_order = models.ForeignKey(DeliveryOrder, on_delete=models.CASCADE, verbose_name="Delivery Order", null=True, blank=True)
    
    # Payment Information
    payment_source = models.ForeignKey('payment_source.PaymentSource', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Payment Source")
    
    # Billing Information
    bill_to = models.CharField(max_length=200, blank=True, verbose_name="Bill To")
    bill_to_address = models.TextField(blank=True, verbose_name="Bill To Address")
    
    # Shipping Information
    shipper = models.CharField(max_length=200, blank=True, verbose_name="Shipper")
    consignee = models.CharField(max_length=200, blank=True, verbose_name="Consignee")
    origin = models.CharField(max_length=200, blank=True, verbose_name="Origin")
    destination = models.CharField(max_length=200, blank=True, verbose_name="Destination")
    bl_number = models.CharField(max_length=100, blank=True, verbose_name="Bill of Lading Number")
    ed_number = models.CharField(max_length=100, blank=True, verbose_name="Entry Declaration Number")
    container_number = models.CharField(max_length=50, blank=True, verbose_name="Container Number")
    items_count = models.CharField(max_length=500, blank=True, verbose_name="Items")
    total_qty = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Total Quantity")
    
    # Invoice Items (stored as JSON)
    invoice_items = models.JSONField(default=list, blank=True, verbose_name="Invoice Items")
    
    # Status and Notes
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True)
    
    # Ledger Posting
    is_posted = models.BooleanField(default=False, verbose_name="Posted to Ledger")
    
    # System fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='invoices_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='invoices_updated')
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-invoice_date', '-created_at']
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'
    
    def __str__(self):
        return f"{self.invoice_number} - {self.customer.customer_name}"
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('invoice:invoice_detail', kwargs={'pk': self.pk})
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        super().save(*args, **kwargs)
    
    def generate_invoice_number(self):
        """Generate invoice number based on year and sequence"""
        from datetime import datetime
        
        today = datetime.now()
        year = today.year
        
        # Find the last invoice for this year
        last_invoice = Invoice.objects.filter(
            invoice_number__startswith=f"INV-{year}-"
        ).order_by('-invoice_number').first()
        
        if last_invoice and last_invoice.invoice_number:
            try:
                # Extract the sequence number and increment
                last_sequence = int(last_invoice.invoice_number.split('-')[-1])
                new_sequence = last_sequence + 1
            except (ValueError, IndexError):
                new_sequence = 1
        else:
            new_sequence = 1
        
        # Format: INV-YYYY-0001
        return f"INV-{year}-{new_sequence:04d}"

    @property
    def total_cost(self):
        """Calculate total cost from invoice items"""
        total = Decimal('0.00')
        if self.invoice_items:
            for item in self.invoice_items:
                cost_total = item.get('cost_total', 0)
                try:
                    total += Decimal(str(cost_total))
                except (ValueError, TypeError):
                    continue
        return total
    
    @property
    def total_sale(self):
        """Calculate total sale from invoice items"""
        total = Decimal('0.00')
        if self.invoice_items:
            for item in self.invoice_items:
                sale_total = item.get('sale_total', 0)
                try:
                    total += Decimal(str(sale_total))
                except (ValueError, TypeError):
                    continue
        return total
    
    @property
    def total_profit(self):
        """Calculate total profit (sale - cost)"""
        return self.total_sale - self.total_cost
    
    def get_invoice_items_count(self):
        """Get the number of invoice items"""
        return len(self.invoice_items) if self.invoice_items else 0
    
    def get_item_names(self):
        """Get a list of item names from invoice items"""
        if not self.invoice_items:
            return []
        names = []
        for item in self.invoice_items:
            description = item.get('description', 'Unnamed Item')
            # Extract only the service name part (after the dash)
            if ' - ' in description:
                service_name = description.split(' - ', 1)[1]
                names.append(service_name)
            else:
                names.append(description)
        return names
    
    def get_item_names_display(self):
        """Get a formatted string of item names"""
        names = self.get_item_names()
        if not names:
            return "-"
        return ", ".join(names)
    
    @property
    def total_amount(self):
        """Get total amount for dunning letters (using total_sale)"""
        return self.total_sale
    
    @property
    def is_overdue(self):
        """Check if the invoice is overdue"""
        if not self.due_date:
            return False
        from datetime import date
        return self.due_date < date.today() and self.status not in ['paid', 'cancelled']
    
    @property
    def days_overdue(self):
        """Calculate days overdue"""
        if not self.due_date or not self.is_overdue:
            return 0
        from datetime import date
        return (date.today() - self.due_date).days
    
    @property
    def vendor(self):
        """Get the primary vendor from invoice items"""
        if not self.invoice_items:
            return None
        
        # Find the first item with vendor information
        for item in self.invoice_items:
            vendor_info = item.get('vendor', '')
            if vendor_info:
                # Extract vendor code (e.g., 'VEN0001' from 'VEN0001 - Waseem Transport (Vendor)')
                vendor_code = vendor_info.split(' - ')[0] if ' - ' in vendor_info else vendor_info
                try:
                    from customer.models import Customer
                    return Customer.objects.filter(customer_code=vendor_code).first()
                except:
                    return None
        return None
    
    @property
    def item_payment_source(self):
        """Get the primary payment source from invoice items"""
        if not self.invoice_items:
            return None
        
        # Find the first item with payment source information
        for item in self.invoice_items:
            payment_source_id = item.get('payment_source_id', '')
            if payment_source_id:
                try:
                    from payment_source.models import PaymentSource
                    return PaymentSource.objects.filter(id=payment_source_id).first()
                except:
                    return None
        return None
    
    @property
    def payable_entity(self):
        """Get the payable entity (vendor or payment source) from invoice items"""
        if not self.invoice_items:
            return None
        
        # Check for payment source first, then vendor
        item_payment_source = self.item_payment_source
        if item_payment_source:
            return {
                'type': 'payment_source',
                'name': item_payment_source.name,
                'entity': item_payment_source
            }
        
        vendor = self.vendor
        if vendor:
            return {
                'type': 'vendor',
                'name': vendor.customer_name,
                'entity': vendor
            }
        
        return None
    
    @property
    def bill_date(self):
        """Alias for invoice_date to match supplier bill interface"""
        return self.invoice_date
    
    @property
    def amount(self):
        """Get the total cost amount for supplier payments"""
        return self.total_cost