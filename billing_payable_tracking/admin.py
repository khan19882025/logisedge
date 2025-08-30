from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Vendor, Bill, BillHistory, BillReminder


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'email', 'tax_id']
    list_editable = ['is_active']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'email', 'phone')
        }),
        ('Address & Tax', {
            'fields': ('address', 'tax_id')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class BillHistoryInline(admin.TabularInline):
    model = BillHistory
    extra = 0
    readonly_fields = ['action', 'user', 'timestamp', 'description']
    can_delete = False
    max_num = 10
    
    def has_add_permission(self, request, obj=None):
        return False


class BillReminderInline(admin.TabularInline):
    model = BillReminder
    extra = 0
    readonly_fields = ['reminder_type', 'sent_date', 'recipient_email', 'sent_successfully']
    can_delete = False
    max_num = 5
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = [
        'bill_no', 'vendor', 'bill_date', 'due_date', 'amount', 
        'status_badge', 'confirmed_badge', 'days_until_due_display', 'created_by'
    ]
    list_filter = [
        'status', 'confirmed', 'bill_date', 'due_date', 'created_at', 'vendor'
    ]
    search_fields = ['bill_no', 'vendor__name', 'notes']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'is_overdue', 'days_until_due', 
        'is_due_today', 'is_due_soon'
    ]
    list_per_page = 25
    date_hierarchy = 'due_date'
    inlines = [BillHistoryInline, BillReminderInline]
    
    fieldsets = (
        ('Bill Information', {
            'fields': ('vendor', 'bill_no', 'bill_date', 'due_date', 'amount')
        }),
        ('Status & Payment', {
            'fields': ('status', 'confirmed', 'paid_date', 'paid_amount')
        }),
        ('Additional Information', {
            'fields': ('notes', 'attachment')
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
        ('System Properties', {
            'fields': ('id', 'is_overdue', 'days_until_due', 'is_due_today', 'is_due_soon'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """Display status with color coding"""
        colors = {
            'pending': 'warning',
            'paid': 'success',
            'overdue': 'danger'
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def confirmed_badge(self, obj):
        """Display confirmed status with badge"""
        if obj.confirmed:
            return format_html('<span class="badge bg-success">✓ Confirmed</span>')
        return format_html('<span class="badge bg-warning">⚠ Unconfirmed</span>')
    confirmed_badge.short_description = 'Confirmed'
    
    def days_until_due_display(self, obj):
        """Display days until due with color coding"""
        days = obj.days_until_due
        if obj.status == 'paid':
            return format_html('<span class="text-success">Paid</span>')
        elif days is None:
            return '-'
        elif days < 0:
            return format_html(
                '<span class="text-danger">Overdue by {} days</span>',
                abs(days)
            )
        elif days == 0:
            return format_html('<span class="text-warning">Due Today</span>')
        elif days <= 7:
            return format_html(
                '<span class="text-warning">Due in {} days</span>',
                days
            )
        else:
            return format_html(
                '<span class="text-muted">Due in {} days</span>',
                days
            )
    days_until_due_display.short_description = 'Due Status'
    
    def save_model(self, request, obj, form, change):
        """Set created_by and updated_by fields"""
        if not change:  # Creating new object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
        
        # Create history entry
        action = 'updated' if change else 'created'
        BillHistory.objects.create(
            bill=obj,
            action=action,
            user=request.user,
            description=f'Bill {action} via admin interface'
        )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('vendor', 'created_by', 'updated_by')
    
    actions = ['mark_as_paid', 'mark_as_confirmed', 'mark_as_overdue']
    
    def mark_as_paid(self, request, queryset):
        """Mark selected bills as paid"""
        updated = 0
        for bill in queryset.filter(status__in=['pending', 'overdue']):
            bill.mark_as_paid(user=request.user)
            BillHistory.objects.create(
                bill=bill,
                action='paid',
                user=request.user,
                description='Marked as paid via admin bulk action'
            )
            updated += 1
        
        self.message_user(
            request,
            f'{updated} bills were successfully marked as paid.'
        )
    mark_as_paid.short_description = 'Mark selected bills as paid'
    
    def mark_as_confirmed(self, request, queryset):
        """Mark selected bills as confirmed"""
        updated = 0
        for bill in queryset.filter(confirmed=False):
            bill.confirm_bill(user=request.user)
            BillHistory.objects.create(
                bill=bill,
                action='confirmed',
                user=request.user,
                description='Confirmed via admin bulk action'
            )
            updated += 1
        
        self.message_user(
            request,
            f'{updated} bills were successfully confirmed.'
        )
    mark_as_confirmed.short_description = 'Mark selected bills as confirmed'
    
    def mark_as_overdue(self, request, queryset):
        """Mark selected bills as overdue"""
        updated = 0
        for bill in queryset.filter(status='pending'):
            if bill.is_overdue:
                bill.mark_as_overdue(user=request.user)
                BillHistory.objects.create(
                    bill=bill,
                    action='overdue',
                    user=request.user,
                    description='Marked as overdue via admin bulk action'
                )
                updated += 1
        
        self.message_user(
            request,
            f'{updated} bills were successfully marked as overdue.'
        )
    mark_as_overdue.short_description = 'Mark overdue bills as overdue'


@admin.register(BillHistory)
class BillHistoryAdmin(admin.ModelAdmin):
    list_display = ['bill', 'action', 'user', 'timestamp', 'description']
    list_filter = ['action', 'timestamp', 'user']
    search_fields = ['bill__bill_no', 'bill__vendor__name', 'description']
    readonly_fields = ['bill', 'action', 'user', 'timestamp', 'description', 'old_values', 'new_values']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(BillReminder)
class BillReminderAdmin(admin.ModelAdmin):
    list_display = [
        'bill', 'reminder_type', 'sent_date', 'recipient_email', 
        'sent_successfully_badge'
    ]
    list_filter = ['reminder_type', 'sent_successfully', 'sent_date']
    search_fields = ['bill__bill_no', 'bill__vendor__name', 'recipient_email']
    readonly_fields = [
        'bill', 'reminder_type', 'sent_date', 'recipient_email', 
        'sent_successfully', 'error_message'
    ]
    date_hierarchy = 'sent_date'
    
    def sent_successfully_badge(self, obj):
        """Display sent status with badge"""
        if obj.sent_successfully:
            return format_html('<span class="badge bg-success">✓ Sent</span>')
        return format_html('<span class="badge bg-danger">✗ Failed</span>')
    sent_successfully_badge.short_description = 'Status'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
