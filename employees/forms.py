from django import forms
from django.contrib.auth.models import User
from .models import (
    Employee, Department, Designation, EmployeeDocument, Attendance, 
    LeaveType, Leave, LeaveBalance, SalaryStructure, Payslip, 
    EmployeeTransfer, ExitForm
)
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date


class DepartmentForm(forms.ModelForm):
    """Form for creating and editing departments"""
    class Meta:
        model = Department
        fields = ['name', 'code', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter department name'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter department code'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter description'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_code(self):
        code = self.cleaned_data['code']
        if len(code) < 2:
            raise ValidationError("Department code must be at least 2 characters long.")
        return code.upper()


class DesignationForm(forms.ModelForm):
    """Form for creating and editing designations"""
    class Meta:
        model = Designation
        fields = ['title', 'department', 'description', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter designation title'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter description'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class EmployeeForm(forms.ModelForm):
    """Form for creating and editing employees"""
    class Meta:
        model = Employee
        fields = [
            'first_name', 'last_name', 'gender', 'date_of_birth',
            'department', 'designation', 'join_date', 'employment_type',
            'status', 'reporting_manager', 'email', 'mobile', 'alternate_phone',
            'current_address', 'permanent_address', 'photo'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter first name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter last name'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'designation': forms.Select(attrs={'class': 'form-select'}),
            'join_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'employment_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'reporting_manager': forms.Select(attrs={'class': 'form-select'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email address'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter mobile number'}),
            'alternate_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter alternate phone'}),
            'current_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter current address'}),
            'permanent_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter permanent address'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter designations based on selected department
        if self.instance.pk:
            self.fields['designation'].queryset = Designation.objects.filter(
                department=self.instance.department
            )

    def clean_date_of_birth(self):
        dob = self.cleaned_data['date_of_birth']
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age < 18:
            raise ValidationError("Employee must be at least 18 years old.")
        if age > 70:
            raise ValidationError("Employee age cannot exceed 70 years.")
        return dob

    def clean_join_date(self):
        join_date = self.cleaned_data['join_date']
        if join_date > date.today():
            raise ValidationError("Join date cannot be in the future.")
        return join_date

    def clean_email(self):
        email = self.cleaned_data['email']
        if Employee.objects.filter(email=email).exclude(pk=self.instance.pk if self.instance.pk else None).exists():
            raise ValidationError("An employee with this email already exists.")
        return email


class EmployeeDocumentForm(forms.ModelForm):
    """Form for uploading employee documents"""
    class Meta:
        model = EmployeeDocument
        fields = ['document_type', 'document_number', 'document_file', 'description']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'document_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter document number'}),
            'document_file': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter description'}),
        }

    def clean_document_file(self):
        file = self.cleaned_data['document_file']
        if file:
            # Check file size (max 5MB)
            if file.size > 5 * 1024 * 1024:
                raise ValidationError("File size must be less than 5MB.")
            
            # Check file extension
            allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']
            file_extension = file.name.lower()
            if not any(file_extension.endswith(ext) for ext in allowed_extensions):
                raise ValidationError("Only PDF, JPG, PNG, and DOC files are allowed.")
        
        return file


class AttendanceForm(forms.ModelForm):
    """Form for recording attendance"""
    class Meta:
        model = Attendance
        fields = ['employee', 'date', 'check_in', 'check_out', 'status', 'notes']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'check_in': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'check_out': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter notes'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get('check_in')
        check_out = cleaned_data.get('check_out')
        date = cleaned_data.get('date')
        
        if check_in and check_out and check_in >= check_out:
            raise ValidationError("Check-out time must be after check-in time.")
        
        if date and date > date.today():
            raise ValidationError("Attendance date cannot be in the future.")
        
        return cleaned_data


