from django.contrib import admin
from .models import CashFlowStatement, CashFlowTemplate, CashFlowCategory, CashFlowItem


@admin.register(CashFlowStatement)
class CashFlowStatementAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'company', 'from_date', 'to_date', 'currency',
        'report_type', 'is_saved', 'created_by', 'created_at'
    ]
    list_filter = [
        'report_type', 'is_saved', 'created_at', 'company', 'currency'
    ]
    search_fields = ['name', 'description', 'company__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'company', 'currency')
        }),
        ('Date Range', {
            'fields': ('from_date', 'to_date', 'fiscal_year')
        }),
        ('Report Configuration', {
            'fields': ('report_type', 'export_format')
        }),
        ('Options', {
            'fields': ('include_comparative', 'include_notes', 'include_charts')
        }),
        ('Status', {
            'fields': ('is_saved', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CashFlowTemplate)
class CashFlowTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'template_type', 'is_active', 'is_public',
        'created_by', 'created_at'
    ]
    list_filter = [
        'template_type', 'is_active', 'is_public', 'created_at'
    ]
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'template_type')
        }),
        ('Configuration', {
            'fields': (
                'include_operating_activities', 'include_investing_activities',
                'include_financing_activities'
            )
        }),
        ('Custom Items', {
            'fields': (
                'custom_operating_items', 'custom_investing_items',
                'custom_financing_items'
            ),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_public', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CashFlowCategory)
class CashFlowCategoryAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category_type', 'display_order', 'is_active', 'created_at'
    ]
    list_filter = ['category_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['category_type', 'display_order', 'name']


@admin.register(CashFlowItem)
class CashFlowItemAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'item_type', 'calculation_method',
        'display_order', 'is_active', 'is_subtotal'
    ]
    list_filter = [
        'category__category_type', 'item_type', 'calculation_method',
        'is_active', 'is_subtotal', 'created_at'
    ]
    search_fields = ['name', 'category__name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['category__display_order', 'display_order', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'item_type')
        }),
        ('Configuration', {
            'fields': ('calculation_method', 'account_codes')
        }),
        ('Display Options', {
            'fields': ('display_order', 'is_active', 'is_subtotal')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    ) 