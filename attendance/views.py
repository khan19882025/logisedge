from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers import serialize
from datetime import date, datetime, timedelta
import json
import csv
from io import StringIO

from .models import (
    Attendance, Break, Shift, Holiday, AttendancePolicy, 
    TimeSheet, AttendanceReport, AttendanceAlert, PunchLog
)
from .forms import (
    AttendanceEntryForm, BulkAttendanceForm, BreakForm, ShiftForm,
    HolidayForm, AttendancePolicyForm, TimeSheetForm, AttendanceReportForm,
    AttendanceSearchForm, PunchInOutForm, AttendanceAlertForm
)
from employees.models import Employee, Department


# Dashboard and Overview Views
@login_required
def attendance_dashboard(request):
    """Attendance & Time Tracking Dashboard"""
    today = date.today()
    
    # Get counts
    total_employees = Employee.objects.filter(status='active').count()
    present_today = Attendance.objects.filter(date=today, status='present').count()
    absent_today = Attendance.objects.filter(date=today, status='absent').count()
    late_today = Attendance.objects.filter(date=today, is_late=True).count()
    
    # Recent activities
    recent_attendance = Attendance.objects.select_related('employee').order_by('-created_at')[:10]
    recent_alerts = AttendanceAlert.objects.select_related('employee').filter(is_resolved=False).order_by('-created_at')[:5]
    
    # Department-wise attendance
    dept_attendance = Department.objects.filter(is_active=True).annotate(
        present_count=Count('employees__attendance_records', filter=Q(
            employees__attendance_records__date=today,
            employees__attendance_records__status='present'
        )),
        total_count=Count('employees', filter=Q(employees__status='active'))
    ).order_by('-present_count')[:5]
    
    # Today's attendance summary
    today_attendance = Attendance.objects.filter(date=today).select_related('employee', 'shift')
    present_employees = today_attendance.filter(status='present')
    absent_employees = today_attendance.filter(status='absent')
    
    # Overtime summary
    overtime_today = today_attendance.filter(overtime_hours__gt=0).aggregate(
        total_overtime=Sum('overtime_hours')
    )['total_overtime'] or 0
    
    context = {
        'total_employees': total_employees,
        'present_today': present_today,
        'absent_today': absent_today,
        'late_today': late_today,
        'recent_attendance': recent_attendance,
        'recent_alerts': recent_alerts,
        'dept_attendance': dept_attendance,
        'present_employees': present_employees,
        'absent_employees': absent_employees,
        'overtime_today': overtime_today,
        'today': today,
    }
    
    return render(request, 'attendance/dashboard.html', context)


# Attendance Management Views
@login_required
def attendance_list(request):
    """List all attendance records with search and filter"""
    form = AttendanceSearchForm(request.GET)
    attendance_records = Attendance.objects.select_related(
        'employee', 'shift', 'created_by'
    ).order_by('-date', '-created_at')
    
    if form.is_valid():
        employee = form.cleaned_data.get('employee')
        department = form.cleaned_data.get('department')
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')
        status = form.cleaned_data.get('status')
        shift = form.cleaned_data.get('shift')
        is_late = form.cleaned_data.get('is_late')
        has_overtime = form.cleaned_data.get('has_overtime')
        
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
        
        if shift:
            attendance_records = attendance_records.filter(shift=shift)
        
        if is_late:
            attendance_records = attendance_records.filter(is_late=True)
        
        if has_overtime:
            attendance_records = attendance_records.filter(overtime_hours__gt=0)
    
    # Pagination
    paginator = Paginator(attendance_records, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_records = attendance_records.count()
    present_count = attendance_records.filter(status='present').count()
    absent_count = attendance_records.filter(status='absent').count()
    late_count = attendance_records.filter(is_late=True).count()
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'total_records': total_records,
        'present_count': present_count,
        'absent_count': absent_count,
        'late_count': late_count,
    }
    
    return render(request, 'attendance/attendance_list.html', context)


