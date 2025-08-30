from django.contrib import admin
from django.utils.html import format_html
from .models import JournalEntry, JournalEntryLine


class JournalEntryLineInline(admin.TabularInline):
    model = JournalEntryLine
    extra = 2
    fields = ['account', 'description', 'debit_amount', 'credit_amount', 'reference']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = [
        'journal_number', 'date', 'reference', 'description', 
        'total_debit', 'total_credit', 'status', 'company', 'fiscal_year', 'created_by'
    ]
    list_filter = ['status', 'date', 'company', 'fiscal_year', 'created_by']
    search_fields = ['journal_number', 'reference', 'description']
    readonly_fields = ['journal_number', 'total_debit', 'total_credit', 'created_at', 'updated_at', 'posted_at']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('journal_number', 'date', 'reference', 'description', 'notes')
        }),
        ('Financial Information', {
            'fields': ('total_debit', 'total_credit', 'status')
        }),
        ('Relationships', {
            'fields': ('company', 'fiscal_year', 'created_by', 'posted_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'posted_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [JournalEntryLineInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'company', 'fiscal_year', 'created_by', 'posted_by'
        ).prefetch_related('lines__account')
    
    def has_add_permission(self, request):
        return True
    
    def has_change_permission(self, request, obj=None):
        if obj and obj.status != 'draft':
            return False
        return True
    
    def has_delete_permission(self, request, obj=None):
        if obj and obj.status != 'draft':
            return False
        return True


@admin.register(JournalEntryLine)
class JournalEntryLineAdmin(admin.ModelAdmin):
    list_display = [
        'journal_entry', 'account', 'description', 'debit_amount', 
        'credit_amount', 'reference', 'created_at'
    ]
    list_filter = ['journal_entry__status', 'account__account_type', 'created_at']
    search_fields = ['journal_entry__journal_number', 'account__account_name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Line Information', {
            'fields': ('journal_entry', 'account', 'description', 'reference')
        }),
        ('Amounts', {
            'fields': ('debit_amount', 'credit_amount')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'journal_entry', 'account__account_type'
        )
