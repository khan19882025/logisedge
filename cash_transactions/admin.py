from django.contrib import admin
from .models import CashTransaction, CashTransactionAudit, CashBalance

@admin.register(CashTransaction)
class CashTransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_number', 'transaction_date', 'transaction_type', 'category', 
                   'amount', 'currency', 'location', 'status', 'created_by', 'created_at']
    list_filter = ['transaction_type', 'category', 'status', 'currency', 'location', 'created_at']
    search_fields = ['transaction_number', 'reference_number', 'narration', 'location']
    readonly_fields = ['transaction_number', 'created_by', 'created_at', 'updated_by', 'updated_at', 
                      'posted_by', 'posted_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('transaction_number', 'transaction_date', 'transaction_type', 'category')
        }),
        ('Account Information', {
            'fields': ('from_account', 'to_account')
        }),
        ('Financial Information', {
            'fields': ('amount', 'currency')
        }),
        ('Additional Information', {
            'fields': ('location', 'reference_number', 'narration', 'attachment')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at', 'posted_by', 'posted_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        else:  # Updating existing object
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CashTransactionAudit)
class CashTransactionAuditAdmin(admin.ModelAdmin):
    list_display = ['transaction', 'action', 'user', 'timestamp']
    list_filter = ['action', 'user', 'timestamp']
    search_fields = ['transaction__transaction_number', 'description', 'user__username']
    readonly_fields = ['transaction', 'action', 'description', 'user', 'timestamp']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False  # Audit records should only be created automatically


@admin.register(CashBalance)
class CashBalanceAdmin(admin.ModelAdmin):
    list_display = ['location', 'currency', 'balance', 'last_updated']
    list_filter = ['currency', 'last_updated']
    search_fields = ['location']
    readonly_fields = ['last_updated']
    
    def has_delete_permission(self, request, obj=None):
        return False  # Prevent deletion of balance records
