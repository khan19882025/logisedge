from django.db import models
from django.contrib.auth.models import User
from employees.models import Employee, Department
from django.utils import timezone
from decimal import Decimal
import uuid
from datetime import date, timedelta


class ExitType(models.Model):
    """Types of exit (resignation, termination, retirement, etc.)"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Exit Type'
        verbose_name_plural = 'Exit Types'

    def __str__(self):
        return self.name


class ClearanceDepartment(models.Model):
    """Departments involved in clearance process"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Clearance Department'
        verbose_name_plural = 'Clearance Departments'
        ordering = ['order']

    def __str__(self):
        return self.name


class ClearanceItem(models.Model):
    """Individual clearance items for each department"""
    department = models.ForeignKey(ClearanceDepartment, on_delete=models.CASCADE, related_name='clearance_items')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_required = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Clearance Item'
        verbose_name_plural = 'Clearance Items'
        ordering = ['department__order', 'order']

    def __str__(self):
        return f"{self.department.name} - {self.name}"


class ResignationRequest(models.Model):
    """Employee resignation request"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('manager_review', 'Manager Review'),
        ('hr_approval', 'HR Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('exit_processing', 'Exit Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    CONTRACT_TYPE_CHOICES = [
        ('limited', 'Limited Contract'),
        ('unlimited', 'Unlimited Contract'),
    ]

    reference_number = models.CharField(max_length=20, unique=True, blank=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='resignation_requests')
    exit_type = models.ForeignKey(ExitType, on_delete=models.CASCADE)
    contract_type = models.CharField(max_length=20, choices=CONTRACT_TYPE_CHOICES, default='unlimited')
    
    # Resignation details
    resignation_date = models.DateField()
    last_working_day = models.DateField()
    notice_period_days = models.PositiveIntegerField(default=30)
    notice_period_served = models.PositiveIntegerField(default=0)
    reason = models.TextField()
    additional_comments = models.TextField(blank=True)
    
    # Status and workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    current_step = models.CharField(max_length=50, default='resignation_submitted')
    
    # Approvals
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='manager_resignations')
    manager_approval_date = models.DateTimeField(null=True, blank=True)
    manager_comments = models.TextField(blank=True)
    
    hr_manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='hr_resignations')
    hr_approval_date = models.DateTimeField(null=True, blank=True)
    hr_comments = models.TextField(blank=True)
    
    # Timestamps
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Documents
    resignation_letter = models.FileField(upload_to='exit_management/resignation_letters/', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Resignation Request'
        verbose_name_plural = 'Resignation Requests'
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.employee.full_name} - {self.reference_number}"

    def save(self, *args, **kwargs):
        if not self.reference_number:
            self.reference_number = f"RES-{timezone.now().strftime('%Y%m')}-{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)

    @property
    def notice_period_remaining(self):
        """Calculate remaining notice period days"""
        return max(0, self.notice_period_days - self.notice_period_served)

    @property
    def is_notice_period_complete(self):
        """Check if notice period is fully served"""
        return self.notice_period_served >= self.notice_period_days


class ClearanceProcess(models.Model):
    """Clearance process for a resignation request"""
    resignation = models.OneToOneField(ResignationRequest, on_delete=models.CASCADE, related_name='clearance_process')
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Clearance Process'
        verbose_name_plural = 'Clearance Processes'

    def __str__(self):
        return f"Clearance for {self.resignation.employee.full_name}"

    @property
    def completion_percentage(self):
        """Calculate completion percentage"""
        total_items = self.clearance_items.count()
        if total_items == 0:
            return 0
        completed_items = self.clearance_items.filter(status='cleared').count()
        return round((completed_items / total_items) * 100, 1)


class ClearanceItemStatus(models.Model):
    """Status of individual clearance items"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('cleared', 'Cleared'),
        ('not_applicable', 'Not Applicable'),
        ('waived', 'Waived'),
    ]

    clearance_process = models.ForeignKey(ClearanceProcess, on_delete=models.CASCADE, related_name='clearance_items')
    clearance_item = models.ForeignKey(ClearanceItem, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    comments = models.TextField(blank=True)
    cleared_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    cleared_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Clearance Item Status'
        verbose_name_plural = 'Clearance Item Statuses'
        unique_together = ['clearance_process', 'clearance_item']

    def __str__(self):
        return f"{self.clearance_item.name} - {self.status}"


class GratuityCalculation(models.Model):
    """Gratuity calculation for UAE labor law compliance"""
    resignation = models.OneToOneField(ResignationRequest, on_delete=models.CASCADE, related_name='gratuity_calculation')
    
    # Basic calculation parameters
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    total_years_service = models.DecimalField(max_digits=5, decimal_places=2)
    contract_type = models.CharField(max_length=20, choices=ResignationRequest.CONTRACT_TYPE_CHOICES)
    
    # Gratuity calculation breakdown
    first_five_years = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    after_five_years = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Daily rates
    daily_rate_21_days = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    daily_rate_30_days = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Gratuity amounts
    gratuity_first_five = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gratuity_after_five = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_gratuity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Deductions
    notice_period_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    final_gratuity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Calculation details
    calculation_date = models.DateField(auto_now_add=True)
    calculated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Gratuity Calculation'
        verbose_name_plural = 'Gratuity Calculations'

    def __str__(self):
        return f"Gratuity for {self.resignation.employee.full_name}"

    def calculate_gratuity(self):
        """Calculate gratuity according to UAE labor law"""
        # Calculate daily rates
        self.daily_rate_21_days = self.basic_salary / 30
        self.daily_rate_30_days = self.basic_salary / 30
        
        # Calculate years
        if self.total_years_service <= 5:
            self.first_five_years = self.total_years_service
            self.after_five_years = 0
        else:
            self.first_five_years = 5
            self.after_five_years = self.total_years_service - 5
        
        # Calculate gratuity amounts
        self.gratuity_first_five = self.first_five_years * 21 * self.daily_rate_21_days
        self.gratuity_after_five = self.after_five_years * 30 * self.daily_rate_30_days
        self.total_gratuity = self.gratuity_first_five + self.gratuity_after_five
        
        # Apply deductions based on resignation timing
        if self.contract_type == 'limited':
            # Limited contract - full gratuity
            self.final_gratuity = self.total_gratuity
        else:
            # Unlimited contract - deductions apply
            if self.total_years_service < 1:
                self.final_gratuity = 0
            elif self.total_years_service < 3:
                self.final_gratuity = self.total_gratuity * Decimal('0.33')
            elif self.total_years_service < 5:
                self.final_gratuity = self.total_gratuity * Decimal('0.66')
            else:
                self.final_gratuity = self.total_gratuity
        
        # Subtract notice period deduction
        self.final_gratuity -= self.notice_period_deduction
        self.final_gratuity -= self.other_deductions
        
        # Ensure final amount is not negative
        self.final_gratuity = max(0, self.final_gratuity)


class FinalSettlement(models.Model):
    """Final settlement calculation and processing"""
    resignation = models.OneToOneField(ResignationRequest, on_delete=models.CASCADE, related_name='final_settlement')
    
    # Salary components
    last_month_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    leave_encashment = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gratuity_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Deductions
    loan_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notice_period_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Final amounts
    gross_settlement = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_settlement = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Processing
    is_processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Documents
    settlement_statement = models.FileField(upload_to='exit_management/settlements/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Final Settlement'
        verbose_name_plural = 'Final Settlements'

    def __str__(self):
        return f"Settlement for {self.resignation.employee.full_name}"

    def calculate_settlement(self):
        """Calculate final settlement amounts"""
        # Get gratuity from related calculation
        if hasattr(self.resignation, 'gratuity_calculation'):
            self.gratuity_amount = self.resignation.gratuity_calculation.final_gratuity
        
        # Calculate gross settlement
        self.gross_settlement = self.last_month_salary + self.leave_encashment + self.gratuity_amount
        
        # Calculate total deductions
        self.total_deductions = self.loan_deductions + self.notice_period_deduction + self.other_deductions
        
        # Calculate net settlement
        self.net_settlement = self.gross_settlement - self.total_deductions


class ExitDocument(models.Model):
    """Documents generated during exit process"""
    DOCUMENT_TYPE_CHOICES = [
        ('resignation_acceptance', 'Resignation Acceptance Letter'),
        ('experience_letter', 'Experience Letter'),
        ('settlement_statement', 'Final Settlement Statement'),
        ('clearance_certificate', 'Clearance Certificate'),
        ('noc_letter', 'NOC Letter'),
    ]

    resignation = models.ForeignKey(ResignationRequest, on_delete=models.CASCADE, related_name='exit_documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    file_path = models.FileField(upload_to='exit_management/documents/')
    is_bilingual = models.BooleanField(default=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = 'Exit Document'
        verbose_name_plural = 'Exit Documents'
        ordering = ['-generated_at']

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.resignation.employee.full_name}"


class ExitAuditLog(models.Model):
    """Audit log for exit process actions"""
    ACTION_CHOICES = [
        ('resignation_submitted', 'Resignation Submitted'),
        ('manager_approved', 'Manager Approved'),
        ('manager_rejected', 'Manager Rejected'),
        ('hr_approved', 'HR Approved'),
        ('hr_rejected', 'HR Rejected'),
        ('clearance_started', 'Clearance Started'),
        ('clearance_completed', 'Clearance Completed'),
        ('gratuity_calculated', 'Gratuity Calculated'),
        ('settlement_processed', 'Settlement Processed'),
        ('document_generated', 'Document Generated'),
        ('exit_completed', 'Exit Completed'),
    ]

    resignation = models.ForeignKey(ResignationRequest, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Exit Audit Log'
        verbose_name_plural = 'Exit Audit Logs'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.get_action_display()} - {self.resignation.employee.full_name}"


class ExitConfiguration(models.Model):
    """System configuration for exit management"""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Exit Configuration'
        verbose_name_plural = 'Exit Configurations'

    def __str__(self):
        return self.key
