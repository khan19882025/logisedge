from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    ExitType, ClearanceDepartment, ClearanceItem, ResignationRequest,
    ClearanceProcess, ClearanceItemStatus, GratuityCalculation,
    FinalSettlement, ExitDocument, ExitAuditLog, ExitConfiguration
)


@admin.register(ExitType)
class ExitTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']


@admin.register(ClearanceDepartment)
class ClearanceDepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['order', 'name']


@admin.register(ClearanceItem)
class ClearanceItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'department', 'is_required', 'is_active', 'order']
    list_filter = ['department', 'is_required', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'department__name']
    ordering = ['department__order', 'order', 'name']


class ClearanceItemStatusInline(admin.TabularInline):
    model = ClearanceItemStatus
    extra = 0
    readonly_fields = ['clearance_item', 'created_at', 'updated_at']
    fields = ['clearance_item', 'status', 'comments', 'cleared_by', 'cleared_at']


@admin.register(ClearanceProcess)
class ClearanceProcessAdmin(admin.ModelAdmin):
    list_display = ['resignation_link', 'completion_percentage', 'is_completed', 'created_at']
    list_filter = ['is_completed', 'created_at']
    search_fields = ['resignation__employee__full_name', 'resignation__reference_number']
    readonly_fields = ['resignation', 'completion_percentage']
    inlines = [ClearanceItemStatusInline]
    
    def resignation_link(self, obj):
        if obj.resignation:
            url = reverse('admin:exit_management_resignationrequest_change', args=[obj.resignation.id])
            return format_html('<a href="{}">{}</a>', url, obj.resignation.employee.full_name)
        return '-'
    resignation_link.short_description = 'Employee'


@admin.register(ClearanceItemStatus)
class ClearanceItemStatusAdmin(admin.ModelAdmin):
    list_display = ['clearance_process', 'clearance_item', 'status', 'cleared_by', 'cleared_at']
    list_filter = ['status', 'cleared_at', 'created_at']
    search_fields = ['clearance_process__resignation__employee__full_name', 'clearance_item__name']
    readonly_fields = ['clearance_process', 'clearance_item', 'created_at', 'updated_at']


class ExitAuditLogInline(admin.TabularInline):
    model = ExitAuditLog
    extra = 0
    readonly_fields = ['action', 'user', 'details', 'timestamp']
    fields = ['action', 'user', 'details', 'timestamp']


