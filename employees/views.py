from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from datetime import date, datetime, timedelta
import json

from .models import (
    Employee, Department, Designation, EmployeeDocument, Attendance, 
    LeaveType, Leave, LeaveBalance, SalaryStructure, Payslip, 
    EmployeeTransfer, ExitForm
)
from .forms import (
    EmployeeForm, DepartmentForm, DesignationForm, EmployeeDocumentForm,
    AttendanceForm, LeaveTypeForm, LeaveForm, LeaveBalanceForm,
    SalaryStructureForm, EmployeeSearchForm, AttendanceSearchForm,
    LeaveSearchForm, EmployeeTransferForm, ExitFormForm
)


# Dashboard and Overview Views
@login_required
def employee_dashboard(request):
    """Employee Management Dashboard"""
    # Get counts
    total_employees = Employee.objects.count()
    active_employees = Employee.objects.filter(status='active').count()
    departments = Department.objects.filter(is_active=True).count()
    
    # Recent activities
    recent_employees = Employee.objects.order_by('-created_at')[:5]
    recent_attendance = Attendance.objects.select_related('employee').order_by('-date')[:10]
    pending_leaves = Leave.objects.filter(status='pending').count()
    
    # Department-wise employee count
    dept_stats = Department.objects.filter(is_active=True).annotate(
        employee_count=Count('employees')
    ).order_by('-employee_count')[:5]
    
    # Today's attendance
    today = date.today()
    today_attendance = Attendance.objects.filter(date=today).select_related('employee')
    present_today = today_attendance.filter(status='present').count()
    absent_today = today_attendance.filter(status='absent').count()
    
    context = {
        'total_employees': total_employees,
        'active_employees': active_employees,
        'departments': departments,
        'recent_employees': recent_employees,
        'recent_attendance': recent_attendance,
        'pending_leaves': pending_leaves,
        'dept_stats': dept_stats,
        'present_today': present_today,
        'absent_today': absent_today,
        'today': today,
    }
    
    return render(request, 'employees/dashboard.html', context)


# Employee Management Views
@login_required
def employee_list(request):
    """List all employees with search and filter"""
    form = EmployeeSearchForm(request.GET)
    employees = Employee.objects.select_related('department', 'designation', 'reporting_manager')
    
    if form.is_valid():
        search = form.cleaned_data.get('search')
        department = form.cleaned_data.get('department')
        designation = form.cleaned_data.get('designation')
        status = form.cleaned_data.get('status')
        employment_type = form.cleaned_data.get('employment_type')
        
        if search:
            employees = employees.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(employee_id__icontains=search) |
                Q(email__icontains=search)
            )
        
        if department:
            employees = employees.filter(department=department)
        
        if designation:
            employees = employees.filter(designation=designation)
        
        if status:
            employees = employees.filter(status=status)
        
        if employment_type:
            employees = employees.filter(employment_type=employment_type)
    
    # Pagination
    paginator = Paginator(employees, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'total_employees': employees.count(),
    }
    
    return render(request, 'employees/employee_list.html', context)


@login_required
def employee_create(request):
    """Create a new employee"""
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            employee = form.save(commit=False)
            employee.created_by = request.user
            employee.save()
            messages.success(request, f'Employee {employee.full_name} created successfully!')
            return redirect('employees:employee_detail', pk=employee.pk)
    else:
        form = EmployeeForm()
    
    context = {
        'form': form,
        'title': 'Add New Employee',
        'submit_text': 'Create Employee',
    }
    
    return render(request, 'employees/employee_form.html', context)


@login_required
def employee_edit(request, pk):
    """Edit an existing employee"""
    employee = get_object_or_404(Employee, pk=pk)
    
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            employee = form.save(commit=False)
            employee.updated_by = request.user
            employee.save()
            messages.success(request, f'Employee {employee.full_name} updated successfully!')
            return redirect('employees:employee_detail', pk=employee.pk)
    else:
        form = EmployeeForm(instance=employee)
    
    context = {
        'form': form,
        'employee': employee,
        'title': f'Edit Employee - {employee.full_name}',
        'submit_text': 'Update Employee',
    }
    
    return render(request, 'employees/employee_form.html', context)


