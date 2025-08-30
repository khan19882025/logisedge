from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import AdjustmentEntry, AdjustmentEntryDetail, AdjustmentEntryAudit


class AdjustmentEntryDetailInline(admin.TabularInline):
    """Inline admin for adjustment entry details"""
    model = AdjustmentEntryDetail
    extra = 2
    fields = ['account', 'debit', 'credit']
    readonly_fields = []
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('account')


class AdjustmentEntryAuditInline(admin.TabularInline):
    """Inline admin for adjustment entry audit trail"""
    model = AdjustmentEntryAudit
    extra = 0
    readonly_fields = ['action', 'description', 'user', 'timestamp']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(AdjustmentEntry)
class AdjustmentEntryAdmin(admin.ModelAdmin):
    """Admin configuration for adjustment entries"""
    list_display = [
        'voucher_number', 'date', 'adjustment_type_display', 'narration_short', 
        'total_debit_display', 'total_credit_display', 'status', 'created_by', 'created_at'
    ]
    list_filter = [
        'status', 'adjustment_type', 'date', 'created_at', 'posted_at'
    ]
    search_fields = [
        'voucher_number', 'narration', 'reference_number', 'created_by__username', 
        'created_by__first_name', 'created_by__last_name'
    ]
    readonly_fields = [
        'voucher_number', 'created_by', 'created_at', 'updated_by', 'updated_at',
        'posted_by', 'posted_at', 'total_debit_display', 'total_credit_display', 
        'is_balanced_display', 'can_post_display', 'can_edit_display', 'can_cancel_display'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('voucher_number', 'date', 'narration', 'reference_number', 'adjustment_type')
        }),
        ('Status & Workflow', {
            'fields': ('status', 'posted_at', 'posted_by')
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at')
        }),
        ('Validation', {
            'fields': ('total_debit_display', 'total_credit_display', 'is_balanced_display', 
                      'can_post_display', 'can_edit_display', 'can_cancel_display'),
            'classes': ('collapse',)
        }),
    )
    inlines = [AdjustmentEntryDetailInline, AdjustmentEntryAuditInline]
    actions = ['post_entries', 'cancel_entries', 'export_to_csv']
    date_hierarchy = 'date'
    ordering = ['-created_at']
    
    def narration_short(self, obj):
        """Display shortened narration"""
        return obj.narration[:50] + '...' if len(obj.narration) > 50 else obj.narration
    narration_short.short_description = 'Narration'
    
    def adjustment_type_display(self, obj):
        """Display adjustment type with color coding"""
        colors = {
            'prepaid_expense': '#28a745',
            'accrued_expense': '#dc3545',
            'accrued_income': '#17a2b8',
            'depreciation': '#ffc107',
            'reclassification': '#6f42c1',
            'others': '#6c757d',
        }
        color = colors.get(obj.adjustment_type, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_adjustment_type_display()
        )
    adjustment_type_display.short_description = 'Type'
    
    def total_debit_display(self, obj):
        """Display total debit amount"""
        return f"AED {obj.total_debit:,.2f}"
    total_debit_display.short_description = 'Total Debit'
    
    def total_credit_display(self, obj):
        """Display total credit amount"""
        return f"AED {obj.total_credit:,.2f}"
    total_credit_display.short_description = 'Total Credit'
    
    def is_balanced_display(self, obj):
        """Display balance status"""
        if obj.is_balanced:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">✓ Balanced</span>'
            )
        else:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">✗ Unbalanced</span>'
            )
    is_balanced_display.short_description = 'Balance Status'
    
    def can_post_display(self, obj):
        """Display if entry can be posted"""
        if obj.can_post:
            return format_html(
                '<span style="color: #28a745;">✓ Can Post</span>'
            )
        else:
            return format_html(
                '<span style="color: #dc3545;">✗ Cannot Post</span>'
            )
    can_post_display.short_description = 'Can Post'
    
    def can_edit_display(self, obj):
        """Display if entry can be edited"""
        if obj.can_edit:
            return format_html(
                '<span style="color: #28a745;">✓ Can Edit</span>'
            )
        else:
            return format_html(
                '<span style="color: #dc3545;">✗ Cannot Edit</span>'
            )
    can_edit_display.short_description = 'Can Edit'
    
    def can_cancel_display(self, obj):
        """Display if entry can be cancelled"""
        if obj.can_cancel:
            return format_html(
                '<span style="color: #28a745;">✓ Can Cancel</span>'
            )
        else:
            return format_html(
                '<span style="color: #dc3545;">✗ Cannot Cancel</span>'
            )
    can_cancel_display.short_description = 'Can Cancel'
    
    def post_entries(self, request, queryset):
        """Admin action to post selected entries"""
        from django.utils import timezone
        
        posted_count = 0
        for entry in queryset:
            if entry.can_post:
                entry.status = 'posted'
                entry.posted_at = timezone.now()
                entry.posted_by = request.user
                entry.save()
                
                # Create audit trail
                AdjustmentEntryAudit.objects.create(
                    adjustment_entry=entry,
                    action='posted',
                    description=f'Adjustment entry posted by admin user {request.user.get_full_name()}',
                    user=request.user
                )
                posted_count += 1
        
        if posted_count > 0:
            self.message_user(
                request, 
                f'Successfully posted {posted_count} adjustment entry(ies).'
            )
        else:
            self.message_user(
                request, 
                'No adjustment entries could be posted. Please check if they meet the posting criteria.',
                level='WARNING'
            )
    post_entries.short_description = 'Post selected adjustment entries'
    
    def cancel_entries(self, request, queryset):
        """Admin action to cancel selected entries"""
        cancelled_count = 0
        for entry in queryset:
            if entry.can_cancel:
                entry.status = 'cancelled'
                entry.save()
                
                # Create audit trail
                AdjustmentEntryAudit.objects.create(
                    adjustment_entry=entry,
                    action='cancelled',
                    description=f'Adjustment entry cancelled by admin user {request.user.get_full_name()}',
                    user=request.user
                )
                cancelled_count += 1
        
        if cancelled_count > 0:
            self.message_user(
                request, 
                f'Successfully cancelled {cancelled_count} adjustment entry(ies).'
            )
        else:
            self.message_user(
                request, 
                'No adjustment entries could be cancelled. Please check if they meet the cancellation criteria.',
                level='WARNING'
            )
    cancel_entries.short_description = 'Cancel selected adjustment entries'
    
    def export_to_csv(self, request, queryset):
        """Admin action to export selected entries to CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="adjustment_entries.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Voucher Number', 'Date', 'Adjustment Type', 'Narration', 'Reference Number',
            'Status', 'Total Debit', 'Total Credit', 'Created By', 'Created At'
        ])
        
        for entry in queryset:
            writer.writerow([
                entry.voucher_number,
                entry.date,
                entry.get_adjustment_type_display(),
                entry.narration,
                entry.reference_number or '',
                entry.get_status_display(),
                entry.total_debit,
                entry.total_credit,
                entry.created_by.get_full_name(),
                entry.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response
    export_to_csv.short_description = 'Export selected entries to CSV'
    
    def save_model(self, request, obj, form, change):
        """Override save to set created_by and updated_by"""
        if not change:  # Creating new object
            obj.created_by = request.user
        else:  # Updating existing object
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related(
            'created_by', 'updated_by', 'posted_by'
        )


@admin.register(AdjustmentEntryDetail)
class AdjustmentEntryDetailAdmin(admin.ModelAdmin):
    """Admin configuration for adjustment entry details"""
    list_display = [
        'adjustment_entry_link', 'account', 'debit_display', 'credit_display', 
        'amount_display', 'entry_type'
    ]
    list_filter = ['adjustment_entry__status', 'adjustment_entry__adjustment_type', 'account']
    search_fields = [
        'adjustment_entry__voucher_number', 'account__name', 'account__account_code'
    ]
    readonly_fields = ['adjustment_entry', 'amount_display', 'entry_type']
    
    def adjustment_entry_link(self, obj):
        """Display adjustment entry as a link"""
        url = reverse('admin:adjustment_entry_adjustmententry_change', args=[obj.adjustment_entry.id])
        return format_html('<a href="{}">{}</a>', url, obj.adjustment_entry.voucher_number)
    adjustment_entry_link.short_description = 'Adjustment Entry'
    
    def debit_display(self, obj):
        """Display debit amount"""
        if obj.debit:
            return f"AED {obj.debit:,.2f}"
        return '-'
    debit_display.short_description = 'Debit'
    
    def credit_display(self, obj):
        """Display credit amount"""
        if obj.credit:
            return f"AED {obj.credit:,.2f}"
        return '-'
    credit_display.short_description = 'Credit'
    
    def amount_display(self, obj):
        """Display amount (debit or credit)"""
        return f"AED {obj.amount:,.2f}"
    amount_display.short_description = 'Amount'
    
    def entry_type(self, obj):
        """Display entry type with color coding"""
        if obj.entry_type == 'debit':
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">Debit</span>'
            )
        else:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">Credit</span>'
            )
    entry_type.short_description = 'Type'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related(
            'adjustment_entry', 'account'
        )


@admin.register(AdjustmentEntryAudit)
class AdjustmentEntryAuditAdmin(admin.ModelAdmin):
    """Admin configuration for adjustment entry audit trail"""
    list_display = [
        'adjustment_entry_link', 'action', 'user', 'timestamp', 'description_short'
    ]
    list_filter = ['action', 'timestamp', 'user']
    search_fields = [
        'adjustment_entry__voucher_number', 'user__username', 'user__first_name', 
        'user__last_name', 'description'
    ]
    readonly_fields = ['adjustment_entry', 'action', 'description', 'user', 'timestamp']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    
    def adjustment_entry_link(self, obj):
        """Display adjustment entry as a link"""
        url = reverse('admin:adjustment_entry_adjustmententry_change', args=[obj.adjustment_entry.id])
        return format_html('<a href="{}">{}</a>', url, obj.adjustment_entry.voucher_number)
    adjustment_entry_link.short_description = 'Adjustment Entry'
    
    def description_short(self, obj):
        """Display shortened description"""
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'
    
    def has_add_permission(self, request):
        """Disable adding audit entries manually"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing audit entries"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable deleting audit entries"""
        return False
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related(
            'adjustment_entry', 'user'
        )
