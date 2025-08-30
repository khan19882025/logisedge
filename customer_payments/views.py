from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings
from django.db.models import Q
from .models import CustomerPayment, CustomerPaymentInvoice
from .forms import CustomerPaymentForm
from customer.models import Customer
from invoice.models import Invoice
from company.company_model import Company
from chart_of_accounts.models import ChartOfAccount, AccountType
from general_journal.models import JournalEntry, JournalEntryLine
from fiscal_year.models import FiscalYear
from ledger.models import Ledger
import json
from weasyprint import HTML
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.views.decorators.http import require_POST

@login_required
def payment_list(request):
    payments = CustomerPayment.objects.all().order_by('-payment_date')
    
    # Calculate total discount for each payment
    for payment in payments:
        payment.total_discount = sum(
            payment_invoice.discount_amount 
            for payment_invoice in payment.payment_invoices.all()
        )
    
    # Filter messages to only show customer payment related messages
    from django.contrib.messages import get_messages
    from django.contrib import messages as django_messages
    
    # Get all messages without consuming them
    storage = get_messages(request)
    filtered_messages = []
    
    for message in storage:
        # Keep messages that are specifically related to customer payments
        message_text = str(message).lower()
        if any(keyword in message_text for keyword in [
            'customer payment', 'payment created', 'payment updated', 
            'payment deleted', 'payment successful', 'payment failed',
            'ledger entries created', 'payment processed'
        ]):
            filtered_messages.append({
                'message': message.message,
                'tags': message.tags,
                'level': message.level,
                'extra_tags': message.extra_tags
            })
    
    # Pass filtered messages to template context
    context = {
        'payments': payments,
        'filtered_messages': filtered_messages
    }
    
    return render(request, 'customer_payments/list.html', context)