@login_required
def attendance_create(request):
    """Create new attendance record"""
    if request.method == 'POST':
        form = AttendanceEntryForm(request.POST)
        if form.is_valid():
            attendance = form.save(commit=False)
            attendance.created_by = request.user
            attendance.save()
            
            messages.success(request, f'Attendance record created for {attendance.employee.get_full_name()}')
            return redirect('attendance:attendance_list')
    else:
        form = AttendanceEntryForm()
    
    context = {
        'form': form,
        'title': 'Add Attendance Record',
    }
    
    return render(request, 'attendance/attendance_form.html', context)


@login_required
def attendance_edit(request, pk):
    """Edit attendance record"""
    attendance = get_object_or_404(Attendance, pk=pk)
    
    if request.method == 'POST':
        form = AttendanceEntryForm(request.POST, instance=attendance)
        if form.is_valid():
            attendance = form.save(commit=False)
            attendance.modified_by = request.user
            attendance.save()
            
            messages.success(request, f'Attendance record updated for {attendance.employee.get_full_name()}')
            return redirect('attendance:attendance_list')
    else:
        form = AttendanceEntryForm(instance=attendance)
    
    context = {
        'form': form,
        'attendance': attendance,
        'title': 'Edit Attendance Record',
    }
    
    return render(request, 'attendance/attendance_form.html', context)


@login_required
def attendance_detail(request, pk):
    """View attendance record details"""
    attendance = get_object_or_404(Attendance, pk=pk)
    breaks = attendance.breaks.all().order_by('start_time')
    punch_logs = attendance.punch_logs.all().order_by('-punch_time')
    
    context = {
        'attendance': attendance,
        'breaks': breaks,
        'punch_logs': punch_logs,
    }
    
    return render(request, 'attendance/attendance_detail.html', context)


@login_required
@require_POST
def attendance_delete(request, pk):
    """Delete attendance record"""
    attendance = get_object_or_404(Attendance, pk=pk)
    employee_name = attendance.employee.get_full_name()
    attendance.delete()
    
    messages.success(request, f'Attendance record deleted for {employee_name}')
    return redirect('attendance:attendance_list')


@login_required
def bulk_attendance(request):
    """Bulk attendance entry"""
    if request.method == 'POST':
        form = BulkAttendanceForm(request.POST)
        if form.is_valid():
            date = form.cleaned_data['date']
            department = form.cleaned_data['department']
            status = form.cleaned_data['status']
            employees = form.cleaned_data['employees']
            notes = form.cleaned_data['notes']
            
            created_count = 0
            for employee in employees:
                # Check if attendance already exists
                if not Attendance.objects.filter(employee=employee, date=date).exists():
                    Attendance.objects.create(
                        employee=employee,
                        date=date,
                        status=status,
                        notes=notes,
                        created_by=request.user
                    )
                    created_count += 1
            
            messages.success(request, f'{created_count} attendance records created')
            return redirect('attendance:attendance_list')
    else:
        form = BulkAttendanceForm()
    
    context = {
        'form': form,
        'title': 'Bulk Attendance Entry',
    }
    
    return render(request, 'attendance/bulk_attendance.html', context)


# Time Tracking Views
@login_required
def time_tracking(request):
    """Time tracking interface"""
    today = date.today()
    employees = Employee.objects.filter(status='active').select_related('department')
    
    # Get today's attendance for all employees
    attendance_data = {}
    for employee in employees:
        try:
            attendance = Attendance.objects.get(employee=employee, date=today)
            attendance_data[employee.id] = attendance
        except Attendance.DoesNotExist:
            attendance_data[employee.id] = None
    
    context = {
        'employees': employees,
        'attendance_data': attendance_data,
        'today': today,
    }
    
    return render(request, 'attendance/time_tracking.html', context)


