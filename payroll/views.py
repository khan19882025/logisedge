from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from datetime import date, datetime, timedelta
from decimal import Decimal
import calendar
import csv
import io

from .models import (
    SalaryStructure, EmployeeSalary, BankAccount, PayrollPeriod, PayrollRecord,
    WPSRecord, EndOfServiceBenefit, Loan, Advance, Payslip, PayrollAuditLog, GPSSARecord
)
from .forms import (
    SalaryStructureForm, EmployeeSalaryForm, BankAccountForm, PayrollPeriodForm,
    PayrollRecordForm, WPSRecordForm, EndOfServiceBenefitForm, LoanForm, AdvanceForm,
    GPSSARecordForm, PayrollSearchForm, BulkPayrollForm, WPSExportForm, EOSBCalculationForm
)


@login_required
def payroll_dashboard(request):
    """Payroll Management Dashboard"""
    today = date.today()
    current_year = today.year
    current_month = today.month
    
    # Get current payroll period
    try:
        current_period = PayrollPeriod.objects.get(year=current_year, month=current_month)
    except PayrollPeriod.DoesNotExist:
        current_period = None
    
    # Dashboard statistics
    total_employees = User.objects.filter(is_active=True).count()
    employees_with_salary = EmployeeSalary.objects.filter(is_active=True).count()
    employees_with_bank = BankAccount.objects.filter(is_active=True).count()
    
    # Payroll statistics
    if current_period:
        payroll_records = PayrollRecord.objects.filter(payroll_period=current_period)
        total_payroll = payroll_records.aggregate(
            total_gross=Sum('gross_salary'),
            total_net=Sum('net_salary'),
            total_deductions=Sum('total_deductions')
        )
        pending_approvals = payroll_records.filter(is_approved=False).count()
    else:
        total_payroll = {'total_gross': 0, 'total_net': 0, 'total_deductions': 0}
        pending_approvals = 0
    
    # Recent payroll periods
    recent_periods = PayrollPeriod.objects.order_by('-year', '-month')[:5]
    
    # Recent payroll records
    recent_records = PayrollRecord.objects.select_related('employee', 'payroll_period').order_by('-created_at')[:10]
    
    # Loan and advance statistics
    active_loans = Loan.objects.filter(status='active').count()
    pending_advances = Advance.objects.filter(status='pending').count()
    
    # WPS statistics
    wps_pending = WPSRecord.objects.filter(status='pending').count()
    wps_sent = WPSRecord.objects.filter(status='sent').count()
    wps_paid = WPSRecord.objects.filter(status='paid').count()
    
    context = {
        'current_period': current_period,
        'total_employees': total_employees,
        'employees_with_salary': employees_with_salary,
        'employees_with_bank': employees_with_bank,
        'total_payroll': total_payroll,
        'pending_approvals': pending_approvals,
        'recent_periods': recent_periods,
        'recent_records': recent_records,
        'active_loans': active_loans,
        'pending_advances': pending_advances,
        'wps_pending': wps_pending,
        'wps_sent': wps_sent,
        'wps_paid': wps_paid,
        'current_year': current_year,
        'current_month': current_month,
    }
    
    return render(request, 'payroll/dashboard.html', context)


@login_required
@permission_required('payroll.can_manage_salary_structures')
def salary_structure_list(request):
    """List salary structures"""
    salary_structures = SalaryStructure.objects.all().order_by('name')
    
    context = {
        'salary_structures': salary_structures,
    }
    return render(request, 'payroll/salary_structure_list.html', context)


@login_required
@permission_required('payroll.can_manage_salary_structures')
def salary_structure_create(request):
    """Create new salary structure"""
    if request.method == 'POST':
        form = SalaryStructureForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Salary structure created successfully!')
            return redirect('payroll:salary_structure_list')
    else:
        form = SalaryStructureForm()
    
    context = {
        'form': form,
        'title': 'Create Salary Structure'
    }
    return render(request, 'payroll/salary_structure_form.html', context)


