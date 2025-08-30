from django.contrib import admin
from .models import (
    BudgetPlan, BudgetItem, BudgetApproval, BudgetTemplate,
    BudgetTemplateItem, BudgetImport, BudgetAuditLog
)


@admin.register(BudgetPlan)
class BudgetPlanAdmin(admin.ModelAdmin):
    list_display = ['budget_code', 'budget_name', 'fiscal_year', 'budget_period', 'status', 'total_budget_amount', 'created_by', 'created_at']
    list_filter = ['status', 'budget_period', 'fiscal_year', 'is_active', 'created_at']
    search_fields = ['budget_code', 'budget_name', 'fiscal_year']
    readonly_fields = ['created_at', 'updated_at', 'approved_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('budget_code', 'budget_name', 'fiscal_year', 'budget_period')
        }),
        ('Date Range', {
            'fields': ('start_date', 'end_date')
        }),
        ('Financial Information', {
            'fields': ('total_budget_amount', 'currency')
        }),
        ('Status and Notes', {
            'fields': ('status', 'notes', 'is_active')
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at', 'approved_by', 'approved_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BudgetItem)
class BudgetItemAdmin(admin.ModelAdmin):
    list_display = ['budget_plan', 'cost_center', 'department', 'account', 'budget_amount', 'actual_amount', 'variance', 'is_over_budget']
    list_filter = ['budget_plan__status', 'cost_center__department', 'is_active', 'created_at']
    search_fields = ['budget_plan__budget_code', 'cost_center__code', 'cost_center__name', 'account__account_code']
    readonly_fields = ['created_at', 'updated_at', 'variance', 'variance_percentage', 'is_over_budget']
    
    fieldsets = (
        ('Budget Information', {
            'fields': ('budget_plan', 'cost_center', 'department', 'account')
        }),
        ('Financial Information', {
            'fields': ('budget_amount', 'actual_amount')
        }),
        ('Additional Information', {
            'fields': ('notes', 'is_active')
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BudgetApproval)
class BudgetApprovalAdmin(admin.ModelAdmin):
    list_display = ['budget_plan', 'approval_type', 'approved_by', 'approved_at']
    list_filter = ['approval_type', 'approved_at']
    search_fields = ['budget_plan__budget_code', 'budget_plan__budget_name', 'approved_by__username']
    readonly_fields = ['approved_at']
    date_hierarchy = 'approved_at'


@admin.register(BudgetTemplate)
class BudgetTemplateAdmin(admin.ModelAdmin):
    list_display = ['template_name', 'fiscal_year', 'budget_period', 'is_active', 'created_by', 'created_at']
    list_filter = ['budget_period', 'fiscal_year', 'is_active', 'created_at']
    search_fields = ['template_name', 'description', 'fiscal_year']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(BudgetTemplateItem)
class BudgetTemplateItemAdmin(admin.ModelAdmin):
    list_display = ['template', 'cost_center', 'account', 'default_amount']
    list_filter = ['template', 'cost_center__department']
    search_fields = ['template__template_name', 'cost_center__code', 'cost_center__name', 'account__account_code']


@admin.register(BudgetImport)
class BudgetImportAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'status', 'total_records', 'processed_records', 'error_records', 'created_by', 'import_date']
    list_filter = ['status', 'import_date']
    search_fields = ['file_name', 'created_by__username']
    readonly_fields = ['import_date', 'total_records', 'processed_records', 'error_records', 'error_log']
    date_hierarchy = 'import_date'


@admin.register(BudgetAuditLog)
class BudgetAuditLogAdmin(admin.ModelAdmin):
    list_display = ['budget_plan', 'action', 'user', 'timestamp', 'ip_address']
    list_filter = ['action', 'timestamp']
    search_fields = ['budget_plan__budget_code', 'user__username', 'field_name']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
