from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    TaxJurisdiction, TaxType, TaxRate, ProductTaxCategory,
    CustomerTaxProfile, SupplierTaxProfile, TaxTransaction, 
    TaxSettingsAuditLog, VATReport
)


@admin.register(TaxJurisdiction)
class TaxJurisdictionAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'jurisdiction_type', 'parent_jurisdiction', 'is_active', 'created_at']
    list_filter = ['jurisdiction_type', 'is_active', 'created_at']
    search_fields = ['name', 'code']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'jurisdiction_type', 'parent_jurisdiction')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(TaxType)
class TaxTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'tax_type', 'is_active', 'created_at']
    list_filter = ['tax_type', 'is_active', 'created_at']
    search_fields = ['name', 'code', 'description']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'tax_type', 'description')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(TaxRate)
class TaxRateAdmin(admin.ModelAdmin):
    list_display = ['name', 'rate_percentage', 'tax_type', 'jurisdiction', 'effective_from', 'effective_to', 'is_current', 'is_active']
    list_filter = ['tax_type', 'jurisdiction', 'rounding_method', 'is_active', 'effective_from', 'effective_to']
    search_fields = ['name', 'tax_type__name', 'jurisdiction__name']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by', 'is_current']
    date_hierarchy = 'effective_from'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'rate_percentage', 'tax_type', 'jurisdiction')
        }),
        ('Effective Dates', {
            'fields': ('effective_from', 'effective_to')
        }),
        ('Settings', {
            'fields': ('rounding_method', 'description')
        }),
        ('Status', {
            'fields': ('is_active', 'is_current')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ProductTaxCategory)
class ProductTaxCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'default_tax_rate', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code', 'description']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'description')
        }),
        ('Tax Settings', {
            'fields': ('default_tax_rate',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CustomerTaxProfile)
class CustomerTaxProfileAdmin(admin.ModelAdmin):
    list_display = ['customer', 'tax_registration_number', 'default_tax_rate', 'is_tax_exempt', 'created_at']
    list_filter = ['is_tax_exempt', 'created_at']
    search_fields = ['customer__name', 'tax_registration_number', 'tax_exemption_number']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('customer',)
        }),
        ('Tax Registration', {
            'fields': ('tax_registration_number', 'tax_exemption_number')
        }),
        ('Tax Settings', {
            'fields': ('default_tax_rate', 'is_tax_exempt', 'tax_exemption_reason')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SupplierTaxProfile)
class SupplierTaxProfileAdmin(admin.ModelAdmin):
    list_display = ['supplier_name', 'supplier_code', 'tax_registration_number', 'default_tax_rate', 'is_tax_exempt', 'created_at']
    list_filter = ['is_tax_exempt', 'created_at']
    search_fields = ['supplier_name', 'supplier_code', 'tax_registration_number', 'tax_exemption_number']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    fieldsets = (
        ('Supplier Information', {
            'fields': ('supplier_name', 'supplier_code')
        }),
        ('Tax Registration', {
            'fields': ('tax_registration_number', 'tax_exemption_number')
        }),
        ('Tax Settings', {
            'fields': ('default_tax_rate', 'is_tax_exempt', 'tax_exemption_reason')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(TaxTransaction)
class TaxTransactionAdmin(admin.ModelAdmin):
    list_display = ['document_type', 'document_number', 'transaction_type', 'tax_rate', 'taxable_amount', 'tax_amount', 'total_amount', 'currency', 'document_date']
    list_filter = ['transaction_type', 'currency', 'document_date', 'created_at']
    search_fields = ['document_type', 'document_number', 'customer__name', 'supplier_name']
    readonly_fields = ['created_at', 'created_by']
    date_hierarchy = 'document_date'
    
    fieldsets = (
        ('Document Information', {
            'fields': ('transaction_type', 'document_type', 'document_number', 'document_date')
        }),
        ('Parties', {
            'fields': ('customer', 'supplier_name')
        }),
        ('Tax Information', {
            'fields': ('tax_rate', 'taxable_amount', 'tax_amount', 'total_amount', 'currency')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(TaxSettingsAuditLog)
class TaxSettingsAuditLogAdmin(admin.ModelAdmin):
    list_display = ['model_name', 'object_id', 'action', 'field_name', 'user', 'timestamp']
    list_filter = ['action', 'model_name', 'timestamp']
    search_fields = ['model_name', 'object_id', 'field_name', 'user__username']
    readonly_fields = ['model_name', 'object_id', 'action', 'field_name', 'old_value', 'new_value', 'timestamp', 'user', 'ip_address']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Audit Information', {
            'fields': ('model_name', 'object_id', 'action')
        }),
        ('Field Changes', {
            'fields': ('field_name', 'old_value', 'new_value')
        }),
        ('User Information', {
            'fields': ('user', 'ip_address', 'timestamp')
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(VATReport)
class VATReportAdmin(admin.ModelAdmin):
    list_display = ['report_name', 'report_period', 'start_date', 'end_date', 'net_vat_payable', 'currency', 'is_filed', 'created_at']
    list_filter = ['report_period', 'currency', 'is_filed', 'created_at']
    search_fields = ['report_name']
    readonly_fields = ['created_at', 'created_by', 'filed_date', 'filed_by', 'net_vat_payable_calculated']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Report Information', {
            'fields': ('report_name', 'report_period', 'start_date', 'end_date', 'currency')
        }),
        ('Financial Summary', {
            'fields': ('total_sales', 'total_purchases', 'total_sales_tax', 'total_purchase_tax', 'net_vat_payable', 'net_vat_payable_calculated')
        }),
        ('Filing Status', {
            'fields': ('is_filed', 'filed_date', 'filed_by')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if not change:  # Creating new object
                instance.created_by = request.user
            instance.save()
        formset.save_m2m()


# Custom admin site configuration
admin.site.site_header = "LogisEdge Tax Settings Administration"
admin.site.site_title = "Tax Settings Admin"
admin.site.index_title = "Welcome to Tax Settings Administration"
