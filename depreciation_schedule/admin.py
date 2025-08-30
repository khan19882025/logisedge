from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum, Count
from .models import DepreciationSchedule, DepreciationEntry, DepreciationSettings


@admin.register(DepreciationSchedule)
class DepreciationScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'schedule_number', 'name', 'start_date', 'end_date', 
        'status', 'total_depreciation', 'total_assets', 'created_by', 'created_at'
    ]
    list_filter = ['status', 'start_date', 'created_at']
    search_fields = ['schedule_number', 'name', 'description']
    readonly_fields = ['schedule_number', 'total_depreciation', 'total_assets', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('schedule_number', 'name', 'description')
        }),
        ('Date Range', {
            'fields': ('start_date', 'end_date')
        }),
        ('Financial Settings', {
            'fields': ('depreciation_expense_account', 'accumulated_depreciation_account')
        }),
        ('Status and Totals', {
            'fields': ('status', 'total_depreciation', 'total_assets')
        }),
        ('Journal Entry', {
            'fields': ('journal_entry',),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at', 'posted_by', 'posted_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'created_by', 'updated_by', 'posted_by', 'journal_entry'
        )
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        else:
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(DepreciationEntry)
class DepreciationEntryAdmin(admin.ModelAdmin):
    list_display = [
        'asset', 'period', 'opening_value', 'depreciation_amount', 
        'accumulated_depreciation', 'closing_value'
    ]
    list_filter = ['period', 'asset__category', 'created_at']
    search_fields = ['asset__asset_code', 'asset__asset_name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'period'
    
    fieldsets = (
        ('Entry Information', {
            'fields': ('schedule', 'asset', 'period')
        }),
        ('Values', {
            'fields': ('opening_value', 'depreciation_amount', 'accumulated_depreciation', 'closing_value')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('schedule', 'asset', 'asset__category')
    
    def has_add_permission(self, request):
        # Only allow adding through the schedule calculation process
        return False


@admin.register(DepreciationSettings)
class DepreciationSettingsAdmin(admin.ModelAdmin):
    list_display = ['default_depreciation_expense_account', 'default_accumulated_depreciation_account', 'auto_post_to_gl', 'require_approval']
    list_editable = ['auto_post_to_gl', 'require_approval']
    
    fieldsets = (
        ('Default Accounts', {
            'fields': ('default_depreciation_expense_account', 'default_accumulated_depreciation_account')
        }),
        ('Calculation Settings', {
            'fields': ('auto_post_to_gl', 'require_approval', 'minimum_depreciation_amount')
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one settings instance
        if DepreciationSettings.objects.exists():
            return False
        return super().has_add_permission(request)
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        else:
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)