@login_required
def payment_create(request):
    if request.method == 'POST':
        print("Form submitted - processing payment creation")
        print(f"POST data: {dict(request.POST)}")
        
        form = CustomerPaymentForm(request.POST)
        if form.is_valid():
            print("Form is valid - creating payment")
            try:
                # Remove transaction.atomic() wrapper to avoid nested atomic blocks
                # Individual model saves will handle their own transactions
                
                # Save the payment first
                payment = form.save()
                print(f"Payment saved with ID: {payment.id}")
                
                # Get selected invoices and amounts
                selected_invoices = request.POST.getlist('invoices')
                invoice_amounts = request.POST.getlist('invoice_amounts')
                partial_payment_option = request.POST.get('partial_payment_option')
                
                print(f"Selected invoices: {selected_invoices}")
                print(f"Invoice amounts: {invoice_amounts}")
                print(f"Partial payment option: {partial_payment_option}")
                
                # Get or create Trade Discount account
                trade_discount_account = get_or_create_trade_discount_account()
                
                # Get current company and fiscal year
                company = Company.objects.filter(is_active=True).first()
                fiscal_year = FiscalYear.objects.filter(is_current=True).first()
                
                if not company or not fiscal_year:
                    raise Exception("Company or Fiscal Year not found")
                
                # Create payment-invoice relationships if invoices are selected
                if selected_invoices:
                    print(f"✅ Processing {len(selected_invoices)} selected invoices")
                    total_paid = Decimal('0.00')
                    total_discount = Decimal('0.00')
                    
                    for i, invoice_id in enumerate(selected_invoices):
                        print(f"Processing invoice {i+1}: ID={invoice_id}")
                        if invoice_id and i < len(invoice_amounts) and invoice_amounts[i]:
                            try:
                                invoice = Invoice.objects.get(id=invoice_id)
                                original_amount = invoice.total_sale
                                print(f"Found invoice {invoice.invoice_number} with amount {original_amount}")
                                
                                # For discount option, use the payment amount you entered, not the invoice amount
                                if partial_payment_option == 'discount':
                                    # Use the payment amount you entered (100 AED) instead of invoice amount (105 AED)
                                    amount_received = payment.amount
                                    # Calculate discount as the difference
                                    discount_amount = original_amount - amount_received
                                    total_discount += discount_amount
                                    print(f"Invoice {invoice.invoice_number}: Original={original_amount}, Received={amount_received}, Discount={discount_amount}")
                                else:
                                    # For keep_open option or regular payments, use the amount from the form
                                    amount_received = Decimal(invoice_amounts[i])
                                    discount_amount = Decimal('0.00')
                                    print(f"Invoice {invoice.invoice_number}: Original={original_amount}, Received={amount_received}, Discount={discount_amount}")
                                
                                # Always create CustomerPaymentInvoice record when invoices are selected
                                payment_invoice = CustomerPaymentInvoice.objects.create(
                                    payment=payment,
                                    invoice=invoice,
                                    amount_received=amount_received,
                                    original_amount=original_amount,
                                    discount_amount=discount_amount
                                )
                                
                                total_paid += amount_received
                                
                                # Update invoice status based on payment
                                if partial_payment_option == 'discount':
                                    # When applying discount, mark as paid since the remaining amount is written off
                                    invoice.status = 'paid'
                                elif amount_received >= original_amount:
                                    invoice.status = 'paid'
                                else:
                                    # For keep_open option, mark as partial to keep it open
                                    invoice.status = 'partial'
                                
                                invoice.save()
                                print(f"✅ Created CustomerPaymentInvoice: {payment_invoice}")
                                print(f"✅ Updated invoice {invoice.invoice_number} status to: {invoice.status}")
                                
                            except Invoice.DoesNotExist:
                                print(f"❌ Invoice {invoice_id} not found")
                                continue
                            except Exception as e:
                                print(f"❌ Error processing invoice {invoice_id}: {e}")
                                continue
                    else:
                        print(f"❌ No valid invoice data found in selected_invoices or invoice_amounts")
                        print(f"Selected invoices: {selected_invoices}")
                        print(f"Invoice amounts: {invoice_amounts}")
                    
                    print(f"Final totals - Total paid: {total_paid}, Total discount: {total_discount}")
                    
                    # Keep the original payment amount - don't update it to total_paid
                    # The payment.amount should remain as entered by the user (100 AED)
                    # The discount amount is stored separately in CustomerPaymentInvoice.discount_amount
                    print(f"Payment amount kept as: {payment.amount}")
                    print(f"Total received from invoices: {total_paid}, Total discount: {total_discount}")
                    
                    # Create main payment journal entry for the amount actually received
                    create_payment_journal_entry(payment, company, fiscal_year, request.user)
                    
                    # Create journal entry for discount if applicable
                    if total_discount > 0 and partial_payment_option == 'discount':
                        create_discount_journal_entry(
                            payment, total_discount, trade_discount_account, 
                            company, fiscal_year, request.user
                        )
                        print(f"✅ Created discount journal entry for AED {total_discount}")
                    else:
                        print(f"ℹ️ No discount journal entry needed")
                else:
                    # No invoices selected - create journal entry for general payment
                    print("⚠️ No invoices selected - creating general payment")
                    create_payment_journal_entry(payment, company, fiscal_year, request.user)
                
                print(f"Payment creation completed.")
                
                # Check if this is an AJAX request
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': f'Payment {payment.formatted_payment_id} created successfully!',
                        'payment_id': payment.id
                    })
                else:
                    messages.success(request, f'Payment {payment.formatted_payment_id} created successfully!')
                    return redirect('customer_payments:payment_list')
                
            except Exception as e:
                print(f"Error saving payment: {e}")
                
                # Check if this is an AJAX request
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    })
                else:
                    messages.error(request, f'Error saving payment: {str(e)}')
                    
        else:
            print(f"Form validation failed: {form.errors.as_json()}")
            print(f"Form errors: {form.errors}")
            
            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Form validation failed',
                    'form_errors': form.errors
                })
            else:
                messages.error(request, f'Please correct the errors below: {form.errors}')
    else:
        form = CustomerPaymentForm()
    
    return render(request, 'customer_payments/form.html', {'form': form})

