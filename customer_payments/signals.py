from django.db.models.signals import post_delete, post_save, pre_delete
from django.dispatch import receiver
from django.db import transaction
from .models import CustomerPayment, CustomerPaymentInvoice
from .views import get_or_create_cash_in_hand_account
from invoice.models import Invoice
from ledger.models import Ledger
from chart_of_accounts.models import ChartOfAccount
from fiscal_year.models import FiscalYear
from company.company_model import Company
from decimal import Decimal

# Store affected invoices before deletion
_affected_invoices = set()

@receiver(pre_delete, sender=CustomerPayment)
def capture_affected_invoices(sender, instance, **kwargs):
    """
    Capture affected invoices before payment deletion
    """
    global _affected_invoices
    _affected_invoices.clear()
    
    try:
        # Get all invoices that will be affected by this payment deletion
        for payment_invoice in instance.payment_invoices.all():
            _affected_invoices.add(payment_invoice.invoice.id)
        
        print(f"📝 Pre-delete: Captured {len(_affected_invoices)} affected invoices for payment {instance.formatted_payment_id}")
        
    except Exception as e:
        print(f"❌ Error in capture_affected_invoices signal: {e}")
        _affected_invoices.clear()

@receiver(post_delete, sender=CustomerPayment)
def update_invoice_status_on_payment_delete(sender, instance, **kwargs):
    """
    Update invoice statuses when a payment is deleted
    """
    global _affected_invoices
    
    try:
        print(f"🔄 Post-delete signal triggered: Payment deleted")
        print(f"📝 Affected invoices captured: {_affected_invoices}")
        
        # Update statuses for the specific invoices that were affected
        updated_count = 0
        
        for invoice_id in _affected_invoices:
            try:
                invoice = Invoice.objects.get(id=invoice_id)
                
                # Get current payment status for this invoice
                remaining_payments = CustomerPaymentInvoice.objects.filter(invoice=invoice)
                
                if remaining_payments.exists():
                    # Calculate total paid from remaining payments
                    total_paid = sum(pi.amount_received for pi in remaining_payments)
                    
                    if total_paid >= invoice.total_sale:
                        new_status = 'paid'
                    elif total_paid > 0:
                        new_status = 'partial'
                    else:
                        new_status = 'sent'
                else:
                    # No payments remain, should be sent status
                    new_status = 'sent'
                
                # Update invoice status if it changed
                if invoice.status != new_status:
                    old_status = invoice.status
                    invoice.status = new_status
                    invoice.save(update_fields=['status'])
                    print(f"  ✅ Invoice {invoice.invoice_number}: '{old_status}' → '{new_status}' (Paid: {total_paid if 'total_paid' in locals() else 0}, Total: {invoice.total_sale})")
                    updated_count += 1
                else:
                    total_paid = sum(pi.amount_received for pi in remaining_payments) if remaining_payments.exists() else 0
                    print(f"  ℹ️ Invoice {invoice.invoice_number}: Status '{invoice.status}' unchanged (Paid: {total_paid}, Total: {invoice.total_sale})")
                    
            except Invoice.DoesNotExist:
                print(f"  ⚠️ Invoice ID {invoice_id} not found (may have been deleted)")
                continue
        
        print(f"🔄 Signal completed: {updated_count} invoice statuses updated")
        
        # Clear the captured invoices
        _affected_invoices.clear()
                
    except Exception as e:
        print(f"❌ Error in update_invoice_status_on_payment_delete signal: {e}")
        import traceback
        traceback.print_exc()
        _affected_invoices.clear()

@receiver(post_save, sender=CustomerPaymentInvoice)
def update_invoice_status_on_payment_save(sender, instance, created, **kwargs):
    """
    Update invoice status when a payment-invoice relationship is created or modified
    """
    try:
        invoice = instance.invoice
        
        # Get all payments for this invoice
        all_payments = CustomerPaymentInvoice.objects.filter(invoice=invoice)
        total_paid = sum(pi.amount_received for pi in all_payments)
        
        # Determine new status
        if total_paid >= invoice.total_sale:
            new_status = 'paid'
        elif total_paid > 0:
            new_status = 'partial'
        else:
            new_status = 'sent'
        
        # Update invoice status if it changed
        if invoice.status != new_status:
            old_status = invoice.status
            invoice.status = new_status
            invoice.save(update_fields=['status'])
            
            action = "created" if created else "modified"
            print(f"🔄 Signal: Invoice {invoice.invoice_number} status updated from '{old_status}' to '{new_status}' after payment {action}")
        else:
            action = "created" if created else "modified"
            print(f"ℹ️ Signal: Invoice {invoice.invoice_number} status unchanged ({invoice.status}) after payment {action}")
            
    except Exception as e:
            print(f"❌ Error in update_invoice_status_on_payment_save signal: {e}")