@login_required
def employee_detail(request, pk):
    """View employee details"""
    employee = get_object_or_404(Employee.objects.select_related(
        'department', 'designation', 'reporting_manager', 'created_by', 'updated_by'
    ), pk=pk)
    
    # Get related data
    documents = employee.documents.all()
    attendance_records = employee.attendances.order_by('-date')[:30]
    leave_records = employee.leaves.order_by('-applied_at')[:10]
    leave_balances = employee.leave_balances.all()
    
    # Calculate attendance stats for current month
    current_month = timezone.now().month
    current_year = timezone.now().year
    month_attendance = employee.attendances.filter(
        date__month=current_month,
        date__year=current_year
    )
    present_days = month_attendance.filter(status='present').count()
    absent_days = month_attendance.filter(status='absent').count()
    leave_days = month_attendance.filter(status='leave').count()
    
    context = {
        'employee': employee,
        'documents': documents,
        'attendance_records': attendance_records,
        'leave_records': leave_records,
        'leave_balances': leave_balances,
        'present_days': present_days,
        'absent_days': absent_days,
        'leave_days': leave_days,
        'current_month': current_month,
        'current_year': current_year,
    }
    
    return render(request, 'employees/employee_detail.html', context)


@login_required
@require_POST
def employee_delete(request, pk):
    """Delete an employee"""
    employee = get_object_or_404(Employee, pk=pk)
    employee_name = employee.full_name
    employee.delete()
    messages.success(request, f'Employee {employee_name} deleted successfully!')
    return redirect('employees:employee_list')


# Department Management Views
@login_required
def department_list(request):
    """List all departments"""
    departments = Department.objects.annotate(
        employee_count=Count('employees')
    ).order_by('name')
    
    context = {
        'departments': departments,
    }
    
    return render(request, 'employees/department_list.html', context)


@login_required
def department_create(request):
    """Create a new department"""
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            department = form.save()
            messages.success(request, f'Department {department.name} created successfully!')
            return redirect('employees:department_list')
    else:
        form = DepartmentForm()
    
    context = {
        'form': form,
        'title': 'Add New Department',
        'submit_text': 'Create Department',
    }
    
    return render(request, 'employees/department_form.html', context)


@login_required
def department_edit(request, pk):
    """Edit a department"""
    department = get_object_or_404(Department, pk=pk)
    
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            department = form.save()
            messages.success(request, f'Department {department.name} updated successfully!')
            return redirect('employees:department_list')
    else:
        form = DepartmentForm(instance=department)
    
    context = {
        'form': form,
        'department': department,
        'title': f'Edit Department - {department.name}',
        'submit_text': 'Update Department',
    }
    
    return render(request, 'employees/department_form.html', context)


# Designation Management Views
@login_required
def designation_list(request):
    """List all designations"""
    designations = Designation.objects.select_related('department').annotate(
        employee_count=Count('employees')
    ).order_by('department__name', 'title')
    
    context = {
        'designations': designations,
    }
    
    return render(request, 'employees/designation_list.html', context)


@login_required
def designation_create(request):
    """Create a new designation"""
    if request.method == 'POST':
        form = DesignationForm(request.POST)
        if form.is_valid():
            designation = form.save()
            messages.success(request, f'Designation {designation.title} created successfully!')
            return redirect('employees:designation_list')
    else:
        form = DesignationForm()
    
    context = {
        'form': form,
        'title': 'Add New Designation',
        'submit_text': 'Create Designation',
    }
    
    return render(request, 'employees/designation_form.html', context)


@login_required
def designation_edit(request, pk):
    """Edit a designation"""
    designation = get_object_or_404(Designation, pk=pk)
    
    if request.method == 'POST':
        form = DesignationForm(request.POST, instance=designation)
        if form.is_valid():
            designation = form.save()
            messages.success(request, f'Designation {designation.title} updated successfully!')
            return redirect('employees:designation_list')
    else:
        form = DesignationForm(instance=designation)
    
    context = {
        'form': form,
        'designation': designation,
        'title': f'Edit Designation - {designation.title}',
        'submit_text': 'Update Designation',
    }
    
    return render(request, 'employees/designation_form.html', context)


