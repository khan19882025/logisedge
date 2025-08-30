from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import ContraEntry, ContraEntryDetail, ContraEntryAudit
from django.utils import timezone


class ContraEntryDetailInline(admin.TabularInline):
    model = ContraEntryDetail
    extra = 2
    fields = ['account', 'debit', 'credit']
    readonly_fields = []
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('account')


class ContraEntryAuditInline(admin.TabularInline):
    model = ContraEntryAudit
    extra = 0
    readonly_fields = ['action', 'description', 'user', 'timestamp']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ContraEntry)
class ContraEntryAdmin(admin.ModelAdmin):
    list_display = [
        'voucher_number', 'date', 'narration_short', 'total_debit', 
        'total_credit', 'status', 'created_by', 'created_at'
    ]
    list_filter = ['status', 'date', 'created_at']
    search_fields = ['voucher_number', 'narration', 'reference_number']
    readonly_fields = [
        'voucher_number', 'created_by', 'created_at', 'updated_by', 
        'updated_at', 'posted_by', 'posted_at', 'total_debit', 'total_credit', 'is_balanced'
    ]
    inlines = [ContraEntryDetailInline, ContraEntryAuditInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('voucher_number', 'date', 'narration', 'reference_number')
        }),
        ('Status', {
            'fields': ('status', 'posted_at', 'posted_by')
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Summary', {
            'fields': ('total_debit', 'total_credit', 'is_balanced'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['post_entries', 'cancel_entries']
    
    def narration_short(self, obj):
        return obj.narration[:50] + '...' if len(obj.narration) > 50 else obj.narration
    narration_short.short_description = 'Narration'
    
    def total_debit(self, obj):
        return f"AED {obj.total_debit:,.2f}"
    total_debit.short_description = 'Total Debit'
    
    def total_credit(self, obj):
        return f"AED {obj.total_credit:,.2f}"
    total_credit.short_description = 'Total Credit'
    
    def is_balanced(self, obj):
        if obj.is_balanced:
            return format_html('<span style="color: green;">✓ Balanced</span>')
        else:
            return format_html('<span style="color: red;">✗ Not Balanced</span>')
    is_balanced.short_description = 'Balanced'
    
    def post_entries(self, request, queryset):
        posted_count = 0
        for entry in queryset:
            if entry.can_post:
                entry.status = 'posted'
                entry.posted_at = timezone.now()
                entry.posted_by = request.user
                entry.save()
                
                # Create audit trail
                ContraEntryAudit.objects.create(
                    contra_entry=entry,
                    action='posted',
                    description=f'Contra entry posted by {request.user.get_full_name()} via admin',
                    user=request.user
                )
                posted_count += 1
        
        if posted_count == 1:
            self.message_user(request, f'{posted_count} contra entry posted successfully.')
        else:
            self.message_user(request, f'{posted_count} contra entries posted successfully.')
    post_entries.short_description = 'Post selected contra entries'
    
    def cancel_entries(self, request, queryset):
        cancelled_count = 0
        for entry in queryset:
            if entry.can_cancel:
                entry.status = 'cancelled'
                entry.save()
                
                # Create audit trail
                ContraEntryAudit.objects.create(
                    contra_entry=entry,
                    action='cancelled',
                    description=f'Contra entry cancelled by {request.user.get_full_name()} via admin',
                    user=request.user
                )
                cancelled_count += 1
        
        if cancelled_count == 1:
            self.message_user(request, f'{cancelled_count} contra entry cancelled successfully.')
        else:
            self.message_user(request, f'{cancelled_count} contra entries cancelled successfully.')
    cancel_entries.short_description = 'Cancel selected contra entries'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        else:  # Updating existing object
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'created_by', 'updated_by', 'posted_by'
        ).prefetch_related('entries__account')


@admin.register(ContraEntryDetail)
class ContraEntryDetailAdmin(admin.ModelAdmin):
    list_display = [
        'contra_entry_link', 'account', 'debit', 'credit', 'amount', 'entry_type'
    ]
    list_filter = ['contra_entry__status', 'account__account_type']
    search_fields = ['contra_entry__voucher_number', 'account__name', 'account__account_code']
    readonly_fields = ['contra_entry_link']
    
    def contra_entry_link(self, obj):
        url = reverse('admin:contra_entry_contraentry_change', args=[obj.contra_entry.id])
        return format_html('<a href="{}">{}</a>', url, obj.contra_entry.voucher_number)
    contra_entry_link.short_description = 'Contra Entry'
    
    def amount(self, obj):
        return f"AED {obj.amount:,.2f}"
    amount.short_description = 'Amount'
    
    def entry_type(self, obj):
        if obj.debit:
            return format_html('<span style="color: red;">Debit</span>')
        else:
            return format_html('<span style="color: green;">Credit</span>')
    entry_type.short_description = 'Type'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'contra_entry', 'account'
        )


@admin.register(ContraEntryAudit)
class ContraEntryAuditAdmin(admin.ModelAdmin):
    list_display = [
        'contra_entry_link', 'action', 'user', 'timestamp', 'description_short'
    ]
    list_filter = ['action', 'timestamp', 'user']
    search_fields = ['contra_entry__voucher_number', 'description', 'user__username']
    readonly_fields = ['contra_entry_link', 'action', 'description', 'user', 'timestamp']
    
    def contra_entry_link(self, obj):
        url = reverse('admin:contra_entry_contraentry_change', args=[obj.contra_entry.id])
        return format_html('<a href="{}">{}</a>', url, obj.contra_entry.voucher_number)
    contra_entry_link.short_description = 'Contra Entry'
    
    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'contra_entry', 'user'
        )
