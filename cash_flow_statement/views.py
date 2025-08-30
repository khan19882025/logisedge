from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.urls import reverse
from chart_of_accounts.models import ChartOfAccount
from company.company_model import Company
from fiscal_year.models import FiscalYear
from ledger.models import Ledger
from multi_currency.models import Currency
from .models import CashFlowStatement, CashFlowTemplate, CashFlowCategory, CashFlowItem
from .forms import CashFlowStatementForm, QuickCashFlowForm, CashFlowTemplateForm
from decimal import Decimal
import json
import csv
from datetime import datetime, timedelta


@login_required
def cash_flow_statement_list(request):
    """List all saved Cash Flow Statements"""
    company = get_user_company(request.user)
    
    try:
        reports = CashFlowStatement.objects.filter(
            company=company,
            is_saved=True
        ).order_by('-created_at')
        
        # Pagination
        paginator = Paginator(reports, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'page_obj': page_obj,
            'reports': page_obj,
            'title': 'Cash Flow Statements',
        }
        
        return render(request, 'cash_flow_statement/report_list.html', context)
    except Exception as e:
        # Handle case where table doesn't exist yet - show empty state instead of error
        context = {
            'page_obj': None,
            'reports': [],
            'title': 'Cash Flow Statements',
        }
        return render(request, 'cash_flow_statement/report_list.html', context)


@login_required
def cash_flow_statement_create(request):
    """Create a new Cash Flow Statement"""
    company = get_user_company(request.user)
    
    try:
        if request.method == 'POST':
            form = CashFlowStatementForm(request.POST, user=request.user, company=company)
            if form.is_valid():
                report = form.save(commit=False)
                report.company = company
                report.fiscal_year = get_current_fiscal_year(company)
                report.created_by = request.user
                report.save()
                
                messages.success(request, 'Cash Flow Statement created successfully.')
                return redirect('cash_flow_statement:report_detail', pk=report.pk)
        else:
            form = CashFlowStatementForm(user=request.user, company=company)
        
        context = {
            'form': form,
            'title': 'Create Cash Flow Statement',
            'company': company,
        }
        
        return render(request, 'cash_flow_statement/report_form.html', context)
        
    except Exception as e:
        # Handle case where table doesn't exist yet
        messages.error(request, 'Cash Flow Statement tables are not set up yet. Please run migrations first.')
        return redirect('cash_flow_statement:report_list')


@login_required
def cash_flow_statement_detail(request, pk):
    """View and generate Cash Flow Statement"""
    company = get_user_company(request.user)
    report = get_object_or_404(CashFlowStatement, pk=pk, company=company)
    
    # Get report data
    report_data = generate_cash_flow_data(report)
    
    context = {
        'report': report,
        'report_data': report_data,
        'title': f'Cash Flow Statement - {report.name}',
        'company': company,
    }
    
    return render(request, 'cash_flow_statement/report_detail.html', context)


@login_required
def cash_flow_statement_quick(request):
    """Quick Cash Flow Statement with simple filters"""
    company = get_user_company(request.user)
    
    try:
        if request.method == 'POST':
            form = QuickCashFlowForm(request.POST, company=company)
            if form.is_valid():
                # Create a temporary report object
                report = CashFlowStatement(
                    name=f"Quick Cash Flow - {timezone.now().strftime('%d/%m/%Y %H:%M')}",
                    from_date=form.cleaned_data['from_date'],
                    to_date=form.cleaned_data['to_date'],
                    currency=form.cleaned_data['currency'],
                    report_type=form.cleaned_data['report_type'],
                    company=company,
                    fiscal_year=get_current_fiscal_year(company),
                    created_by=request.user,
                    export_format='PDF',
                    include_notes=True,
                    include_charts=True
                )
                
                # Generate report data
                report_data = generate_cash_flow_data(report)
                
                context = {
                    'report': report,
                    'report_data': report_data,
                    'form': form,
                    'title': 'Quick Cash Flow Statement',
                    'company': company,
                    'is_quick_report': True,
                }
                
                return render(request, 'cash_flow_statement/report_quick.html', context)
        else:
            form = QuickCashFlowForm(company=company)
        
        context = {
            'form': form,
            'title': 'Quick Cash Flow Statement',
            'company': company,
        }
        
        return render(request, 'cash_flow_statement/report_quick.html', context)
        
    except Exception as e:
        # Handle case where table doesn't exist yet
        messages.error(request, 'Cash Flow Statement tables are not set up yet. Please run migrations first.')
        return redirect('cash_flow_statement:report_list')


