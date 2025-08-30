from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import PaymentVoucher, PaymentVoucherAttachment, PaymentVoucherAudit


@admin.register(PaymentVoucher)
class PaymentVoucherAdmin(admin.ModelAdmin):
    list_display = [
        'voucher_number', 'voucher_date', 'payee_name', 'payee_type', 
        'amount', 'currency', 'payment_mode', 'status', 'created_by', 'created_at'
    ]
    list_filter = [
        'status', 'payment_mode', 'payee_type', 'currency', 'voucher_date', 'created_at'
    ]
    search_fields = [
        'voucher_number', 'payee_name', 'payee_id', 'description', 
        'reference_number', 'reference_invoices'
    ]
    readonly_fields = [
        'voucher_number', 'created_at', 'updated_at', 'approved_at',
        'created_by', 'updated_by', 'approved_by'
    ]
    date_hierarchy = 'voucher_date'
    ordering = ['-voucher_date', '-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('voucher_number', 'voucher_date', 'payment_mode')
        }),
        ('Payee Information', {
            'fields': ('payee_type', 'payee_name', 'payee_id')
        }),
        ('Financial Information', {
            'fields': ('amount', 'currency', 'account_to_debit')
        }),
        ('Description & References', {
            'fields': ('description', 'reference_invoices', 'reference_number')
        }),
        ('Status & Approval', {
            'fields': ('status', 'approved_by', 'approved_at')
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'currency', 'account_to_debit', 'created_by', 'updated_by', 'approved_by'
        )
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        else:
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status in ['approved', 'paid', 'cancelled']:
            return self.readonly_fields + ('voucher_date', 'payment_mode', 'payee_type', 
                                         'payee_name', 'payee_id', 'amount', 'currency', 
                                         'account_to_debit', 'description', 'reference_invoices', 
                                         'reference_number')
        return self.readonly_fields
    
    def has_delete_permission(self, request, obj=None):
        if obj and obj.status not in ['draft']:
            return False
        return super().has_delete_permission(request, obj)
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions


@admin.register(PaymentVoucherAttachment)
class PaymentVoucherAttachmentAdmin(admin.ModelAdmin):
    list_display = [
        'voucher_link', 'file_name', 'file_type', 'uploaded_by', 'uploaded_at'
    ]
    list_filter = ['file_type', 'uploaded_at']
    search_fields = ['file_name', 'description', 'voucher__voucher_number']
    readonly_fields = ['uploaded_at', 'uploaded_by']
    ordering = ['-uploaded_at']
    
    fieldsets = (
        ('File Information', {
            'fields': ('voucher', 'file', 'file_name', 'file_type')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Upload Information', {
            'fields': ('uploaded_by', 'uploaded_at'),
            'classes': ('collapse',)
        }),
    )
    
    def voucher_link(self, obj):
        if obj.voucher:
            url = reverse('admin:payment_voucher_paymentvoucher_change', args=[obj.voucher.id])
            return format_html('<a href="{}">{}</a>', url, obj.voucher.voucher_number)
        return '-'
    voucher_link.short_description = 'Voucher'
    voucher_link.admin_order_field = 'voucher__voucher_number'
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PaymentVoucherAudit)
class PaymentVoucherAuditAdmin(admin.ModelAdmin):
    list_display = [
        'voucher_link', 'action', 'user', 'timestamp', 'ip_address'
    ]
    list_filter = ['action', 'timestamp', 'user']
    search_fields = [
        'voucher__voucher_number', 'description', 'user__username', 
        'user__first_name', 'user__last_name'
    ]
    readonly_fields = ['voucher', 'action', 'description', 'old_values', 
                      'new_values', 'timestamp', 'user', 'ip_address']
    ordering = ['-timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Audit Information', {
            'fields': ('voucher', 'action', 'description')
        }),
        ('User Information', {
            'fields': ('user', 'ip_address', 'timestamp')
        }),
        ('Data Changes', {
            'fields': ('old_values', 'new_values'),
            'classes': ('collapse',)
        }),
    )
    
    def voucher_link(self, obj):
        if obj.voucher:
            url = reverse('admin:payment_voucher_paymentvoucher_change', args=[obj.voucher.id])
            return format_html('<a href="{}">{}</a>', url, obj.voucher.voucher_number)
        return '-'
    voucher_link.short_description = 'Voucher'
    voucher_link.admin_order_field = 'voucher__voucher_number'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
