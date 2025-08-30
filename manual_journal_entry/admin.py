from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import JournalEntry, JournalEntryLine


class JournalEntryLineInline(admin.TabularInline):
    model = JournalEntryLine
    extra = 2
    fields = ['account', 'description', 'debit', 'credit', 'order']
    readonly_fields = ['order']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('account')


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = [
        'voucher_number', 'date', 'narration_short', 'total_debit', 
        'total_credit', 'status', 'created_by', 'created_at'
    ]
    list_filter = ['status', 'date', 'created_at', 'currency', 'fiscal_year']
    search_fields = ['voucher_number', 'narration', 'reference_number']
    readonly_fields = [
        'voucher_number', 'total_debit', 'total_credit', 'created_at', 
        'updated_at', 'posted_at', 'is_balanced', 'balance_difference'
    ]
    date_hierarchy = 'date'
    inlines = [JournalEntryLineInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('voucher_number', 'date', 'reference_number', 'narration')
        }),
        ('Financial Information', {
            'fields': ('currency', 'fiscal_year', 'total_debit', 'total_credit')
        }),
        ('Status', {
            'fields': ('status', 'is_balanced', 'balance_difference')
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at', 'posted_by', 'posted_at'),
            'classes': ('collapse',)
        }),
    )
    
    def narration_short(self, obj):
        return obj.narration[:50] + '...' if len(obj.narration) > 50 else obj.narration
    narration_short.short_description = 'Narration'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        else:
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if not change:
                instance.created_by = request.user
            else:
                instance.updated_by = request.user
            instance.save()
        formset.save_m2m()


@admin.register(JournalEntryLine)
class JournalEntryLineAdmin(admin.ModelAdmin):
    list_display = [
        'journal_entry_link', 'account', 'description_short', 
        'debit', 'credit', 'amount', 'is_debit'
    ]
    list_filter = ['journal_entry__status', 'account__account_type', 'created_at']
    search_fields = [
        'journal_entry__voucher_number', 'account__account_code', 
        'account__name', 'description'
    ]
    readonly_fields = ['created_at', 'updated_at', 'amount', 'is_debit', 'is_credit']
    
    def journal_entry_link(self, obj):
        if obj.journal_entry:
            url = reverse('admin:manual_journal_entry_journalentry_change', args=[obj.journal_entry.id])
            return format_html('<a href="{}">{}</a>', url, obj.journal_entry.voucher_number)
        return '-'
    journal_entry_link.short_description = 'Journal Entry'
    
    def description_short(self, obj):
        return obj.description[:30] + '...' if len(obj.description) > 30 else obj.description
    description_short.short_description = 'Description'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('journal_entry', 'account') 