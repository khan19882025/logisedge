from django.db import models
from django.contrib.auth.models import User, Group
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.db.models import Q
import uuid


class WorkflowType(models.Model):
    """Model for different types of workflows"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=True)
    auto_approval_threshold = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        help_text="Amount threshold for auto-approval"
    )
    max_approval_days = models.PositiveIntegerField(
        default=7,
        help_text="Maximum days for approval before escalation"
    )
    escalation_enabled = models.BooleanField(default=True)
    notification_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class WorkflowDefinition(models.Model):
    """Model for defining workflow rules and conditions"""
    APPROVAL_TYPE_CHOICES = [
        ('sequential', 'Sequential'),
        ('parallel', 'Parallel'),
        ('hybrid', 'Hybrid'),
    ]
    
    CONDITION_TYPE_CHOICES = [
        ('amount', 'Amount Threshold'),
        ('department', 'Department'),
        ('cost_center', 'Cost Center'),
        ('project', 'Project'),
        ('role', 'Role'),
        ('user', 'Specific User'),
    ]

    name = models.CharField(max_length=200)
    workflow_type = models.ForeignKey(WorkflowType, on_delete=models.CASCADE, related_name='definitions')
    description = models.TextField(blank=True)
    approval_type = models.CharField(max_length=20, choices=APPROVAL_TYPE_CHOICES, default='sequential')
    is_active = models.BooleanField(default=True)
    
    # Conditions
    condition_type = models.CharField(max_length=20, choices=CONDITION_TYPE_CHOICES, blank=True)
    condition_value = models.CharField(max_length=500, blank=True, help_text="JSON or specific value")
    min_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    max_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Approval levels
    approval_levels = models.PositiveIntegerField(default=1)
    auto_approve_if_no_approvers = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.workflow_type.name}"


class WorkflowLevel(models.Model):
    """Model for individual approval levels within a workflow"""
    LEVEL_TYPE_CHOICES = [
        ('sequential', 'Sequential'),
        ('parallel', 'Parallel'),
    ]

    workflow_definition = models.ForeignKey(WorkflowDefinition, on_delete=models.CASCADE, related_name='levels')
    level_number = models.PositiveIntegerField()
    level_type = models.CharField(max_length=20, choices=LEVEL_TYPE_CHOICES, default='sequential')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Approvers
    approvers = models.ManyToManyField(User, related_name='workflow_levels', blank=True)
    approver_groups = models.ManyToManyField(Group, related_name='workflow_levels', blank=True)
    approver_roles = models.CharField(max_length=500, blank=True, help_text="Comma-separated role names")
    
    # Conditions
    min_approvals_required = models.PositiveIntegerField(default=1)
    deadline_hours = models.PositiveIntegerField(default=24, help_text="Hours before escalation")
    
    # Actions
    can_approve = models.BooleanField(default=True)
    can_reject = models.BooleanField(default=True)
    can_return = models.BooleanField(default=True)
    can_comment = models.BooleanField(default=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['workflow_definition', 'level_number']
        unique_together = ['workflow_definition', 'level_number']

    def __str__(self):
        return f"{self.workflow_definition.name} - Level {self.level_number}"


class ApprovalRequest(models.Model):
    """Model for individual approval requests"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('pending', 'Pending Approval'),
        ('in_progress', 'In Progress'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    request_id = models.CharField(max_length=50, unique=True, blank=True)
    workflow_definition = models.ForeignKey(WorkflowDefinition, on_delete=models.CASCADE, related_name='requests')
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='approval_requests')
    
    # Request details
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Document details
    document_type = models.CharField(max_length=100, blank=True)
    document_id = models.CharField(max_length=100, blank=True)
    document_reference = models.CharField(max_length=200, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Approval tracking
    current_level = models.ForeignKey(WorkflowLevel, on_delete=models.SET_NULL, null=True, blank=True)
    current_approvers = models.ManyToManyField(User, related_name='current_approval_requests', blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_requests')
    rejected_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='rejected_requests')
    
    # Timestamps
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deadline = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.request_id} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.request_id:
            self.request_id = f"AWR{timezone.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        if self.deadline and self.status in ['pending', 'in_progress']:
            return timezone.now() > self.deadline
        return False

    @property
    def can_be_approved(self):
        return self.status in ['pending', 'in_progress']

    @property
    def approval_progress(self):
        """Calculate approval progress percentage"""
        total_levels = self.workflow_definition.levels.count()
        if total_levels == 0:
            return 100
        completed_levels = self.workflow_level_approvals.filter(status='approved').count()
        return int((completed_levels / total_levels) * 100)


class WorkflowLevelApproval(models.Model):
    """Model for tracking approvals at each level"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('returned', 'Returned for Revision'),
        ('escalated', 'Escalated'),
    ]

    approval_request = models.ForeignKey(ApprovalRequest, on_delete=models.CASCADE, related_name='workflow_level_approvals')
    workflow_level = models.ForeignKey(WorkflowLevel, on_delete=models.CASCADE, related_name='approvals')
    approver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='level_approvals')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    comments = models.TextField(blank=True)
    
    # Timestamps
    assigned_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['workflow_level__level_number', '-assigned_at']
        unique_together = ['approval_request', 'workflow_level', 'approver']

    def __str__(self):
        return f"{self.approval_request.request_id} - Level {self.workflow_level.level_number} - {self.approver.username}"


class ApprovalComment(models.Model):
    """Model for comments and notes on approval requests"""
    approval_request = models.ForeignKey(ApprovalRequest, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='approval_comments')
    comment = models.TextField()
    is_internal = models.BooleanField(default=False, help_text="Internal comment not visible to requester")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.approval_request.request_id} - {self.user.username}"


class ApprovalNotification(models.Model):
    """Model for tracking notifications sent for approvals"""
    NOTIFICATION_TYPE_CHOICES = [
        ('request_submitted', 'Request Submitted'),
        ('approval_required', 'Approval Required'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('escalated', 'Escalated'),
        ('overdue', 'Overdue'),
        ('reminder', 'Reminder'),
    ]

    NOTIFICATION_METHOD_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
        ('in_app', 'In-App'),
        ('push', 'Push Notification'),
    ]

    approval_request = models.ForeignKey(ApprovalRequest, on_delete=models.CASCADE, related_name='notifications')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='approval_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    notification_method = models.CharField(max_length=20, choices=NOTIFICATION_METHOD_CHOICES, default='in_app')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.approval_request.request_id} - {self.notification_type} - {self.recipient.username}"


class ApprovalAuditLog(models.Model):
    """Model for comprehensive audit trail of all approval actions"""
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('submitted', 'Submitted'),
        ('assigned', 'Assigned'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('returned', 'Returned'),
        ('escalated', 'Escalated'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('commented', 'Commented'),
        ('notified', 'Notified'),
    ]

    approval_request = models.ForeignKey(ApprovalRequest, on_delete=models.CASCADE, related_name='audit_logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='approval_audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.approval_request.request_id} - {self.action} - {self.user.username}"


class WorkflowTemplate(models.Model):
    """Model for pre-defined workflow templates"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    workflow_definition = models.ForeignKey(WorkflowDefinition, on_delete=models.CASCADE, related_name='templates')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_workflow_templates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
