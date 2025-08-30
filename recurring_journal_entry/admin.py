from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import RecurringEntry, RecurringEntryLine, GeneratedEntry


class RecurringEntryLineInline(admin.TabularInline):
    model = RecurringEntryLine
    extra = 2
    fields = ['account', 'description', 'debit', 'credit', 'order']
    readonly_fields = ['order']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('account')


class GeneratedEntryInline(admin.TabularInline):
    model = GeneratedEntry
    extra = 0
    readonly_fields = ['journal_entry', 'posting_date', 'generated_at', 'generated_by']
    can_delete = False
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('journal_entry', 'generated_by')


@admin.register(RecurringEntry)
class RecurringEntryAdmin(admin.ModelAdmin):
    list_display = [
        'template_name', 'journal_type', 'frequency', 'start_date', 
        'status', 'total_debit', 'total_credit', 'auto_post', 'created_by'
    ]
    list_filter = [
        'status', 'journal_type', 'frequency', 'auto_post', 
        'start_date', 'created_at', 'currency', 'fiscal_year'
    ]
    search_fields = ['template_name', 'narration']
    readonly_fields = [
        'total_debit', 'total_credit', 'created_at', 'updated_at', 
        'is_balanced', 'balance_difference'
    ]
    date_hierarchy = 'start_date'
    inlines = [RecurringEntryLineInline, GeneratedEntryInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('template_name', 'journal_type', 'narration')
        }),
        ('Scheduling', {
            'fields': ('start_date', 'end_date', 'number_of_occurrences', 'frequency', 'posting_day', 'custom_day')
        }),
        ('Financial Information', {
            'fields': ('currency', 'fiscal_year', 'total_debit', 'total_credit')
        }),
        ('Settings', {
            'fields': ('auto_post', 'status', 'is_balanced', 'balance_difference')
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
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


@admin.register(RecurringEntryLine)
class RecurringEntryLineAdmin(admin.ModelAdmin):
    list_display = [
        'recurring_entry_link', 'account', 'description_short', 
        'debit', 'credit', 'amount', 'is_debit'
    ]
    list_filter = ['recurring_entry__status', 'account__account_type', 'created_at']
    search_fields = [
        'recurring_entry__template_name', 'account__account_code', 
        'account__name', 'description'
    ]
    readonly_fields = ['created_at', 'updated_at', 'amount', 'is_debit', 'is_credit']
    
    def recurring_entry_link(self, obj):
        if obj.recurring_entry:
            url = reverse('admin:recurring_journal_entry_recurringentry_change', args=[obj.recurring_entry.id])
            return format_html('<a href="{}">{}</a>', url, obj.recurring_entry.template_name)
        return '-'
    recurring_entry_link.short_description = 'Recurring Entry'
    
    def description_short(self, obj):
        return obj.description[:30] + '...' if len(obj.description) > 30 else obj.description
    description_short.short_description = 'Description'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('recurring_entry', 'account')


@admin.register(GeneratedEntry)
class GeneratedEntryAdmin(admin.ModelAdmin):
    list_display = [
        'recurring_entry_link', 'journal_entry_link', 'posting_date', 
        'generated_at', 'generated_by'
    ]
    list_filter = ['posting_date', 'generated_at', 'recurring_entry__status']
    search_fields = [
        'recurring_entry__template_name', 'journal_entry__voucher_number'
    ]
    readonly_fields = ['generated_at']
    date_hierarchy = 'posting_date'
    
    def recurring_entry_link(self, obj):
        if obj.recurring_entry:
            url = reverse('admin:recurring_journal_entry_recurringentry_change', args=[obj.recurring_entry.id])
            return format_html('<a href="{}">{}</a>', url, obj.recurring_entry.template_name)
        return '-'
    recurring_entry_link.short_description = 'Recurring Entry'
    
    def journal_entry_link(self, obj):
        if obj.journal_entry:
            url = reverse('admin:manual_journal_entry_journalentry_change', args=[obj.journal_entry.id])
            return format_html('<a href="{}">{}</a>', url, obj.journal_entry.voucher_number)
        return '-'
    journal_entry_link.short_description = 'Journal Entry'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('recurring_entry', 'journal_entry', 'generated_by')
