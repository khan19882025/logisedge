from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid
from datetime import date, datetime
import calendar
from multi_currency.models import Currency


class SalaryStructure(models.Model):
    """Salary structure template for different roles/grades"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, default=3)  # Default to AED
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    housing_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transport_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def total_ctc(self):
        """Cost to Company"""
        return (self.basic_salary + self.housing_allowance + 
                self.transport_allowance + self.other_allowances)

    @property
    def net_salary(self):
        """Net salary after deductions (basic calculation)"""
        # This would be calculated based on tax and other deductions
        return self.total_ctc


class EmployeeSalary(models.Model):
    """Employee-specific salary details"""
    employee = models.OneToOneField(User, on_delete=models.CASCADE, related_name='salary')
    salary_structure = models.ForeignKey(SalaryStructure, on_delete=models.PROTECT)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, default=3)  # Default to AED
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    housing_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transport_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    effective_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Employee Salaries"

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.basic_salary}"

    @property
    def total_ctc(self):
        return (self.basic_salary + self.housing_allowance + 
                self.transport_allowance + self.other_allowances)

    @property
    def net_salary(self):
        return self.total_ctc


class BankAccount(models.Model):
    """Employee bank account details for WPS"""
    employee = models.OneToOneField(User, on_delete=models.CASCADE, related_name='bank_account')
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=50)
    iban = models.CharField(max_length=50)
    swift_code = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Bank Accounts"

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.bank_name}"


class PayrollPeriod(models.Model):
    """Payroll period (monthly)"""
    year = models.IntegerField()
    month = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    start_date = models.DateField()
    end_date = models.DateField()
    is_processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['year', 'month']
        ordering = ['-year', '-month']

    def __str__(self):
        return f"{self.year}-{self.month:02d}"

    @property
    def period_name(self):
        return f"{calendar.month_name[self.month]} {self.year}"


class PayrollRecord(models.Model):
    """Individual employee payroll record for a period"""
    payroll_period = models.ForeignKey(PayrollPeriod, on_delete=models.CASCADE, related_name='records')
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payroll_records')
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, default=3)  # Default to AED
    
    # Basic salary components
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    housing_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transport_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Additional earnings
    overtime_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Deductions
    loan_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    advance_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    absence_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Attendance and leave
    working_days = models.IntegerField(default=0)
    absent_days = models.IntegerField(default=0)
    leave_days = models.IntegerField(default=0)
    overtime_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    
    # Calculated fields
    gross_salary = models.DecimalField(max_digits=10, decimal_places=2)
    total_deductions = models.DecimalField(max_digits=10, decimal_places=2)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_payrolls')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['payroll_period', 'employee']
        ordering = ['-payroll_period', 'employee__first_name']

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.payroll_period}"

    def save(self, *args, **kwargs):
        # Calculate totals before saving
        self.gross_salary = (self.basic_salary + self.housing_allowance + 
                            self.transport_allowance + self.other_allowances +
                            self.overtime_pay + self.bonus + self.commission + 
                            self.other_earnings)
        
        self.total_deductions = (self.loan_deduction + self.advance_deduction + 
                                self.absence_deduction + self.other_deductions)
        
        self.net_salary = self.gross_salary - self.total_deductions
        
        super().save(*args, **kwargs)


class WPSRecord(models.Model):
    """WPS (Wage Protection System) record"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent to Bank'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    payroll_period = models.ForeignKey(PayrollPeriod, on_delete=models.CASCADE, related_name='wps_records')
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wps_records')
    payroll_record = models.OneToOneField(PayrollRecord, on_delete=models.CASCADE, related_name='wps_record')
    
    # WPS specific fields
    company_wps_code = models.CharField(max_length=20)
    employee_wps_code = models.CharField(max_length=20)
    bank_code = models.CharField(max_length=10)
    account_number = models.CharField(max_length=50)
    iban = models.CharField(max_length=50)
    salary_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sif_file_name = models.CharField(max_length=255, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['payroll_period', 'employee']
        ordering = ['-payroll_period', 'employee__first_name']

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.payroll_period} - {self.status}"