@receiver(post_save, sender=CustomerPayment)
def create_ledger_entries_for_customer_payment(sender, instance, created, **kwargs):
    """
    Create ledger entries when a customer payment is created
    
    Professional ERP Accounting Logic:
    - Debit: Selected Ledger Account (MUST be ASSET account with DEBIT nature)
    - Credit: Accounts Receivable (reduces asset)
    
    This follows professional ERP standards where:
    1. Customer payments ALWAYS debit the selected cash/bank account
    2. Only ASSET accounts with DEBIT nature are allowed
    3. Proper validation ensures accounting integrity
    """
    if created:  # Only create entries for new payments
        try:
            # Get the current fiscal year and active company
            fiscal_year = FiscalYear.objects.filter(
                start_date__lte=instance.payment_date,
                end_date__gte=instance.payment_date
            ).first()
            
            if not fiscal_year:
                print(f"Warning: No fiscal year found for payment date {instance.payment_date}")
                return
                
            company = Company.objects.filter(is_active=True).first()
            if not company:
                print(f"Warning: No active company found for payment {instance.formatted_payment_id}")
                return
            
            # Find Accounts Receivable account - use exact match first, then fallback
            accounts_receivable = None
            
            # Try exact match first
            try:
                accounts_receivable = ChartOfAccount.objects.get(
                    name='Accounts Receivable',
                    account_type__category='ASSET',
                    is_active=True
                )
            except ChartOfAccount.DoesNotExist:
                # Fallback to partial match and get the first active one
                accounts_receivable = ChartOfAccount.objects.filter(
                    name__icontains='receivable',
                    account_type__category='ASSET',
                    is_active=True
                ).first()
            except ChartOfAccount.MultipleObjectsReturned:
                # If multiple exact matches, get the first one
                accounts_receivable = ChartOfAccount.objects.filter(
                    name='Accounts Receivable',
                    account_type__category='ASSET',
                    is_active=True
                ).first()
            
            if not accounts_receivable:
                print(f"Warning: No Accounts Receivable account found for customer payment {instance.formatted_payment_id}")
                return
            
            # Determine the ledger account to use with professional ERP validation
            if instance.ledger_account:
                cash_account = instance.ledger_account
                
                # Professional ERP validation: Ensure selected account follows standards
                if not _validate_ledger_account_for_debit_posting(cash_account, instance):
                    print(f"❌ Professional ERP Error: Invalid ledger account selection for payment {instance.formatted_payment_id}")
                    return
                
                print(f"✅ Professional ERP: Using user-selected ledger account: {cash_account.account_code} - {cash_account.name}")
            else:
                # Fallback logic when no ledger account is selected
                if instance.payment_method == 'cash':
                    cash_account = get_or_create_cash_in_hand_account()
                    if not cash_account:
                        print(f"Warning: Cash in Hand account not available for payment {instance.formatted_payment_id}")
                        return
                elif instance.payment_method == 'bank':
                    # Use the selected bank account's chart of account
                    if instance.bank_account and instance.bank_account.chart_account:
                        cash_account = instance.bank_account.chart_account
                    else:
                        print(f"Warning: Bank account not selected or chart account not linked for payment {instance.formatted_payment_id}")
                        return
                else:
                    # For other payment methods, find appropriate account
                    if instance.payment_method == 'credit_card':
                        cash_account = ChartOfAccount.objects.filter(
                            name__icontains='Credit Card',
                            account_type__category='ASSET',
                            is_active=True
                        ).first()
                    else:
                        # Default to Cash in Hand for unknown payment methods
                        cash_account = get_or_create_cash_in_hand_account()
                    
                    if not cash_account:
                        print(f"Warning: No appropriate account found for payment method {instance.payment_method} in payment {instance.formatted_payment_id}")
                        return
                
                print(f"Using fallback ledger account: {cash_account.name} for payment method: {instance.payment_method}")
                
                # Update the payment record with the determined ledger account ONLY when no account was selected
                instance.ledger_account = cash_account
                instance.save(update_fields=['ledger_account'])
            
            # Company already retrieved above
            
            # Create debit entry for selected ledger account (cash/bank)
            # Professional ERP Standard: Customer payments ALWAYS debit the cash/bank account
            debit_entry = Ledger.objects.create(
                entry_date=instance.payment_date,
                reference=instance.formatted_payment_id,
                description=f"Customer Payment - DEBIT {cash_account.name} - {instance.customer.customer_name} - {instance.payment_method}",
                account=cash_account,
                entry_type='DR',  # Professional ERP: ALWAYS debit for customer payments
                amount=instance.amount,
                voucher_number=instance.formatted_payment_id,
                company=company,
                fiscal_year=fiscal_year,
                created_by=getattr(instance, 'created_by', None),
                updated_by=getattr(instance, 'created_by', None),
                status='POSTED'
            )
            
            # Create credit entry for Accounts Receivable (reduces asset)
            # Professional ERP Standard: Credit A/R to reduce customer debt
            credit_entry = Ledger.objects.create(
                entry_date=instance.payment_date,
                reference=instance.formatted_payment_id,
                description=f"Customer Payment - CREDIT A/R - {instance.customer.customer_name} - {instance.payment_method}",
                account=accounts_receivable,
                entry_type='CR',  # Professional ERP: ALWAYS credit A/R for customer payments
                amount=instance.amount,
                voucher_number=instance.formatted_payment_id,
                company=company,
                fiscal_year=fiscal_year,
                created_by=getattr(instance, 'created_by', None),
                updated_by=getattr(instance, 'created_by', None),
                status='POSTED'
            )
            
            print(f"✅ Professional ERP: Created balanced ledger entries for customer payment {instance.formatted_payment_id}:")
            print(f"   - DEBIT: {cash_account.account_code} - {cash_account.name} - {instance.amount} (Increases {cash_account.name.lower()})")
            print(f"   - CREDIT: {accounts_receivable.account_code} - {accounts_receivable.name} - {instance.amount} (Reduces customer debt)")
            print(f"   - Professional ERP Validation: ✅ ASSET account debited, ✅ A/R credited, ✅ Books balanced")
            
        except Exception as e:
            print(f"❌ Professional ERP Error: Failed to create ledger entries for customer payment {instance.formatted_payment_id}: {e}")
            import traceback
            traceback.print_exc()


