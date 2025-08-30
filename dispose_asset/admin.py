from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count
from django.utils import timezone

from .models import (
    DisposalRequest, DisposalItem, DisposalDocument, DisposalApproval,
    DisposalType, ApprovalLevel, DisposalAuditLog, DisposalNotification,
    DisposalJournalEntry, DisposalJournalLine
)


@admin.register(DisposalType)
class DisposalTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(ApprovalLevel)
class ApprovalLevelAdmin(admin.ModelAdmin):
    list_display = ['name', 'level', 'required_role', 'min_amount', 'max_amount', 'is_active']
    list_filter = ['is_active', 'level']
    search_fields = ['name', 'required_role']
    ordering = ['level']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'level', 'description')
        }),
        ('Approval Settings', {
            'fields': ('required_role', 'min_amount', 'max_amount')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


class DisposalItemInline(admin.TabularInline):
    model = DisposalItem
    extra = 0
    readonly_fields = ['asset', 'final_disposal_value', 'gain_loss_amount']
    fields = ['asset', 'disposal_value', 'reason', 'is_approved', 'is_disposed']
    
    def final_disposal_value(self, obj):
        return f"AED {obj.final_disposal_value:,.2f}"
    final_disposal_value.short_description = 'Final Value'
    
    def gain_loss_amount(self, obj):
        amount = obj.gain_loss_amount
        color = 'green' if amount >= 0 else 'red'
        return format_html('<span style="color: {};">AED {:,.2f}</span>', color, amount)
    gain_loss_amount.short_description = 'Gain/Loss'


class DisposalDocumentInline(admin.TabularInline):
    model = DisposalDocument
    extra = 0
    readonly_fields = ['file_type', 'file_size', 'uploaded_by', 'uploaded_at']
    fields = ['title', 'file', 'file_type', 'file_size', 'uploaded_by', 'uploaded_at']


class DisposalApprovalInline(admin.TabularInline):
    model = DisposalApproval
    extra = 0
    readonly_fields = ['approver', 'approved_at', 'ip_address']
    fields = ['approval_level', 'action', 'comments', 'approver', 'approved_at']


class DisposalJournalEntryInline(admin.TabularInline):
    model = DisposalJournalEntry
    extra = 0
    readonly_fields = ['entry_date', 'reference', 'total_debit', 'total_credit', 'is_posted']
    fields = ['entry_date', 'reference', 'description', 'total_debit', 'total_credit', 'is_posted']


@admin.register(DisposalRequest)
class DisposalRequestAdmin(admin.ModelAdmin):
    list_display = [
        'request_id', 'title', 'disposal_type', 'status', 'is_batch',
        'total_asset_value', 'disposal_value', 'gain_loss_amount',
        'created_by', 'created_at'
    ]
    list_filter = [
        'status', 'disposal_type', 'is_batch', 'disposal_date',
        'created_at', 'submitted_at', 'disposed_at'
    ]
    search_fields = [
        'request_id', 'title', 'description', 'reason',
        'disposal_items__asset__asset_name',
        'disposal_items__asset__asset_code'
    ]
    readonly_fields = [
        'request_id', 'total_asset_value', 'gain_loss_amount',
        'is_gain', 'is_loss', 'created_by', 'created_at',
        'updated_by', 'updated_at', 'submitted_at', 'disposed_at'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    inlines = [
        DisposalItemInline,
        DisposalDocumentInline,
        DisposalApprovalInline,
        DisposalJournalEntryInline,
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('request_id', 'title', 'description', 'is_batch')
        }),
        ('Disposal Details', {
            'fields': ('disposal_type', 'disposal_date', 'disposal_value', 'reason', 'remarks')
        }),
        ('Status & Workflow', {
            'fields': ('status', 'current_approval_level')
        }),
        ('Financial Accounts', {
            'fields': ('asset_account', 'disposal_account', 'bank_account'),
            'classes': ('collapse',)
        }),
        ('Financial Summary', {
            'fields': ('total_asset_value', 'gain_loss_amount', 'is_gain', 'is_loss'),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': (
                'created_by', 'created_at', 'updated_by', 'updated_at',
                'submitted_at', 'disposed_at'
            ),
            'classes': ('collapse',)
        }),
        ('Reversal Information', {
            'fields': ('reversed_by', 'reversed_at', 'reversal_reason'),
            'classes': ('collapse',)
        }),
    )
    
    def total_asset_value(self, obj):
        return f"AED {obj.total_asset_value:,.2f}"
    total_asset_value.short_description = 'Total Asset Value'
    
    def disposal_value(self, obj):
        return f"AED {obj.disposal_value:,.2f}"
    disposal_value.short_description = 'Disposal Value'
    
    def gain_loss_amount(self, obj):
        amount = obj.gain_loss_amount
        color = 'green' if amount >= 0 else 'red'
        return format_html('<span style="color: {};">AED {:,.2f}</span>', color, amount)
    gain_loss_amount.short_description = 'Gain/Loss'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'disposal_type', 'created_by', 'asset_account', 'disposal_account'
        ).prefetch_related('disposal_items__asset')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        else:  # Updating existing object
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(DisposalItem)
class DisposalItemAdmin(admin.ModelAdmin):
    list_display = [
        'asset', 'disposal_request', 'final_disposal_value',
        'gain_loss_amount', 'is_approved', 'is_disposed'
    ]
    list_filter = [
        'is_approved', 'is_disposed', 'disposal_request__disposal_type',
        'disposal_request__status', 'created_at'
    ]
    search_fields = [
        'asset__asset_name', 'asset__asset_code',
        'disposal_request__request_id', 'disposal_request__title'
    ]
    readonly_fields = [
        'final_disposal_value', 'gain_loss_amount', 'created_at', 'updated_at'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Asset Information', {
            'fields': ('disposal_request', 'asset')
        }),
        ('Disposal Details', {
            'fields': ('disposal_value', 'reason', 'remarks')
        }),
        ('Status', {
            'fields': ('is_approved', 'is_disposed', 'disposed_at')
        }),
        ('Financial Summary', {
            'fields': ('final_disposal_value', 'gain_loss_amount'),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def final_disposal_value(self, obj):
        return f"AED {obj.final_disposal_value:,.2f}"
    final_disposal_value.short_description = 'Final Disposal Value'
    
    def gain_loss_amount(self, obj):
        amount = obj.gain_loss_amount
        color = 'green' if amount >= 0 else 'red'
        return format_html('<span style="color: {};">AED {:,.2f}</span>', color, amount)
    gain_loss_amount.short_description = 'Gain/Loss'


@admin.register(DisposalDocument)
class DisposalDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'disposal_request', 'file_type', 'file_size', 'uploaded_by', 'uploaded_at']
    list_filter = ['file_type', 'uploaded_at', 'disposal_request__status']
    search_fields = ['title', 'disposal_request__request_id', 'disposal_request__title']
    readonly_fields = ['file_type', 'file_size', 'uploaded_by', 'uploaded_at']
    date_hierarchy = 'uploaded_at'
    ordering = ['-uploaded_at']


@admin.register(DisposalApproval)
class DisposalApprovalAdmin(admin.ModelAdmin):
    list_display = [
        'disposal_request', 'approval_level', 'action', 'approver', 'approved_at'
    ]
    list_filter = [
        'action', 'approval_level', 'approved_at',
        'disposal_request__status', 'disposal_request__disposal_type'
    ]
    search_fields = [
        'disposal_request__request_id', 'disposal_request__title',
        'approver__username', 'approver__first_name', 'approver__last_name'
    ]
    readonly_fields = ['approver', 'approved_at', 'ip_address']
    date_hierarchy = 'approved_at'
    ordering = ['-approved_at']


class DisposalJournalLineInline(admin.TabularInline):
    model = DisposalJournalLine
    extra = 0
    readonly_fields = ['line_number']
    fields = ['line_number', 'account', 'description', 'debit_amount', 'credit_amount', 'asset']


@admin.register(DisposalJournalEntry)
class DisposalJournalEntryAdmin(admin.ModelAdmin):
    list_display = [
        'reference', 'disposal_request', 'entry_date', 'total_debit',
        'total_credit', 'is_posted', 'is_reversed'
    ]
    list_filter = [
        'is_posted', 'is_reversed', 'entry_date', 'created_at',
        'disposal_request__status'
    ]
    search_fields = [
        'reference', 'description', 'disposal_request__request_id'
    ]
    readonly_fields = [
        'total_debit', 'total_credit', 'created_by', 'created_at',
        'posted_by', 'posted_at', 'reversed_by', 'reversed_at'
    ]
    date_hierarchy = 'entry_date'
    ordering = ['-entry_date', '-created_at']
    
    inlines = [DisposalJournalLineInline]
    
    fieldsets = (
        ('Journal Entry Details', {
            'fields': ('disposal_request', 'entry_date', 'reference', 'description')
        }),
        ('Financial Impact', {
            'fields': ('total_debit', 'total_credit')
        }),
        ('Status', {
            'fields': ('is_posted', 'posted_at', 'posted_by')
        }),
        ('Reversal Information', {
            'fields': ('is_reversed', 'reversed_at', 'reversed_by'),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DisposalJournalLine)
class DisposalJournalLineAdmin(admin.ModelAdmin):
    list_display = [
        'journal_entry', 'line_number', 'account', 'description',
        'debit_amount', 'credit_amount'
    ]
    list_filter = [
        'account', 'journal_entry__entry_date',
        'journal_entry__disposal_request__status'
    ]
    search_fields = [
        'description', 'account__account_name',
        'journal_entry__reference'
    ]
    readonly_fields = ['line_number']
    ordering = ['journal_entry', 'line_number']


@admin.register(DisposalAuditLog)
class DisposalAuditLogAdmin(admin.ModelAdmin):
    list_display = [
        'disposal_request', 'action', 'user', 'timestamp', 'ip_address'
    ]
    list_filter = [
        'action', 'timestamp', 'disposal_request__status',
        'disposal_request__disposal_type'
    ]
    search_fields = [
        'description', 'user__username', 'user__first_name',
        'disposal_request__request_id'
    ]
    readonly_fields = [
        'disposal_request', 'action', 'description', 'user',
        'ip_address', 'user_agent', 'timestamp', 'additional_data'
    ]
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    
    fieldsets = (
        ('Audit Information', {
            'fields': ('disposal_request', 'action', 'description', 'timestamp')
        }),
        ('User Information', {
            'fields': ('user', 'ip_address', 'user_agent')
        }),
        ('Additional Data', {
            'fields': ('additional_data',),
            'classes': ('collapse',)
        }),
    )


@admin.register(DisposalNotification)
class DisposalNotificationAdmin(admin.ModelAdmin):
    list_display = [
        'disposal_request', 'notification_type', 'recipient',
        'is_read', 'is_sent', 'created_at'
    ]
    list_filter = [
        'notification_type', 'is_read', 'is_sent', 'created_at',
        'disposal_request__status'
    ]
    search_fields = [
        'title', 'message', 'recipient__username',
        'disposal_request__request_id'
    ]
    readonly_fields = [
        'disposal_request', 'notification_type', 'title', 'message',
        'recipient', 'is_read', 'read_at', 'is_sent', 'sent_at', 'created_at'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']


# Custom admin site configuration
admin.site.site_header = "LogisEdge ERP - Disposal Asset Management"
admin.site.site_title = "Disposal Asset Admin"
admin.site.index_title = "Disposal Asset Administration"
