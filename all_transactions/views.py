from django.shortcuts import render, get_object_or_404
from django.http import Http404, HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from datetime import datetime, timedelta
import csv

from .forms import TransactionFilterForm, TransactionDetailForm

# Import actual transaction models
try:
    from invoice.models import Invoice
    from payment_voucher.models import PaymentVoucher
    from receipt_voucher.models import ReceiptVoucher
    from general_journal.models import GeneralJournal
    from contra_entry.models import ContraEntry
    from adjustment_entry.models import AdjustmentEntry
    INVOICE_AVAILABLE = True
except ImportError:
    INVOICE_AVAILABLE = False


def get_all_transactions(queryset=None, filters=None):
    """
    Get transactions from all available modules
    Returns a list of transaction dictionaries
    """
    transactions = []
    
    if not INVOICE_AVAILABLE:
        return transactions
    
    # Get invoices
    try:
        invoices = Invoice.objects.all()
        if filters:
            if filters.get('date_from'):
                invoices = invoices.filter(date__gte=filters['date_from'])
            if filters.get('date_to'):
                invoices = invoices.filter(date__lte=filters['date_to'])
            if filters.get('search'):
                search = filters['search']
                invoices = invoices.filter(
                    Q(invoice_number__icontains=search) |
                    Q(narration__icontains=search)
                )
        
        for invoice in invoices:
            transactions.append({
                'id': f'invoice_{invoice.id}',
                'transaction_date': invoice.date,
                'transaction_type': 'sales_invoice',
                'document_number': invoice.invoice_number,
                'reference_number': invoice.reference_number or '',
                'debit_account': invoice.customer.account if hasattr(invoice, 'customer') else None,
                'credit_account': None,  # Would need to get from invoice items
                'amount': invoice.total_amount,
                'narration': invoice.narration or '',
                'posted_by': invoice.created_by,
                'status': 'posted' if invoice.is_posted else 'draft',
                'source_model': 'invoice.Invoice',
                'source_id': invoice.id,
                'created_at': invoice.created_at,
                'updated_at': invoice.updated_at,
            })
    except Exception as e:
        print(f"Error getting invoices: {e}")
    
    # Get payment vouchers
    try:
        payment_vouchers = PaymentVoucher.objects.all()
        if filters:
            if filters.get('date_from'):
                payment_vouchers = payment_vouchers.filter(date__gte=filters['date_from'])
            if filters.get('date_to'):
                payment_vouchers = payment_vouchers.filter(date__lte=filters['date_to'])
            if filters.get('search'):
                search = filters['search']
                payment_vouchers = payment_vouchers.filter(
                    Q(voucher_number__icontains=search) |
                    Q(narration__icontains=search)
                )
        
        for pv in payment_vouchers:
            transactions.append({
                'id': f'payment_voucher_{pv.id}',
                'transaction_date': pv.date,
                'transaction_type': 'payment_voucher',
                'document_number': pv.voucher_number,
                'reference_number': pv.reference_number or '',
                'debit_account': None,  # Would need to get from entries
                'credit_account': None,  # Would need to get from entries
                'amount': pv.total_amount,
                'narration': pv.narration or '',
                'posted_by': pv.created_by,
                'status': 'posted' if pv.is_posted else 'draft',
                'source_model': 'payment_voucher.PaymentVoucher',
                'source_id': pv.id,
                'created_at': pv.created_at,
                'updated_at': pv.updated_at,
            })
    except Exception as e:
        print(f"Error getting payment vouchers: {e}")
    
    # Get adjustment entries
    try:
        adjustment_entries = AdjustmentEntry.objects.all()
        if filters:
            if filters.get('date_from'):
                adjustment_entries = adjustment_entries.filter(date__gte=filters['date_from'])
            if filters.get('date_to'):
                adjustment_entries = adjustment_entries.filter(date__lte=filters['date_to'])
            if filters.get('search'):
                search = filters['search']
                adjustment_entries = adjustment_entries.filter(
                    Q(voucher_number__icontains=search) |
                    Q(narration__icontains=search)
                )
        
        for ae in adjustment_entries:
            transactions.append({
                'id': f'adjustment_entry_{ae.id}',
                'transaction_date': ae.date,
                'transaction_type': 'adjustment_entry',
                'document_number': ae.voucher_number,
                'reference_number': ae.reference_number or '',
                'debit_account': None,  # Would need to get from entries
                'credit_account': None,  # Would need to get from entries
                'amount': ae.total_amount,
                'narration': ae.narration or '',
                'posted_by': ae.created_by,
                'status': 'posted' if ae.is_posted else 'draft',
                'source_model': 'adjustment_entry.AdjustmentEntry',
                'source_id': ae.id,
                'created_at': ae.created_at,
                'updated_at': ae.updated_at,
            })
    except Exception as e:
        print(f"Error getting adjustment entries: {e}")
    
    # Sort by date (newest first)
    transactions.sort(key=lambda x: x['transaction_date'], reverse=True)
    
    return transactions