def get_or_create_trade_discount_account():
    """Get or create Trade Discount account in chart of accounts"""
    try:
        # Try to find existing Trade Discount account
        trade_discount_account = ChartOfAccount.objects.filter(
            name__icontains='Trade Discount',
            account_type__category='EXPENSE'
        ).first()
        
        if trade_discount_account:
            return trade_discount_account
        
        # Create Trade Discount account if it doesn't exist
        company = Company.objects.filter(is_active=True).first()
        if not company:
            raise Exception("No active company found")
        
        # Get or create Expense account type
        expense_account_type, created = AccountType.objects.get_or_create(
            name='Expense',
            defaults={
                'category': 'EXPENSE',
                'description': 'Expense accounts for business operations'
            }
        )
        
        # Create Trade Discount account
        trade_discount_account = ChartOfAccount.objects.create(
            account_code='5001',  # You may want to make this dynamic
            name='Trade Discount',
            description='Trade discounts given to customers',
            account_type=expense_account_type,
            account_nature='DEBIT',
            currency_id=1,  # Default to AED
            company=company,
            created_by_id=1  # Default user ID, you may want to make this dynamic
        )
        
        print(f"Created Trade Discount account: {trade_discount_account}")
        return trade_discount_account
        
    except Exception as e:
        print(f"Error creating Trade Discount account: {e}")
        # Return None if we can't create the account
        return None

def get_or_create_cash_in_hand_account():
    """Get or create Cash in Hand account in chart of accounts"""
    try:
        # Try to find existing Cash in Hand account
        cash_account = ChartOfAccount.objects.filter(
            name__icontains='Cash in Hand',
            account_type__category='ASSET'
        ).first()
        
        if cash_account:
            return cash_account
        
        # Create Cash in Hand account if it doesn't exist
        company = Company.objects.filter(is_active=True).first()
        if not company:
            raise Exception("No active company found")
        
        # Get or create Asset account type
        asset_account_type, created = AccountType.objects.get_or_create(
            name='Asset',
            defaults={
                'category': 'ASSET',
                'description': 'Asset accounts for business resources'
            }
        )
        
        # Create Cash in Hand account
        cash_account = ChartOfAccount.objects.create(
            account_code='1000',  # You may want to make this dynamic
            name='Cash in Hand',
            description='Physical cash available for transactions',
            account_type=asset_account_type,
            account_nature='DEBIT',
            currency_id=1,  # Default to AED
            company=company,
            created_by_id=1  # Default user ID, you may want to make this dynamic
        )
        
        print(f"Created Cash in Hand account: {cash_account}")
        return cash_account
        
    except Exception as e:
        print(f"Error creating Cash in Hand account: {e}")
        # Return None if we can't create the account
        return None

def create_payment_journal_entry(payment, company, fiscal_year, user):
    """Create main journal entry for customer payment"""
    try:
        # Use the selected ledger account if available, otherwise fall back to payment method logic
        if payment.ledger_account:
            cash_account = payment.ledger_account
            print(f"Using selected ledger account: {cash_account.name}")
        else:
            # Fallback to original logic if no ledger account is selected
            if payment.payment_method == 'cash':
                cash_account = get_or_create_cash_in_hand_account()
                if not cash_account:
                    print("Cash in Hand account not available, skipping journal entry")
                    return
            elif payment.payment_method == 'bank':
                # Use the selected bank account's chart of account
                if payment.bank_account and payment.bank_account.chart_account:
                    cash_account = payment.bank_account.chart_account
                else:
                    print("Bank account not selected or chart account not linked, skipping journal entry")
                    return
            else:
                # For other payment methods, find appropriate account
                if payment.payment_method == 'credit_card':
                    cash_account = ChartOfAccount.objects.filter(
                        name__icontains='Credit Card',
                        account_type__category='ASSET'
                    ).first()
                else:
                    # Default to Cash in Hand for other methods
                    cash_account = get_or_create_cash_in_hand_account()
                
                if not cash_account:
                    print(f"Appropriate account for {payment.payment_method} not available, skipping journal entry")
                    return
        
        # Find Accounts Receivable account
        ar_account = ChartOfAccount.objects.filter(
            name__icontains='Accounts Receivable',
            account_type__category='ASSET'
        ).first()
        
        if not ar_account:
            print("Accounts Receivable account not available, skipping journal entry")
            return
        
        # Create journal entry
        journal_entry = JournalEntry.objects.create(
            journal_number=f'PAY-{payment.formatted_payment_id}',
            date=payment.payment_date,
            reference=f'Customer Payment {payment.formatted_payment_id}',
            description=f'Customer payment {payment.formatted_payment_id} - {payment.customer.customer_name}',
            status='posted',
            company=company,
            fiscal_year=fiscal_year,
            created_by=user,
            posted_by=user,
            posted_at=timezone.now()
        )
        
        # Create journal entry lines
        # Line 1: Debit Cash/Bank (Asset)
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            account=cash_account,
            description=f'Cash received from {payment.customer.customer_name}',
            debit_amount=payment.amount,
            credit_amount=Decimal('0.00'),
            reference=f'Payment {payment.formatted_payment_id}'
        )
        
        # Line 2: Credit Accounts Receivable (Asset)
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            account=ar_account,
            description=f'Payment received from {payment.customer.customer_name}',
            debit_amount=Decimal('0.00'),
            credit_amount=payment.amount,
            reference=f'Payment {payment.formatted_payment_id}'
        )
        
        # Calculate totals and save
        journal_entry.calculate_totals()
        journal_entry.save()
        
        print(f"Created payment journal entry: {journal_entry.journal_number}")
        
    except Exception as e:
        print(f"Error creating payment journal entry: {e}")
        # Don't raise the exception as this is not critical for payment creation

