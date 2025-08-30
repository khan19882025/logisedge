from django.contrib import admin
from .models import DepositSlip, DepositSlipItem, DepositSlipAudit

@admin.register(DepositSlip)
class DepositSlipAdmin(admin.ModelAdmin):
    list_display = ['slip_number', 'deposit_date', 'deposit_to', 'total_amount', 'status', 'created_by', 'created_at']
    list_filter = ['status', 'deposit_date', 'deposit_to', 'created_at']
    search_fields = ['slip_number', 'reference_number', 'narration']
    readonly_fields = ['slip_number', 'total_amount', 'created_at', 'updated_at', 'submitted_at', 'confirmed_at']
    date_hierarchy = 'deposit_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('slip_number', 'deposit_date', 'deposit_to', 'reference_number', 'narration')
        }),
        ('Financial Information', {
            'fields': ('total_amount', 'currency')
        }),
        ('Status Information', {
            'fields': ('status', 'submitted_at', 'confirmed_at')
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at', 'submitted_by', 'confirmed_by'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('deposit_to', 'created_by', 'submitted_by', 'confirmed_by')


@admin.register(DepositSlipItem)
class DepositSlipItemAdmin(admin.ModelAdmin):
    list_display = ['deposit_slip', 'receipt_voucher', 'amount', 'created_at']
    list_filter = ['created_at', 'receipt_voucher__receipt_mode']
    search_fields = ['deposit_slip__slip_number', 'receipt_voucher__voucher_number', 'receipt_voucher__payer_name']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('deposit_slip', 'receipt_voucher', 'created_by')


@admin.register(DepositSlipAudit)
class DepositSlipAuditAdmin(admin.ModelAdmin):
    list_display = ['deposit_slip', 'action', 'user', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['deposit_slip__slip_number', 'description', 'user__username']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('deposit_slip', 'user')