@login_required
@permission_required('payroll.can_manage_salary_structures')
def salary_structure_edit(request, structure_id):
    """Edit salary structure"""
    salary_structure = get_object_or_404(SalaryStructure, id=structure_id)
    
    if request.method == 'POST':
        form = SalaryStructureForm(request.POST, instance=salary_structure)
        if form.is_valid():
            form.save()
            messages.success(request, 'Salary structure updated successfully!')
            return redirect('payroll:salary_structure_list')
    else:
        form = SalaryStructureForm(instance=salary_structure)
    
    context = {
        'form': form,
        'salary_structure': salary_structure,
        'title': 'Edit Salary Structure'
    }
    return render(request, 'payroll/salary_structure_form.html', context)


@login_required
@permission_required('payroll.can_manage_employee_salaries')
def employee_salary_list(request):
    """List employee salaries"""
    employee_salaries = EmployeeSalary.objects.select_related('employee', 'salary_structure').order_by('employee__first_name')
    
    # Pagination
    paginator = Paginator(employee_salaries, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'payroll/employee_salary_list.html', context)


@login_required
@permission_required('payroll.can_manage_employee_salaries')
def employee_salary_create(request):
    """Create employee salary"""
    if request.method == 'POST':
        form = EmployeeSalaryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Employee salary created successfully!')
            return redirect('payroll:employee_salary_list')
    else:
        form = EmployeeSalaryForm()
    
    context = {
        'form': form,
        'title': 'Create Employee Salary'
    }
    return render(request, 'payroll/employee_salary_form.html', context)


@login_required
@permission_required('payroll.can_manage_employee_salaries')
def employee_salary_edit(request, salary_id):
    """Edit employee salary"""
    employee_salary = get_object_or_404(EmployeeSalary, id=salary_id)
    
    if request.method == 'POST':
        form = EmployeeSalaryForm(request.POST, instance=employee_salary)
        if form.is_valid():
            form.save()
            messages.success(request, 'Employee salary updated successfully!')
            return redirect('payroll:employee_salary_list')
    else:
        form = EmployeeSalaryForm(instance=employee_salary)
    
    context = {
        'form': form,
        'employee_salary': employee_salary,
        'title': 'Edit Employee Salary'
    }
    return render(request, 'payroll/employee_salary_form.html', context)


@login_required
@permission_required('payroll.can_manage_bank_accounts')
def bank_account_list(request):
    """List bank accounts"""
    bank_accounts = BankAccount.objects.select_related('employee').order_by('employee__first_name')
    
    # Pagination
    paginator = Paginator(bank_accounts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'payroll/bank_account_list.html', context)


@login_required
@permission_required('payroll.can_manage_bank_accounts')
def bank_account_create(request):
    """Create bank account"""
    if request.method == 'POST':
        form = BankAccountForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Bank account created successfully!')
            return redirect('payroll:bank_account_list')
    else:
        form = BankAccountForm()
    
    context = {
        'form': form,
        'title': 'Create Bank Account'
    }
    return render(request, 'payroll/bank_account_form.html', context)


@login_required
@permission_required('payroll.can_manage_bank_accounts')
def bank_account_edit(request, account_id):
    """Edit bank account"""
    bank_account = get_object_or_404(BankAccount, id=account_id)
    
    if request.method == 'POST':
        form = BankAccountForm(request.POST, instance=bank_account)
        if form.is_valid():
            form.save()
            messages.success(request, 'Bank account updated successfully!')
            return redirect('payroll:bank_account_list')
    else:
        form = BankAccountForm(instance=bank_account)
    
    context = {
        'form': form,
        'bank_account': bank_account,
        'title': 'Edit Bank Account'
    }
    return render(request, 'payroll/bank_account_form.html', context)


@login_required
@permission_required('payroll.can_process_payroll')
def payroll_period_list(request):
    """List payroll periods"""
    payroll_periods = PayrollPeriod.objects.all().order_by('-year', '-month')
    
    context = {
        'payroll_periods': payroll_periods,
    }
    return render(request, 'payroll/payroll_period_list.html', context)


@login_required
@permission_required('payroll.can_process_payroll')
def payroll_period_create(request):
    """Create payroll period"""
    if request.method == 'POST':
        form = PayrollPeriodForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payroll period created successfully!')
            return redirect('payroll:payroll_period_list')
    else:
        form = PayrollPeriodForm()
    
    context = {
        'form': form,
        'title': 'Create Payroll Period'
    }
    return render(request, 'payroll/payroll_period_form.html', context)