def create_discount_journal_entry(payment, total_discount, trade_discount_account, company, fiscal_year, user):
    """Create journal entry for trade discount"""
    try:
        if not trade_discount_account:
            print("Trade Discount account not available, skipping journal entry")
            return
        
        # Create journal entry
        journal_entry = JournalEntry.objects.create(
            journal_number=f'DIS-{payment.formatted_payment_id}',
            date=payment.payment_date,
            reference=f'Customer Payment {payment.formatted_payment_id}',
            description=f'Trade discount for customer payment {payment.formatted_payment_id}',
            status='posted',
            company=company,
            fiscal_year=fiscal_year,
            created_by=user,
            posted_by=user,
            posted_at=timezone.now()
        )
        
        # Create journal entry lines
        # Line 1: Debit Trade Discount (Expense)
        JournalEntryLine.objects.create(
            journal_entry=journal_entry,
            account=trade_discount_account,
            description=f'Trade discount for payment {payment.formatted_payment_id}',
            debit_amount=total_discount,
            credit_amount=Decimal('0.00'),
            reference=f'Payment {payment.formatted_payment_id}'
        )
        
        # Line 2: Credit Accounts Receivable (Asset)
        # Find Accounts Receivable account
        ar_account = ChartOfAccount.objects.filter(
            name__icontains='Accounts Receivable',
            account_type__category='ASSET'
        ).first()
        
        if ar_account:
            JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                account=ar_account,
                description=f'Trade discount write-off for payment {payment.formatted_payment_id}',
                debit_amount=Decimal('0.00'),
                credit_amount=total_discount,
                reference=f'Payment {payment.formatted_payment_id}'
            )
        
        # Calculate totals and save
        journal_entry.calculate_totals()
        journal_entry.save()
        
        print(f"Created discount journal entry: {journal_entry.journal_number}")
        
    except Exception as e:
        print(f"Error creating discount journal entry: {e}")
        # Don't raise the exception as this is not critical for payment creation

def payment_detail(request, pk):
    payment = get_object_or_404(CustomerPayment, pk=pk)
    
    # Calculate total discount for the payment
    payment.total_discount = sum(
        payment_invoice.discount_amount 
        for payment_invoice in payment.payment_invoices.all()
    )
    
    return render(request, 'customer_payments/detail.html', {'payment': payment})