@login_required
def employee_punch(request):
    """Employee punch-in/out interface"""
    if request.method == 'POST':
        form = PunchInOutForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            location = form.cleaned_data['location']
            latitude = form.cleaned_data['latitude']
            longitude = form.cleaned_data['longitude']
            notes = form.cleaned_data['notes']
            
            # Get current user's employee record
            try:
                employee = Employee.objects.get(user=request.user)
            except Employee.DoesNotExist:
                return JsonResponse({'error': 'Employee record not found'}, status=400)
            
            today = date.today()
            now = timezone.now()
            
            # Get or create attendance record
            attendance, created = Attendance.objects.get_or_create(
                employee=employee,
                date=today,
                defaults={
                    'status': 'present',
                    'created_by': request.user
                }
            )
            
            # Update attendance based on action
            if action == 'check_in':
                attendance.check_in_time = now
                attendance.check_in_location = location
                if latitude and longitude:
                    attendance.check_in_latitude = latitude
                    attendance.check_in_longitude = longitude
                attendance.check_in_type = 'web'
                attendance.status = 'present'
                message = 'Check-in successful'
            else:  # check_out
                attendance.check_out_time = now
                attendance.check_out_location = location
                if latitude and longitude:
                    attendance.check_out_latitude = latitude
                    attendance.check_out_longitude = longitude
                attendance.check_out_type = 'web'
                message = 'Check-out successful'
            
            attendance.save()
            
            # Create punch log
            PunchLog.objects.create(
                employee=employee,
                attendance=attendance,
                punch_action=action,
                punch_method='web',
                punch_time=now,
                location=location,
                latitude=latitude,
                longitude=longitude,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                notes=notes,
                created_by=request.user
            )
            
            return JsonResponse({
                'success': True,
                'message': message,
                'check_in_time': attendance.check_in_time.isoformat() if attendance.check_in_time else None,
                'check_out_time': attendance.check_out_time.isoformat() if attendance.check_out_time else None,
            })
    
    # Get current employee's attendance status
    try:
        employee = Employee.objects.get(user=request.user)
        today = date.today()
        try:
            attendance = Attendance.objects.get(employee=employee, date=today)
        except Attendance.DoesNotExist:
            attendance = None
    except Employee.DoesNotExist:
        employee = None
        attendance = None
    
    context = {
        'employee': employee,
        'attendance': attendance,
        'today': date.today(),
    }
    
    return render(request, 'attendance/employee_punch.html', context)