def _validate_ledger_account_for_debit_posting(ledger_account, payment_instance):
    """
    Professional ERP validation for ledger account before creating debit entries.
    Ensures the selected account follows proper accounting principles.
    
    Returns:
        bool: True if account is valid for debit posting, False otherwise
    """
    try:
        # Rule 1: Must be an ASSET account (cash, bank accounts are assets)
        if ledger_account.account_type.category != 'ASSET':
            print(f"❌ Professional ERP Error: Customer payments must debit ASSET accounts only. "
                  f"Account '{ledger_account.name}' is {ledger_account.account_type.get_category_display()}.")
            return False
        
        # Rule 2: Must have DEBIT or BOTH nature (assets increase with debits)
        if ledger_account.account_nature not in ['DEBIT', 'BOTH']:
            print(f"❌ Professional ERP Error: Customer payments require DEBIT or BOTH nature accounts. "
                  f"Account '{ledger_account.name}' has {ledger_account.account_nature} nature.")
            return False
        
        # Rule 3: Must be active and not a group account
        if not ledger_account.is_active:
            print(f"❌ Professional ERP Error: Cannot post to inactive account '{ledger_account.name}'.")
            return False
        
        if ledger_account.is_group:
            print(f"❌ Professional ERP Error: Cannot post to group account '{ledger_account.name}'. Use detail accounts only.")
            return False
        
        # Rule 4: Validate payment amount is positive
        if payment_instance.amount <= 0:
            print(f"❌ Professional ERP Error: Payment amount must be positive. Amount: {payment_instance.amount}")
            return False
        
        print(f"✅ Professional ERP Validation: Account '{ledger_account.account_code} - {ledger_account.name}' "
              f"is valid for DEBIT posting (ASSET account with {ledger_account.account_nature} nature)")
        return True
        
    except Exception as e:
        print(f"❌ Professional ERP Error: Validation failed for account '{ledger_account.name}': {e}")
        return False
