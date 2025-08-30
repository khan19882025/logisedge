from django.contrib import admin
from .models import BankTransfer, BankTransferAudit, BankTransferTemplate

@admin.register(BankTransfer)
class BankTransferAdmin(admin.ModelAdmin):
    list_display = ['transfer_number', 'transfer_date', 'from_account', 'to_account', 'amount', 'currency', 'status', 'created_by', 'created_at']
    list_filter = ['status', 'transfer_type', 'transfer_date', 'currency', 'created_at']
    search_fields = ['transfer_number', 'reference_number', 'narration']
    readonly_fields = ['transfer_number', 'converted_amount', 'created_at', 'updated_at', 'completed_at', 'cancelled_at']
    date_hierarchy = 'transfer_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('transfer_number', 'transfer_date', 'transfer_type', 'reference_number', 'narration')
        }),
        ('Account Information', {
            'fields': ('from_account', 'to_account')
        }),
        ('Financial Information', {
            'fields': ('amount', 'currency', 'exchange_rate', 'converted_amount')
        }),
        ('Status Information', {
            'fields': ('status', 'completed_at', 'cancelled_at')
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at', 'completed_by', 'cancelled_by'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('from_account', 'to_account', 'currency', 'created_by', 'completed_by', 'cancelled_by')


@admin.register(BankTransferAudit)
class BankTransferAuditAdmin(admin.ModelAdmin):
    list_display = ['transfer', 'action', 'user', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['transfer__transfer_number', 'description', 'user__username']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('transfer', 'user')


@admin.register(BankTransferTemplate)
class BankTransferTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'from_account', 'to_account', 'default_amount', 'default_currency', 'is_active', 'created_by']
    list_filter = ['is_active', 'default_currency', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Default Values', {
            'fields': ('from_account', 'to_account', 'default_amount', 'default_currency', 'default_narration')
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('from_account', 'to_account', 'default_currency', 'created_by')
