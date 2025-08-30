from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    SalaryStructure, EmployeeSalary, BankAccount, PayrollPeriod, PayrollRecord,
    WPSRecord, EndOfServiceBenefit, Loan, Advance, Payslip, PayrollAuditLog, GPSSARecord
)


@admin.register(SalaryStructure)
class SalaryStructureAdmin(admin.ModelAdmin):
    list_display = ['name', 'basic_salary', 'housing_allowance', 'transport_allowance', 
                   'other_allowances', 'total_ctc', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['total_ctc', 'created_at', 'updated_at']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Salary Components', {
            'fields': ('basic_salary', 'housing_allowance', 'transport_allowance', 'other_allowances')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EmployeeSalary)
class EmployeeSalaryAdmin(admin.ModelAdmin):
    list_display = ['employee', 'salary_structure', 'basic_salary', 'total_ctc', 
                   'effective_date', 'is_active']
    list_filter = ['is_active', 'effective_date', 'salary_structure']
    search_fields = ['employee__first_name', 'employee__last_name', 'employee__username']
    readonly_fields = ['total_ctc', 'created_at', 'updated_at']
    ordering = ['employee__first_name']
    
    fieldsets = (
        ('Employee Information', {
            'fields': ('employee', 'salary_structure')
        }),
        ('Salary Details', {
            'fields': ('basic_salary', 'housing_allowance', 'transport_allowance', 'other_allowances')
        }),
        ('Effective Period', {
            'fields': ('effective_date', 'is_active')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ['employee', 'bank_name', 'account_number', 'iban', 'is_active']
    list_filter = ['is_active', 'bank_name', 'created_at']
    search_fields = ['employee__first_name', 'employee__last_name', 'bank_name', 'account_number']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['employee__first_name']
    
    fieldsets = (
        ('Employee Information', {
            'fields': ('employee',)
        }),
        ('Bank Details', {
            'fields': ('bank_name', 'account_number', 'iban', 'swift_code')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PayrollPeriod)
class PayrollPeriodAdmin(admin.ModelAdmin):
    list_display = ['year', 'month', 'period_name', 'start_date', 'end_date', 
                   'is_processed', 'processed_at', 'processed_by']
    list_filter = ['year', 'month', 'is_processed', 'processed_at']
    search_fields = ['year', 'month']
    readonly_fields = ['period_name', 'created_at']
    ordering = ['-year', '-month']
    
    fieldsets = (
        ('Period Information', {
            'fields': ('year', 'month', 'start_date', 'end_date')
        }),
        ('Processing Status', {
            'fields': ('is_processed', 'processed_at', 'processed_by')
        }),
        ('System Information', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(PayrollRecord)
class PayrollRecordAdmin(admin.ModelAdmin):
    list_display = ['employee', 'payroll_period', 'gross_salary', 'total_deductions', 
                   'net_salary', 'is_approved', 'approved_by']
    list_filter = ['payroll_period', 'is_approved', 'approved_at', 'created_at']
    search_fields = ['employee__first_name', 'employee__last_name', 'payroll_period__period_name']
    readonly_fields = ['gross_salary', 'total_deductions', 'net_salary', 'created_at', 'updated_at']
    ordering = ['-payroll_period', 'employee__first_name']
    
    fieldsets = (
        ('Employee & Period', {
            'fields': ('employee', 'payroll_period')
        }),
        ('Salary Components', {
            'fields': ('basic_salary', 'housing_allowance', 'transport_allowance', 'other_allowances')
        }),
        ('Additional Earnings', {
            'fields': ('overtime_pay', 'bonus', 'commission', 'other_earnings')
        }),
        ('Deductions', {
            'fields': ('loan_deduction', 'advance_deduction', 'absence_deduction', 'other_deductions')
        }),
        ('Attendance', {
            'fields': ('working_days', 'absent_days', 'leave_days', 'overtime_hours')
        }),
        ('Calculated Fields', {
            'fields': ('gross_salary', 'total_deductions', 'net_salary'),
            'classes': ('collapse',)
        }),
        ('Approval', {
            'fields': ('is_approved', 'approved_by', 'approved_at')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(WPSRecord)
class WPSRecordAdmin(admin.ModelAdmin):
    list_display = ['employee', 'payroll_period', 'company_wps_code', 'employee_wps_code', 
                   'salary_amount', 'status', 'sent_at', 'paid_at']
    list_filter = ['status', 'payroll_period', 'sent_at', 'paid_at']
    search_fields = ['employee__first_name', 'employee__last_name', 'company_wps_code', 'employee_wps_code']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-payroll_period', 'employee__first_name']
    
    fieldsets = (
        ('Employee & Period', {
            'fields': ('employee', 'payroll_period', 'payroll_record')
        }),
        ('WPS Information', {
            'fields': ('company_wps_code', 'employee_wps_code', 'bank_code', 'account_number', 'iban')
        }),
        ('Salary Information', {
            'fields': ('salary_amount',)
        }),
        ('Status Tracking', {
            'fields': ('status', 'sif_file_name', 'sent_at', 'paid_at', 'failure_reason')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EndOfServiceBenefit)
class EndOfServiceBenefitAdmin(admin.ModelAdmin):
    list_display = ['employee', 'contract_type', 'joining_date', 'termination_date', 
                   'years_of_service', 'gratuity_amount', 'total_settlement', 'is_processed']
    list_filter = ['contract_type', 'is_processed', 'processed_at', 'joining_date', 'termination_date']
    search_fields = ['employee__first_name', 'employee__last_name']
    readonly_fields = ['years_of_service', 'months_of_service', 'days_of_service', 
                      'gratuity_days_per_year', 'total_gratuity_days', 'gratuity_amount', 
                      'total_settlement', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Employee Information', {
            'fields': ('employee', 'contract_type')
        }),
        ('Service Period', {
            'fields': ('joining_date', 'termination_date')
        }),
        ('Service Calculation', {
            'fields': ('years_of_service', 'months_of_service', 'days_of_service'),
            'classes': ('collapse',)
        }),
        ('Gratuity Calculation', {
            'fields': ('basic_salary_for_gratuity', 'gratuity_days_per_year', 'total_gratuity_days', 'gratuity_amount')
        }),
        ('Additional Benefits', {
            'fields': ('leave_encashment_days', 'leave_encashment_amount', 'other_benefits')
        }),
        ('Total Settlement', {
            'fields': ('total_settlement',)
        }),
        ('Processing', {
            'fields': ('is_processed', 'processed_at', 'processed_by')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ['employee', 'loan_type', 'loan_amount', 'monthly_installment', 
                   'total_installments', 'remaining_installments', 'remaining_amount', 'status']
    list_filter = ['loan_type', 'status', 'start_date', 'end_date']
    search_fields = ['employee__first_name', 'employee__last_name', 'loan_type']
    readonly_fields = ['remaining_installments', 'remaining_amount', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Employee Information', {
            'fields': ('employee', 'loan_type')
        }),
        ('Loan Details', {
            'fields': ('loan_amount', 'monthly_installment', 'total_installments')
        }),
        ('Period', {
            'fields': ('start_date', 'end_date')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Remaining Information', {
            'fields': ('remaining_installments', 'remaining_amount'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Advance)
class AdvanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'amount', 'reason_short', 'requested_date', 'status', 
                   'approved_by', 'approved_date']
    list_filter = ['status', 'requested_date', 'approved_date']
    search_fields = ['employee__first_name', 'employee__last_name', 'reason']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Employee Information', {
            'fields': ('employee',)
        }),
        ('Advance Details', {
            'fields': ('amount', 'reason', 'requested_date')
        }),
        ('Approval', {
            'fields': ('status', 'approved_by', 'approved_date', 'paid_date')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def reason_short(self, obj):
        return obj.reason[:50] + '...' if len(obj.reason) > 50 else obj.reason
    reason_short.short_description = 'Reason'


@admin.register(Payslip)
class PayslipAdmin(admin.ModelAdmin):
    list_display = ['payslip_number', 'employee_name', 'payroll_period_display', 'generated_at', 
                   'generated_by', 'is_emailed', 'emailed_at']
    list_filter = ['generated_at', 'is_emailed', 'emailed_at']
    search_fields = ['payslip_number', 'payroll_record__employee__first_name', 
                    'payroll_record__employee__last_name']
    readonly_fields = ['payslip_number', 'generated_at']
    ordering = ['-generated_at']
    
    fieldsets = (
        ('Payslip Information', {
            'fields': ('payslip_number', 'payroll_record')
        }),
        ('Generation Details', {
            'fields': ('generated_by', 'generated_at')
        }),
        ('Email Status', {
            'fields': ('is_emailed', 'emailed_at')
        }),
        ('File', {
            'fields': ('pdf_file',)
        }),
    )
    
    def employee_name(self, obj):
        return obj.payroll_record.employee.get_full_name()
    employee_name.short_description = 'Employee'
    
    def payroll_period_display(self, obj):
        return obj.payroll_record.payroll_period.period_name
    payroll_period_display.short_description = 'Payroll Period'


@admin.register(GPSSARecord)
class GPSSARecordAdmin(admin.ModelAdmin):
    list_display = ['employee', 'payroll_period', 'employee_contribution', 'employer_contribution', 
                   'total_contribution', 'is_submitted', 'submitted_at']
    list_filter = ['is_submitted', 'submitted_at', 'payroll_period']
    search_fields = ['employee__first_name', 'employee__last_name', 'emirates_id', 'passport_number']
    readonly_fields = ['total_contribution', 'created_at', 'updated_at']
    ordering = ['-payroll_period', 'employee__first_name']
    
    fieldsets = (
        ('Employee & Period', {
            'fields': ('employee', 'payroll_period')
        }),
        ('Contributions', {
            'fields': ('employee_contribution', 'employer_contribution', 'total_contribution')
        }),
        ('Employee Details', {
            'fields': ('emirates_id', 'passport_number', 'nationality')
        }),
        ('Submission', {
            'fields': ('is_submitted', 'submitted_at', 'submitted_by')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PayrollAuditLog)
class PayrollAuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'model_name', 'object_id', 'description', 'created_at']
    list_filter = ['action', 'model_name', 'created_at']
    search_fields = ['user__first_name', 'user__last_name', 'description']
    readonly_fields = ['user', 'action', 'model_name', 'object_id', 'description', 'ip_address', 'created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Audit Information', {
            'fields': ('user', 'action', 'model_name', 'object_id')
        }),
        ('Details', {
            'fields': ('description', 'ip_address')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