@login_required
def cash_flow_statement_export(request, pk):
    """Export Cash Flow Statement in various formats"""
    company = get_user_company(request.user)
    report = get_object_or_404(CashFlowStatement, pk=pk, company=company)
    export_format = request.GET.get('format', 'PDF')
    
    # Generate report data
    report_data = generate_cash_flow_data(report)
    
    if export_format == 'PDF':
        return export_report_pdf(report, report_data)
    elif export_format == 'EXCEL':
        return export_report_excel(report, report_data)
    elif export_format == 'CSV':
        return export_report_csv(report, report_data)
    else:
        messages.error(request, 'Invalid export format.')
        return redirect('cash_flow_statement:report_detail', pk=pk)


@login_required
def cash_flow_statement_save(request, pk):
    """Save a report configuration"""
    company = get_user_company(request.user)
    report = get_object_or_404(CashFlowStatement, pk=pk, company=company)
    
    if request.method == 'POST':
        report.is_saved = True
        report.save()
        messages.success(request, 'Report saved successfully.')
    
    return redirect('cash_flow_statement:report_detail', pk=pk)


@login_required
def cash_flow_statement_delete(request, pk):
    """Delete a saved report"""
    company = get_user_company(request.user)
    report = get_object_or_404(CashFlowStatement, pk=pk, company=company)
    
    if request.method == 'POST':
        report.delete()
        messages.success(request, 'Report deleted successfully.')
        return redirect('cash_flow_statement:report_list')
    
    context = {
        'report': report,
        'title': 'Delete Report',
    }
    
    return render(request, 'cash_flow_statement/report_confirm_delete.html', context)


@login_required
def report_template_list(request):
    """List report templates"""
    company = get_user_company(request.user)
    
    templates = CashFlowTemplate.objects.filter(
        Q(is_public=True) | Q(created_by=request.user),
        is_active=True
    ).order_by('name')
    
    context = {
        'templates': templates,
        'title': 'Cash Flow Templates',
        'company': company,
    }
    
    return render(request, 'cash_flow_statement/template_list.html', context)


