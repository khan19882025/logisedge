from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    GrievanceCategory, DisciplinaryActionType, Grievance, GrievanceAttachment,
    GrievanceNote, DisciplinaryCase, DisciplinaryAction, DisciplinaryActionDocument,
    Appeal, CaseAuditLog, EscalationMatrix
)


@admin.register(GrievanceCategory)
class GrievanceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    list_editable = ['is_active']


@admin.register(DisciplinaryActionType)
class DisciplinaryActionTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'severity_level', 'description', 'is_active', 'created_at']
    list_filter = ['severity_level', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['severity_level', 'name']
    list_editable = ['severity_level', 'is_active']


class GrievanceAttachmentInline(admin.TabularInline):
    model = GrievanceAttachment
    extra = 1
    fields = ['file', 'filename', 'description', 'uploaded_by', 'uploaded_at']
    readonly_fields = ['uploaded_by', 'uploaded_at']


class GrievanceNoteInline(admin.TabularInline):
    model = GrievanceNote
    extra = 1
    fields = ['note', 'is_internal', 'created_by', 'created_at']
    readonly_fields = ['created_by', 'created_at']


@admin.register(Grievance)
class GrievanceAdmin(admin.ModelAdmin):
    list_display = [
        'ticket_number', 'title', 'employee', 'category', 'priority', 'status',
        'assigned_to', 'created_at', 'is_confidential'
    ]
    list_filter = [
        'status', 'priority', 'category', 'is_anonymous', 'is_confidential',
        'created_at', 'incident_date'
    ]
    search_fields = ['ticket_number', 'title', 'description', 'employee__name']
    readonly_fields = ['ticket_number', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    list_per_page = 25
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('ticket_number', 'title', 'description', 'category', 'priority', 'status')
        }),
        ('Employee Information', {
            'fields': ('employee', 'is_anonymous')
        }),
        ('Incident Details', {
            'fields': ('incident_date', 'incident_location', 'witnesses')
        }),
        ('Assignment & Tracking', {
            'fields': ('assigned_to', 'created_by', 'created_at', 'updated_at')
        }),
        ('Resolution', {
            'fields': ('resolution_notes', 'resolved_at', 'resolved_by')
        }),
        ('Settings', {
            'fields': ('is_confidential',)
        }),
    )
    
    inlines = [GrievanceAttachmentInline, GrievanceNoteInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'employee', 'category', 'assigned_to', 'created_by', 'resolved_by'
        )


@admin.register(GrievanceAttachment)
class GrievanceAttachmentAdmin(admin.ModelAdmin):
    list_display = ['filename', 'grievance', 'uploaded_by', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['filename', 'grievance__ticket_number', 'uploaded_by__username']
    readonly_fields = ['uploaded_by', 'uploaded_at']


@admin.register(GrievanceNote)
class GrievanceNoteAdmin(admin.ModelAdmin):
    list_display = ['grievance', 'note_preview', 'is_internal', 'created_by', 'created_at']
    list_filter = ['is_internal', 'created_at']
    search_fields = ['note', 'grievance__ticket_number', 'created_by__username']
    readonly_fields = ['created_by', 'created_at']
    
    def note_preview(self, obj):
        return obj.note[:100] + '...' if len(obj.note) > 100 else obj.note
    note_preview.short_description = 'Note Preview'


class DisciplinaryActionInline(admin.TabularInline):
    model = DisciplinaryAction
    extra = 1
    fields = ['action_type', 'description', 'status', 'effective_date']
    readonly_fields = ['created_at']


@admin.register(DisciplinaryCase)
class DisciplinaryCaseAdmin(admin.ModelAdmin):
    list_display = [
        'case_number', 'title', 'employee', 'severity', 'status',
        'assigned_investigator', 'created_at', 'is_confidential'
    ]
    list_filter = [
        'status', 'severity', 'is_confidential', 'created_at', 'incident_date'
    ]
    search_fields = ['case_number', 'title', 'description', 'employee__name']
    readonly_fields = ['case_number', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    list_per_page = 25
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('case_number', 'title', 'description', 'severity', 'status')
        }),
        ('Employee Information', {
            'fields': ('employee',)
        }),
        ('Incident Details', {
            'fields': ('incident_date', 'incident_time', 'incident_location', 'policy_violation', 'witnesses', 'evidence_description')
        }),
        ('Case Management', {
            'fields': ('reported_by', 'assigned_investigator', 'committee_members')
        }),
        ('Dates', {
            'fields': ('hearing_date', 'decision_date', 'closed_at', 'created_at', 'updated_at')
        }),
        ('Related Cases', {
            'fields': ('related_grievance', 'previous_cases')
        }),
        ('Settings', {
            'fields': ('is_confidential',)
        }),
    )
    
    inlines = [DisciplinaryActionInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'employee', 'reported_by', 'assigned_investigator', 'related_grievance'
        )


