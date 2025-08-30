from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    LeaveType, LeavePolicy, LeaveRequest, LeaveBalance, 
    LeaveApproval, LeaveNotification, LeaveCalendar, LeaveEncashment
)


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'color_display', 'is_active', 'requires_approval', 'max_days_per_year', 'created_at']
    list_filter = ['is_active', 'requires_approval', 'is_paid', 'can_carry_forward', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active', 'requires_approval']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'color')
        }),
        ('Settings', {
            'fields': ('is_active', 'requires_approval', 'is_paid')
        }),
        ('Limits', {
            'fields': ('max_days_per_year', 'max_consecutive_days', 'min_notice_days')
        }),
        ('Advanced', {
            'fields': ('can_carry_forward', 'max_carry_forward_days')
        }),
    )
    
    def color_display(self, obj):
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 4px;">{}</span>',
            obj.color, obj.color
        )
    color_display.short_description = 'Color'


@admin.register(LeavePolicy)
class LeavePolicyAdmin(admin.ModelAdmin):
    list_display = ['name', 'probation_period_months', 'annual_leave_days', 'sick_leave_days', 'is_active', 'created_at']
    list_filter = ['is_active', 'encashment_allowed', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description')
        }),
        ('Leave Days', {
            'fields': ('annual_leave_days', 'sick_leave_days', 'casual_leave_days', 
                      'maternity_leave_days', 'paternity_leave_days')
        }),
        ('Settings', {
            'fields': ('probation_period_months', 'carry_forward_percentage', 'is_active')
        }),
        ('Encashment', {
            'fields': ('encashment_allowed', 'encashment_percentage')
        }),
    )


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ['request_id', 'employee_name', 'leave_type', 'date_range', 'total_days', 
                   'status', 'priority', 'submitted_at']
    list_filter = ['status', 'priority', 'leave_type', 'is_half_day', 'is_emergency', 'submitted_at']
    search_fields = ['request_id', 'employee__first_name', 'employee__last_name', 'reason']
    readonly_fields = ['request_id', 'submitted_at', 'updated_at']
    ordering = ['-submitted_at']
    
    fieldsets = (
        ('Request Information', {
            'fields': ('request_id', 'employee', 'leave_type', 'reason')
        }),
        ('Leave Details', {
            'fields': ('start_date', 'end_date', 'total_days', 'is_half_day', 'half_day_type', 'is_emergency')
        }),
        ('Settings', {
            'fields': ('priority', 'status', 'attachment')
        }),
        ('Approval', {
            'fields': ('current_approver', 'approved_by', 'approved_at', 'approval_comments')
        }),
        ('Timestamps', {
            'fields': ('submitted_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def employee_name(self, obj):
        return obj.employee.get_full_name()
    employee_name.short_description = 'Employee'
    
    def date_range(self, obj):
        return f"{obj.start_date} to {obj.end_date}"
    date_range.short_description = 'Date Range'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('employee', 'leave_type', 'approved_by')


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ['employee_name', 'leave_type', 'year', 'allocated_days', 'used_days', 
                   'available_days', 'utilization_percentage']
    list_filter = ['year', 'leave_type', 'created_at']
    search_fields = ['employee__first_name', 'employee__last_name', 'leave_type__name']
    ordering = ['-year', 'employee__first_name']
    
    fieldsets = (
        ('Employee & Leave Type', {
            'fields': ('employee', 'leave_type', 'year')
        }),
        ('Balance Details', {
            'fields': ('allocated_days', 'used_days', 'carried_forward_days', 'encashed_days')
        }),
        ('Calculated Fields', {
            'fields': ('available_days', 'total_balance'),
            'classes': ('collapse',)
        }),
    )
    
    def employee_name(self, obj):
        return obj.employee.get_full_name()
    employee_name.short_description = 'Employee'
    
    def utilization_percentage(self, obj):
        return f"{obj.utilization_percentage:.1f}%"
    utilization_percentage.short_description = 'Utilization %'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('employee', 'leave_type')


@admin.register(LeaveApproval)
class LeaveApprovalAdmin(admin.ModelAdmin):
    list_display = ['leave_request_link', 'approver_name', 'action', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['leave_request__request_id', 'approver__first_name', 'approver__last_name', 'comments']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Approval Details', {
            'fields': ('leave_request', 'approver', 'action', 'comments')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def leave_request_link(self, obj):
        url = reverse('admin:leave_management_leaverequest_change', args=[obj.leave_request.id])
        return format_html('<a href="{}">{}</a>', url, obj.leave_request.request_id)
    leave_request_link.short_description = 'Leave Request'
    
    def approver_name(self, obj):
        return obj.approver.get_full_name()
    approver_name.short_description = 'Approver'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('leave_request', 'approver')


@admin.register(LeaveNotification)
class LeaveNotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient_name', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['recipient__first_name', 'recipient__last_name', 'title', 'message']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Notification Details', {
            'fields': ('recipient', 'notification_type', 'title', 'message')
        }),
        ('Related Information', {
            'fields': ('related_leave_request', 'is_read')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def recipient_name(self, obj):
        return obj.recipient.get_full_name()
    recipient_name.short_description = 'Recipient'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('recipient', 'related_leave_request')


@admin.register(LeaveCalendar)
class LeaveCalendarAdmin(admin.ModelAdmin):
    list_display = ['employee_name', 'date', 'leave_request_link', 'is_half_day', 'half_day_type']
    list_filter = ['date', 'is_half_day', 'half_day_type', 'created_at']
    search_fields = ['employee__first_name', 'employee__last_name']
    ordering = ['-date']
    
    fieldsets = (
        ('Calendar Entry', {
            'fields': ('employee', 'leave_request', 'date')
        }),
        ('Half Day Details', {
            'fields': ('is_half_day', 'half_day_type')
        }),
    )
    
    def employee_name(self, obj):
        return obj.employee.get_full_name()
    employee_name.short_description = 'Employee'
    
    def leave_request_link(self, obj):
        url = reverse('admin:leave_management_leaverequest_change', args=[obj.leave_request.id])
        return format_html('<a href="{}">{}</a>', url, obj.leave_request.request_id)
    leave_request_link.short_description = 'Leave Request'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('employee', 'leave_request')


@admin.register(LeaveEncashment)
class LeaveEncashmentAdmin(admin.ModelAdmin):
    list_display = ['employee_name', 'leave_type', 'encashment_year', 'days_to_encash', 
                   'encashment_amount', 'status', 'created_at']
    list_filter = ['status', 'encashment_year', 'leave_type', 'created_at']
    search_fields = ['employee__first_name', 'employee__last_name', 'reason']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Encashment Details', {
            'fields': ('employee', 'leave_type', 'encashment_year', 'days_to_encash', 'reason')
        }),
        ('Financial', {
            'fields': ('encashment_amount', 'status')
        }),
        ('Approval', {
            'fields': ('approved_by', 'approved_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def employee_name(self, obj):
        return obj.employee.get_full_name()
    employee_name.short_description = 'Employee'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('employee', 'leave_type', 'approved_by')


# Custom admin site configuration
admin.site.site_header = "LogisEdge Leave Management"
admin.site.site_title = "Leave Management Admin"
admin.site.index_title = "Welcome to Leave Management Administration"