# Break Management Views
@login_required
def break_list(request):
    """List all breaks"""
    breaks = Break.objects.select_related('attendance__employee').order_by('-start_time')
    
    # Pagination
    paginator = Paginator(breaks, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    
    return render(request, 'attendance/break_list.html', context)


@login_required
def break_create(request):
    """Create new break record"""
    if request.method == 'POST':
        form = BreakForm(request.POST)
        if form.is_valid():
            break_record = form.save()
            messages.success(request, 'Break record created successfully')
            return redirect('attendance:break_list')
    else:
        form = BreakForm()
    
    context = {
        'form': form,
        'title': 'Add Break Record',
    }
    
    return render(request, 'attendance/break_form.html', context)


@login_required
def break_edit(request, pk):
    """Edit break record"""
    break_record = get_object_or_404(Break, pk=pk)
    
    if request.method == 'POST':
        form = BreakForm(request.POST, instance=break_record)
        if form.is_valid():
            form.save()
            messages.success(request, 'Break record updated successfully')
            return redirect('attendance:break_list')
    else:
        form = BreakForm(instance=break_record)
    
    context = {
        'form': form,
        'break_record': break_record,
        'title': 'Edit Break Record',
    }
    
    return render(request, 'attendance/break_form.html', context)


# Shift Management Views
@login_required
def shift_list(request):
    """List all shifts"""
    shifts = Shift.objects.all().order_by('start_time')
    
    context = {
        'shifts': shifts,
    }
    
    return render(request, 'attendance/shift_list.html', context)


@login_required
def shift_create(request):
    """Create new shift"""
    if request.method == 'POST':
        form = ShiftForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Shift created successfully')
            return redirect('attendance:shift_list')
    else:
        form = ShiftForm()
    
    context = {
        'form': form,
        'title': 'Add Shift',
    }
    
    return render(request, 'attendance/shift_form.html', context)


@login_required
def shift_edit(request, pk):
    """Edit shift"""
    shift = get_object_or_404(Shift, pk=pk)
    
    if request.method == 'POST':
        form = ShiftForm(request.POST, instance=shift)
        if form.is_valid():
            form.save()
            messages.success(request, 'Shift updated successfully')
            return redirect('attendance:shift_list')
    else:
        form = ShiftForm(instance=shift)
    
    context = {
        'form': form,
        'shift': shift,
        'title': 'Edit Shift',
    }
    
    return render(request, 'attendance/shift_form.html', context)


# Holiday Management Views
@login_required
def holiday_list(request):
    """List all holidays"""
    holidays = Holiday.objects.all().order_by('date')
    
    context = {
        'holidays': holidays,
    }
    
    return render(request, 'attendance/holiday_list.html', context)


@login_required
def holiday_create(request):
    """Create new holiday"""
    if request.method == 'POST':
        form = HolidayForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Holiday created successfully')
            return redirect('attendance:holiday_list')
    else:
        form = HolidayForm()
    
    context = {
        'form': form,
        'title': 'Add Holiday',
    }
    
    return render(request, 'attendance/holiday_form.html', context)


@login_required
def holiday_edit(request, pk):
    """Edit holiday"""
    holiday = get_object_or_404(Holiday, pk=pk)
    
    if request.method == 'POST':
        form = HolidayForm(request.POST, instance=holiday)
        if form.is_valid():
            form.save()
            messages.success(request, 'Holiday updated successfully')
            return redirect('attendance:holiday_list')
    else:
        form = HolidayForm(instance=holiday)
    
    context = {
        'form': form,
        'holiday': holiday,
        'title': 'Edit Holiday',
    }
    
    return render(request, 'attendance/holiday_form.html', context)


# Reports Views
@login_required
def reports_dashboard(request):
    """Reports dashboard"""
    context = {
        'title': 'Attendance Reports',
    }
    
    return render(request, 'attendance/reports_dashboard.html', context)


@login_required
def generate_report(request):
    """Generate attendance report"""
    if request.method == 'POST':
        form = AttendanceReportForm(request.POST)
        if form.is_valid():
            # Generate report logic here
            messages.success(request, 'Report generated successfully')
            return redirect('attendance:reports_dashboard')
    else:
        form = AttendanceReportForm()
    
    context = {
        'form': form,
        'title': 'Generate Report',
    }
    
    return render(request, 'attendance/generate_report.html', context)


@login_required
def export_attendance(request):
    """Export attendance data to CSV/Excel"""
    # Get filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    department_id = request.GET.get('department')
    format_type = request.GET.get('format', 'csv')
    
    # Filter attendance records
    attendance_records = Attendance.objects.select_related('employee', 'shift')
    
    if start_date:
        attendance_records = attendance_records.filter(date__gte=start_date)
    if end_date:
        attendance_records = attendance_records.filter(date__lte=end_date)
    if department_id:
        attendance_records = attendance_records.filter(employee__department_id=department_id)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="attendance_export_{date.today()}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Employee ID', 'Employee Name', 'Department', 'Date', 'Check In', 'Check Out',
        'Total Hours', 'Overtime Hours', 'Status', 'Is Late', 'Notes'
    ])
    
    for record in attendance_records:
        writer.writerow([
            record.employee.employee_id,
            record.employee.get_full_name(),
            record.employee.department.name if record.employee.department else '',
            record.date,
            record.check_in_time.strftime('%H:%M:%S') if record.check_in_time else '',
            record.check_out_time.strftime('%H:%M:%S') if record.check_out_time else '',
            record.total_hours or 0,
            record.overtime_hours or 0,
            record.get_status_display(),
            'Yes' if record.is_late else 'No',
            record.notes or ''
        ])
    
    return response


