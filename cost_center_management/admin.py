from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Department, CostCenter, CostCenterBudget, CostCenterTransaction,
    CostCenterReport, CostCenterAuditLog
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'created_at', 'created_by']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code', 'description']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        else:  # Updating existing object
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CostCenter)
class CostCenterAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'name', 'department', 'manager', 'status', 'budget_amount',
        'total_expenses_display', 'budget_variance_display', 'is_active'
    ]
    list_filter = ['status', 'is_active', 'department', 'created_at']
    search_fields = ['code', 'name', 'description']
    ordering = ['code']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'description', 'department', 'manager')
        }),
        ('Hierarchy', {
            'fields': ('parent_cost_center',),
            'classes': ('collapse',)
        }),
        ('Status & Dates', {
            'fields': ('status', 'start_date', 'end_date', 'is_active')
        }),
        ('Budget', {
            'fields': ('budget_amount', 'currency')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def total_expenses_display(self, obj):
        return f"{obj.total_expenses:,.2f} {obj.currency}"
    total_expenses_display.short_description = 'Total Expenses'
    
    def budget_variance_display(self, obj):
        variance = obj.budget_variance
        color = 'red' if variance < 0 else 'green'
        return format_html('<span style="color: {};">{:.2f} {}</span>', color, variance, obj.currency)
    budget_variance_display.short_description = 'Budget Variance'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        else:  # Updating existing object
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CostCenterBudget)
class CostCenterBudgetAdmin(admin.ModelAdmin):
    list_display = [
        'cost_center', 'budget_period', 'start_date', 'end_date',
        'budget_amount', 'total_expenses_display', 'budget_variance_display', 'is_active'
    ]
    list_filter = ['budget_period', 'is_active', 'start_date', 'end_date']
    search_fields = ['cost_center__name', 'cost_center__code']
    ordering = ['-start_date']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    def total_expenses_display(self, obj):
        return f"{obj.total_expenses:,.2f} {obj.currency}"
    total_expenses_display.short_description = 'Total Expenses'
    
    def budget_variance_display(self, obj):
        variance = obj.budget_variance
        color = 'red' if variance < 0 else 'green'
        return format_html('<span style="color: {};">{:.2f} {}</span>', color, variance, obj.currency)
    budget_variance_display.short_description = 'Budget Variance'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        else:  # Updating existing object
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CostCenterTransaction)
class CostCenterTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'cost_center', 'transaction_type', 'transaction_date',
        'reference_number', 'amount', 'currency', 'is_active'
    ]
    list_filter = ['transaction_type', 'is_active', 'transaction_date', 'currency']
    search_fields = ['cost_center__name', 'cost_center__code', 'reference_number', 'description']
    ordering = ['-transaction_date']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    date_hierarchy = 'transaction_date'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        else:  # Updating existing object
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CostCenterReport)
class CostCenterReportAdmin(admin.ModelAdmin):
    list_display = [
        'report_name', 'report_type', 'cost_center', 'start_date',
        'end_date', 'generated_at', 'generated_by'
    ]
    list_filter = ['report_type', 'generated_at']
    search_fields = ['report_name', 'cost_center__name']
    ordering = ['-generated_at']
    readonly_fields = ['generated_at', 'generated_by', 'report_data']
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.generated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CostCenterAuditLog)
class CostCenterAuditLogAdmin(admin.ModelAdmin):
    list_display = [
        'cost_center', 'action', 'field_name', 'user', 'timestamp'
    ]
    list_filter = ['action', 'timestamp']
    search_fields = ['cost_center__name', 'cost_center__code', 'user__username']
    ordering = ['-timestamp']
    readonly_fields = ['cost_center', 'action', 'field_name', 'old_value', 'new_value', 'timestamp', 'user', 'ip_address']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
