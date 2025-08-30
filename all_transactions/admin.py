from django.contrib import admin
from .models import TransactionView

@admin.register(TransactionView)
class TransactionViewAdmin(admin.ModelAdmin):
    list_display = ['transaction_date', 'transaction_type', 'document_number', 'debit_account', 'credit_account', 'amount', 'status']
    list_filter = ['transaction_type', 'status', 'transaction_date', 'posted_by']
    search_fields = ['document_number', 'narration', 'debit_account__account_name', 'credit_account__account_name']
    readonly_fields = ['transaction_date', 'transaction_type', 'document_number', 'debit_account', 'credit_account', 'amount', 'narration', 'posted_by', 'status']
    ordering = ['-transaction_date']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False 