# API Views
@login_required
@csrf_exempt
def api_attendance_status(request):
    """API to get attendance status for employees"""
    if request.method == 'GET':
        date_param = request.GET.get('date', date.today())
        department_id = request.GET.get('department')
        
        attendance_records = Attendance.objects.filter(date=date_param).select_related('employee')
        
        if department_id:
            attendance_records = attendance_records.filter(employee__department_id=department_id)
        
        data = []
        for record in attendance_records:
            data.append({
                'employee_id': record.employee.employee_id,
                'employee_name': record.employee.get_full_name(),
                'department': record.employee.department.name if record.employee.department else '',
                'check_in_time': record.check_in_time.isoformat() if record.check_in_time else None,
                'check_out_time': record.check_out_time.isoformat() if record.check_out_time else None,
                'total_hours': float(record.total_hours) if record.total_hours else 0,
                'status': record.status,
                'is_late': record.is_late,
            })
        
        return JsonResponse({'data': data})


@login_required
@csrf_exempt
def api_punch_in_out(request):
    """API for punch-in/out"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            employee_id = data.get('employee_id')
            action = data.get('action')  # 'check_in' or 'check_out'
            location = data.get('location', '')
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            
            employee = get_object_or_404(Employee, employee_id=employee_id)
            today = date.today()
            now = timezone.now()
            
            # Get or create attendance record
            attendance, created = Attendance.objects.get_or_create(
                employee=employee,
                date=today,
                defaults={
                    'status': 'present',
                    'created_by': request.user
                }
            )
            
            # Update attendance based on action
            if action == 'check_in':
                attendance.check_in_time = now
                attendance.check_in_location = location
                if latitude and longitude:
                    attendance.check_in_latitude = latitude
                    attendance.check_in_longitude = longitude
                attendance.check_in_type = 'api'
                attendance.status = 'present'
            else:  # check_out
                attendance.check_out_time = now
                attendance.check_out_location = location
                if latitude and longitude:
                    attendance.check_out_latitude = latitude
                    attendance.check_out_longitude = longitude
                attendance.check_out_type = 'api'
            
            attendance.save()
            
            # Create punch log
            PunchLog.objects.create(
                employee=employee,
                attendance=attendance,
                punch_action=action,
                punch_method='api',
                punch_time=now,
                location=location,
                latitude=latitude,
                longitude=longitude,
                ip_address=request.META.get('REMOTE_ADDR'),
                created_by=request.user
            )
            
            return JsonResponse({
                'success': True,
                'message': f'{action.replace("_", " ").title()} successful',
                'employee_name': employee.get_full_name(),
                'punch_time': now.isoformat(),
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


# Calendar Views
@login_required
def attendance_calendar(request):
    """Calendar view of attendance"""
    year = int(request.GET.get('year', date.today().year))
    month = int(request.GET.get('month', date.today().month))
    employee_id = request.GET.get('employee')
    
    if employee_id:
        employee = get_object_or_404(Employee, employee_id=employee_id)
        attendance_records = Attendance.objects.filter(
            employee=employee,
            date__year=year,
            date__month=month
        )
    else:
        employee = None
        attendance_records = Attendance.objects.filter(
            date__year=year,
            date__month=month
        )
    
    # Create calendar data
    calendar_data = {}
    for record in attendance_records:
        day = record.date.day
        if day not in calendar_data:
            calendar_data[day] = []
        calendar_data[day].append({
            'employee': record.employee.get_full_name(),
            'status': record.status,
            'check_in': record.check_in_time.strftime('%H:%M') if record.check_in_time else '',
            'check_out': record.check_out_time.strftime('%H:%M') if record.check_out_time else '',
            'total_hours': float(record.total_hours) if record.total_hours else 0,
        })
    
    context = {
        'year': year,
        'month': month,
        'employee': employee,
        'calendar_data': calendar_data,
        'employees': Employee.objects.filter(status='active'),
    }
    
    return render(request, 'attendance/attendance_calendar.html', context)