def payment_delete(request, pk):
    payment = get_object_or_404(CustomerPayment, pk=pk)
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Get all payment-invoice relationships before deleting
                payment_invoices = list(payment.payment_invoices.all())
                
                # Delete related ledger entries before deleting the payment
                ledger_entries = Ledger.objects.filter(
                    Q(reference=payment.formatted_payment_id) |
                    Q(voucher_number=payment.formatted_payment_id) |
                    Q(description__icontains=payment.formatted_payment_id)
                )
                ledger_count = ledger_entries.count()
                if ledger_count > 0:
                    ledger_entries.delete()
                    print(f"✅ Deleted {ledger_count} related ledger entries for payment {payment.formatted_payment_id}")
                else:
                    print(f"ℹ️ No ledger entries found for payment {payment.formatted_payment_id}")
                
                # Delete the payment (this will cascade delete CustomerPaymentInvoice records)
                payment.delete()
                
                # Revert invoice statuses to allow customers to create new payments
                for pi in payment_invoices:
                    try:
                        invoice = pi.invoice
                        
                        # Since the payment was already deleted, we need to check for any remaining payments
                        # by looking at the current state of CustomerPaymentInvoice records
                        remaining_payments = CustomerPaymentInvoice.objects.filter(invoice=invoice)
                        
                        if remaining_payments.exists():
                            # Calculate total paid from remaining payments
                            total_paid = sum(pi.amount_received for pi in remaining_payments)
                            print(f"Invoice {invoice.invoice_number}: Remaining payments total: {total_paid}, Invoice amount: {invoice.total_sale}")
                            
                            if total_paid >= invoice.total_sale:
                                invoice.status = 'paid'
                                print(f"  → Status set to: paid (fully paid)")
                            elif total_paid > 0:
                                invoice.status = 'partial'
                                print(f"  → Status set to: partial (partially paid)")
                            else:
                                invoice.status = 'sent'
                                print(f"  → Status set to: sent (no payments)")
                        else:
                            # No payments remain, revert to sent status
                            if invoice.status in ['paid', 'partial']:
                                invoice.status = 'sent'
                                print(f"  → Status reverted to: sent (no payments remain)")
                        
                        invoice.save()
                        print(f"✅ Invoice {invoice.invoice_number} status updated to: {invoice.status}")
                        
                    except Exception as e:
                        print(f"❌ Error reverting invoice {pi.invoice.invoice_number}: {e}")
                        continue
                
                messages.success(request, f'Payment {payment.formatted_payment_id} deleted successfully! Invoice statuses have been reverted.')
                
                # Force refresh the page to show updated invoice statuses
                return redirect('customer_payments:payment_list')
                
        except Exception as e:
            messages.error(request, f'Error deleting payment: {str(e)}')
            print(f"Error deleting payment: {e}")
        
        return redirect('customer_payments:payment_list')
    
    return render(request, 'customer_payments/delete.html', {'payment': payment})

def payment_print(request, pk):
    payment = get_object_or_404(CustomerPayment, pk=pk)
    company = Company.objects.first()
    
    context = {
        'payment': payment,
        'company': company,
        'payment_invoices': payment.payment_invoices.all()
    }
    
    html_string = render_to_string('customer_payments/print_payment.html', context)
    
    # Generate PDF
    pdf = HTML(string=html_string).write_pdf()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="payment_receipt_{payment.formatted_payment_id}.pdf"'
    return response

def payment_email(request, pk):
    payment = get_object_or_404(CustomerPayment, pk=pk)
    
    if request.method == 'POST':
        recipient_email = request.POST.get('recipient_email')
        subject = request.POST.get('subject', f'Payment Receipt - {payment.formatted_payment_id}')
        message = request.POST.get('message', '')
        
        if recipient_email:
            try:
                # Generate PDF
                company = Company.objects.first()
                context = {'payment': payment, 'company': company}
                html_string = render_to_string('customer_payments/print/receipt.html', context)
                pdf = HTML(string=html_string).write_pdf()
                
                # Send email
                email = EmailMessage(
                    subject=subject,
                    body=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[recipient_email]
                )
                email.attach(f'payment_receipt_{payment.formatted_payment_id}.pdf', pdf, 'application/pdf')
                email.send()
                
                messages.success(request, f'Payment receipt sent to {recipient_email}')
            except Exception as e:
                messages.error(request, f'Failed to send email: {str(e)}')
        else:
            messages.error(request, 'Please provide a valid email address.')
    
    return redirect('customer_payments:payment_detail', pk=pk)

