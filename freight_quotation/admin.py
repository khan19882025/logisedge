from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Customer, CargoType, Incoterm, ChargeType, FreightQuotation,
    QuotationCharge, QuotationAttachment, QuotationHistory
)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'country', 'is_active', 'created_at']
    list_filter = ['is_active', 'country', 'created_at']
    search_fields = ['name', 'email', 'phone', 'address']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']


@admin.register(CargoType)
class CargoTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    ordering = ['name']


@admin.register(Incoterm)
class IncotermAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'description', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name', 'description']
    list_editable = ['is_active']
    ordering = ['code']


@admin.register(ChargeType)
class ChargeTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    ordering = ['name']


class QuotationChargeInline(admin.TabularInline):
    model = QuotationCharge
    extra = 1
    fields = ['charge_type', 'description', 'currency', 'rate', 'unit', 'quantity', 'total_amount']
    readonly_fields = ['total_amount']


class QuotationAttachmentInline(admin.TabularInline):
    model = QuotationAttachment
    extra = 1
    fields = ['file', 'filename', 'description', 'uploaded_by', 'uploaded_at']
    readonly_fields = ['filename', 'uploaded_by', 'uploaded_at']


class QuotationHistoryInline(admin.TabularInline):
    model = QuotationHistory
    extra = 0
    readonly_fields = ['action', 'user', 'timestamp', 'notes']
    can_delete = False
    max_num = 10

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(FreightQuotation)
class FreightQuotationAdmin(admin.ModelAdmin):
    list_display = [
        'quotation_number', 'customer', 'mode_of_transport', 'origin', 
        'destination', 'status', 'total_amount', 'currency', 'created_at'
    ]
    list_filter = [
        'status', 'mode_of_transport', 'cargo_type', 'currency', 
        'created_at', 'quotation_date'
    ]
    search_fields = [
        'quotation_number', 'customer__name', 'origin', 'destination',
        'cargo_details'
    ]
    readonly_fields = [
        'quotation_number', 'created_by', 'created_at', 'updated_at',
        'sent_at', 'accepted_at', 'rejected_at', 'total_amount', 
        'vat_amount', 'grand_total'
    ]
    list_editable = ['status']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('quotation_number', 'quotation_date', 'validity_date', 'status')
        }),
        ('Customer Information', {
            'fields': ('customer',)
        }),
        ('Transport Details', {
            'fields': ('mode_of_transport', 'origin', 'destination', 'transit_time_estimate')
        }),
        ('Cargo Details', {
            'fields': ('cargo_type', 'cargo_details', 'weight', 'volume', 'packages')
        }),
        ('Terms and Conditions', {
            'fields': ('incoterm', 'remarks', 'internal_notes')
        }),
        ('Financial Information', {
            'fields': ('currency', 'vat_percentage', 'total_amount', 'vat_amount', 'grand_total')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at', 'sent_at', 'accepted_at', 'rejected_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [QuotationChargeInline, QuotationAttachmentInline, QuotationHistoryInline]
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'customer', 'cargo_type', 'incoterm', 'created_by'
        )


@admin.register(QuotationCharge)
class QuotationChargeAdmin(admin.ModelAdmin):
    list_display = [
        'quotation', 'charge_type', 'description', 'currency', 
        'rate', 'unit', 'quantity', 'total_amount'
    ]
    list_filter = ['charge_type', 'currency', 'unit', 'created_at']
    search_fields = ['quotation__quotation_number', 'charge_type__name', 'description']
    readonly_fields = ['total_amount', 'created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(QuotationAttachment)
class QuotationAttachmentAdmin(admin.ModelAdmin):
    list_display = ['quotation', 'filename', 'description', 'uploaded_by', 'uploaded_at']
    list_filter = ['uploaded_at', 'uploaded_by']
    search_fields = ['quotation__quotation_number', 'filename', 'description']
    readonly_fields = ['uploaded_by', 'uploaded_at']
    ordering = ['-uploaded_at']


@admin.register(QuotationHistory)
class QuotationHistoryAdmin(admin.ModelAdmin):
    list_display = ['quotation', 'action', 'user', 'timestamp', 'notes']
    list_filter = ['action', 'user', 'timestamp']
    search_fields = ['quotation__quotation_number', 'notes']
    readonly_fields = ['quotation', 'action', 'user', 'timestamp', 'notes']
    ordering = ['-timestamp']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
