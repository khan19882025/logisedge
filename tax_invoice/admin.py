from django.contrib import admin
from .models import TaxInvoice, TaxInvoiceItem, TaxInvoiceTemplate, TaxInvoiceSettings, TaxInvoiceExport


class TaxInvoiceItemInline(admin.TabularInline):
    model = TaxInvoiceItem
    extra = 1
    fields = ['description', 'quantity', 'unit_price', 'vat_percentage', 'taxable_amount', 'vat_amount', 'total_amount']


class TaxInvoiceExportInline(admin.TabularInline):
    model = TaxInvoiceExport
    extra = 0
    readonly_fields = ['exported_at', 'exported_by']
    can_delete = False


@admin.register(TaxInvoice)
class TaxInvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'customer_name', 'invoice_date', 'due_date', 'status', 'grand_total', 'currency']
    list_filter = ['status', 'currency', 'invoice_date', 'due_date']
    search_fields = ['invoice_number', 'customer_name', 'company_name']
    readonly_fields = ['invoice_number', 'subtotal', 'total_vat', 'grand_total', 'created_at', 'created_by', 'updated_at', 'updated_by']
    date_hierarchy = 'invoice_date'
    inlines = [TaxInvoiceItemInline, TaxInvoiceExportInline]
    
    fieldsets = (
        ('Invoice Information', {
            'fields': ('invoice_number', 'invoice_date', 'due_date', 'currency', 'status')
        }),
        ('Company Details', {
            'fields': ('company_name', 'company_address', 'company_trn', 'company_phone', 'company_email', 'company_website')
        }),
        ('Customer Details', {
            'fields': ('customer_name', 'customer_address', 'customer_trn', 'customer_phone', 'customer_email')
        }),
        ('Invoice Totals', {
            'fields': ('subtotal', 'total_vat', 'grand_total'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('notes', 'terms_conditions', 'payment_instructions'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        else:
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(TaxInvoiceItem)
class TaxInvoiceItemAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'description', 'quantity', 'unit_price', 'vat_percentage', 'total_amount']
    list_filter = ['vat_percentage', 'product_category']
    search_fields = ['description', 'product_code', 'invoice__invoice_number']
    readonly_fields = ['taxable_amount', 'vat_amount', 'total_amount']


@admin.register(TaxInvoiceTemplate)
class TaxInvoiceTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'is_active', 'created_at', 'created_by']
    list_filter = ['template_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'created_by']
    
    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'template_type', 'description', 'is_active')
        }),
        ('Template Settings', {
            'fields': ('include_logo', 'include_qr_code', 'include_bank_details', 'include_terms')
        }),
        ('Styling Options', {
            'fields': ('primary_color', 'secondary_color', 'font_family')
        }),
        ('Content', {
            'fields': ('header_text', 'footer_text', 'terms_conditions')
        }),
        ('Metadata', {
            'fields': ('created_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(TaxInvoiceSettings)
class TaxInvoiceSettingsAdmin(admin.ModelAdmin):
    list_display = ['default_company_name', 'default_currency', 'default_vat_rate', 'updated_at']
    readonly_fields = ['updated_at', 'updated_by']
    
    fieldsets = (
        ('Company Defaults', {
            'fields': ('default_company_name', 'default_company_address', 'default_company_trn', 'default_company_phone', 'default_company_email', 'default_company_website')
        }),
        ('Invoice Defaults', {
            'fields': ('default_currency', 'default_payment_terms', 'default_vat_rate', 'default_template')
        }),
        ('Export Settings', {
            'fields': ('pdf_orientation', 'pdf_page_size')
        }),
        ('Email Settings', {
            'fields': ('email_subject_template', 'email_body_template')
        }),
        ('Validation Settings', {
            'fields': ('require_customer_trn', 'require_vat_number', 'validate_vat_rates')
        }),
        ('Metadata', {
            'fields': ('updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(TaxInvoiceExport)
class TaxInvoiceExportAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'export_format', 'exported_at', 'exported_by']
    list_filter = ['export_format', 'exported_at']
    search_fields = ['invoice__invoice_number']
    readonly_fields = ['invoice', 'export_format', 'file_path', 'file_size', 'exported_at', 'exported_by']
    
    def has_add_permission(self, request):
        return False  # Exports are created automatically