@login_required
@permission_required('payroll.can_process_payroll')
def payroll_process(request, period_id):
    """Process payroll for a period"""
    payroll_period = get_object_or_404(PayrollPeriod, id=period_id)
    
    if request.method == 'POST':
        form = BulkPayrollForm(request.POST)
        if form.is_valid():
            employees = form.cleaned_data['employees']
            include_overtime = form.cleaned_data['include_overtime']
            include_deductions = form.cleaned_data['include_deductions']
            
            # Process payroll for selected employees
            processed_count = 0
            for employee in employees:
                try:
                    # Get employee salary
                    employee_salary = EmployeeSalary.objects.get(employee=employee, is_active=True)
                    
                    # Create or update payroll record
                    payroll_record, created = PayrollRecord.objects.get_or_create(
                        payroll_period=payroll_period,
                        employee=employee,
                        defaults={
                            'basic_salary': employee_salary.basic_salary,
                            'housing_allowance': employee_salary.housing_allowance,
                            'transport_allowance': employee_salary.transport_allowance,
                            'other_allowances': employee_salary.other_allowances,
                        }
                    )
                    
                    if not created:
                        # Update existing record
                        payroll_record.basic_salary = employee_salary.basic_salary
                        payroll_record.housing_allowance = employee_salary.housing_allowance
                        payroll_record.transport_allowance = employee_salary.transport_allowance
                        payroll_record.other_allowances = employee_salary.other_allowances
                    
                    # Calculate working days (basic calculation)
                    working_days = 22  # Default working days per month
                    payroll_record.working_days = working_days
                    
                    # Calculate deductions if enabled
                    if include_deductions:
                        # Loan deductions
                        active_loans = Loan.objects.filter(employee=employee, status='active')
                        loan_deduction = sum(loan.monthly_installment for loan in active_loans)
                        payroll_record.loan_deduction = loan_deduction
                        
                        # Advance deductions
                        pending_advances = Advance.objects.filter(employee=employee, status='approved')
                        advance_deduction = sum(advance.amount for advance in pending_advances)
                        payroll_record.advance_deduction = advance_deduction
                    
                    payroll_record.save()
                    processed_count += 1
                    
                except EmployeeSalary.DoesNotExist:
                    messages.warning(request, f'No salary record found for {employee.get_full_name()}')
                    continue
            
            messages.success(request, f'Payroll processed for {processed_count} employees!')
            return redirect('payroll:payroll_record_list', period_id=period_id)
    else:
        form = BulkPayrollForm(initial={'payroll_period': payroll_period})
    
    context = {
        'form': form,
        'payroll_period': payroll_period,
    }
    return render(request, 'payroll/payroll_process.html', context)


@login_required
@permission_required('payroll.can_process_payroll')
def payroll_record_list(request, period_id):
    """List payroll records for a period"""
    payroll_period = get_object_or_404(PayrollPeriod, id=period_id)
    payroll_records = PayrollRecord.objects.filter(payroll_period=payroll_period).select_related('employee')
    
    # Search and filter
    search_form = PayrollSearchForm(request.GET)
    if search_form.is_valid():
        if search_form.cleaned_data.get('employee'):
            payroll_records = payroll_records.filter(employee=search_form.cleaned_data['employee'])
        if search_form.cleaned_data.get('status'):
            if search_form.cleaned_data['status'] == 'approved':
                payroll_records = payroll_records.filter(is_approved=True)
            elif search_form.cleaned_data['status'] == 'pending':
                payroll_records = payroll_records.filter(is_approved=False)
    
    # Pagination
    paginator = Paginator(payroll_records, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'payroll_period': payroll_period,
        'search_form': search_form,
    }
    return render(request, 'payroll/payroll_record_list.html', context)


@login_required
@permission_required('payroll.can_process_payroll')
def payroll_record_edit(request, record_id):
    """Edit payroll record"""
    payroll_record = get_object_or_404(PayrollRecord, id=record_id)
    
    if request.method == 'POST':
        form = PayrollRecordForm(request.POST, instance=payroll_record)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payroll record updated successfully!')
            return redirect('payroll:payroll_record_list', period_id=payroll_record.payroll_period.id)
    else:
        form = PayrollRecordForm(instance=payroll_record)
    
    context = {
        'form': form,
        'payroll_record': payroll_record,
    }
    return render(request, 'payroll/payroll_record_form.html', context)