@admin.register(ResignationRequest)
class ResignationRequestAdmin(admin.ModelAdmin):
    list_display = [
        'reference_number', 'employee_link', 'exit_type', 'status', 
        'resignation_date', 'last_working_day', 'submitted_at'
    ]
    list_filter = [
        'status', 'exit_type', 'contract_type', 'resignation_date', 
        'submitted_at', 'employee__department'
    ]
    search_fields = [
        'reference_number', 'employee__full_name', 'employee__employee_id',
        'reason', 'exit_type__name'
    ]
    readonly_fields = [
        'reference_number', 'submitted_at', 'updated_at', 'manager_approval_date',
        'hr_approval_date', 'completed_at'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('reference_number', 'employee', 'exit_type', 'contract_type')
        }),
        ('Resignation Details', {
            'fields': ('resignation_date', 'last_working_day', 'notice_period_days', 
                      'notice_period_served', 'reason', 'additional_comments')
        }),
        ('Status & Workflow', {
            'fields': ('status', 'current_step')
        }),
        ('Approvals', {
            'fields': ('manager', 'manager_approval_date', 'manager_comments',
                      'hr_manager', 'hr_approval_date', 'hr_comments')
        }),
        ('Documents', {
            'fields': ('resignation_letter',)
        }),
        ('Timestamps', {
            'fields': ('submitted_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [ExitAuditLogInline]
    ordering = ['-submitted_at']
    
    def employee_link(self, obj):
        if obj.employee:
            url = reverse('admin:employees_employee_change', args=[obj.employee.id])
            return format_html('<a href="{}">{}</a>', url, obj.employee.full_name)
        return '-'
    employee_link.short_description = 'Employee'


@admin.register(GratuityCalculation)
class GratuityCalculationAdmin(admin.ModelAdmin):
    list_display = [
        'resignation_link', 'basic_salary', 'total_years_service', 
        'contract_type', 'final_gratuity', 'calculated_by', 'calculation_date'
    ]
    list_filter = ['contract_type', 'calculation_date', 'created_at']
    search_fields = ['resignation__employee__full_name', 'resignation__reference_number']
    readonly_fields = [
        'resignation', 'first_five_years', 'after_five_years', 'daily_rate_21_days',
        'daily_rate_30_days', 'gratuity_first_five', 'gratuity_after_five',
        'total_gratuity', 'final_gratuity', 'calculation_date', 'created_at', 'updated_at'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('resignation', 'basic_salary', 'total_years_service', 'contract_type')
        }),
        ('Calculation Breakdown', {
            'fields': ('first_five_years', 'after_five_years', 'daily_rate_21_days', 'daily_rate_30_days')
        }),
        ('Gratuity Amounts', {
            'fields': ('gratuity_first_five', 'gratuity_after_five', 'total_gratuity')
        }),
        ('Deductions', {
            'fields': ('notice_period_deduction', 'other_deductions')
        }),
        ('Final Amount', {
            'fields': ('final_gratuity',)
        }),
        ('Details', {
            'fields': ('calculated_by', 'calculation_date', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    ordering = ['-calculation_date']
    
    def resignation_link(self, obj):
        if obj.resignation:
            url = reverse('admin:exit_management_resignationrequest_change', args=[obj.resignation.id])
            return format_html('<a href="{}">{}</a>', url, obj.resignation.employee.full_name)
        return '-'
    resignation_link.short_description = 'Employee'


@admin.register(FinalSettlement)
class FinalSettlementAdmin(admin.ModelAdmin):
    list_display = [
        'resignation_link', 'gross_settlement', 'total_deductions', 
        'net_settlement', 'is_processed', 'processed_by', 'processed_at'
    ]
    list_filter = ['is_processed', 'processed_at', 'created_at']
    search_fields = ['resignation__employee__full_name', 'resignation__reference_number']
    readonly_fields = [
        'resignation', 'gratuity_amount', 'gross_settlement', 'total_deductions',
        'net_settlement', 'created_at', 'updated_at'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('resignation', 'gratuity_amount')
        }),
        ('Salary Components', {
            'fields': ('last_month_salary', 'leave_encashment')
        }),
        ('Deductions', {
            'fields': ('loan_deductions', 'notice_period_deduction', 'other_deductions')
        }),
        ('Final Amounts', {
            'fields': ('gross_settlement', 'total_deductions', 'net_settlement')
        }),
        ('Processing', {
            'fields': ('is_processed', 'processed_by', 'processed_at')
        }),
        ('Documents', {
            'fields': ('settlement_statement',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    ordering = ['-created_at']
    
    def resignation_link(self, obj):
        if obj.resignation:
            url = reverse('admin:exit_management_resignationrequest_change', args=[obj.resignation.id])
            return format_html('<a href="{}">{}</a>', url, obj.resignation.employee.full_name)
        return '-'
    resignation_link.short_description = 'Employee'


@admin.register(ExitDocument)
class ExitDocumentAdmin(admin.ModelAdmin):
    list_display = [
        'resignation_link', 'document_type', 'title', 'is_bilingual', 
        'generated_by', 'generated_at'
    ]
    list_filter = ['document_type', 'is_bilingual', 'generated_at']
    search_fields = [
        'resignation__employee__full_name', 'resignation__reference_number',
        'title', 'document_type'
    ]
    readonly_fields = ['resignation', 'generated_at']
    ordering = ['-generated_at']
    
    def resignation_link(self, obj):
        if obj.resignation:
            url = reverse('admin:exit_management_resignationrequest_change', args=[obj.resignation.id])
            return format_html('<a href="{}">{}</a>', url, obj.resignation.employee.full_name)
        return '-'
    resignation_link.short_description = 'Employee'


@admin.register(ExitAuditLog)
class ExitAuditLogAdmin(admin.ModelAdmin):
    list_display = [
        'resignation_link', 'action', 'user', 'timestamp'
    ]
    list_filter = ['action', 'timestamp', 'user']
    search_fields = [
        'resignation__employee__full_name', 'resignation__reference_number',
        'action', 'user__username', 'details'
    ]
    readonly_fields = ['resignation', 'action', 'user', 'details', 'timestamp']
    ordering = ['-timestamp']
    
    def resignation_link(self, obj):
        if obj.resignation:
            url = reverse('admin:exit_management_resignationrequest_change', args=[obj.resignation.id])
            return format_html('<a href="{}">{}</a>', url, obj.resignation.employee.full_name)
        return '-'
    resignation_link.short_description = 'Employee'


@admin.register(ExitConfiguration)
class ExitConfigurationAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['key', 'value', 'description']
    ordering = ['key']
