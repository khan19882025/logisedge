from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class GrievanceCategory(models.Model):
    """Categories for grievances"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Grievance Category"
        verbose_name_plural = "Grievance Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class DisciplinaryActionType(models.Model):
    """Types of disciplinary actions"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    severity_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1=Lowest, 5=Highest severity"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Disciplinary Action Type"
        verbose_name_plural = "Disciplinary Action Types"
        ordering = ['severity_level', 'name']

    def __str__(self):
        return f"{self.name} (Level {self.severity_level})"


class Grievance(models.Model):
    """Grievance case model"""
    STATUS_CHOICES = [
        ('new', 'New'),
        ('under_review', 'Under Review'),
        ('investigating', 'Investigating'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('escalated', 'Escalated'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    # Basic Information
    ticket_number = models.CharField(max_length=20, unique=True, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(GrievanceCategory, on_delete=models.CASCADE)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    
    # Employee Information
    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='grievances')
    is_anonymous = models.BooleanField(default=False)
    
    # Case Details
    incident_date = models.DateField()
    incident_location = models.CharField(max_length=200, blank=True)
    witnesses = models.TextField(blank=True, help_text="Names and contact details of witnesses")
    
    # Assignment and Tracking
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_grievances')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_grievances')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Resolution
    resolution_notes = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_grievances')
    
    # Confidentiality
    is_confidential = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Grievance"
        verbose_name_plural = "Grievances"
        ordering = ['-created_at']

    def __str__(self):
        return f"GRV-{self.ticket_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            self.ticket_number = f"GRV-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)


class GrievanceAttachment(models.Model):
    """Attachments for grievances"""
    grievance = models.ForeignKey(Grievance, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='grievance_attachments/')
    filename = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Grievance Attachment"
        verbose_name_plural = "Grievance Attachments"

    def __str__(self):
        return f"{self.filename} - {self.grievance.ticket_number}"


class GrievanceNote(models.Model):
    """Notes and updates for grievances"""
    grievance = models.ForeignKey(Grievance, on_delete=models.CASCADE, related_name='notes')
    note = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_internal = models.BooleanField(default=False, help_text="Internal notes not visible to employee")

    class Meta:
        verbose_name = "Grievance Note"
        verbose_name_plural = "Grievance Notes"
        ordering = ['-created_at']

    def __str__(self):
        return f"Note by {self.created_by.username} on {self.created_at.strftime('%Y-%m-%d')}"


class DisciplinaryCase(models.Model):
    """Disciplinary case model"""
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('investigating', 'Investigating'),
        ('hearing_scheduled', 'Hearing Scheduled'),
        ('hearing_completed', 'Hearing Completed'),
        ('decision_pending', 'Decision Pending'),
        ('action_taken', 'Action Taken'),
        ('closed', 'Closed'),
        ('appealed', 'Appealed'),
    ]

    SEVERITY_CHOICES = [
        ('minor', 'Minor'),
        ('moderate', 'Moderate'),
        ('major', 'Major'),
        ('critical', 'Critical'),
    ]

    # Basic Information
    case_number = models.CharField(max_length=20, unique=True, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='moderate')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    # Employee Information
    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='disciplinary_cases')
    
    # Incident Details
    incident_date = models.DateField()
    incident_time = models.TimeField(null=True, blank=True)
    incident_location = models.CharField(max_length=200, blank=True)
    policy_violation = models.CharField(max_length=200, blank=True)
    witnesses = models.TextField(blank=True)
    evidence_description = models.TextField(blank=True)
    
    # Case Management
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_cases')
    assigned_investigator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='investigating_cases')
    committee_members = models.ManyToManyField(User, blank=True, related_name='committee_cases')
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    hearing_date = models.DateTimeField(null=True, blank=True)
    decision_date = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    # Related Cases
    related_grievance = models.ForeignKey(Grievance, on_delete=models.SET_NULL, null=True, blank=True, related_name='disciplinary_cases')
    previous_cases = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='subsequent_cases')
    
    # Confidentiality
    is_confidential = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Disciplinary Case"
        verbose_name_plural = "Disciplinary Cases"
        ordering = ['-created_at']

    def __str__(self):
        return f"DC-{self.case_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.case_number:
            self.case_number = f"DC-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)


