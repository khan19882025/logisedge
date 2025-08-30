from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    WorkflowType, WorkflowDefinition, WorkflowLevel, ApprovalRequest,
    WorkflowLevelApproval, ApprovalComment, ApprovalNotification,
    ApprovalAuditLog, WorkflowTemplate
)


@admin.register(WorkflowType)
class WorkflowTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'requires_approval', 'auto_approval_threshold', 'max_approval_days', 'created_at']
    list_filter = ['is_active', 'requires_approval', 'escalation_enabled', 'notification_enabled']
    search_fields = ['name', 'description']
    ordering = ['name']


@admin.register(WorkflowDefinition)
class WorkflowDefinitionAdmin(admin.ModelAdmin):
    list_display = ['name', 'workflow_type', 'approval_type', 'is_active', 'approval_levels', 'created_at']
    list_filter = ['workflow_type', 'approval_type', 'is_active', 'condition_type']
    search_fields = ['name', 'description']
    ordering = ['name']
    filter_horizontal = []


@admin.register(WorkflowLevel)
class WorkflowLevelAdmin(admin.ModelAdmin):
    list_display = ['name', 'workflow_definition', 'level_number', 'level_type', 'is_active', 'min_approvals_required']
    list_filter = ['workflow_definition', 'level_type', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['workflow_definition', 'level_number']
    filter_horizontal = ['approvers', 'approver_groups']


@admin.register(ApprovalRequest)
class ApprovalRequestAdmin(admin.ModelAdmin):
    list_display = [
        'request_id', 'title', 'requester', 'workflow_definition', 'status', 
        'priority', 'amount', 'created_at', 'is_overdue_display'
    ]
    list_filter = [
        'status', 'priority', 'workflow_definition', 'created_at', 
        'submitted_at', 'approved_at'
    ]
    search_fields = ['request_id', 'title', 'description', 'requester__username']
    ordering = ['-created_at']
    readonly_fields = ['request_id', 'created_at', 'updated_at']
    filter_horizontal = ['current_approvers']
    
    def is_overdue_display(self, obj):
        if obj.is_overdue:
            return format_html('<span style="color: red;">Overdue</span>')
        return format_html('<span style="color: green;">On Time</span>')
    is_overdue_display.short_description = 'Status'


@admin.register(WorkflowLevelApproval)
class WorkflowLevelApprovalAdmin(admin.ModelAdmin):
    list_display = [
        'approval_request', 'workflow_level', 'approver', 'status', 
        'assigned_at', 'approved_at'
    ]
    list_filter = ['status', 'workflow_level', 'assigned_at', 'approved_at']
    search_fields = ['approval_request__request_id', 'approver__username']
    ordering = ['-assigned_at']
    readonly_fields = ['assigned_at', 'updated_at']


@admin.register(ApprovalComment)
class ApprovalCommentAdmin(admin.ModelAdmin):
    list_display = ['approval_request', 'user', 'is_internal', 'created_at']
    list_filter = ['is_internal', 'created_at']
    search_fields = ['approval_request__request_id', 'user__username', 'comment']
    ordering = ['-created_at']
    readonly_fields = ['created_at']


@admin.register(ApprovalNotification)
class ApprovalNotificationAdmin(admin.ModelAdmin):
    list_display = [
        'approval_request', 'recipient', 'notification_type', 
        'notification_method', 'is_sent', 'is_read', 'created_at'
    ]
    list_filter = [
        'notification_type', 'notification_method', 'is_sent', 
        'is_read', 'created_at'
    ]
    search_fields = ['approval_request__request_id', 'recipient__username', 'title']
    ordering = ['-created_at']
    readonly_fields = ['created_at']


@admin.register(ApprovalAuditLog)
class ApprovalAuditLogAdmin(admin.ModelAdmin):
    list_display = [
        'approval_request', 'user', 'action', 'created_at', 'ip_address'
    ]
    list_filter = ['action', 'created_at']
    search_fields = ['approval_request__request_id', 'user__username', 'description']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'ip_address', 'user_agent']


@admin.register(WorkflowTemplate)
class WorkflowTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'workflow_definition', 'is_active', 'created_by', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']