class LeaveTypeForm(forms.ModelForm):
    """Form for creating and editing leave types"""
    class Meta:
        model = LeaveType
        fields = ['name', 'code', 'default_days', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter leave type name'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter leave type code'}),
            'default_days': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter description'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class LeaveForm(forms.ModelForm):
    """Form for leave applications"""
    class Meta:
        model = Leave
        fields = ['leave_type', 'start_date', 'end_date', 'days_requested', 'reason']
        widgets = {
            'leave_type': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'days_requested': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter reason for leave'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        days_requested = cleaned_data.get('days_requested')
        
        if start_date and end_date:
            if start_date > end_date:
                raise ValidationError("End date must be after start date.")
            
            if start_date < date.today():
                raise ValidationError("Start date cannot be in the past.")
            
            # Calculate actual days difference
            from datetime import timedelta
            actual_days = (end_date - start_date).days + 1
            if days_requested and days_requested != actual_days:
                raise ValidationError(f"Days requested ({days_requested}) should match the date range ({actual_days} days).")
        
        return cleaned_data


class LeaveBalanceForm(forms.ModelForm):
    """Form for managing leave balances"""
    class Meta:
        model = LeaveBalance
        fields = ['employee', 'leave_type', 'year', 'total_days', 'used_days']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'leave_type': forms.Select(attrs={'class': 'form-select'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'min': 2020, 'max': 2030}),
            'total_days': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'used_days': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }

    def clean(self):
        cleaned_data = super().clean()
        total_days = cleaned_data.get('total_days')
        used_days = cleaned_data.get('used_days')
        
        if total_days and used_days and used_days > total_days:
            raise ValidationError("Used days cannot exceed total days.")
        
        return cleaned_data


class SalaryStructureForm(forms.ModelForm):
    """Form for managing salary structures"""
    class Meta:
        model = SalaryStructure
        fields = [
            'basic_salary', 'hra', 'da', 'conveyance', 'medical_allowance',
            'other_allowances', 'effective_from', 'is_active'
        ]
        widgets = {
            'basic_salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            'hra': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            'da': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            'conveyance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            'medical_allowance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            'other_allowances': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            'effective_from': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_effective_from(self):
        effective_from = self.cleaned_data['effective_from']
        if effective_from > date.today():
            raise ValidationError("Effective date cannot be in the future.")
        return effective_from


class EmployeeSearchForm(forms.Form):
    """Form for searching employees"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, ID, email...'
        })
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        required=False,
        empty_label="All Departments",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    designation = forms.ModelChoiceField(
        queryset=Designation.objects.filter(is_active=True),
        required=False,
        empty_label="All Designations",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + Employee.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    employment_type = forms.ChoiceField(
        choices=[('', 'All Types')] + Employee.EMPLOYMENT_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class AttendanceSearchForm(forms.Form):
    """Form for searching attendance records"""
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(status='active'),
        required=False,
        empty_label="All Employees",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        required=False,
        empty_label="All Departments",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + [
            ('present', 'Present'),
            ('absent', 'Absent'),
            ('half_day', 'Half Day'),
            ('leave', 'On Leave'),
            ('holiday', 'Holiday'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class LeaveSearchForm(forms.Form):
    """Form for searching leave applications"""
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(status='active'),
        required=False,
        empty_label="All Employees",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    leave_type = forms.ModelChoiceField(
        queryset=LeaveType.objects.filter(is_active=True),
        required=False,
        empty_label="All Leave Types",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + Leave.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )


class EmployeeTransferForm(forms.ModelForm):
    """Form for employee transfers"""
    class Meta:
        model = EmployeeTransfer
        fields = ['employee', 'from_department', 'to_department', 'from_designation', 'to_designation', 'transfer_date', 'reason']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'from_department': forms.Select(attrs={'class': 'form-select'}),
            'to_department': forms.Select(attrs={'class': 'form-select'}),
            'from_designation': forms.Select(attrs={'class': 'form-select'}),
            'to_designation': forms.Select(attrs={'class': 'form-select'}),
            'transfer_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter transfer reason'}),
        }

    def clean_transfer_date(self):
        transfer_date = self.cleaned_data['transfer_date']
        if transfer_date < date.today():
            raise ValidationError("Transfer date cannot be in the past.")
        return transfer_date


class ExitFormForm(forms.ModelForm):
    """Form for employee exit/resignation"""
    class Meta:
        model = ExitForm
        fields = [
            'employee', 'resignation_date', 'last_working_date', 'reason',
            'exit_interview_date', 'exit_interview_notes', 'handover_notes',
            'final_settlement_amount', 'final_settlement_date'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'resignation_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'last_working_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter resignation reason'}),
            'exit_interview_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'exit_interview_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter exit interview notes'}),
            'handover_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter handover notes'}),
            'final_settlement_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            'final_settlement_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        resignation_date = cleaned_data.get('resignation_date')
        last_working_date = cleaned_data.get('last_working_date')
        
        if resignation_date and last_working_date:
            if resignation_date > last_working_date:
                raise ValidationError("Last working date must be after resignation date.")
            
            if resignation_date < date.today():
                raise ValidationError("Resignation date cannot be in the past.")
        
        return cleaned_data 