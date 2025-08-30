from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q, Case, When, DecimalField
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta
import csv
import json

from .forms import SourcePaymentLedgerForm, SourcePaymentLedgerExportForm
from payment_source.models import PaymentSource
from ledger.models import Ledger
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch
from io import BytesIO


@login_required
def source_payment_ledger_report(request):
    """Main view for Source Payment Ledger report"""
    form = SourcePaymentLedgerForm(request.GET or None)
    export_form = SourcePaymentLedgerExportForm()
    
    report_data = []
    total_debit = Decimal('0.00')
    total_credit = Decimal('0.00')
    total_balance = Decimal('0.00')
    
    if form.is_valid():
        # Get filter parameters
        payment_sources = form.cleaned_data.get('payment_sources')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        
        # If no payment sources selected, get all active ones
        if not payment_sources:
            payment_sources = PaymentSource.objects.filter(active=True)
        
        # Calculate ledger data for each payment source
        for payment_source in payment_sources:
            ledger_data = calculate_payment_source_ledger(payment_source, date_from, date_to)
            if ledger_data:
                report_data.append(ledger_data)
                total_debit += ledger_data['total_debit']
                total_credit += ledger_data['total_credit']
                total_balance += ledger_data['balance']
    
    context = {
        'form': form,
        'export_form': export_form,
        'report_data': report_data,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'total_balance': total_balance,
        'has_data': bool(report_data),
    }
    
    return render(request, 'source_payment_ledger/report.html', context)


def calculate_payment_source_ledger(payment_source, date_from=None, date_to=None):
    """Calculate debit, credit, and balance for a payment source"""
    
    # Build query filters
    filters = Q(payment_source=payment_source, status='POSTED')
    
    if date_from:
        filters &= Q(entry_date__gte=date_from)
    if date_to:
        filters &= Q(entry_date__lte=date_to)
    
    # Get ledger entries for this payment source
    ledger_entries = Ledger.objects.filter(filters)
    
    # Calculate totals using conditional aggregation
    totals = ledger_entries.aggregate(
        total_debit=Sum(
            Case(
                When(entry_type='DR', then='amount'),
                default=Decimal('0.00'),
                output_field=DecimalField(max_digits=15, decimal_places=2)
            )
        ),
        total_credit=Sum(
            Case(
                When(entry_type='CR', then='amount'),
                default=Decimal('0.00'),
                output_field=DecimalField(max_digits=15, decimal_places=2)
            )
        )
    )
    
    total_debit = totals['total_debit'] or Decimal('0.00')
    total_credit = totals['total_credit'] or Decimal('0.00')
    balance = total_debit - total_credit
    
    return {
        'payment_source': payment_source,
        'payment_source_name': payment_source.name,
        'payment_source_code': payment_source.code or '',
        'total_debit': total_debit,
        'total_credit': total_credit,
        'balance': balance,
        'entry_count': ledger_entries.count(),
    }


@login_required
def export_source_payment_ledger(request):
    """Export Source Payment Ledger report in various formats"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed'}, status=405)
    
    # Get form data
    main_form = SourcePaymentLedgerForm(request.POST)
    export_form = SourcePaymentLedgerExportForm(request.POST)
    
    if not export_form.is_valid():
        return JsonResponse({'error': 'Invalid export parameters'}, status=400)
    
    # Extract filter values directly from POST data for more lenient validation
    payment_source_ids = request.POST.getlist('payment_sources')
    date_from_str = request.POST.get('date_from')
    date_to_str = request.POST.get('date_to')
    export_format = request.POST.get('export_format', 'pdf')
    include_details = request.POST.get('include_details') == 'on'
    
    # Parse dates
    date_from = None
    date_to = None
    
    if date_from_str:
        try:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    if date_to_str:
        try:
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    # Get payment sources
    if payment_source_ids:
        payment_sources = PaymentSource.objects.filter(id__in=payment_source_ids, active=True)
    else:
        payment_sources = PaymentSource.objects.filter(active=True)
    
    # Generate report data
    report_data = []
    for payment_source in payment_sources:
        ledger_data = calculate_payment_source_ledger(payment_source, date_from, date_to)
        if ledger_data:
            report_data.append(ledger_data)
    
    # Export based on format
    if export_format == 'pdf':
        return export_pdf(report_data, date_from, date_to, include_details)
    elif export_format == 'excel':
        return export_excel(report_data, date_from, date_to, include_details)
    elif export_format == 'csv':
        return export_csv(report_data, date_from, date_to, include_details)
    else:
        return JsonResponse({'error': 'Invalid export format'}, status=400)


def export_pdf(report_data, date_from, date_to, include_details):
    """Export report as PDF"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    elements.append(Paragraph("Source Payment Ledger Report", title_style))
    
    # Date range
    if date_from or date_to:
        date_range = f"Period: {date_from or 'Beginning'} to {date_to or 'End'}"
        elements.append(Paragraph(date_range, styles['Normal']))
        elements.append(Spacer(1, 12))
    
    # Table data
    table_data = [[
        'Payment Source',
        'Code',
        'Total Debit',
        'Total Credit',
        'Balance'
    ]]
    
    total_debit = Decimal('0.00')
    total_credit = Decimal('0.00')
    total_balance = Decimal('0.00')
    
    for data in report_data:
        table_data.append([
            data['payment_source_name'],
            data['payment_source_code'],
            f"{data['total_debit']:,.2f}",
            f"{data['total_credit']:,.2f}",
            f"{data['balance']:,.2f}"
        ])
        total_debit += data['total_debit']
        total_credit += data['total_credit']
        total_balance += data['balance']
    
    # Add totals row
    table_data.append([
        'TOTAL',
        '',
        f"{total_debit:,.2f}",
        f"{total_credit:,.2f}",
        f"{total_balance:,.2f}"
    ])
    
    # Create table
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    # Create response
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    filename = f"source_payment_ledger_{timezone.now().strftime('%Y-%m-%d')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


def export_excel(report_data, date_from, date_to, include_details):
    """Export report as Excel (placeholder - requires openpyxl)"""
    # For now, return CSV format
    return export_csv(report_data, date_from, date_to, include_details)


def export_csv(report_data, date_from, date_to, include_details):
    """Export report as CSV"""
    response = HttpResponse(content_type='text/csv')
    filename = f"source_payment_ledger_{timezone.now().strftime('%Y-%m-%d')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    
    # Header
    writer.writerow(['Source Payment Ledger Report'])
    if date_from or date_to:
        writer.writerow([f'Period: {date_from or "Beginning"} to {date_to or "End"}'])
    writer.writerow([])  # Empty row
    
    # Column headers
    writer.writerow([
        'Payment Source',
        'Code',
        'Total Debit',
        'Total Credit',
        'Balance'
    ])
    
    # Data rows
    total_debit = Decimal('0.00')
    total_credit = Decimal('0.00')
    total_balance = Decimal('0.00')
    
    for data in report_data:
        writer.writerow([
            data['payment_source_name'],
            data['payment_source_code'],
            float(data['total_debit']),
            float(data['total_credit']),
            float(data['balance'])
        ])
        total_debit += data['total_debit']
        total_credit += data['total_credit']
        total_balance += data['balance']
    
    # Totals row
    writer.writerow([
        'TOTAL',
        '',
        float(total_debit),
        float(total_credit),
        float(total_balance)
    ])
    
    return response