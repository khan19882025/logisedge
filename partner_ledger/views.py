from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum, Case, When, DecimalField, F, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from decimal import Decimal
import json
import csv
import xlsxwriter
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime, timedelta

from customer.models import Customer
from invoice.models import Invoice
from customer_payments.models import CustomerPayment, CustomerPaymentInvoice
from company.company_model import Company
from fiscal_year.models import FiscalYear
from .models import PartnerLedgerReport, PartnerLedgerEntry
from .forms import PartnerLedgerFilterForm, PartnerLedgerReportForm, QuickFilterForm


@login_required
def partner_ledger_report(request):
    """Main partner ledger report view"""
    # Set default values for initial load
    today = timezone.now().date()
    first_day_of_month = today.replace(day=1)
    initial_data = {
        'date_from': first_day_of_month,
        'date_to': today,
        'payment_status': 'all'
    }
    
    if request.GET and any(key in request.GET for key in ['customer', 'date_from', 'date_to', 'payment_status']):
        # Only use GET data if it contains actual form fields, not just IDE parameters
        form = PartnerLedgerFilterForm(request.GET)
    else:
        form = PartnerLedgerFilterForm(initial=initial_data)
    
    quick_form = QuickFilterForm(request.GET or None)
    
    context = {
        'form': form,
        'quick_form': quick_form,
        'report_data': None,
        'summary': None,
        'customers': Customer.objects.filter(is_active=True).order_by('customer_name'),
    }
    
    if form.is_valid():
        # Get filter parameters
        customer = form.cleaned_data.get('customer')
        date_from = form.cleaned_data['date_from']
        date_to = form.cleaned_data['date_to']
        payment_status = form.cleaned_data.get('payment_status', 'all')
        
        # Generate report data
        report_data, summary = generate_partner_ledger_data(
            customer=customer,
            date_from=date_from,
            date_to=date_to,
            payment_status=payment_status
        )
        
        context.update({
            'report_data': report_data,
            'summary': summary,
            'filters': {
                'customer': customer,
                'date_from': date_from,
                'date_to': date_to,
                'payment_status': payment_status,
            }
        })
        
    # If form is not valid, context will show empty state with form errors
    
    return render(request, 'partner_ledger/report.html', context)