class DisciplinaryActionDocumentInline(admin.TabularInline):
    model = DisciplinaryActionDocument
    extra = 1
    fields = ['document_type', 'file', 'filename', 'description', 'uploaded_by', 'uploaded_at']
    readonly_fields = ['uploaded_by', 'uploaded_at']


@admin.register(DisciplinaryAction)
class DisciplinaryActionAdmin(admin.ModelAdmin):
    list_display = [
        'action_type', 'case', 'status', 'effective_date', 'duration_days',
        'employee_acknowledged', 'created_at'
    ]
    list_filter = [
        'status', 'action_type', 'effective_date', 'employee_acknowledged', 'created_at'
    ]
    search_fields = ['case__case_number', 'case__title', 'action_type__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'effective_date'
    
    fieldsets = (
        ('Action Details', {
            'fields': ('case', 'action_type', 'description', 'justification', 'effective_date', 'duration_days')
        }),
        ('Approval Workflow', {
            'fields': ('status', 'approved_by_hr', 'approved_by_legal', 'approved_by_management')
        }),
        ('Implementation', {
            'fields': ('implemented_by', 'implemented_at')
        }),
        ('Employee Acknowledgment', {
            'fields': ('employee_acknowledged', 'acknowledgment_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    inlines = [DisciplinaryActionDocumentInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'case', 'action_type', 'approved_by_hr', 'approved_by_legal', 'approved_by_management'
        )


@admin.register(DisciplinaryActionDocument)
class DisciplinaryActionDocumentAdmin(admin.ModelAdmin):
    list_display = ['document_type', 'action', 'filename', 'uploaded_by', 'uploaded_at']
    list_filter = ['document_type', 'uploaded_at']
    search_fields = ['filename', 'action__case__case_number', 'uploaded_by__username']
    readonly_fields = ['uploaded_by', 'uploaded_at']


@admin.register(Appeal)
class AppealAdmin(admin.ModelAdmin):
    list_display = [
        'action', 'employee', 'status', 'submitted_at', 'reviewed_by', 'reviewed_at'
    ]
    list_filter = ['status', 'submitted_at', 'reviewed_at']
    search_fields = ['action__case__case_number', 'employee__name', 'grounds_for_appeal']
    readonly_fields = ['submitted_at']
    date_hierarchy = 'submitted_at'
    
    fieldsets = (
        ('Appeal Information', {
            'fields': ('action', 'employee', 'grounds_for_appeal', 'supporting_evidence', 'requested_outcome')
        }),
        ('Review Process', {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'review_notes')
        }),
        ('Outcome', {
            'fields': ('outcome', 'outcome_date')
        }),
        ('Timestamps', {
            'fields': ('submitted_at',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'action', 'employee', 'reviewed_by'
        )


@admin.register(CaseAuditLog)
class CaseAuditLogAdmin(admin.ModelAdmin):
    list_display = [
        'content_type', 'object_id', 'action', 'user', 'timestamp'
    ]
    list_filter = ['action', 'content_type', 'timestamp']
    search_fields = ['description', 'user__username']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    list_per_page = 50
    
    fieldsets = (
        ('Log Information', {
            'fields': ('content_type', 'object_id', 'action', 'description', 'user', 'timestamp')
        }),
        ('Change Details', {
            'fields': ('old_values', 'new_values'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EscalationMatrix)
class EscalationMatrixAdmin(admin.ModelAdmin):
    list_display = ['level', 'department', 'role', 'user', 'is_active', 'created_at']
    list_filter = ['level', 'department', 'is_active', 'created_at']
    search_fields = ['department', 'role', 'user__username']
    ordering = ['level', 'department', 'role']
    list_editable = ['is_active']


# Custom admin site configuration
admin.site.site_header = "Disciplinary & Grievance Management System"
admin.site.site_title = "D&G Admin"
admin.site.index_title = "Welcome to Disciplinary & Grievance Management"