@login_required
def transaction_list(request):
    """Main transaction list view with filters"""
    
    # Get filter form
    filter_form = TransactionFilterForm(request.GET or None)
    
    # Get filters from form
    filters = {}
    if filter_form.is_valid():
        if filter_form.cleaned_data.get('date_from'):
            filters['date_from'] = filter_form.cleaned_data['date_from']
        if filter_form.cleaned_data.get('date_to'):
            filters['date_to'] = filter_form.cleaned_data['date_to']
        if filter_form.cleaned_data.get('search'):
            filters['search'] = filter_form.cleaned_data['search']
    
    # Get all transactions
    all_transactions = get_all_transactions(filters=filters)
    
    # Apply additional filters in Python
    filtered_transactions = all_transactions
    
    if filter_form.is_valid():
        # Transaction type filter
        if filter_form.cleaned_data.get('transaction_type'):
            filtered_transactions = [
                t for t in filtered_transactions 
                if t['transaction_type'] == filter_form.cleaned_data['transaction_type']
            ]
        
        # Amount range filters
        if filter_form.cleaned_data.get('amount_from'):
            filtered_transactions = [
                t for t in filtered_transactions 
                if t['amount'] >= filter_form.cleaned_data['amount_from']
            ]
        
        if filter_form.cleaned_data.get('amount_to'):
            filtered_transactions = [
                t for t in filtered_transactions 
                if t['amount'] <= filter_form.cleaned_data['amount_to']
            ]
        
        # Status filter
        if filter_form.cleaned_data.get('status'):
            filtered_transactions = [
                t for t in filtered_transactions 
                if t['status'] == filter_form.cleaned_data['status']
            ]
        
        # Reference number filter
        if filter_form.cleaned_data.get('reference_number'):
            ref_num = filter_form.cleaned_data['reference_number'].lower()
            filtered_transactions = [
                t for t in filtered_transactions 
                if ref_num in (t['reference_number'] or '').lower()
            ]
    
    # Get summary statistics
    total_count = len(filtered_transactions)
    total_amount = sum(t['amount'] for t in filtered_transactions)
    
    # Group by transaction type
    type_summary = {}
    for transaction in filtered_transactions:
        t_type = transaction['transaction_type']
        if t_type not in type_summary:
            type_summary[t_type] = {'count': 0, 'total_amount': 0}
        type_summary[t_type]['count'] += 1
        type_summary[t_type]['total_amount'] += transaction['amount']
    
    # Convert to list and sort
    type_summary = [
        {'transaction_type': k, 'count': v['count'], 'total_amount': v['total_amount']}
        for k, v in type_summary.items()
    ]
    type_summary.sort(key=lambda x: x['total_amount'], reverse=True)
    
    # Pagination
    paginator = Paginator(filtered_transactions, 50)  # 50 transactions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Export functionality
    export_format = filter_form.cleaned_data.get('export_format') if filter_form.is_valid() else None
    if export_format:
        return export_transactions(filtered_transactions, export_format)
    
    context = {
        'filter_form': filter_form,
        'transactions': page_obj,
        'total_count': total_count,
        'total_amount': total_amount,
        'type_summary': type_summary,
        'page_obj': page_obj,
    }
    
    return render(request, 'all_transactions/transaction_list.html', context)


