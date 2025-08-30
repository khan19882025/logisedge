from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from django.utils import timezone
from django.db import transaction
from django.core.files.base import ContentFile
import json
import csv
import io
from datetime import datetime, timedelta, date
from decimal import Decimal

from .models import (
    BankReconciliationSession, ERPTransaction, BankStatementEntry, 
    MatchedEntry, ReconciliationReport
)
from .forms import (
    BankReconciliationSessionForm, BankStatementImportForm, BankStatementEntryForm,
    ReconciliationFilterForm, ManualMatchForm, BulkMatchForm, ReconciliationReportForm
)
from bank_accounts.models import BankAccount
from bank_accounts.models import BankAccountTransaction
from chart_of_accounts.models import ChartOfAccount
from company.company_model import Company


class DateEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle date objects"""
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)


@login_required
def reconciliation_dashboard(request):
    """Dashboard view for bank reconciliation overview"""
    
    # Get company
    company = Company.objects.filter(is_active=True).first()
    if not company:
        messages.error(request, "No active company found.")
        return redirect('dashboard:dashboard')
    
    # Get active bank accounts
    bank_accounts = BankAccount.objects.filter(
        company=company,
        status='active'
    ).select_related('currency')
    
    # Get recent reconciliation sessions
    recent_sessions = BankReconciliationSession.objects.filter(
        bank_account__company=company
    ).select_related('bank_account').order_by('-created_at')[:5]
    
    # Get reconciliation statistics
    total_sessions = BankReconciliationSession.objects.filter(
        bank_account__company=company
    ).count()
    
    completed_sessions = BankReconciliationSession.objects.filter(
        bank_account__company=company,
        status='completed'
    ).count()
    
    open_sessions = BankReconciliationSession.objects.filter(
        bank_account__company=company,
        status__in=['open', 'in_progress']
    ).count()
    
    context = {
        'bank_accounts': bank_accounts,
        'recent_sessions': recent_sessions,
        'total_sessions': total_sessions,
        'completed_sessions': completed_sessions,
        'open_sessions': open_sessions,
    }
    
    return render(request, 'bank_reconciliation/dashboard.html', context)


@login_required
def session_list(request):
    """List view for reconciliation sessions"""
    
    # Get search parameters
    bank_account_id = request.GET.get('bank_account')
    status = request.GET.get('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Base queryset
    queryset = BankReconciliationSession.objects.select_related(
        'bank_account', 'bank_account__currency', 'created_by'
    )
    
    # Apply filters
    if bank_account_id:
        queryset = queryset.filter(bank_account_id=bank_account_id)
    
    if status:
        queryset = queryset.filter(status=status)
    
    if date_from:
        queryset = queryset.filter(reconciliation_date__gte=date_from)
    
    if date_to:
        queryset = queryset.filter(reconciliation_date__lte=date_to)
    
    # Pagination
    paginator = Paginator(queryset, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get bank accounts for filter
    bank_accounts = BankAccount.objects.filter(status='active')
    
    context = {
        'page_obj': page_obj,
        'bank_accounts': bank_accounts,
        'status_choices': BankReconciliationSession.STATUS_CHOICES,
    }
    
    return render(request, 'bank_reconciliation/session_list.html', context)


@login_required
def session_create(request):
    """Create new reconciliation session"""
    
    if request.method == 'POST':
        form = BankReconciliationSessionForm(request.POST, user=request.user)
        if form.is_valid():
            session = form.save(commit=False)
            session.created_by = request.user
            session.save()
            
            messages.success(request, f'Reconciliation session "{session.session_name}" created successfully.')
            return redirect('bank_reconciliation:session_detail', pk=session.pk)
    else:
        form = BankReconciliationSessionForm(user=request.user)
    
    context = {
        'form': form,
        'title': 'Create Reconciliation Session',
        'submit_text': 'Create Session',
    }
    
    return render(request, 'bank_reconciliation/session_form.html', context)


@login_required
def session_detail(request, pk):
    """Detail view for reconciliation session"""
    
    session = get_object_or_404(BankReconciliationSession.objects.select_related(
        'bank_account', 'bank_account__currency', 'created_by'
    ), pk=pk)
    
    # Get entries with pagination
    erp_entries = ERPTransaction.objects.filter(
        reconciliation_session=session
    ).order_by('transaction_date', 'created_at')
    
    bank_entries = BankStatementEntry.objects.filter(
        reconciliation_session=session
    ).order_by('transaction_date', 'created_at')
    
    # Apply filters if provided
    filter_form = ReconciliationFilterForm(request.GET)
    if filter_form.is_valid():
        start_date = filter_form.cleaned_data.get('start_date')
        end_date = filter_form.cleaned_data.get('end_date')
        search_term = filter_form.cleaned_data.get('search_term')
        match_status = filter_form.cleaned_data.get('match_status')
        transaction_type = filter_form.cleaned_data.get('transaction_type')
        
        if start_date:
            erp_entries = erp_entries.filter(transaction_date__gte=start_date)
            bank_entries = bank_entries.filter(transaction_date__gte=start_date)
        
        if end_date:
            erp_entries = erp_entries.filter(transaction_date__lte=end_date)
            bank_entries = bank_entries.filter(transaction_date__lte=end_date)
        
        if search_term:
            erp_entries = erp_entries.filter(
                Q(description__icontains=search_term) |
                Q(reference_number__icontains=search_term)
            )
            bank_entries = bank_entries.filter(
                Q(description__icontains=search_term) |
                Q(reference_number__icontains=search_term)
            )
        
        if match_status == 'matched':
            erp_entries = erp_entries.filter(is_matched=True)
            bank_entries = bank_entries.filter(is_matched=True)
        elif match_status == 'unmatched':
            erp_entries = erp_entries.filter(is_matched=False)
            bank_entries = bank_entries.filter(is_matched=False)
        
        if transaction_type == 'credit':
            erp_entries = erp_entries.filter(credit_amount__gt=0)
            bank_entries = bank_entries.filter(credit_amount__gt=0)
        elif transaction_type == 'debit':
            erp_entries = erp_entries.filter(debit_amount__gt=0)
            bank_entries = bank_entries.filter(debit_amount__gt=0)
    
    # Pagination
    erp_paginator = Paginator(erp_entries, 50)
    bank_paginator = Paginator(bank_entries, 50)
    
    erp_page = request.GET.get('erp_page')
    bank_page = request.GET.get('bank_page')
    
    erp_page_obj = erp_paginator.get_page(erp_page)
    bank_page_obj = bank_paginator.get_page(bank_page)
    
    # Calculate summary statistics
    total_erp_credits = erp_entries.filter(credit_amount__gt=0).aggregate(
        total=Sum('credit_amount')
    )['total'] or 0
    
    total_erp_debits = erp_entries.filter(debit_amount__gt=0).aggregate(
        total=Sum('debit_amount')
    )['total'] or 0
    
    total_bank_credits = bank_entries.filter(credit_amount__gt=0).aggregate(
        total=Sum('credit_amount')
    )['total'] or 0
    
    total_bank_debits = bank_entries.filter(debit_amount__gt=0).aggregate(
        total=Sum('debit_amount')
    )['total'] or 0
    
    context = {
        'session': session,
        'erp_page_obj': erp_page_obj,
        'bank_page_obj': bank_page_obj,
        'filter_form': filter_form,
        'total_erp_credits': total_erp_credits,
        'total_erp_debits': total_erp_debits,
        'total_bank_credits': total_bank_credits,
        'total_bank_debits': total_bank_debits,
    }
    
    return render(request, 'bank_reconciliation/session_detail.html', context)


@login_required
def session_edit(request, pk):
    """Edit reconciliation session"""
    
    session = get_object_or_404(BankReconciliationSession, pk=pk)
    
    if session.status in ['completed', 'locked']:
        messages.error(request, 'Cannot edit a completed or locked session.')
        return redirect('bank_reconciliation:session_detail', pk=session.pk)
    
    if request.method == 'POST':
        form = BankReconciliationSessionForm(request.POST, instance=session, user=request.user)
        if form.is_valid():
            session = form.save(commit=False)
            session.updated_by = request.user
            session.save()
            
            messages.success(request, f'Reconciliation session "{session.session_name}" updated successfully.')
            return redirect('bank_reconciliation:session_detail', pk=session.pk)
    else:
        form = BankReconciliationSessionForm(instance=session, user=request.user)
    
    context = {
        'form': form,
        'session': session,
        'title': 'Edit Reconciliation Session',
        'submit_text': 'Update Session',
    }
    
    return render(request, 'bank_reconciliation/session_form.html', context)


@login_required
def import_bank_statement(request, session_pk):
    """Import bank statement entries"""
    
    session = get_object_or_404(BankReconciliationSession, pk=session_pk)
    
    if session.status in ['completed', 'locked']:
        messages.error(request, 'Cannot import into a completed or locked session.')
        return redirect('bank_reconciliation:session_detail', pk=session.pk)
    
    if request.method == 'POST':
        form = BankStatementImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                imported_count = process_bank_statement_import(
                    session, 
                    form.cleaned_data, 
                    request.FILES['import_file']
                )
                messages.success(request, f'Successfully imported {imported_count} bank statement entries.')
                return redirect('bank_reconciliation:session_detail', pk=session.pk)
            except Exception as e:
                messages.error(request, f'Import failed: {str(e)}')
    else:
        form = BankStatementImportForm(initial={'reconciliation_session': session})
    
    context = {
        'form': form,
        'session': session,
        'title': 'Import Bank Statement',
        'submit_text': 'Import Statement',
    }
    
    return render(request, 'bank_reconciliation/import_form.html', context)


def process_bank_statement_import(session, form_data, file):
    """Process bank statement import"""
    
    import_format = form_data['import_format']
    skip_first_row = form_data['skip_first_row']
    date_format = form_data['date_format']
    
    # Column mappings
    date_col = form_data['date_column']
    desc_col = form_data['description_column']
    ref_col = form_data['reference_column']
    debit_col = form_data['debit_column']
    credit_col = form_data['credit_column']
    
    imported_count = 0
    
    if import_format == 'csv':
        # Read CSV file
        decoded_file = file.read().decode('utf-8')
        csv_data = csv.DictReader(io.StringIO(decoded_file))
        
        for row in csv_data:
            if skip_first_row and imported_count == 0:
                continue
            
            try:
                # Parse date
                date_str = row.get(date_col, '').strip()
                if not date_str:
                    continue
                
                transaction_date = datetime.strptime(date_str, date_format).date()
                
                # Parse amounts
                debit_amount = Decimal(row.get(debit_col, '0').replace(',', '')) or 0
                credit_amount = Decimal(row.get(credit_col, '0').replace(',', '')) or 0
                
                # Create bank statement entry
                BankStatementEntry.objects.create(
                    reconciliation_session=session,
                    transaction_date=transaction_date,
                    description=row.get(desc_col, '').strip(),
                    reference_number=row.get(ref_col, '').strip() or None,
                    debit_amount=debit_amount,
                    credit_amount=credit_amount,
                    import_source='csv',
                    import_reference=file.name
                )
                
                imported_count += 1
                
            except (ValueError, KeyError) as e:
                # Skip invalid rows
                continue
    
    return imported_count


@login_required
def add_bank_entry(request, session_pk):
    """Add manual bank statement entry"""
    
    session = get_object_or_404(BankReconciliationSession, pk=session_pk)
    
    if session.status in ['completed', 'locked']:
        messages.error(request, 'Cannot add entries to a completed or locked session.')
        return redirect('bank_reconciliation:session_detail', pk=session.pk)
    
    if request.method == 'POST':
        form = BankStatementEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.reconciliation_session = session
            entry.import_source = 'manual'
            entry.save()
            
            messages.success(request, 'Bank statement entry added successfully.')
            return redirect('bank_reconciliation:session_detail', pk=session.pk)
    else:
        form = BankStatementEntryForm()
    
    context = {
        'form': form,
        'session': session,
        'title': 'Add Bank Statement Entry',
        'submit_text': 'Add Entry',
    }
    
    return render(request, 'bank_reconciliation/bank_entry_form.html', context)


@login_required
def manual_match(request, session_pk):
    """Manual matching interface"""
    
    session = get_object_or_404(BankReconciliationSession, pk=session_pk)
    
    if request.method == 'POST':
        form = ManualMatchForm(request.POST, reconciliation_session=session)
        if form.is_valid():
            erp_entry = form.cleaned_data['erp_entry']
            bank_entry = form.cleaned_data['bank_entry']
            match_type = form.cleaned_data['match_type']
            notes = form.cleaned_data['notes']
            
            # Create match
            with transaction.atomic():
                # Mark entries as matched
                erp_entry.match_with_bank_entry(bank_entry, notes)
                
                # Create matched entry record
                MatchedEntry.objects.create(
                    reconciliation_session=session,
                    erp_entry=erp_entry,
                    bank_entry=bank_entry,
                    match_type=match_type,
                    notes=notes,
                    created_by=request.user
                )
            
            messages.success(request, 'Entries matched successfully.')
            return redirect('bank_reconciliation:session_detail', pk=session.pk)
    else:
        form = ManualMatchForm(reconciliation_session=session)
    
    context = {
        'form': form,
        'session': session,
        'title': 'Manual Match Entries',
        'submit_text': 'Match Entries',
    }
    
    return render(request, 'bank_reconciliation/manual_match_form.html', context)


@login_required
def bulk_match(request, session_pk):
    """Bulk matching interface"""
    
    session = get_object_or_404(BankReconciliationSession, pk=session_pk)
    
    if request.method == 'POST':
        form = BulkMatchForm(request.POST)
        if form.is_valid():
            criteria = form.cleaned_data['match_criteria']
            date_tolerance = form.cleaned_data['date_tolerance']
            amount_tolerance = form.cleaned_data['amount_tolerance']
            auto_confirm = form.cleaned_data['auto_confirm_matches']
            
            # Perform bulk matching
            matches_found = perform_bulk_matching(
                session, criteria, date_tolerance, amount_tolerance, auto_confirm, request.user
            )
            
            messages.success(request, f'Found {matches_found} potential matches.')
            return redirect('bank_reconciliation:session_detail', pk=session.pk)
    else:
        form = BulkMatchForm()
    
    context = {
        'form': form,
        'session': session,
        'title': 'Bulk Match Entries',
        'submit_text': 'Find Matches',
    }
    
    return render(request, 'bank_reconciliation/bulk_match_form.html', context)


def perform_bulk_matching(session, criteria, date_tolerance, amount_tolerance, auto_confirm, user):
    """Perform bulk matching based on criteria"""
    
    matches_found = 0
    
    # Get unmatched entries
    unmatched_erp = ERPTransaction.objects.filter(
        reconciliation_session=session,
        is_matched=False
    )
    
    unmatched_bank = BankStatementEntry.objects.filter(
        reconciliation_session=session,
        is_matched=False
    )
    
    for erp_entry in unmatched_erp:
        for bank_entry in unmatched_bank:
            if is_match_candidate(erp_entry, bank_entry, criteria, date_tolerance, amount_tolerance):
                if auto_confirm:
                    # Auto-confirm match
                    with transaction.atomic():
                        erp_entry.match_with_bank_entry(bank_entry, "Auto-matched")
                        
                        MatchedEntry.objects.create(
                            reconciliation_session=session,
                            erp_entry=erp_entry,
                            bank_entry=bank_entry,
                            match_type='exact' if criteria == 'amount_date' else 'partial',
                            notes="Auto-matched",
                            created_by=user
                        )
                else:
                    # Just count potential matches
                    matches_found += 1
    
    return matches_found


def is_match_candidate(erp_entry, bank_entry, criteria, date_tolerance, amount_tolerance):
    """Check if two entries are potential matches"""
    
    # Check amount match
    amount_diff = abs(erp_entry.amount - bank_entry.amount)
    if amount_diff > amount_tolerance:
        return False
    
    if criteria == 'amount_only':
        return True
    
    # Check date match
    if criteria in ['amount_date', 'reference']:
        date_diff = abs((erp_entry.transaction_date - bank_entry.transaction_date).days)
        if date_diff > date_tolerance:
            return False
    
    # Check reference match
    if criteria == 'reference':
        if erp_entry.reference_number and bank_entry.reference_number:
            return erp_entry.reference_number.lower() == bank_entry.reference_number.lower()
    
    return True


@login_required
def generate_report(request, session_pk):
    """Generate reconciliation report"""
    
    session = get_object_or_404(BankReconciliationSession, pk=session_pk)
    
    if request.method == 'POST':
        form = ReconciliationReportForm(request.POST)
        if form.is_valid():
            report_type = form.cleaned_data['report_type']
            export_format = form.cleaned_data['export_format']
            
            # Generate report
            report_data = generate_reconciliation_report(session, form.cleaned_data)
            
            # Ensure report_data is JSON serializable
            try:
                # Test serialization to catch any remaining date objects
                json.dumps(report_data, cls=DateEncoder)
            except TypeError as e:
                # If there are still date objects, convert them
                report_data = json.loads(json.dumps(report_data, cls=DateEncoder))
            
            # Create report record
            report = ReconciliationReport.objects.create(
                reconciliation_session=session,
                report_type=report_type,
                report_data=report_data,
                generated_by=request.user
            )
            
            # Generate file if needed
            if export_format != 'web':
                report_file = generate_report_file(report_data, export_format)
                report.report_file.save(
                    f'reconciliation_report_{session.pk}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.{export_format}',
                    ContentFile(report_file)
                )
                report.save()
            
            messages.success(request, 'Report generated successfully.')
            return redirect('bank_reconciliation:session_detail', pk=session.pk)
    else:
        form = ReconciliationReportForm()
    
    context = {
        'form': form,
        'session': session,
        'title': 'Generate Report',
        'submit_text': 'Generate Report',
    }
    
    return render(request, 'bank_reconciliation/report_form.html', context)


def generate_reconciliation_report(session, form_data):
    """Generate reconciliation report data"""
    
    report_data = {
        'session_info': {
            'name': session.session_name,
            'bank_account': session.bank_account.bank_name,
            'reconciliation_date': session.reconciliation_date.isoformat() if session.reconciliation_date else None,
            'status': session.get_status_display(),
        },
        'summary': {
            'opening_balance_erp': float(session.opening_balance_erp),
            'opening_balance_bank': float(session.opening_balance_bank),
            'closing_balance_erp': float(session.closing_balance_erp),
            'closing_balance_bank': float(session.closing_balance_bank),
            'difference': float(session.difference_amount),
        },
        'entries': {
            'matched': [],
            'unmatched_erp': [],
            'unmatched_bank': [],
        }
    }
    
    # Get matched entries
    if form_data.get('include_matched_entries'):
        matched_entries = MatchedEntry.objects.filter(
            reconciliation_session=session
        ).select_related('erp_entry', 'bank_entry')
        
        for match in matched_entries:
            report_data['entries']['matched'].append({
                'erp_entry': {
                    'date': match.erp_entry.transaction_date.isoformat() if match.erp_entry.transaction_date else None,
                    'description': match.erp_entry.description,
                    'reference': match.erp_entry.reference_number,
                    'amount': float(match.erp_entry.amount),
                },
                'bank_entry': {
                    'date': match.bank_entry.transaction_date.isoformat() if match.bank_entry.transaction_date else None,
                    'description': match.bank_entry.description,
                    'reference': match.bank_entry.reference_number,
                    'amount': float(match.bank_entry.amount),
                },
                'match_type': match.match_type,
                'difference': float(match.difference_amount),
                'notes': match.notes,
            })
    
    # Get unmatched entries
    if form_data.get('include_unmatched_entries'):
        unmatched_erp = ERPTransaction.objects.filter(
            reconciliation_session=session,
            is_matched=False
        )
        
        unmatched_bank = BankStatementEntry.objects.filter(
            reconciliation_session=session,
            is_matched=False
        )
        
        for entry in unmatched_erp:
            report_data['entries']['unmatched_erp'].append({
                'date': entry.transaction_date.isoformat() if entry.transaction_date else None,
                'description': entry.description,
                'reference': entry.reference_number,
                'amount': float(entry.amount),
            })
        
        for entry in unmatched_bank:
            report_data['entries']['unmatched_bank'].append({
                'date': entry.transaction_date.isoformat() if entry.transaction_date else None,
                'description': entry.description,
                'reference': entry.reference_number,
                'amount': float(entry.amount),
            })
    
    return report_data


def generate_report_file(report_data, format_type):
    """Generate report file in specified format"""
    
    if format_type == 'csv':
        return generate_csv_report(report_data)
    elif format_type == 'excel':
        return generate_excel_report(report_data)
    else:
        return generate_pdf_report(report_data)


def generate_csv_report(report_data):
    """Generate CSV report"""
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Bank Reconciliation Report'])
    writer.writerow(['Session:', report_data['session_info']['name']])
    writer.writerow(['Bank Account:', report_data['session_info']['bank_account']])
    writer.writerow(['Date:', report_data['session_info']['reconciliation_date']])
    writer.writerow([])
    
    # Write summary
    writer.writerow(['Summary'])
    writer.writerow(['Opening Balance (ERP)', report_data['summary']['opening_balance_erp']])
    writer.writerow(['Opening Balance (Bank)', report_data['summary']['opening_balance_bank']])
    writer.writerow(['Closing Balance (ERP)', report_data['summary']['closing_balance_erp']])
    writer.writerow(['Closing Balance (Bank)', report_data['summary']['closing_balance_bank']])
    writer.writerow(['Difference', report_data['summary']['difference']])
    writer.writerow([])
    
    # Write matched entries
    if report_data['entries']['matched']:
        writer.writerow(['Matched Entries'])
        writer.writerow(['ERP Date', 'ERP Description', 'ERP Amount', 'Bank Date', 'Bank Description', 'Bank Amount', 'Difference'])
        
        for match in report_data['entries']['matched']:
            writer.writerow([
                match['erp_entry']['date'],
                match['erp_entry']['description'],
                match['erp_entry']['amount'],
                match['bank_entry']['date'],
                match['bank_entry']['description'],
                match['bank_entry']['amount'],
                match['difference'],
            ])
        writer.writerow([])
    
    # Write unmatched entries
    if report_data['entries']['unmatched_erp']:
        writer.writerow(['Unmatched ERP Entries'])
        writer.writerow(['Date', 'Description', 'Reference', 'Amount'])
        
        for entry in report_data['entries']['unmatched_erp']:
            writer.writerow([
                entry['date'],
                entry['description'],
                entry['reference'] or '',
                entry['amount'],
            ])
        writer.writerow([])
    
    if report_data['entries']['unmatched_bank']:
        writer.writerow(['Unmatched Bank Entries'])
        writer.writerow(['Date', 'Description', 'Reference', 'Amount'])
        
        for entry in report_data['entries']['unmatched_bank']:
            writer.writerow([
                entry['date'],
                entry['description'],
                entry['reference'] or '',
                entry['amount'],
            ])
    
    return output.getvalue().encode('utf-8')


def generate_excel_report(report_data):
    """Generate Excel report (placeholder)"""
    # This would use openpyxl or xlsxwriter to create Excel file
    # For now, return CSV format
    return generate_csv_report(report_data)


def generate_pdf_report(report_data):
    """Generate PDF report (placeholder)"""
    # This would use reportlab or weasyprint to create PDF
    # For now, return CSV format
    return generate_csv_report(report_data)


@login_required
@csrf_exempt
def ajax_unmatch_entry(request, entry_type, entry_id):
    """AJAX endpoint to unmatch an entry"""
    
    if entry_type == 'erp':
        entry = get_object_or_404(ERPTransaction, pk=entry_id)
        entry.unmatch()
    elif entry_type == 'bank':
        entry = get_object_or_404(BankStatementEntry, pk=entry_id)
        entry.unmatch()
    else:
        return JsonResponse({'success': False, 'error': 'Invalid entry type'})
    
    return JsonResponse({'success': True})


@login_required
@csrf_exempt
def ajax_get_matching_suggestions(request, session_pk):
    """AJAX endpoint to get matching suggestions"""
    
    session = get_object_or_404(BankReconciliationSession, pk=session_pk)
    entry_id = request.GET.get('entry_id')
    entry_type = request.GET.get('entry_type')
    
    if entry_type == 'erp':
        entry = get_object_or_404(ERPTransaction, pk=entry_id)
        suggestions = BankStatementEntry.objects.filter(
            reconciliation_session=session,
            is_matched=False,
            amount=entry.amount
        )[:5]
    else:
        entry = get_object_or_404(BankStatementEntry, pk=entry_id)
        suggestions = ERPTransaction.objects.filter(
            reconciliation_session=session,
            is_matched=False,
            amount=entry.amount
        )[:5]
    
    suggestions_data = []
    for suggestion in suggestions:
        suggestions_data.append({
            'id': suggestion.id,
            'date': suggestion.transaction_date.strftime('%Y-%m-%d'),
            'description': suggestion.description,
            'reference': suggestion.reference_number or '',
            'amount': float(suggestion.amount),
        })
    
    return JsonResponse({'suggestions': suggestions_data})