@login_required
def report_template_create(request):
    """Create a new report template"""
    if request.method == 'POST':
        form = CashFlowTemplateForm(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            template.created_by = request.user
            template.save()
            
            messages.success(request, 'Report template created successfully.')
            return redirect('cash_flow_statement:template_list')
    else:
        form = CashFlowTemplateForm()
    
    context = {
        'form': form,
        'title': 'Create Template',
    }
    
    return render(request, 'cash_flow_statement/template_form.html', context)


@login_required
def report_template_use(request, pk):
    """Use a template to create a report"""
    company = get_user_company(request.user)
    template = get_object_or_404(CashFlowTemplate, pk=pk, is_active=True)
    
    # Create report from template
    report = CashFlowStatement(
        name=f"Cash Flow from {template.name}",
        description=f"Generated from template: {template.name}",
        from_date=timezone.now().date().replace(day=1),
        to_date=timezone.now().date(),
        company=company,
        fiscal_year=get_current_fiscal_year(company),
        created_by=request.user,
        currency=Currency.objects.filter(code='AED').first(),
        report_type='DETAILED',
        export_format='PDF',
        include_notes=template.include_operating_activities,
        include_charts=True
    )
    report.save()
    
    messages.success(request, f'Report created from template "{template.name}".')
    return redirect('cash_flow_statement:report_detail', pk=report.pk)


@csrf_exempt
@login_required
def ajax_get_accounts(request):
    """AJAX endpoint to get accounts for dropdown"""
    company = get_user_company(request.user)
    search_term = request.GET.get('search', '')
    
    accounts = ChartOfAccount.objects.filter(
        company=company,
        is_active=True
    )
    
    if search_term:
        accounts = accounts.filter(
            Q(name__icontains=search_term) | Q(account_code__icontains=search_term)
        )
    
    accounts = accounts[:20]  # Limit results
    
    data = [{'id': acc.pk, 'text': f"{acc.account_code} - {acc.name}"} for acc in accounts]
    
    return JsonResponse({'results': data})


def generate_cash_flow_data(report):
    """Generate cash flow statement data based on report configuration"""
    
    # Initialize data structure
    data = {
        'operating_activities': {
            'net_income': Decimal('0.00'),
            'adjustments': [],
            'working_capital_changes': [],
            'cash_from_operations': Decimal('0.00'),
        },
        'investing_activities': {
            'asset_purchases': [],
            'asset_sales': [],
            'investments': [],
            'cash_used_in_investing': Decimal('0.00'),
        },
        'financing_activities': {
            'loan_inflows': [],
            'loan_outflows': [],
            'equity_transactions': [],
            'cash_from_financing': Decimal('0.00'),
        },
        'summary': {
            'net_change_in_cash': Decimal('0.00'),
            'opening_cash_balance': Decimal('0.00'),
            'closing_cash_balance': Decimal('0.00'),
        },
        'period_info': {
            'from_date': report.from_date,
            'to_date': report.to_date,
            'currency': report.currency,
            'company': report.company,
        }
    }
    
    # Calculate Operating Activities
    data['operating_activities'] = calculate_operating_activities(report)
    
    # Calculate Investing Activities
    data['investing_activities'] = calculate_investing_activities(report)
    
    # Calculate Financing Activities
    data['financing_activities'] = calculate_financing_activities(report)
    
    # Calculate Summary
    data['summary'] = calculate_cash_flow_summary(report, data)
    
    return data


def calculate_operating_activities(report):
    """Calculate operating activities section"""
    operating_data = {
        'net_income': Decimal('0.00'),
        'adjustments': [],
        'working_capital_changes': [],
        'cash_from_operations': Decimal('0.00'),
    }
    
    # Calculate Net Income (Revenue - Expenses)
    revenue_accounts = ChartOfAccount.objects.filter(
        company=report.company,
        account_type__category='REVENUE',
        is_active=True
    )
    
    expense_accounts = ChartOfAccount.objects.filter(
        company=report.company,
        account_type__category='EXPENSE',
        is_active=True
    )
    
    # Get revenue total
    revenue_total = Ledger.objects.filter(
        company=report.company,
        fiscal_year=report.fiscal_year,
        account__in=revenue_accounts,
        entry_date__range=[report.from_date, report.to_date],
        status='POSTED',
        entry_type='CR'
    ).aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total']
    
    # Get expense total
    expense_total = Ledger.objects.filter(
        company=report.company,
        fiscal_year=report.fiscal_year,
        account__in=expense_accounts,
        entry_date__range=[report.from_date, report.to_date],
        status='POSTED',
        entry_type='DR'
    ).aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total']
    
    operating_data['net_income'] = revenue_total - expense_total
    
    # Add common adjustments
    operating_data['adjustments'] = [
        {'name': 'Depreciation', 'amount': Decimal('0.00')},
        {'name': 'Amortization', 'amount': Decimal('0.00')},
        {'name': 'Bad Debt Expense', 'amount': Decimal('0.00')},
    ]
    
    # Calculate working capital changes
    operating_data['working_capital_changes'] = [
        {'name': 'Accounts Receivable', 'amount': Decimal('0.00')},
        {'name': 'Inventory', 'amount': Decimal('0.00')},
        {'name': 'Accounts Payable', 'amount': Decimal('0.00')},
        {'name': 'Accrued Expenses', 'amount': Decimal('0.00')},
    ]
    
    # Calculate cash from operations
    adjustments_total = sum(item['amount'] for item in operating_data['adjustments'])
    working_capital_total = sum(item['amount'] for item in operating_data['working_capital_changes'])
    operating_data['cash_from_operations'] = operating_data['net_income'] + adjustments_total + working_capital_total
    
    return operating_data


def calculate_investing_activities(report):
    """Calculate investing activities section"""
    investing_data = {
        'asset_purchases': [],
        'asset_sales': [],
        'investments': [],
        'cash_used_in_investing': Decimal('0.00'),
    }
    
    # Get asset accounts
    asset_accounts = ChartOfAccount.objects.filter(
        company=report.company,
        account_type__category='ASSET',
        is_active=True
    )
    
    # Calculate asset purchases and sales
    asset_entries = Ledger.objects.filter(
        company=report.company,
        fiscal_year=report.fiscal_year,
        account__in=asset_accounts,
        entry_date__range=[report.from_date, report.to_date],
        status='POSTED'
    )
    
    for entry in asset_entries:
        if entry.entry_type == 'DR':  # Asset purchase
            investing_data['asset_purchases'].append({
                'name': entry.account.name,
                'amount': entry.amount or Decimal('0.00')
            })
        else:  # Asset sale
            investing_data['asset_sales'].append({
                'name': entry.account.name,
                'amount': entry.amount or Decimal('0.00')
            })
    
    # Calculate total cash used in investing
    purchases_total = sum(item['amount'] for item in investing_data['asset_purchases'])
    sales_total = sum(item['amount'] for item in investing_data['asset_sales'])
    investing_data['cash_used_in_investing'] = purchases_total - sales_total
    
    return investing_data


def calculate_financing_activities(report):
    """Calculate financing activities section"""
    financing_data = {
        'loan_inflows': [],
        'loan_outflows': [],
        'equity_transactions': [],
        'cash_from_financing': Decimal('0.00'),
    }
    
    # Get liability and equity accounts
    liability_accounts = ChartOfAccount.objects.filter(
        company=report.company,
        account_type__category='LIABILITY',
        is_active=True
    )
    
    equity_accounts = ChartOfAccount.objects.filter(
        company=report.company,
        account_type__category='EQUITY',
        is_active=True
    )
    
    # Calculate loan transactions
    loan_entries = Ledger.objects.filter(
        company=report.company,
        fiscal_year=report.fiscal_year,
        account__in=liability_accounts,
        entry_date__range=[report.from_date, report.to_date],
        status='POSTED'
    )
    
    for entry in loan_entries:
        if entry.entry_type == 'CR':  # Loan inflow
            financing_data['loan_inflows'].append({
                'name': entry.account.name,
                'amount': entry.amount or Decimal('0.00')
            })
        else:  # Loan repayment
            financing_data['loan_outflows'].append({
                'name': entry.account.name,
                'amount': entry.amount or Decimal('0.00')
            })
    
    # Calculate equity transactions
    equity_entries = Ledger.objects.filter(
        company=report.company,
        fiscal_year=report.fiscal_year,
        account__in=equity_accounts,
        entry_date__range=[report.from_date, report.to_date],
        status='POSTED'
    )
    
    for entry in equity_entries:
        financing_data['equity_transactions'].append({
            'name': entry.account.name,
            'amount': entry.amount or Decimal('0.00'),
            'type': entry.entry_type
        })
    
    # Calculate total cash from financing
    inflows_total = sum(item['amount'] for item in financing_data['loan_inflows'])
    outflows_total = sum(item['amount'] for item in financing_data['loan_outflows'])
    equity_total = sum(item['amount'] for item in financing_data['equity_transactions'])
    financing_data['cash_from_financing'] = inflows_total - outflows_total + equity_total
    
    return financing_data


def calculate_cash_flow_summary(report, data):
    """Calculate cash flow summary"""
    summary = {
        'net_change_in_cash': Decimal('0.00'),
        'opening_cash_balance': Decimal('0.00'),
        'closing_cash_balance': Decimal('0.00'),
    }
    
    # Calculate net change in cash
    operating_cash = data['operating_activities']['cash_from_operations']
    investing_cash = data['investing_activities']['cash_used_in_investing']
    financing_cash = data['financing_activities']['cash_from_financing']
    
    summary['net_change_in_cash'] = operating_cash + investing_cash + financing_cash
    
    # Calculate opening cash balance (cash balance before report period)
    cash_accounts = ChartOfAccount.objects.filter(
        company=report.company,
        account_type__category='ASSET',
        name__icontains='cash',
        is_active=True
    )
    
    opening_balance = Ledger.objects.filter(
        company=report.company,
        fiscal_year=report.fiscal_year,
        account__in=cash_accounts,
        entry_date__lt=report.from_date,
        status='POSTED'
    ).aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total']
    
    summary['opening_cash_balance'] = opening_balance
    summary['closing_cash_balance'] = opening_balance + summary['net_change_in_cash']
    
    return summary


def get_user_company(user):
    """Get the company for the current user"""
    try:
        return Company.objects.first()  # Assuming single company for now
    except Company.DoesNotExist:
        return None


def get_current_fiscal_year(company):
    """Get the current fiscal year for the company"""
    # First try to get the current fiscal year
    current_fy = FiscalYear.objects.filter(is_current=True).first()
    if current_fy:
        return current_fy
    
    # If no current fiscal year, get the most recent one
    return FiscalYear.objects.order_by('-start_date').first()


def export_report_pdf(report, report_data):
    """Export report as PDF"""
    # This is a placeholder - you'll need to implement actual PDF generation
    html_content = render_to_string('cash_flow_statement/report_pdf.html', {
        'report': report,
        'report_data': report_data,
    })
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="cash_flow_statement_{report.pk}.pdf"'
    
    # For now, return HTML content - you'll need to convert to PDF
    response.write(html_content)
    return response


def export_report_excel(report, report_data):
    """Export report as Excel"""
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="cash_flow_statement_{report.pk}.xlsx"'
    
    # For now, return CSV format
    response.write("Cash Flow Statement\n")
    response.write(f"Period: {report.from_date} to {report.to_date}\n\n")
    
    # Operating Activities
    response.write("Operating Activities\n")
    response.write(f"Net Income,{report_data['operating_activities']['net_income']}\n")
    response.write(f"Cash from Operations,{report_data['operating_activities']['cash_from_operations']}\n\n")
    
    # Investing Activities
    response.write("Investing Activities\n")
    response.write(f"Cash used in Investing,{report_data['investing_activities']['cash_used_in_investing']}\n\n")
    
    # Financing Activities
    response.write("Financing Activities\n")
    response.write(f"Cash from Financing,{report_data['financing_activities']['cash_from_financing']}\n\n")
    
    # Summary
    response.write("Summary\n")
    response.write(f"Net Change in Cash,{report_data['summary']['net_change_in_cash']}\n")
    response.write(f"Opening Cash Balance,{report_data['summary']['opening_cash_balance']}\n")
    response.write(f"Closing Cash Balance,{report_data['summary']['closing_cash_balance']}\n")
    
    return response


def export_report_csv(report, report_data):
    """Export report as CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="cash_flow_statement_{report.pk}.csv"'
    
    response.write("Cash Flow Statement\n")
    response.write(f"Period: {report.from_date} to {report.to_date}\n\n")
    
    # Operating Activities
    response.write("Operating Activities\n")
    response.write(f"Net Income,{report_data['operating_activities']['net_income']}\n")
    response.write(f"Cash from Operations,{report_data['operating_activities']['cash_from_operations']}\n\n")
    
    # Investing Activities
    response.write("Investing Activities\n")
    response.write(f"Cash used in Investing,{report_data['investing_activities']['cash_used_in_investing']}\n\n")
    
    # Financing Activities
    response.write("Financing Activities\n")
    response.write(f"Cash from Financing,{report_data['financing_activities']['cash_from_financing']}\n\n")
    
    # Summary
    response.write("Summary\n")
    response.write(f"Net Change in Cash,{report_data['summary']['net_change_in_cash']}\n")
    response.write(f"Opening Cash Balance,{report_data['summary']['opening_cash_balance']}\n")
    response.write(f"Closing Cash Balance,{report_data['summary']['closing_cash_balance']}\n")
    
    return response


@login_required
def quick_report_export(request):
    """Export quick report in various formats"""
    try:
        if request.method != 'POST':
            return JsonResponse({'error': 'Invalid request method'}, status=400)
        
        company = get_user_company(request.user)
        export_format = request.POST.get('export_format', 'PDF')
        
        # Create a temporary report object
        report = CashFlowStatement(
            name=f"Quick Cash Flow - {timezone.now().strftime('%d/%m/%Y %H:%M')}",
            from_date=request.POST.get('from_date'),
            to_date=request.POST.get('to_date'),
            currency_id=request.POST.get('currency'),
            report_type=request.POST.get('report_type', 'DETAILED'),
            company=company,
            fiscal_year=get_current_fiscal_year(company),
            created_by=request.user,
            export_format=export_format,
            include_notes=True,
            include_charts=True
        )
        
        # Generate report data
        report_data = generate_cash_flow_data(report)
        
        if export_format == 'PDF':
            return export_report_pdf(report, report_data)
        elif export_format == 'EXCEL':
            return export_report_excel(report, report_data)
        elif export_format == 'CSV':
            return export_report_csv(report, report_data)
        else:
            return JsonResponse({'error': 'Invalid export format'}, status=400)
            
    except Exception as e:
        return JsonResponse({'error': 'Cash Flow Statement tables are not set up yet. Please run migrations first.'}, status=500)


@login_required
def quick_report_save(request):
    """Save a quick report"""
    try:
        if request.method != 'POST':
            return JsonResponse({'error': 'Invalid request method'}, status=400)
        
        company = get_user_company(request.user)
        
        # Create and save the report
        report = CashFlowStatement(
            name=f"Quick Cash Flow - {timezone.now().strftime('%d/%m/%Y %H:%M')}",
            from_date=request.POST.get('from_date'),
            to_date=request.POST.get('to_date'),
            currency_id=request.POST.get('currency'),
            report_type=request.POST.get('report_type', 'DETAILED'),
            company=company,
            fiscal_year=get_current_fiscal_year(company),
            created_by=request.user,
            export_format='PDF',
            include_notes=True,
            include_charts=True,
            is_saved=True
        )
        report.save()
        
        return JsonResponse({
            'success': True,
            'redirect_url': reverse('cash_flow_statement:report_detail', kwargs={'pk': report.pk})
        })
        
    except Exception as e:
        return JsonResponse({'error': 'Cash Flow Statement tables are not set up yet. Please run migrations first.'}, status=500) 