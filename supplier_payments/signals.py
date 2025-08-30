from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from decimal import Decimal
from .models import SupplierPayment
from ledger.models import Ledger
from chart_of_accounts.models import ChartOfAccount
from fiscal_year.models import FiscalYear


@receiver(post_save, sender=SupplierPayment)
def create_ledger_entries_for_supplier_payment(sender, instance, created, **kwargs):
    """
    Create ledger entries when a supplier payment is created
    
    Accounting Logic:
    - Debit: Accounts Payable (reduces liability)
    - Credit: Selected Ledger Account (cash/bank account)
    """
    if created:  # Only create entries for new payments
        try:
            # Get the current fiscal year
            fiscal_year = FiscalYear.objects.filter(
                start_date__lte=instance.payment_date,
                end_date__gte=instance.payment_date
            ).first()
            
            if not fiscal_year:
                print(f"Warning: No fiscal year found for payment date {instance.payment_date}")
                return
            
            # Find Accounts Payable account
            # First try to find account with matching company
            accounts_payable = ChartOfAccount.objects.filter(
                name__icontains='payable',
                account_type__category='LIABILITY',
                is_active=True,
                company=instance.company
            ).first()
            
            # If no account found with company filter (e.g., when company is None),
            # try to find any available accounts payable account
            if not accounts_payable:
                accounts_payable = ChartOfAccount.objects.filter(
                    name__icontains='payable',
                    account_type__category='LIABILITY',
                    is_active=True
                ).first()
            
            if not accounts_payable:
                print(f"Warning: No Accounts Payable account found for supplier payment {instance.payment_id}")
                return
            
            # Ensure ledger account is selected
            if not instance.ledger_account:
                print(f"Warning: No ledger account selected for supplier payment {instance.payment_id}")
                return
            
            # Use the company from accounts_payable if payment company is None
            ledger_company = instance.company or accounts_payable.company
            
            # Create debit entry for Accounts Payable (reduces liability)
            debit_entry = Ledger.objects.create(
                entry_date=instance.payment_date,
                reference=instance.payment_id,
                description=f"Payment to {instance.supplier.customer_name} - {instance.payment_method}",
                account=accounts_payable,
                entry_type='DR',
                amount=instance.amount,
                voucher_number=instance.payment_id,
                company=ledger_company,
                fiscal_year=fiscal_year,
                created_by=instance.created_by,
                updated_by=instance.created_by,
                status='POSTED'
            )
            
            # Create credit entry for selected ledger account (cash/bank)
            credit_entry = Ledger.objects.create(
                entry_date=instance.payment_date,
                reference=instance.payment_id,
                description=f"Payment to {instance.supplier.customer_name} - {instance.payment_method}",
                account=instance.ledger_account,
                entry_type='CR',
                amount=instance.amount,
                voucher_number=instance.payment_id,
                company=ledger_company,
                fiscal_year=fiscal_year,
                created_by=instance.created_by,
                updated_by=instance.created_by,
                status='POSTED'
            )
            
            print(f"✅ Created ledger entries for supplier payment {instance.payment_id}:")
            print(f"   - Debit: {accounts_payable.name} - {instance.amount}")
            print(f"   - Credit: {instance.ledger_account.name} - {instance.amount}")
            
        except Exception as e:
            print(f"❌ Error creating ledger entries for supplier payment {instance.payment_id}: {e}")
            import traceback
            traceback.print_exc()