@login_required
@permission_required('payroll.can_approve_payroll')
def payroll_approve(request, record_id):
    """Approve payroll record"""
    payroll_record = get_object_or_404(PayrollRecord, id=record_id)
    
    if request.method == 'POST':
        payroll_record.is_approved = True
        payroll_record.approved_by = request.user
        payroll_record.approved_at = timezone.now()
        payroll_record.save()
        
        messages.success(request, 'Payroll record approved successfully!')
        return redirect('payroll:payroll_record_list', period_id=payroll_record.payroll_period.id)
    
    context = {
        'payroll_record': payroll_record,
    }
    return render(request, 'payroll/payroll_approve.html', context)


@login_required
@permission_required('payroll.can_generate_payslips')
def payslip_generate(request, record_id):
    """Generate payslip for payroll record"""
    payroll_record = get_object_or_404(PayrollRecord, id=record_id)
    
    # Check if payslip already exists
    if hasattr(payroll_record, 'payslip'):
        messages.warning(request, 'Payslip already exists for this record.')
        return redirect('payroll:payslip_detail', payslip_id=payroll_record.payslip.id)
    
    if request.method == 'POST':
        # Create payslip
        payslip = Payslip.objects.create(
            payroll_record=payroll_record,
            generated_by=request.user
        )
        
        # Generate PDF (placeholder for now)
        # In a real implementation, you would use a library like ReportLab or WeasyPrint
        
        messages.success(request, 'Payslip generated successfully!')
        return redirect('payroll:payslip_detail', payslip_id=payslip.id)
    
    context = {
        'payroll_record': payroll_record,
    }
    return render(request, 'payroll/payslip_generate.html', context)


@login_required
def payslip_detail(request, payslip_id):
    """View payslip details"""
    payslip = get_object_or_404(Payslip, id=payslip_id)
    
    # Check if user has permission to view this payslip
    if not (request.user == payslip.payroll_record.employee or 
            request.user.has_perm('payroll.can_view_all_payslips')):
        messages.error(request, 'You do not have permission to view this payslip.')
        return redirect('payroll:payroll_dashboard')
    
    context = {
        'payslip': payslip,
    }
    return render(request, 'payroll/payslip_detail.html', context)


@login_required
@permission_required('payroll.can_manage_wps')
def wps_list(request):
    """List WPS records"""
    wps_records = WPSRecord.objects.select_related('employee', 'payroll_period').order_by('-payroll_period', 'employee__first_name')
    
    # Pagination
    paginator = Paginator(wps_records, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'payroll/wps_list.html', context)


@login_required
@permission_required('payroll.can_manage_wps')
def wps_export(request):
    """Export WPS SIF file"""
    if request.method == 'POST':
        form = WPSExportForm(request.POST)
        if form.is_valid():
            payroll_period = form.cleaned_data['payroll_period']
            company_wps_code = form.cleaned_data['company_wps_code']
            bank_code = form.cleaned_data['bank_code']
            include_all_employees = form.cleaned_data['include_all_employees']
            
            # Get payroll records for the period
            payroll_records = PayrollRecord.objects.filter(
                payroll_period=payroll_period,
                is_approved=True
            ).select_related('employee')
            
            if not include_all_employees:
                # Only include employees with bank accounts
                payroll_records = payroll_records.filter(employee__bank_account__isnull=False)
            
            # Generate SIF file content (simplified format)
            sif_content = []
            for record in payroll_records:
                try:
                    bank_account = record.employee.bank_account
                    sif_line = {
                        'company_code': company_wps_code,
                        'employee_code': f"EMP{record.employee.id:04d}",
                        'bank_code': bank_code,
                        'account_number': bank_account.account_number,
                        'iban': bank_account.iban,
                        'salary_amount': record.net_salary,
                    }
                    sif_content.append(sif_line)
                except BankAccount.DoesNotExist:
                    continue
            
            # Create CSV response
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="wps_{payroll_period.year}_{payroll_period.month:02d}.csv"'
            
            writer = csv.writer(response)
            writer.writerow(['Company Code', 'Employee Code', 'Bank Code', 'Account Number', 'IBAN', 'Salary Amount'])
            
            for line in sif_content:
                writer.writerow([
                    line['company_code'],
                    line['employee_code'],
                    line['bank_code'],
                    line['account_number'],
                    line['iban'],
                    line['salary_amount']
                ])
            
            return response
    else:
        form = WPSExportForm()
    
    context = {
        'form': form,
    }
    return render(request, 'payroll/wps_export.html', context)