@csrf_exempt
@require_http_methods(["POST"])
def customer_invoices_ajax(request):
    customer_id = request.POST.get('customer_id')
    if customer_id:
        invoices = Invoice.objects.filter(
            customer_id=customer_id,
            status__in=['draft', 'sent', 'overdue', 'partial']
        ).order_by('-invoice_date')
        
        invoice_data = []
        for invoice in invoices:
            # Calculate payment status and balance
            total_amount = invoice.total_sale
            paid_amount = Decimal('0.00')
            balance_amount = total_amount
            
            # Check if there are any payments for this invoice
            payment_invoices = CustomerPaymentInvoice.objects.filter(invoice=invoice)
            for payment_invoice in payment_invoices:
                paid_amount += payment_invoice.amount_received
            
            balance_amount = total_amount - paid_amount
            
            # Determine payment status
            if paid_amount >= total_amount:
                payment_status = "Fully Paid"
            elif paid_amount > 0:
                payment_status = "Partially Paid"
            else:
                payment_status = "Unpaid"
            
            # Only include invoices with balance due greater than 0
            if balance_amount > 0:
                invoice_data.append({
                    'id': invoice.id,
                    'number': invoice.invoice_number,
                    'date': invoice.invoice_date.strftime('%Y-%m-%d'),
                    'amount': float(total_amount),
                    'paid_amount': float(paid_amount),
                    'balance_amount': float(balance_amount),
                    'payment_status': payment_status,
                    'status': invoice.status,
                    'items': invoice.get_item_names_display()
                })
        
        return JsonResponse({'invoices': invoice_data})


@login_required
@require_POST
@csrf_exempt
def filter_ledger_accounts(request):
    """AJAX endpoint to filter ledger accounts based on payment method"""
    try:
        data = json.loads(request.body)
        payment_method = data.get('payment_method', '')
        
        print(f"Filtering ledger accounts for payment method: {payment_method}")
        
        # Define account filters based on payment method using parent accounts
        if payment_method == 'cash':
            # For cash payments, find parent accounts related to cash
            cash_parent_accounts = ChartOfAccount.objects.filter(
                Q(name__icontains='cash') | Q(account_type__name__icontains='cash'),
                is_active=True,
                is_group=True  # Parent accounts
            )
            
            # Get all child accounts under cash parent accounts
            accounts = ChartOfAccount.objects.filter(
                parent_account__in=cash_parent_accounts,
                is_active=True,
                is_group=False  # Only leaf accounts
            )
            
            # If no parent accounts found, fallback to direct cash accounts
            if not accounts.exists():
                accounts = ChartOfAccount.objects.filter(
                    Q(name__icontains='cash') | Q(account_type__name__icontains='cash'),
                    account_type__category='ASSET',
                    is_active=True,
                    is_group=False
                )
                
        elif payment_method == 'bank':
            # For bank payments, find parent accounts related to bank
            bank_parent_accounts = ChartOfAccount.objects.filter(
                Q(name__icontains='bank') | Q(account_type__name__icontains='bank'),
                is_active=True,
                is_group=True  # Parent accounts
            )
            
            # Get all child accounts under bank parent accounts
            accounts = ChartOfAccount.objects.filter(
                parent_account__in=bank_parent_accounts,
                is_active=True,
                is_group=False  # Only leaf accounts
            )
            
            # If no parent accounts found, fallback to direct bank accounts
            if not accounts.exists():
                accounts = ChartOfAccount.objects.filter(
                    Q(name__icontains='bank') | Q(account_type__name__icontains='bank'),
                    account_type__category='ASSET',
                    is_active=True,
                    is_group=False
                )
                
        else:
            # For other payment methods, show all asset accounts
            accounts = ChartOfAccount.objects.filter(
                account_type__category='ASSET',
                is_active=True,
                is_group=False
            )
        
        # Final fallback to all asset accounts if nothing found
        if not accounts.exists():
            accounts = ChartOfAccount.objects.filter(
                account_type__category='ASSET',
                is_active=True,
                is_group=False
            ).order_by('account_code')
        
        account_data = []
        for account in accounts:
            account_data.append({
                'id': account.id,
                'account_code': account.account_code,
                'name': account.name,
                'account_type': account.account_type.name
            })
        
        print(f"Found {len(account_data)} accounts for {payment_method}")
        
        return JsonResponse({
            'success': True,
            'accounts': account_data
        })
        
    except Exception as e:
        print(f"Error filtering ledger accounts: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
    
    return JsonResponse({'invoices': []})