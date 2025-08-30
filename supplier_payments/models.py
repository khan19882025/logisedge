from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid

class SupplierPaymentInvoice(models.Model):
    """Model to track the relationship between supplier payments and invoices"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier_payment = models.ForeignKey('SupplierPayment', on_delete=models.CASCADE, related_name='payment_invoices')
    invoice = models.ForeignKey('invoice.Invoice', on_delete=models.CASCADE, related_name='supplier_payments')
    allocated_amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Supplier Payment Invoice'
        verbose_name_plural = 'Supplier Payment Invoices'
        unique_together = ['supplier_payment', 'invoice']
    
    def __str__(self):
        return f"{self.supplier_payment.payment_id} - {self.invoice.invoice_number} - {self.allocated_amount}"

class SupplierPaymentBill(models.Model):
    """Model to track the relationship between supplier payments and supplier bills"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier_payment = models.ForeignKey('SupplierPayment', on_delete=models.CASCADE, related_name='payment_bills')
    supplier_bill = models.ForeignKey('supplier_bills.SupplierBill', on_delete=models.CASCADE, related_name='supplier_payments')
    allocated_amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Supplier Payment Bill'
        verbose_name_plural = 'Supplier Payment Bills'
        unique_together = ['supplier_payment', 'supplier_bill']
    
    def __str__(self):
        return f"{self.supplier_payment.payment_id} - {self.supplier_bill.number} - {self.allocated_amount}"

class SupplierPayment(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('credit_card', 'Credit Card'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment_id = models.CharField(max_length=20, unique=True, blank=True)
    supplier = models.ForeignKey('customer.Customer', on_delete=models.CASCADE, related_name='supplier_payments')
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='bank_transfer')
    ledger_account = models.ForeignKey('chart_of_accounts.ChartOfAccount', on_delete=models.SET_NULL, null=True, blank=True,
                                     help_text="Select ledger account for this payment")
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    # Company and user tracking
    company = models.ForeignKey('company.Company', on_delete=models.CASCADE, null=True, blank=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='supplier_payments_created')
    updated_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='supplier_payments_updated')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-payment_date', '-created_at']
        verbose_name = 'Supplier Payment'
        verbose_name_plural = 'Supplier Payments'
    
    def __str__(self):
        return f"{self.payment_id} - {self.supplier.name} - {self.amount}"
    
    def save(self, *args, **kwargs):
        if not self.payment_id:
            # Generate payment ID: SPR-YYYY-0001
            year = self.payment_date.year
            last_payment = SupplierPayment.objects.filter(
                payment_id__startswith=f'SPR-{year}-'
            ).order_by('-payment_id').first()
            
            if last_payment:
                try:
                    last_number = int(last_payment.payment_id.split('-')[-1])
                    new_number = last_number + 1
                except (ValueError, IndexError):
                    new_number = 1
            else:
                new_number = 1
            
            self.payment_id = f'SPR-{year}-{new_number:04d}'
        
        super().save(*args, **kwargs)

    def get_related_invoices(self):
        """Get invoices related to this supplier payment based on supplier and amount"""
        from invoice.models import Invoice
        from decimal import Decimal
        
        supplier_code = self.supplier.customer_code
        supplier_name = self.supplier.customer_name
        
        # Find invoices with this supplier in the cost section
        related_invoices = []
        
        # Get all invoices with status draft, sent, or overdue
        # Exclude invoices that have already been paid for this supplier
        paid_invoice_ids = SupplierPaymentInvoice.objects.filter(
            supplier_payment__supplier=self.supplier
        ).values_list('invoice_id', flat=True)
        
        invoices = Invoice.objects.filter(
            status__in=['draft', 'sent', 'overdue', 'paid']
        ).exclude(id__in=paid_invoice_ids).order_by('-invoice_date')
        
        for invoice in invoices:
            # Find items for this supplier
            items = []
            cost_total = Decimal('0.00')
            
            for item in invoice.invoice_items:
                vendor_field = item.get('vendor', '')
                # Match by code or name (e.g., 'VEN0001 - Waseem Transport')
                if supplier_code in vendor_field or supplier_name in vendor_field:
                    items.append(item)
                    try:
                        cost_total += Decimal(str(item.get('cost_total', 0)))
                    except Exception:
                        pass
            
            if items and cost_total > 0:
                related_invoices.append({
                    'invoice': invoice,
                    'cost_total': cost_total,
                    'items_count': len(items)
                })
        
        return related_invoices
