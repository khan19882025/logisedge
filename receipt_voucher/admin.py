from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import ReceiptVoucher, ReceiptVoucherAttachment, ReceiptVoucherAudit
from django.utils import timezone


class ReceiptVoucherAttachmentInline(admin.TabularInline):
    """Inline admin for receipt voucher attachments"""
    model = ReceiptVoucherAttachment
    extra = 0
    readonly_fields = ['filename', 'file_type', 'file_size', 'uploaded_by', 'uploaded_at']
    fields = ['file', 'filename', 'file_type', 'file_size', 'uploaded_by', 'uploaded_at']
    
    def has_add_permission(self, request, obj=None):
        return True
    
    def has_delete_permission(self, request, obj=None):
        return True


class ReceiptVoucherAuditInline(admin.TabularInline):
    """Inline admin for receipt voucher audit trail"""
    model = ReceiptVoucherAudit
    extra = 0
    readonly_fields = ['action', 'description', 'user', 'timestamp']
    fields = ['action', 'description', 'user', 'timestamp']
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ReceiptVoucher)
class ReceiptVoucherAdmin(admin.ModelAdmin):
    """Admin configuration for ReceiptVoucher model"""
    
    list_display = [
        'voucher_number', 'voucher_date', 'payer_name', 'payer_type', 
        'amount', 'currency', 'receipt_mode', 'status', 'created_by', 'created_at'
    ]
    
    list_filter = [
        'status', 'receipt_mode', 'payer_type', 'currency', 'voucher_date', 'created_at'
    ]
    
    search_fields = [
        'voucher_number', 'payer_name', 'payer_code', 'description', 
        'reference_number', 'reference_invoices'
    ]
    
    readonly_fields = [
        'voucher_number', 'created_by', 'created_at', 'updated_by', 'updated_at',
        'approved_by', 'approved_at', 'received_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'voucher_number', 'voucher_date', 'receipt_mode', 'status'
            )
        }),
        ('Payer Information', {
            'fields': (
                'payer_type', 'payer_name', 'payer_code', 'payer_contact', 'payer_email'
            )
        }),
        ('Financial Information', {
            'fields': (
                'amount', 'currency', 'account_to_credit'
            )
        }),
        ('Additional Information', {
            'fields': (
                'description', 'reference_number', 'reference_invoices'
            )
        }),
        ('Audit Information', {
            'fields': (
                'created_by', 'created_at', 'updated_by', 'updated_at',
                'approved_by', 'approved_at', 'received_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ReceiptVoucherAttachmentInline, ReceiptVoucherAuditInline]
    
    list_per_page = 25
    
    date_hierarchy = 'voucher_date'
    
    actions = ['approve_vouchers', 'mark_as_received', 'cancel_vouchers']
    
    def approve_vouchers(self, request, queryset):
        """Admin action to approve selected vouchers"""
        count = 0
        for voucher in queryset.filter(status='draft'):
            voucher.status = 'approved'
            voucher.approved_by = request.user
            voucher.approved_at = timezone.now()
            voucher.save()
            
            # Create audit trail
            ReceiptVoucherAudit.objects.create(
                voucher=voucher,
                action='approved',
                description=f'Receipt voucher approved by admin {request.user.get_full_name()}',
                user=request.user
            )
            count += 1
        
        self.message_user(request, f'{count} receipt voucher(s) approved successfully.')
    
    approve_vouchers.short_description = "Approve selected vouchers"
    
    def mark_as_received(self, request, queryset):
        """Admin action to mark selected vouchers as received"""
        count = 0
        for voucher in queryset.filter(status='approved'):
            voucher.status = 'received'
            voucher.received_at = timezone.now()
            voucher.save()
            
            # Create audit trail
            ReceiptVoucherAudit.objects.create(
                voucher=voucher,
                action='marked_received',
                description=f'Receipt voucher marked as received by admin {request.user.get_full_name()}',
                user=request.user
            )
            count += 1
        
        self.message_user(request, f'{count} receipt voucher(s) marked as received successfully.')
    
    mark_as_received.short_description = "Mark selected vouchers as received"
    
    def cancel_vouchers(self, request, queryset):
        """Admin action to cancel selected vouchers"""
        count = 0
        for voucher in queryset.exclude(status='received'):
            voucher.status = 'cancelled'
            voucher.save()
            
            # Create audit trail
            ReceiptVoucherAudit.objects.create(
                voucher=voucher,
                action='cancelled',
                description=f'Receipt voucher cancelled by admin {request.user.get_full_name()}',
                user=request.user
            )
            count += 1
        
        self.message_user(request, f'{count} receipt voucher(s) cancelled successfully.')
    
    cancel_vouchers.short_description = "Cancel selected vouchers"
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        else:  # Updating existing object
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ReceiptVoucherAttachment)
class ReceiptVoucherAttachmentAdmin(admin.ModelAdmin):
    """Admin configuration for ReceiptVoucherAttachment model"""
    
    list_display = [
        'filename', 'voucher_link', 'file_type', 'file_size', 
        'uploaded_by', 'uploaded_at'
    ]
    
    list_filter = ['file_type', 'uploaded_at']
    
    search_fields = ['filename', 'voucher__voucher_number']
    
    readonly_fields = [
        'filename', 'file_type', 'file_size', 'uploaded_by', 'uploaded_at'
    ]
    
    fields = [
        'voucher', 'file', 'filename', 'file_type', 'file_size', 
        'uploaded_by', 'uploaded_at'
    ]
    
    def voucher_link(self, obj):
        """Create a link to the voucher"""
        if obj.voucher:
            url = reverse('admin:receipt_voucher_receiptvoucher_change', args=[obj.voucher.id])
            return format_html('<a href="{}">{}</a>', url, obj.voucher.voucher_number)
        return '-'
    
    voucher_link.short_description = 'Voucher'
    voucher_link.admin_order_field = 'voucher__voucher_number'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ReceiptVoucherAudit)
class ReceiptVoucherAuditAdmin(admin.ModelAdmin):
    """Admin configuration for ReceiptVoucherAudit model"""
    
    list_display = [
        'voucher_link', 'action', 'user', 'timestamp', 'description'
    ]
    
    list_filter = ['action', 'timestamp']
    
    search_fields = [
        'voucher__voucher_number', 'user__username', 'user__first_name', 
        'user__last_name', 'description'
    ]
    
    readonly_fields = [
        'voucher', 'action', 'description', 'user', 'timestamp'
    ]
    
    fields = ['voucher', 'action', 'description', 'user', 'timestamp']
    
    def voucher_link(self, obj):
        """Create a link to the voucher"""
        if obj.voucher:
            url = reverse('admin:receipt_voucher_receiptvoucher_change', args=[obj.voucher.id])
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