@login_required
@permission_required('payroll.can_manage_eosb')
def eosb_list(request):
    """List EOSB records"""
    eosb_records = EndOfServiceBenefit.objects.select_related('employee').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(eosb_records, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'payroll/eosb_list.html', context)


@login_required
@permission_required('payroll.can_manage_eosb')
def eosb_calculate(request):
    """Calculate EOSB"""
    if request.method == 'POST':
        form = EOSBCalculationForm(request.POST)
        if form.is_valid():
            employee = form.cleaned_data['employee']
            termination_date = form.cleaned_data['termination_date']
            contract_type = form.cleaned_data['contract_type']
            basic_salary_for_gratuity = form.cleaned_data['basic_salary_for_gratuity']
            leave_encashment_days = form.cleaned_data['leave_encashment_days']
            other_benefits = form.cleaned_data['other_benefits']
            
            # Calculate years of service (simplified)
            # In a real implementation, you would get the actual joining date
            joining_date = date(2020, 1, 1)  # Placeholder
            
            years_of_service = (termination_date - joining_date).days / 365.25
            months_of_service = int(years_of_service * 12)
            days_of_service = (termination_date - joining_date).days
            
            # Calculate gratuity
            if years_of_service <= 5:
                gratuity_days_per_year = 21
            else:
                gratuity_days_per_year = 30
            
            total_gratuity_days = years_of_service * gratuity_days_per_year
            gratuity_amount = (basic_salary_for_gratuity / 30) * total_gratuity_days
            
            # Calculate leave encashment
            leave_encashment_amount = (basic_salary_for_gratuity / 30) * leave_encashment_days
            
            # Calculate total settlement
            total_settlement = gratuity_amount + leave_encashment_amount + other_benefits
            
            # Create EOSB record
            eosb = EndOfServiceBenefit.objects.create(
                employee=employee,
                contract_type=contract_type,
                joining_date=joining_date,
                termination_date=termination_date,
                years_of_service=years_of_service,
                months_of_service=months_of_service,
                days_of_service=days_of_service,
                basic_salary_for_gratuity=basic_salary_for_gratuity,
                gratuity_days_per_year=gratuity_days_per_year,
                total_gratuity_days=total_gratuity_days,
                gratuity_amount=gratuity_amount,
                leave_encashment_days=leave_encashment_days,
                leave_encashment_amount=leave_encashment_amount,
                other_benefits=other_benefits,
                total_settlement=total_settlement,
                processed_by=request.user,
                processed_at=timezone.now(),
                is_processed=True
            )
            
            messages.success(request, 'EOSB calculated successfully!')
            return redirect('payroll:eosb_detail', eosb_id=eosb.id)
    else:
        form = EOSBCalculationForm()
    
    context = {
        'form': form,
    }
    return render(request, 'payroll/eosb_calculate.html', context)


@login_required
@permission_required('payroll.can_manage_eosb')
def eosb_detail(request, eosb_id):
    """View EOSB details"""
    eosb = get_object_or_404(EndOfServiceBenefit, id=eosb_id)
    
    context = {
        'eosb': eosb,
    }
    return render(request, 'payroll/eosb_detail.html', context)


@login_required
@permission_required('payroll.can_manage_loans')
def loan_list(request):
    """List loans"""
    loans = Loan.objects.select_related('employee').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(loans, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'payroll/loan_list.html', context)


@login_required
@permission_required('payroll.can_manage_loans')
def loan_create(request):
    """Create loan"""
    if request.method == 'POST':
        form = LoanForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Loan created successfully!')
            return redirect('payroll:loan_list')
    else:
        form = LoanForm()
    
    context = {
        'form': form,
        'title': 'Create Loan'
    }
    return render(request, 'payroll/loan_form.html', context)