def generate_partner_ledger_data(customer=None, date_from=None, date_to=None, payment_status='all'):
    """Generate partner ledger report data with running balance calculation"""
    
    # Base query for customers
    customers_query = Customer.objects.filter(is_active=True)
    if customer:
        customers_query = customers_query.filter(id=customer.id)
    
    report_data = []
    total_invoice_amount = Decimal('0.00')
    total_payment_received = Decimal('0.00')
    total_pending_amount = Decimal('0.00')
    
    for customer_obj in customers_query:
        # Get invoices for this customer
        invoices_query = Invoice.objects.filter(
            customer=customer_obj,
            invoice_date__range=[date_from, date_to]
        ).order_by('invoice_date', 'invoice_number')
        
        customer_data = {
            'customer': customer_obj,
            'invoices': [],
            'customer_total_invoice': Decimal('0.00'),
            'customer_total_payment': Decimal('0.00'),
            'customer_pending': Decimal('0.00'),
            'running_balance': Decimal('0.00')
        }
        
        running_balance = Decimal('0.00')
        
        for invoice in invoices_query:
            # Calculate invoice totals
            invoice_amount = invoice.total_sale or Decimal('0.00')
            
            # Get payments for this invoice
            payments = CustomerPaymentInvoice.objects.filter(
                invoice=invoice,
                payment__payment_date__range=[date_from, date_to]
            ).select_related('payment').order_by('payment__payment_date')
            
            total_payments = payments.aggregate(
                total=Coalesce(Sum('amount_received'), Decimal('0.00'))
            )['total']
            
            pending_amount = invoice_amount - total_payments
            
            # Determine payment status
            if total_payments == Decimal('0.00'):
                invoice_status = 'pending'
            elif pending_amount == Decimal('0.00'):
                invoice_status = 'fully_paid'
            else:
                invoice_status = 'partially_paid'
            
            # Filter by payment status if specified
            if payment_status != 'all' and invoice_status != payment_status:
                continue
            
            # Update running balance
            running_balance += invoice_amount
            
            invoice_data = {
                'invoice': invoice,
                'invoice_amount': invoice_amount,
                'total_payments': total_payments,
                'pending_amount': pending_amount,
                'status': invoice_status,
                'running_balance': running_balance,
                'payments': []
            }
            
            # Add payment details
            payment_running_balance = running_balance
            for payment_invoice in payments:
                payment_running_balance -= payment_invoice.amount_received
                payment_data = {
                    'payment': payment_invoice.payment,
                    'amount_received': payment_invoice.amount_received,
                    'payment_date': payment_invoice.payment.payment_date,
                    'payment_method': payment_invoice.payment.get_payment_method_display(),
                    'running_balance': payment_running_balance
                }
                invoice_data['payments'].append(payment_data)
            
            # Update running balance after payments
            running_balance = payment_running_balance
            
            customer_data['invoices'].append(invoice_data)
            customer_data['customer_total_invoice'] += invoice_amount
            customer_data['customer_total_payment'] += total_payments
            customer_data['customer_pending'] += pending_amount
        
        customer_data['running_balance'] = running_balance
        
        # Only add customer if they have invoices in the period
        if customer_data['invoices']:
            report_data.append(customer_data)
            total_invoice_amount += customer_data['customer_total_invoice']
            total_payment_received += customer_data['customer_total_payment']
            total_pending_amount += customer_data['customer_pending']
    
    # Calculate summary
    summary = {
        'total_invoice_amount': total_invoice_amount,
        'total_payment_received': total_payment_received,
        'total_pending_amount': total_pending_amount,
        'ending_balance': total_invoice_amount - total_payment_received,
        'total_customers': len(report_data),
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return report_data, summary


@login_required
@require_http_methods(["GET"])
def export_partner_ledger_excel(request):
    """Export partner ledger report to Excel"""
    form = PartnerLedgerFilterForm(request.GET)
    
    if not form.is_valid():
        messages.error(request, "Invalid filter parameters")
        return redirect('partner_ledger:report')
    
    # Get filter parameters
    customer = form.cleaned_data.get('customer')
    date_from = form.cleaned_data['date_from']
    date_to = form.cleaned_data['date_to']
    payment_status = form.cleaned_data.get('payment_status', 'all')
    
    # Generate report data
    report_data, summary = generate_partner_ledger_data(
        customer=customer,
        date_from=date_from,
        date_to=date_to,
        payment_status=payment_status
    )
    
    # Create Excel file
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet('Partner Ledger')
    
    # Define formats
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#4472C4',
        'font_color': 'white',
        'border': 1
    })
    
    customer_format = workbook.add_format({
        'bold': True,
        'bg_color': '#D9E1F2',
        'border': 1
    })
    
    invoice_format = workbook.add_format({
        'bg_color': '#F2F2F2',
        'border': 1
    })
    
    payment_format = workbook.add_format({
        'bg_color': '#E2EFDA',
        'border': 1,
        'indent': 1
    })
    
    currency_format = workbook.add_format({
        'num_format': '#,##0.00',
        'border': 1
    })
    
    # Write headers
    headers = ['Customer', 'Type', 'Date', 'Reference', 'Description', 
               'Invoice Amount', 'Payment Amount', 'Balance', 'Running Balance']
    
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)
    
    row = 1
    
    # Write data
    for customer_data in report_data:
        customer_obj = customer_data['customer']
        
        # Write customer header
        worksheet.write(row, 0, f"{customer_obj.customer_code} - {customer_obj.customer_name}", customer_format)
        for col in range(1, len(headers)):
            worksheet.write(row, col, '', customer_format)
        row += 1
        
        for invoice_data in customer_data['invoices']:
            invoice = invoice_data['invoice']
            
            # Write invoice row
            worksheet.write(row, 0, customer_obj.customer_name, invoice_format)
            worksheet.write(row, 1, 'Invoice', invoice_format)
            worksheet.write(row, 2, invoice.invoice_date.strftime('%Y-%m-%d'), invoice_format)
            worksheet.write(row, 3, invoice.invoice_number, invoice_format)
            worksheet.write(row, 4, f"Invoice {invoice.invoice_number}", invoice_format)
            worksheet.write(row, 5, float(invoice_data['invoice_amount']), currency_format)
            worksheet.write(row, 6, '', invoice_format)
            worksheet.write(row, 7, float(invoice_data['pending_amount']), currency_format)
            worksheet.write(row, 8, float(invoice_data['running_balance']), currency_format)
            row += 1
            
            # Write payment rows
            for payment_data in invoice_data['payments']:
                payment = payment_data['payment']
                worksheet.write(row, 0, '', payment_format)
                worksheet.write(row, 1, 'Payment', payment_format)
                worksheet.write(row, 2, payment.payment_date.strftime('%Y-%m-%d'), payment_format)
                worksheet.write(row, 3, payment.formatted_payment_id, payment_format)
                worksheet.write(row, 4, f"Payment - {payment_data['payment_method']}", payment_format)
                worksheet.write(row, 5, '', payment_format)
                worksheet.write(row, 6, float(payment_data['amount_received']), currency_format)
                worksheet.write(row, 7, '', payment_format)
                worksheet.write(row, 8, float(payment_data['running_balance']), currency_format)
                row += 1
    
    # Write summary
    row += 2
    worksheet.write(row, 0, 'SUMMARY', header_format)
    row += 1
    worksheet.write(row, 0, 'Total Invoice Amount:', customer_format)
    worksheet.write(row, 1, float(summary['total_invoice_amount']), currency_format)
    row += 1
    worksheet.write(row, 0, 'Total Payment Received:', customer_format)
    worksheet.write(row, 1, float(summary['total_payment_received']), currency_format)
    row += 1
    worksheet.write(row, 0, 'Total Pending Amount:', customer_format)
    worksheet.write(row, 1, float(summary['total_pending_amount']), currency_format)
    row += 1
    worksheet.write(row, 0, 'Ending Balance:', customer_format)
    worksheet.write(row, 1, float(summary['ending_balance']), currency_format)
    
    # Auto-adjust column widths
    worksheet.set_column('A:A', 25)
    worksheet.set_column('B:B', 12)
    worksheet.set_column('C:C', 12)
    worksheet.set_column('D:D', 15)
    worksheet.set_column('E:E', 30)
    worksheet.set_column('F:I', 15)
    
    workbook.close()
    output.seek(0)
    
    # Create response
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    
    filename = f"partner_ledger_{date_from}_{date_to}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