@login_required
def transaction_detail(request, pk):
    """Transaction detail view"""
    # Parse the composite ID (e.g., 'invoice_123')
    if '_' in pk:
        source_type, source_id = pk.split('_', 1)
        source_id = int(source_id)
        
        # Get the actual transaction from the source model
        transaction = None
        try:
            if source_type == 'invoice':
                from invoice.models import Invoice
                transaction = Invoice.objects.get(id=source_id)
            elif source_type == 'payment_voucher':
                from payment_voucher.models import PaymentVoucher
                transaction = PaymentVoucher.objects.get(id=source_id)
            elif source_type == 'adjustment_entry':
                from adjustment_entry.models import AdjustmentEntry
                transaction = AdjustmentEntry.objects.get(id=source_id)
            # Add more source types as needed
        except Exception as e:
            print(f"Error getting transaction: {e}")
            transaction = None
        
        if not transaction:
            raise Http404("Transaction not found")
        
        # Convert to the expected format
        transaction_data = {
            'transaction_date': transaction.date,
            'transaction_type': source_type.replace('_', ' ').title(),
            'document_number': getattr(transaction, 'invoice_number', getattr(transaction, 'voucher_number', '')),
            'reference_number': getattr(transaction, 'reference_number', ''),
            'debit_account': None,  # Would need to get from entries
            'credit_account': None,  # Would need to get from entries
            'amount': getattr(transaction, 'total_amount', 0),
            'narration': getattr(transaction, 'narration', ''),
            'posted_by': transaction.created_by,
            'status': 'posted' if getattr(transaction, 'is_posted', False) else 'draft',
        }
        
        context = {
            'transaction': transaction_data,
            'source_transaction': transaction,
        }
        
        return render(request, 'all_transactions/transaction_detail.html', context)
    else:
        raise Http404("Invalid transaction ID")


@login_required
def transaction_dashboard(request):
    """Dashboard view with transaction statistics"""
    
    # Get date range (default to last 30 days)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    if request.GET.get('date_from'):
        start_date = datetime.strptime(request.GET['date_from'], '%Y-%m-%d').date()
    if request.GET.get('date_to'):
        end_date = datetime.strptime(request.GET['date_to'], '%Y-%m-%d').date()
    
    # Get transactions for the date range
    filters = {'date_from': start_date, 'date_to': end_date}
    all_transactions = get_all_transactions(filters=filters)
    
    # Filter by date range
    transactions = [
        t for t in all_transactions 
        if start_date <= t['transaction_date'] <= end_date
    ]
    
    # Calculate statistics
    total_transactions = len(transactions)
    total_amount = sum(t['amount'] for t in transactions)
    
    # Group by transaction type
    type_stats = {}
    for transaction in transactions:
        t_type = transaction['transaction_type']
        if t_type not in type_stats:
            type_stats[t_type] = {'count': 0, 'total_amount': 0}
        type_stats[t_type]['count'] += 1
        type_stats[t_type]['total_amount'] += transaction['amount']
    
    # Convert to list and calculate percentages
    type_stats = []
    for t_type, data in type_stats.items():
        percent = (data['total_amount'] / total_amount * 100) if total_amount else 0
        average = (data['total_amount'] / data['count']) if data['count'] else 0
        type_stats.append({
            'transaction_type': t_type,
            'count': data['count'],
            'total_amount': data['total_amount'],
            'percent': percent,
            'average': average
        })
    type_stats.sort(key=lambda x: x['total_amount'], reverse=True)

    # Group by status
    status_stats = {}
    for transaction in transactions:
        status = transaction['status']
        if status not in status_stats:
            status_stats[status] = {'count': 0, 'total_amount': 0}
        status_stats[status]['count'] += 1
        status_stats[status]['total_amount'] += transaction['amount']
    
    # Convert to list and calculate percentages
    status_stats = []
    for status, data in status_stats.items():
        percent = (data['total_amount'] / total_amount * 100) if total_amount else 0
        average = (data['total_amount'] / data['count']) if data['count'] else 0
        status_stats.append({
            'status': status,
            'count': data['count'],
            'total_amount': data['total_amount'],
            'percent': percent,
            'average': average
        })
    status_stats.sort(key=lambda x: x['total_amount'], reverse=True)

    # Daily transaction trend
    daily_trend = {}
    for transaction in transactions:
        date = transaction['transaction_date']
        if date not in daily_trend:
            daily_trend[date] = {'count': 0, 'total_amount': 0}
        daily_trend[date]['count'] += 1
        daily_trend[date]['total_amount'] += transaction['amount']
    
    # Convert to list and sort by date
    daily_trend = [
        {
            'transaction_date': date,
            'count': data['count'],
            'total_amount': data['total_amount']
        }
        for date, data in daily_trend.items()
    ]
    daily_trend.sort(key=lambda x: x['transaction_date'])

    # Top accounts (simplified for now)
    top_debit_accounts = []
    top_credit_accounts = []

    # Convert to JSON for JavaScript
    import json
    from django.core.serializers.json import DjangoJSONEncoder
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'total_transactions': total_transactions,
        'total_amount': total_amount,
        'type_stats_json': json.dumps(type_stats, cls=DjangoJSONEncoder),
        'status_stats_json': json.dumps(status_stats, cls=DjangoJSONEncoder),
        'daily_trend_json': json.dumps(daily_trend, cls=DjangoJSONEncoder),
        'top_debit_accounts': top_debit_accounts,
        'top_credit_accounts': top_credit_accounts,
    }
    
    return render(request, 'all_transactions/transaction_dashboard.html', context)