# Attendance Management Views
@login_required
def attendance_list(request):
    """List attendance records with search and filter"""
    form = AttendanceSearchForm(request.GET)
    attendance_records = Attendance.objects.select_related('employee', 'employee__department')
    
    if form.is_valid():
        employee = form.cleaned_data.get('employee')
        department = form.cleaned_data.get('department')
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')
        status = form.cleaned_data.get('status')
        
        if employee:
            attendance_records = attendance_records.filter(employee=employee)
        
        if department:
            attendance_records = attendance_records.filter(employee__department=department)
        
        if start_date:
            attendance_records = attendance_records.filter(date__gte=start_date)
        
        if end_date:
            attendance_records = attendance_records.filter(date__lte=end_date)
        
        if status:
            attendance_records = attendance_records.filter(status=status)
    
    # Pagination
    paginator = Paginator(attendance_records, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'form': form,
    }
    
    return render(request, 'employees/attendance_list.html', context)


@login_required
def attendance_create(request):
    """Create attendance record"""
    if request.method == 'POST':
        form = AttendanceForm(request.POST)
        if form.is_valid():
            attendance = form.save()
            messages.success(request, f'Attendance record for {attendance.employee.full_name} created successfully!')
            return redirect('employees:attendance_list')
    else:
        form = AttendanceForm()
    
    context = {
        'form': form,
        'title': 'Add Attendance Record',
        'submit_text': 'Create Record',
    }
    
    return render(request, 'employees/attendance_form.html', context)


@login_required
def attendance_edit(request, pk):
    """Edit attendance record"""
    attendance = get_object_or_404(Attendance, pk=pk)
    
    if request.method == 'POST':
        form = AttendanceForm(request.POST, instance=attendance)
        if form.is_valid():
            attendance = form.save()
            messages.success(request, f'Attendance record updated successfully!')
            return redirect('employees:attendance_list')
    else:
        form = AttendanceForm(instance=attendance)
    
    context = {
        'form': form,
        'attendance': attendance,
        'title': f'Edit Attendance - {attendance.employee.full_name}',
        'submit_text': 'Update Record',
    }
    
    return render(request, 'employees/attendance_form.html', context)


# Leave Management Views
@login_required
def leave_list(request):
    """List leave applications with search and filter"""
    form = LeaveSearchForm(request.GET)
    leaves = Leave.objects.select_related('employee', 'leave_type', 'approved_by')
    
    if form.is_valid():
        employee = form.cleaned_data.get('employee')
        leave_type = form.cleaned_data.get('leave_type')
        status = form.cleaned_data.get('status')
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')
        
        if employee:
            leaves = leaves.filter(employee=employee)
        
        if leave_type:
            leaves = leaves.filter(leave_type=leave_type)
        
        if status:
            leaves = leaves.filter(status=status)
        
        if start_date:
            leaves = leaves.filter(start_date__gte=start_date)
        
        if end_date:
            leaves = leaves.filter(end_date__lte=end_date)
    
    # Pagination
    paginator = Paginator(leaves, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'form': form,
    }
    
    return render(request, 'employees/leave_list.html', context)


@login_required
def leave_create(request):
    """Create leave application"""
    if request.method == 'POST':
        form = LeaveForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.employee = request.user.employee if hasattr(request.user, 'employee') else None
            leave.save()
            messages.success(request, 'Leave application submitted successfully!')
            return redirect('employees:leave_list')
    else:
        form = LeaveForm()
    
    context = {
        'form': form,
        'title': 'Submit Leave Application',
        'submit_text': 'Submit Application',
    }
    
    return render(request, 'employees/leave_form.html', context)