@login_required
@require_http_methods(["GET"])
def export_partner_ledger_pdf(request):
    """Export partner ledger report to PDF with custom layout"""
    form = PartnerLedgerFilterForm(request.GET)
    
    if not form.is_valid():
        messages.error(request, "Invalid filter parameters")
        return redirect('partner_ledger:report')
    
    # Get filter parameters
    customer = form.cleaned_data.get('customer')
    date_from = form.cleaned_data['date_from']
    date_to = form.cleaned_data['date_to']
    payment_status = form.cleaned_data.get('payment_status', 'all')
    
    # Generate report data
    report_data, summary = generate_partner_ledger_data(
        customer=customer,
        date_from=date_from,
        date_to=date_to,
        payment_status=payment_status
    )
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=36, leftMargin=36,
                           topMargin=20, bottomMargin=36)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Header styles
    company_style = ParagraphStyle(
        'CompanyStyle',
        parent=styles['Normal'],
        fontSize=12,
        fontName='Helvetica-Bold',
        alignment=0  # Left alignment
    )
    
    report_title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontSize=16,
        fontName='Helvetica-Bold',
        alignment=2  # Right alignment
    )
    
    customer_header_style = ParagraphStyle(
        'CustomerHeader',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=10,
        spaceBefore=5,
        alignment=0  # Left alignment
    )
    
    period_style = ParagraphStyle(
        'PeriodStyle',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=15,
        alignment=0  # Left alignment
    )
    
    # Get company details
    company = Company.objects.filter(is_active=True).first()
    if company:
        company_details = f"<b>{company.name}</b><br/>"
        if hasattr(company, 'address') and company.address:
            company_details += f"{company.address}<br/>"
        if hasattr(company, 'phone') and company.phone:
            company_details += f"Phone: {company.phone}<br/>"
        if hasattr(company, 'email') and company.email:
            company_details += f"Email: {company.email}"
    else:
        company_details = "<b>Company Name</b><br/>Company Address<br/>Phone: XXX-XXX-XXXX"
    
    # Create right column content with report title and customer/period info
    right_column_content = f"<b>Partner Ledger Report</b><br/><br/>"
    
    # Add customer and period information if available
    if report_data:
        first_customer = report_data[0]['customer']
        right_column_content += f"<b>Customer:</b> {first_customer.customer_code} - {first_customer.customer_name}<br/>"
        right_column_content += f"<b>Period:</b> {date_from} to {date_to}"
    
    # Create header table with company details on left and report info on right
    header_data = [[
        Paragraph(company_details, company_style),
        Paragraph(right_column_content, report_title_style)
    ]]
    
    # Get page width for full-width table
    page_width = landscape(A4)[0] - 72  # Total width minus margins
    
    header_table = Table(header_data, colWidths=[page_width*0.6, page_width*0.4])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10)
    ]))
    
    elements.append(header_table)
    elements.append(Spacer(1, 10))
    
    # Process each customer separately
    for customer_data in report_data:
        customer_obj = customer_data['customer']
        
        # Create table data with custom columns
        table_data = []
        table_data.append(['Date', 'Invoice No', 'Type', 'ED', 'CNTR', 'Items', 'Credit', 'Debit', 'Balance'])
        
        running_balance = 0
        
        for invoice_data in customer_data['invoices']:
            invoice = invoice_data['invoice']
            
            # Get invoice items (simplified - you may need to adjust based on your invoice model)
            items_description = "Various Items"  # Default description
            ed_info = ""
            cntr_info = ""
            
            # Try to get more detailed information if available
            try:
                # Assuming invoice has related items or job information
                if hasattr(invoice, 'job') and invoice.job:
                    items_description = f"Job: {invoice.job.job_number}"
                    if hasattr(invoice.job, 'container_number'):
                        cntr_info = invoice.job.container_number or ""
                elif hasattr(invoice, 'invoice_items') and invoice.invoice_items.exists():
                    items_list = [item.item.item_name for item in invoice.invoice_items.all()[:3]]
                    items_description = ", ".join(items_list)
                    if len(invoice.invoice_items.all()) > 3:
                        items_description += "..."
            except:
                pass
            
            running_balance += float(invoice_data['invoice_amount'])
            
            # Add invoice row
            table_data.append([
                invoice.invoice_date.strftime('%d/%m/%Y'),
                invoice.invoice_number,
                'Invoice',
                ed_info,
                cntr_info,
                items_description,
                f"₹ {invoice_data['invoice_amount']:,.2f}",
                '',
                f"₹ {running_balance:,.2f}"
            ])
            
            # Add payment rows
            for payment_data in invoice_data['payments']:
                payment = payment_data['payment']
                running_balance -= float(payment_data['amount_received'])
                
                table_data.append([
                    payment.payment_date.strftime('%d/%m/%Y'),
                    payment.formatted_payment_id,
                    'Payment',
                    '',
                    '',
                    f"Payment - {payment_data.get('payment_method', 'Cash')}",
                    '',
                    f"₹ {payment_data['amount_received']:,.2f}",
                    f"₹ {running_balance:,.2f}"
                ])
        
        # Calculate totals for this customer
        total_credit = sum(float(invoice_data['invoice_amount']) for invoice_data in customer_data['invoices'])
        total_debit = sum(float(payment_data['amount_received']) 
                         for invoice_data in customer_data['invoices'] 
                         for payment_data in invoice_data['payments'])
        final_balance = total_credit - total_debit
        
        # Add total row
        table_data.append([
            '', '', 'TOTAL', '', '', '',
            f"₹ {total_credit:,.2f}",
            f"₹ {total_debit:,.2f}",
            f"₹ {final_balance:,.2f}"
        ])
        
        # Create table with full page width
        # Calculate column widths as percentages of page width
        col_widths = [
            page_width * 0.10,  # Date
            page_width * 0.12,  # Invoice No
            page_width * 0.08,  # Type
            page_width * 0.08,  # ED
            page_width * 0.10,  # CNTR
            page_width * 0.25,  # Items
            page_width * 0.09,  # Credit
            page_width * 0.09,  # Debit
            page_width * 0.09   # Balance
        ]
        table = Table(table_data, colWidths=col_widths)
        
        table.setStyle(TableStyle([
            # Header row styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (5, 0), (5, -1), 'LEFT'),  # Items column left aligned
            ('ALIGN', (6, 0), (-1, -1), 'RIGHT'),  # Credit, Debit, Balance right aligned
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            
            # Data rows styling
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Alternate row colors for better readability (excluding total row)
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#F8F9FA')]),
            
            # Total row styling
            ('BACKGROUND', (-1, -1), (-1, -1), colors.HexColor('#E8F4FD')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 9),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black)
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
    
    # Summary section removed - totals are now integrated into each customer table
    
    # Build PDF
    doc.build(elements)
    
    # Get the value of the BytesIO buffer and write it to the response
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(content_type='application/pdf')
    filename = f"partner_ledger_{date_from}_{date_to}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write(pdf)
    
    return response


@login_required
def ajax_quick_filter(request):
    """AJAX endpoint for quick date filter"""
    if request.method == 'GET':
        filter_type = request.GET.get('filter_type')
        quick_form = QuickFilterForm()
        
        try:
            date_from, date_to = quick_form.get_date_range(filter_type)
            return JsonResponse({
                'success': True,
                'date_from': date_from.strftime('%Y-%m-%d'),
                'date_to': date_to.strftime('%Y-%m-%d')
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def ajax_customer_search(request):
    """AJAX endpoint for customer search"""
    if request.method == 'GET':
        query = request.GET.get('q', '')
        customers = Customer.objects.filter(
            Q(customer_name__icontains=query) | Q(customer_code__icontains=query),
            is_active=True
        ).order_by('customer_name')[:20]
        
        results = []
        for customer in customers:
            results.append({
                'id': customer.id,
                'text': f"{customer.customer_code} - {customer.customer_name}"
            })
        
        return JsonResponse({
            'results': results,
            'pagination': {'more': False}
        })
    
    return JsonResponse({'results': [], 'pagination': {'more': False}})