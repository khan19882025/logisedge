from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    TransactionTagging, DefaultCostCenterMapping, TransactionTaggingRule,
    TransactionTaggingAuditLog, TransactionTaggingReport
)


@admin.register(TransactionTagging)
class TransactionTaggingAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_id', 'reference_number', 'transaction_type', 'cost_center_link',
        'amount', 'currency', 'transaction_date', 'status', 'is_active', 'created_by'
    ]
    list_filter = [
        'transaction_type', 'status', 'is_active', 'transaction_date', 'currency',
        'cost_center__department'
    ]
    search_fields = [
        'transaction_id', 'reference_number', 'description', 'cost_center__code',
        'cost_center__name'
    ]
    readonly_fields = ['transaction_id', 'created_at', 'updated_at', 'created_by', 'updated_by']
    date_hierarchy = 'transaction_date'
    ordering = ['-transaction_date', '-created_at']
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('transaction_id', 'reference_number', 'transaction_type', 'transaction_date')
        }),
        ('Cost Center & Amount', {
            'fields': ('cost_center', 'amount', 'currency')
        }),
        ('Details', {
            'fields': ('description', 'status', 'is_active')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def cost_center_link(self, obj):
        if obj.cost_center:
            url = reverse('admin:cost_center_management_costcenter_change', args=[obj.cost_center.id])
            return format_html('<a href="{}">{}</a>', url, obj.cost_center)
        return '-'
    cost_center_link.short_description = 'Cost Center'
    cost_center_link.admin_order_field = 'cost_center__code'
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(DefaultCostCenterMapping)
class DefaultCostCenterMappingAdmin(admin.ModelAdmin):
    list_display = [
        'mapping_type', 'entity_name', 'entity_id', 'cost_center_link', 'is_active'
    ]
    list_filter = ['mapping_type', 'is_active', 'created_at']
    search_fields = ['entity_name', 'entity_id', 'cost_center__code', 'cost_center__name']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    ordering = ['mapping_type', 'entity_name']
    
    fieldsets = (
        ('Mapping Information', {
            'fields': ('mapping_type', 'entity_id', 'entity_name')
        }),
        ('Cost Center', {
            'fields': ('cost_center', 'is_active')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def cost_center_link(self, obj):
        if obj.cost_center:
            url = reverse('admin:cost_center_management_costcenter_change', args=[obj.cost_center.id])
            return format_html('<a href="{}">{}</a>', url, obj.cost_center)
        return '-'
    cost_center_link.short_description = 'Cost Center'
    cost_center_link.admin_order_field = 'cost_center__code'
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(TransactionTaggingRule)
class TransactionTaggingRuleAdmin(admin.ModelAdmin):
    list_display = [
        'rule_name', 'rule_type', 'transaction_type', 'cost_center_link',
        'priority', 'is_active'
    ]
    list_filter = ['rule_type', 'transaction_type', 'is_active', 'created_at']
    search_fields = ['rule_name', 'cost_center__code', 'cost_center__name']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    ordering = ['priority', 'rule_name']
    
    fieldsets = (
        ('Rule Information', {
            'fields': ('rule_name', 'rule_type', 'transaction_type', 'account_type')
        }),
        ('Cost Center & Priority', {
            'fields': ('cost_center', 'priority', 'is_active')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def cost_center_link(self, obj):
        if obj.cost_center:
            url = reverse('admin:cost_center_management_costcenter_change', args=[obj.cost_center.id])
            return format_html('<a href="{}">{}</a>', url, obj.cost_center)
        return '-'
    cost_center_link.short_description = 'Cost Center'
    cost_center_link.admin_order_field = 'cost_center__code'
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(TransactionTaggingAuditLog)
class TransactionTaggingAuditLogAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_tagging', 'action', 'user', 'timestamp', 'ip_address'
    ]
    list_filter = ['action', 'timestamp', 'user']
    search_fields = [
        'transaction_tagging__transaction_id', 'transaction_tagging__reference_number',
        'user__username', 'user__first_name', 'user__last_name'
    ]
    readonly_fields = [
        'transaction_tagging', 'action', 'field_name', 'old_value', 'new_value',
        'timestamp', 'user', 'ip_address'
    ]
    ordering = ['-timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Audit Information', {
            'fields': ('transaction_tagging', 'action', 'user', 'timestamp', 'ip_address')
        }),
        ('Change Details', {
            'fields': ('field_name', 'old_value', 'new_value'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(TransactionTaggingReport)
class TransactionTaggingReportAdmin(admin.ModelAdmin):
    list_display = [
        'report_name', 'report_type', 'cost_center_link', 'start_date', 'end_date',
        'generated_by', 'generated_at'
    ]
    list_filter = ['report_type', 'generated_at', 'cost_center__department']
    search_fields = [
        'report_name', 'cost_center__code', 'cost_center__name',
        'generated_by__username', 'generated_by__first_name', 'generated_by__last_name'
    ]
    readonly_fields = ['generated_at', 'generated_by', 'report_data']
    ordering = ['-generated_at']
    date_hierarchy = 'generated_at'
    
    fieldsets = (
        ('Report Information', {
            'fields': ('report_name', 'report_type', 'cost_center', 'start_date', 'end_date')
        }),
        ('Report Data', {
            'fields': ('report_data',),
            'classes': ('collapse',)
        }),
        ('Generation Information', {
            'fields': ('generated_at', 'generated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def cost_center_link(self, obj):
        if obj.cost_center:
            url = reverse('admin:cost_center_management_costcenter_change', args=[obj.cost_center.id])
            return format_html('<a href="{}">{}</a>', url, obj.cost_center)
        return 'All Cost Centers'
    cost_center_link.short_description = 'Cost Center'
    cost_center_link.admin_order_field = 'cost_center__code'
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.generated_by = request.user
        super().save_model(request, obj, form, change)
