from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils import timezone
import uuid
import os


def employee_photo_path(instance, filename):
    """Generate file path for employee photos"""
    ext = filename.split('.')[-1]
    filename = f"{instance.employee_id}_{instance.id}.{ext}"
    return os.path.join('employees/photos', filename)


def employee_document_path(instance, filename):
    """Generate file path for employee documents"""
    ext = filename.split('.')[-1]
    filename = f"{instance.employee.employee_id}_{instance.document_type}_{instance.id}.{ext}"
    return os.path.join('employees/documents', filename)


class Department(models.Model):
    """Department model for organizing employees"""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Designation(models.Model):
    """Designation/Job Title model"""
    title = models.CharField(max_length=100, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='designations')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return f"{self.title} - {self.department.name}"


class Employee(models.Model):
    """Main Employee model"""
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('resigned', 'Resigned'),
        ('terminated', 'Terminated'),
    ]
    
    EMPLOYMENT_TYPE_CHOICES = [
        ('full_time', 'Full-time'),
        ('part_time', 'Part-time'),
        ('contract', 'Contract'),
        ('intern', 'Intern'),
    ]

    # Auto-generated Employee ID
    employee_id = models.CharField(max_length=10, unique=True, editable=False)
    
    # Personal Information
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    
    # Employment Information
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='employees')
    designation = models.ForeignKey(Designation, on_delete=models.CASCADE, related_name='employees')
    join_date = models.DateField()
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES, default='full_time')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    reporting_manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates')
    
    # Contact Information
    email = models.EmailField(unique=True)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    mobile = models.CharField(validators=[phone_regex], max_length=17)
    alternate_phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    
    # Address Information
    current_address = models.TextField()
    permanent_address = models.TextField()
    
    # Documents
    photo = models.ImageField(upload_to=employee_photo_path, blank=True, null=True)
    
    # System Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_employees')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_employees')

    class Meta:
        ordering = ['employee_id']

    def __str__(self):
        return f"{self.employee_id} - {self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if not self.employee_id:
            # Generate employee ID: EMP + 6 digit number
            last_employee = Employee.objects.order_by('-employee_id').first()
            if last_employee:
                last_number = int(last_employee.employee_id[3:])
                new_number = last_number + 1
            else:
                new_number = 1
            self.employee_id = f"EMP{new_number:06d}"
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))


class EmployeeDocument(models.Model):
    """Employee documents like Aadhaar, Passport, etc."""
    DOCUMENT_TYPE_CHOICES = [
        ('aadhaar', 'Aadhaar Card'),
        ('passport', 'Passport'),
        ('pan', 'PAN Card'),
        ('driving_license', 'Driving License'),
        ('educational', 'Educational Certificate'),
        ('experience', 'Experience Certificate'),
        ('offer_letter', 'Offer Letter'),
        ('appointment_letter', 'Appointment Letter'),
        ('other', 'Other'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    document_number = models.CharField(max_length=50, blank=True)
    document_file = models.FileField(upload_to=employee_document_path)
    description = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.employee.employee_id} - {self.get_document_type_display()}"


class Attendance(models.Model):
    """Daily attendance records"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('half_day', 'Half Day'),
        ('leave', 'On Leave'),
        ('holiday', 'Holiday'),
    ], default='absent')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['employee', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.employee.employee_id} - {self.date} - {self.status}"

    @property
    def working_hours(self):
        if self.check_in and self.check_out:
            duration = self.check_out - self.check_in
            return duration.total_seconds() / 3600  # Convert to hours
        return 0


class LeaveType(models.Model):
    """Types of leave available"""
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=10, unique=True)
    default_days = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Leave(models.Model):
    """Leave application and tracking"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leaves')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, related_name='leaves')
    start_date = models.DateField()
    end_date = models.DateField()
    days_requested = models.PositiveIntegerField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.employee.employee_id} - {self.leave_type.name} - {self.start_date} to {self.end_date}"


class LeaveBalance(models.Model):
    """Employee leave balance tracking"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_balances')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, related_name='balances')
    year = models.PositiveIntegerField()
    total_days = models.PositiveIntegerField(default=0)
    used_days = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['employee', 'leave_type', 'year']
        ordering = ['-year']

    def __str__(self):
        return f"{self.employee.employee_id} - {self.leave_type.name} - {self.year}"

    @property
    def remaining_days(self):
        return self.total_days - self.used_days


class SalaryStructure(models.Model):
    """Employee salary structure"""
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='salary_structure')
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    hra = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    da = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    conveyance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    medical_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    effective_from = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-effective_from']

    def __str__(self):
        return f"{self.employee.employee_id} - {self.effective_from}"

    @property
    def gross_salary(self):
        return (self.basic_salary + self.hra + self.da + self.conveyance + 
                self.medical_allowance + self.other_allowances)


class Payslip(models.Model):
    """Monthly payslip generation"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payslips')
    month = models.PositiveIntegerField()
    year = models.PositiveIntegerField()
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    hra = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    da = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    conveyance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    medical_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2)
    days_worked = models.PositiveIntegerField()
    days_present = models.PositiveIntegerField()
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='generated_payslips')

    class Meta:
        unique_together = ['employee', 'month', 'year']
        ordering = ['-year', '-month']

    def __str__(self):
        return f"{self.employee.employee_id} - {self.month}/{self.year}"


class EmployeeTransfer(models.Model):
    """Employee department/role transfer tracking"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='transfers')
    from_department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='transfers_from')
    to_department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='transfers_to')
    from_designation = models.ForeignKey(Designation, on_delete=models.CASCADE, related_name='transfers_from')
    to_designation = models.ForeignKey(Designation, on_delete=models.CASCADE, related_name='transfers_to')
    transfer_date = models.DateField()
    reason = models.TextField()
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='approved_transfers')
    approved_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-transfer_date']

    def __str__(self):
        return f"{self.employee.employee_id} - {self.from_department} to {self.to_department}"


class ExitForm(models.Model):
    """Employee exit/resignation form"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='exit_forms')
    resignation_date = models.DateField()
    last_working_date = models.DateField()
    reason = models.TextField()
    exit_interview_date = models.DateField(null=True, blank=True)
    exit_interview_conducted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='conducted_exits')
    exit_interview_notes = models.TextField(blank=True)
    handover_completed = models.BooleanField(default=False)
    handover_notes = models.TextField(blank=True)
    final_settlement_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    final_settlement_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('completed', 'Completed'),
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-resignation_date']

    def __str__(self):
        return f"{self.employee.employee_id} - {self.resignation_date}"
