from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import ChequeRegister, ChequeStatusHistory, ChequeAlert


@admin.register(ChequeRegister)
class ChequeRegisterAdmin(admin.ModelAdmin):
    list_display = [
        'cheque_number', 'cheque_date', 'cheque_type', 'get_party_name',
        'amount', 'bank_account', 'status_badge', 'is_post_dated', 'is_overdue'
    ]
    list_filter = [
        'cheque_type', 'status', 'party_type', 'bank_account', 'is_post_dated',
        'cheque_date', 'created_at'
    ]
    search_fields = [
        'cheque_number', 'customer__customer_name', 'supplier__supplier_name',
        'remarks', 'related_transaction'
    ]
    readonly_fields = [
        'created_by', 'updated_by', 'created_at', 'updated_at',
        'is_post_dated', 'is_overdue', 'days_overdue'
    ]
    date_hierarchy = 'cheque_date'
    ordering = ['-cheque_date', '-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('cheque_number', 'cheque_date', 'cheque_type')
        }),
        ('Party Information', {
            'fields': ('party_type', 'customer', 'supplier')
        }),
        ('Financial Information', {
            'fields': ('amount', 'bank_account', 'related_transaction', 'transaction_reference')
        }),
        ('Status Information', {
            'fields': ('status', 'clearing_date', 'stop_payment_date')
        }),
        ('Additional Information', {
            'fields': ('remarks', 'is_post_dated')
        }),
        ('Audit Information', {
            'fields': ('company', 'created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_party_name(self, obj):
        return obj.get_party_name()
    get_party_name.short_description = 'Party Name'
    get_party_name.admin_order_field = 'customer__customer_name'
    
    def status_badge(self, obj):
        colors = {
            'pending': 'warning',
            'cleared': 'success',
            'bounced': 'danger',
            'cancelled': 'secondary',
            'stopped': 'info'
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def is_overdue(self, obj):
        if obj.is_overdue:
            return format_html(
                '<span class="badge bg-danger">Overdue ({})</span>',
                obj.days_overdue
            )
        return format_html('<span class="badge bg-success">On Time</span>')
    is_overdue.short_description = 'Due Status'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        else:  # Updating existing object
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'customer', 'supplier', 'bank_account', 'company'
        )


@admin.register(ChequeStatusHistory)
class ChequeStatusHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'cheque', 'old_status', 'new_status', 'changed_by', 'changed_at'
    ]
    list_filter = ['old_status', 'new_status', 'changed_at']
    search_fields = ['cheque__cheque_number', 'remarks']
    readonly_fields = ['changed_by', 'changed_at']
    ordering = ['-changed_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'cheque', 'changed_by'
        )


@admin.register(ChequeAlert)
class ChequeAlertAdmin(admin.ModelAdmin):
    list_display = [
        'cheque', 'alert_type', 'is_read', 'created_at'
    ]
    list_filter = ['alert_type', 'is_read', 'created_at']
    search_fields = ['cheque__cheque_number', 'message']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} alerts marked as read.')
    mark_as_read.short_description = "Mark selected alerts as read"
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} alerts marked as unread.')
    mark_as_unread.short_description = "Mark selected alerts as unread"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('cheque')