@login_required
@permission_required('payroll.can_manage_loans')
def loan_edit(request, loan_id):
    """Edit loan"""
    loan = get_object_or_404(Loan, id=loan_id)
    
    if request.method == 'POST':
        form = LoanForm(request.POST, instance=loan)
        if form.is_valid():
            form.save()
            messages.success(request, 'Loan updated successfully!')
            return redirect('payroll:loan_list')
    else:
        form = LoanForm(instance=loan)
    
    context = {
        'form': form,
        'loan': loan,
        'title': 'Edit Loan'
    }
    return render(request, 'payroll/loan_form.html', context)


@login_required
@permission_required('payroll.can_manage_advances')
def advance_list(request):
    """List advances"""
    advances = Advance.objects.select_related('employee', 'approved_by').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(advances, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'payroll/advance_list.html', context)


@login_required
@permission_required('payroll.can_manage_advances')
def advance_create(request):
    """Create advance"""
    if request.method == 'POST':
        form = AdvanceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Advance created successfully!')
            return redirect('payroll:advance_list')
    else:
        form = AdvanceForm()
    
    context = {
        'form': form,
        'title': 'Create Advance'
    }
    return render(request, 'payroll/advance_form.html', context)


@login_required
@permission_required('payroll.can_manage_advances')
def advance_edit(request, advance_id):
    """Edit advance"""
    advance = get_object_or_404(Advance, id=advance_id)
    
    if request.method == 'POST':
        form = AdvanceForm(request.POST, instance=advance)
        if form.is_valid():
            form.save()
            messages.success(request, 'Advance updated successfully!')
            return redirect('payroll:advance_list')
    else:
        form = AdvanceForm(instance=advance)
    
    context = {
        'form': form,
        'advance': advance,
        'title': 'Edit Advance'
    }
    return render(request, 'payroll/advance_form.html', context)


@login_required
@permission_required('payroll.can_approve_advances')
def advance_approve(request, advance_id):
    """Approve/reject advance"""
    advance = get_object_or_404(Advance, id=advance_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action in ['approve', 'reject']:
            advance.status = action
            advance.approved_by = request.user
            advance.approved_date = date.today()
            advance.save()
            
            messages.success(request, f'Advance {action}d successfully!')
            return redirect('payroll:advance_list')
    
    context = {
        'advance': advance,
    }
    return render(request, 'payroll/advance_approve.html', context)


@login_required
@permission_required('payroll.can_view_reports')
def payroll_reports(request):
    """Payroll reports"""
    # Get report parameters
    report_type = request.GET.get('type', 'summary')
    year = request.GET.get('year', date.today().year)
    month = request.GET.get('month', '')
    
    if report_type == 'summary':
        # Payroll summary report
        if month:
            payroll_records = PayrollRecord.objects.filter(
                payroll_period__year=year,
                payroll_period__month=month
            )
        else:
            payroll_records = PayrollRecord.objects.filter(payroll_period__year=year)
        
        summary_data = payroll_records.aggregate(
            total_employees=Count('employee', distinct=True),
            total_gross=Sum('gross_salary'),
            total_net=Sum('net_salary'),
            total_deductions=Sum('total_deductions'),
            avg_salary=Avg('net_salary')
        )
        
        context = {
            'report_type': report_type,
            'year': year,
            'month': month,
            'summary_data': summary_data,
            'payroll_records': payroll_records,
        }
        
    elif report_type == 'employee_cost':
        # Employee cost report
        employee_costs = PayrollRecord.objects.filter(
            payroll_period__year=year
        ).values('employee__first_name', 'employee__last_name').annotate(
            total_cost=Sum('gross_salary'),
            total_net=Sum('net_salary'),
            avg_cost=Avg('gross_salary')
        ).order_by('-total_cost')
        
        context = {
            'report_type': report_type,
            'year': year,
            'employee_costs': employee_costs,
        }
    
    else:
        context = {
            'report_type': report_type,
            'year': year,
            'month': month,
        }
    
    return render(request, 'payroll/reports.html', context)