@login_required
def leave_approve(request, pk):
    """Approve or reject leave application"""
    leave = get_object_or_404(Leave, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            leave.status = 'approved'
            leave.approved_by = request.user
            leave.approved_at = timezone.now()
            messages.success(request, 'Leave application approved!')
        elif action == 'reject':
            leave.status = 'rejected'
            leave.approved_by = request.user
            leave.approved_at = timezone.now()
            leave.rejection_reason = request.POST.get('rejection_reason', '')
            messages.success(request, 'Leave application rejected!')
        
        leave.save()
        return redirect('employees:leave_list')
    
    context = {
        'leave': leave,
    }
    
    return render(request, 'employees/leave_approve.html', context)


# Reports Views
@login_required
def employee_reports(request):
    """Employee reports dashboard"""
    # Department-wise employee count
    dept_stats = Department.objects.filter(is_active=True).annotate(
        employee_count=Count('employees'),
        active_count=Count('employees', filter=Q(employees__status='active'))
    ).order_by('-employee_count')
    
    # Employment type distribution
    emp_type_stats = Employee.objects.values('employment_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Recent joiners (last 30 days)
    thirty_days_ago = date.today() - timedelta(days=30)
    recent_joiners = Employee.objects.filter(
        join_date__gte=thirty_days_ago
    ).order_by('-join_date')
    
    # Upcoming birthdays (next 30 days)
    today = date.today()
    upcoming_birthdays = []
    for i in range(30):
        check_date = today + timedelta(days=i)
        birthdays = Employee.objects.filter(
            date_of_birth__month=check_date.month,
            date_of_birth__day=check_date.day,
            status='active'
        )
        if birthdays.exists():
            upcoming_birthdays.append({
                'date': check_date,
                'employees': birthdays
            })
    
    context = {
        'dept_stats': dept_stats,
        'emp_type_stats': emp_type_stats,
        'recent_joiners': recent_joiners,
        'upcoming_birthdays': upcoming_birthdays[:10],  # Limit to 10
    }
    
    return render(request, 'employees/reports.html', context)


@login_required
def attendance_report(request):
    """Generate attendance report"""
    # Get date range from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date:
        start_date = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = date.today().strftime('%Y-%m-%d')
    
    # Get attendance data
    attendance_data = Attendance.objects.filter(
        date__range=[start_date, end_date]
    ).select_related('employee', 'employee__department')
    
    # Group by employee
    employee_stats = {}
    for record in attendance_data:
        emp_id = record.employee.id
        if emp_id not in employee_stats:
            employee_stats[emp_id] = {
                'employee': record.employee,
                'present': 0,
                'absent': 0,
                'half_day': 0,
                'leave': 0,
                'total_days': 0,
            }
        
        employee_stats[emp_id]['total_days'] += 1
        employee_stats[emp_id][record.status] += 1
    
    context = {
        'employee_stats': employee_stats.values(),
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'employees/attendance_report.html', context)


# AJAX Views for dynamic functionality
@login_required
@csrf_exempt
def get_designations(request):
    """Get designations for a department (AJAX)"""
    if request.method == 'POST':
        department_id = request.POST.get('department_id')
        if department_id:
            designations = Designation.objects.filter(
                department_id=department_id,
                is_active=True
            ).values('id', 'title')
            return JsonResponse({'designations': list(designations)})
    return JsonResponse({'designations': []})


@login_required
@csrf_exempt
def bulk_attendance(request):
    """Bulk attendance entry (AJAX)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            date_str = data.get('date')
            attendance_data = data.get('attendance', [])
            
            attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Delete existing attendance for this date
            Attendance.objects.filter(date=attendance_date).delete()
            
            # Create new attendance records
            for record in attendance_data:
                employee_id = record.get('employee_id')
                status = record.get('status')
                check_in = record.get('check_in')
                check_out = record.get('check_out')
                notes = record.get('notes', '')
                
                if employee_id and status:
                    attendance = Attendance(
                        employee_id=employee_id,
                        date=attendance_date,
                        status=status,
                        notes=notes
                    )
                    
                    if check_in:
                        attendance.check_in = datetime.fromisoformat(check_in.replace('Z', '+00:00'))
                    if check_out:
                        attendance.check_out = datetime.fromisoformat(check_out.replace('Z', '+00:00'))
                    
                    attendance.save()
            
            return JsonResponse({'success': True, 'message': 'Attendance saved successfully!'})
        
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
def export_employees(request):
    """Export employees to CSV"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="employees.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Employee ID', 'First Name', 'Last Name', 'Email', 'Mobile',
        'Department', 'Designation', 'Join Date', 'Status', 'Employment Type'
    ])
    
    employees = Employee.objects.select_related('department', 'designation')
    for employee in employees:
        writer.writerow([
            employee.employee_id,
            employee.first_name,
            employee.last_name,
            employee.email,
            employee.mobile,
            employee.department.name if employee.department else '',
            employee.designation.title if employee.designation else '',
            employee.join_date,
            employee.get_status_display(),
            employee.get_employment_type_display(),
        ])
    
    return response