class DisciplinaryAction(models.Model):
    """Disciplinary actions taken"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('implemented', 'Implemented'),
    ]

    case = models.ForeignKey(DisciplinaryCase, on_delete=models.CASCADE, related_name='actions')
    action_type = models.ForeignKey(DisciplinaryActionType, on_delete=models.CASCADE)
    description = models.TextField()
    justification = models.TextField()
    effective_date = models.DateField()
    duration_days = models.IntegerField(null=True, blank=True, help_text="For suspensions, terminations, etc.")
    
    # Approval Workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by_hr = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='hr_approved_actions')
    approved_by_legal = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='legal_approved_actions')
    approved_by_management = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='management_approved_actions')
    
    # Implementation
    implemented_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='implemented_actions')
    implemented_at = models.DateTimeField(null=True, blank=True)
    
    # Employee Acknowledgment
    employee_acknowledged = models.BooleanField(default=False)
    acknowledgment_date = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Disciplinary Action"
        verbose_name_plural = "Disciplinary Actions"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action_type.name} - {self.case.case_number}"


class DisciplinaryActionDocument(models.Model):
    """Documents related to disciplinary actions"""
    action = models.ForeignKey(DisciplinaryAction, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=[
        ('warning_letter', 'Warning Letter'),
        ('suspension_notice', 'Suspension Notice'),
        ('termination_letter', 'Termination Letter'),
        ('decision_letter', 'Decision Letter'),
        ('other', 'Other'),
    ])
    file = models.FileField(upload_to='disciplinary_documents/')
    filename = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Disciplinary Action Document"
        verbose_name_plural = "Disciplinary Action Documents"

    def __str__(self):
        return f"{self.document_type} - {self.filename}"


class Appeal(models.Model):
    """Appeals against disciplinary actions"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]

    action = models.ForeignKey(DisciplinaryAction, on_delete=models.CASCADE, related_name='appeals')
    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='appeals')
    grounds_for_appeal = models.TextField()
    supporting_evidence = models.TextField(blank=True)
    requested_outcome = models.TextField()
    
    # Appeal Process
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_appeals')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    
    # Outcome
    outcome = models.TextField(blank=True)
    outcome_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Appeal"
        verbose_name_plural = "Appeals"
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Appeal by {self.employee} - {self.action}"


class CaseAuditLog(models.Model):
    """Audit trail for all case changes"""
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('status_changed', 'Status Changed'),
        ('assigned', 'Assigned'),
        ('action_taken', 'Action Taken'),
        ('document_uploaded', 'Document Uploaded'),
        ('note_added', 'Note Added'),
        ('appeal_filed', 'Appeal Filed'),
        ('closed', 'Closed'),
    ]

    # Generic fields for both grievance and disciplinary cases
    content_type = models.CharField(max_length=50)  # 'grievance' or 'disciplinary'
    object_id = models.IntegerField()
    
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Additional data
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name = "Case Audit Log"
        verbose_name_plural = "Case Audit Logs"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} by {self.user.username} on {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class EscalationMatrix(models.Model):
    """Escalation matrix for different roles and departments"""
    LEVEL_CHOICES = [
        (1, 'Level 1'),
        (2, 'Level 2'),
        (3, 'Level 3'),
        (4, 'Level 4'),
        (5, 'Level 5'),
    ]

    level = models.IntegerField(choices=LEVEL_CHOICES)
    department = models.CharField(max_length=100, blank=True)
    role = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='escalation_levels')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Escalation Matrix"
        verbose_name_plural = "Escalation Matrix"
        unique_together = ['level', 'department', 'role']
        ordering = ['level', 'department', 'role']

    def __str__(self):
        return f"Level {self.level} - {self.department} - {self.role}"