def export_transactions(transactions, format_type):
    """Export transactions to Excel or PDF"""
    if format_type == 'excel':
        try:
            import xlsxwriter
            from io import BytesIO
        except ImportError:
            # Fallback to CSV if xlsxwriter is not available
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
            
            import csv
            writer = csv.writer(response)
            writer.writerow(['Date', 'Type', 'Document Number', 'Reference', 'Debit Account', 'Credit Account', 'Amount', 'Narration', 'Posted By', 'Status'])
            
            for transaction in transactions:
                writer.writerow([
                    transaction['transaction_date'],
                    transaction['transaction_type'].replace('_', ' ').title(),
                    transaction['document_number'],
                    transaction['reference_number'] or '',
                    transaction['debit_account'].name if transaction['debit_account'] else '',
                    transaction['credit_account'].name if transaction['credit_account'] else '',
                    transaction['amount'],
                    transaction['narration'] or '',
                    transaction['posted_by'].username,
                    transaction['status'].title()
                ])
            
            return response
        
        # Create Excel file
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Transactions')
        
        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4CAF50',
            'font_color': 'white',
            'border': 1
        })
        
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
        amount_format = workbook.add_format({'num_format': '#,##0.00'})
        
        # Write headers
        headers = [
            'Date', 'Type', 'Document Number', 'Reference', 'Debit Account',
            'Credit Account', 'Amount', 'Narration', 'Posted By', 'Status'
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Write data
        for row, transaction in enumerate(transactions, start=1):
            worksheet.write(row, 0, transaction['transaction_date'], date_format)
            worksheet.write(row, 1, transaction['transaction_type'].replace('_', ' ').title())
            worksheet.write(row, 2, transaction['document_number'])
            worksheet.write(row, 3, transaction['reference_number'] or '')
            worksheet.write(row, 4, transaction['debit_account'].name if transaction['debit_account'] else '')
            worksheet.write(row, 5, transaction['credit_account'].name if transaction['credit_account'] else '')
            worksheet.write(row, 6, float(transaction['amount']), amount_format)
            worksheet.write(row, 7, transaction['narration'] or '')
            worksheet.write(row, 8, transaction['posted_by'].username)
            worksheet.write(row, 9, transaction['status'].title())
        
        # Auto-adjust column widths
        for col in range(len(headers)):
            worksheet.autofit_column(col)
        
        workbook.close()
        output.seek(0)
        
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="transactions.xlsx"'
        return response
    
    elif format_type == 'pdf':
        # PDF export implementation would go here
        # For now, return a simple text response
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="transactions.txt"'
        
        lines = ['Date,Type,Document Number,Reference,Debit Account,Credit Account,Amount,Narration,Posted By,Status\n']
        
        for transaction in transactions:
            line = f"{transaction['transaction_date']},{transaction['transaction_type'].replace('_', ' ').title()},{transaction['document_number']},"
            line += f"{transaction['reference_number'] or ''},{transaction['debit_account'].name if transaction['debit_account'] else ''},"
            line += f"{transaction['credit_account'].name if transaction['credit_account'] else ''},{transaction['amount']},"
            line += f"{transaction['narration'] or ''},{transaction['posted_by'].username},{transaction['status'].title()}\n"
            lines.append(line)
        
        response.writelines(lines)
        return response
    
    return None 