class EndOfServiceBenefit(models.Model):
    """End of Service Benefits calculation"""
    CONTRACT_TYPE_CHOICES = [
        ('limited', 'Limited Contract'),
        ('unlimited', 'Unlimited Contract'),
    ]
    
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='eosb_records')
    contract_type = models.CharField(max_length=20, choices=CONTRACT_TYPE_CHOICES)
    joining_date = models.DateField()
    termination_date = models.DateField()
    
    # Service calculation
    years_of_service = models.DecimalField(max_digits=5, decimal_places=2)
    months_of_service = models.IntegerField()
    days_of_service = models.IntegerField()
    
    # Gratuity calculation
    basic_salary_for_gratuity = models.DecimalField(max_digits=10, decimal_places=2)
    gratuity_days_per_year = models.IntegerField()  # 21 or 30 based on years
    total_gratuity_days = models.DecimalField(max_digits=8, decimal_places=2)
    gratuity_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Additional benefits
    leave_encashment_days = models.IntegerField(default=0)
    leave_encashment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_benefits = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Total settlement
    total_settlement = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Status
    is_processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "End of Service Benefits"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee.get_full_name()} - EOSB {self.termination_date}"

    def calculate_gratuity(self):
        """Calculate gratuity based on UAE Labour Law"""
        if self.years_of_service <= 5:
            self.gratuity_days_per_year = 21
        else:
            self.gratuity_days_per_year = 30
        
        self.total_gratuity_days = self.years_of_service * self.gratuity_days_per_year
        self.gratuity_amount = (self.basic_salary_for_gratuity / 30) * self.total_gratuity_days
        
        # Calculate total settlement
        self.total_settlement = (self.gratuity_amount + self.leave_encashment_amount + 
                                self.other_benefits)


class Loan(models.Model):
    """Employee loan records"""
    LOAN_TYPE_CHOICES = [
        ('personal', 'Personal Loan'),
        ('housing', 'Housing Loan'),
        ('vehicle', 'Vehicle Loan'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loans')
    loan_type = models.CharField(max_length=20, choices=LOAN_TYPE_CHOICES)
    loan_amount = models.DecimalField(max_digits=10, decimal_places=2)
    monthly_installment = models.DecimalField(max_digits=10, decimal_places=2)
    total_installments = models.IntegerField()
    remaining_installments = models.IntegerField()
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.loan_type} - {self.loan_amount}"


class Advance(models.Model):
    """Employee advance payment records"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('rejected', 'Rejected'),
    ]
    
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='advances')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    requested_date = models.DateField()
    approved_date = models.DateField(null=True, blank=True)
    paid_date = models.DateField(null=True, blank=True)
    
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_advances')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.amount} - {self.status}"


class Payslip(models.Model):
    """Employee payslip"""
    payroll_record = models.OneToOneField(PayrollRecord, on_delete=models.CASCADE, related_name='payslip')
    payslip_number = models.CharField(max_length=20, unique=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    pdf_file = models.FileField(upload_to='payslips/', null=True, blank=True)
    is_emailed = models.BooleanField(default=False)
    emailed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-generated_at']

    def __str__(self):
        return f"Payslip {self.payslip_number} - {self.payroll_record.employee.get_full_name()}"

    def save(self, *args, **kwargs):
        if not self.payslip_number:
            # Generate payslip number
            year = self.payroll_record.payroll_period.year
            month = self.payroll_record.payroll_period.month
            employee_id = self.payroll_record.employee.id
            self.payslip_number = f"PS{year}{month:02d}{employee_id:04d}"
        super().save(*args, **kwargs)


class PayrollAuditLog(models.Model):
    """Audit log for payroll changes"""
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('deleted', 'Deleted'),
        ('processed', 'Processed'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payroll_audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50)
    object_id = models.IntegerField()
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.action} - {self.model_name}"


class GPSSARecord(models.Model):
    """GPSSA (General Pension and Social Security Authority) records for UAE nationals"""
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gpssa_records')
    payroll_period = models.ForeignKey(PayrollPeriod, on_delete=models.CASCADE, related_name='gpssa_records')
    
    # GPSSA contributions
    employee_contribution = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    employer_contribution = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_contribution = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Employee details for GPSSA
    emirates_id = models.CharField(max_length=20)
    passport_number = models.CharField(max_length=20)
    nationality = models.CharField(max_length=50, default='UAE')
    
    is_submitted = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(null=True, blank=True)
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['payroll_period', 'employee']
        ordering = ['-payroll_period', 'employee__first_name']

    def __str__(self):
        return f"{self.employee.get_full_name()} - GPSSA {self.payroll_period}"

    def save(self, *args, **kwargs):
        # Calculate total contribution
        self.total_contribution = self.employee_contribution + self.employer_contribution
        super().save(*args, **kwargs)
