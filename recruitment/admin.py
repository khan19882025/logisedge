from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    JobRequisition, JobPosting, Candidate, Application, 
    Interview, Offer, Onboarding, RecruitmentMetrics
)


@admin.register(JobRequisition)
class JobRequisitionAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'department', 'location', 'position_type', 
        'priority', 'status', 'requested_by', 'requested_date', 'is_active'
    ]
    list_filter = [
        'status', 'priority', 'position_type', 'department', 
        'is_active', 'requested_date'
    ]
    search_fields = ['title', 'department', 'location', 'job_description']
    readonly_fields = ['requested_by', 'requested_date', 'hr_approval_date', 'director_approval_date']
    list_editable = ['status', 'priority', 'is_active']
    ordering = ['-requested_date']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'department', 'location', 'position_type', 'headcount')
        }),
        ('Salary & Priority', {
            'fields': ('salary_range_min', 'salary_range_max', 'currency', 'priority')
        }),
        ('Job Details', {
            'fields': ('job_description', 'required_skills', 'preferred_skills', 'experience_required', 'education_required', 'benefits')
        }),
        ('Timeline', {
            'fields': ('target_start_date', 'closing_date')
        }),
        ('Approval Workflow', {
            'fields': ('status', 'requested_by', 'approved_by_hr', 'approved_by_director', 'hr_approval_date', 'director_approval_date')
        }),
        ('Notes', {
            'fields': ('internal_notes', 'external_notes')
        }),
        ('System', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('requested_by', 'approved_by_hr', 'approved_by_director')


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'requisition', 'source', 'status', 'posting_date', 
        'expiry_date', 'views_count', 'applications_count'
    ]
    list_filter = ['status', 'source', 'posting_date', 'expiry_date']
    search_fields = ['title', 'description', 'requisition__title']
    readonly_fields = ['posting_date', 'views_count', 'applications_count']
    list_editable = ['status']
    ordering = ['-posting_date']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('requisition', 'title', 'status', 'source')
        }),
        ('Content', {
            'fields': ('description', 'requirements', 'benefits')
        }),
        ('External Details', {
            'fields': ('external_url', 'expiry_date')
        }),
        ('Analytics', {
            'fields': ('views_count', 'applications_count', 'posting_date')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('requisition')


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 'email', 'phone', 'current_position', 
        'current_company', 'years_of_experience', 'source', 'is_active'
    ]
    list_filter = [
        'source', 'gender', 'years_of_experience', 'is_active', 
        'created_at', 'country'
    ]
    search_fields = [
        'first_name', 'last_name', 'email', 'phone', 
        'current_position', 'current_company'
    ]
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_active']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'gender', 'date_of_birth')
        }),
        ('Address', {
            'fields': ('address', 'city', 'country')
        }),
        ('Professional Information', {
            'fields': ('current_position', 'current_company', 'years_of_experience', 'education_level', 'skills')
        }),
        ('Documents', {
            'fields': ('resume', 'cover_letter', 'profile_picture')
        }),
        ('Source & Referral', {
            'fields': ('source', 'referred_by')
        }),
        ('System', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )
    
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = 'Full Name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('referred_by')


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = [
        'candidate_name', 'job_title', 'status', 'applied_date', 
        'overall_score', 'expected_salary'
    ]
    list_filter = [
        'status', 'applied_date', 'job_posting__source', 
        'candidate__years_of_experience'
    ]
    search_fields = [
        'candidate__first_name', 'candidate__last_name', 
        'candidate__email', 'job_posting__title'
    ]
    readonly_fields = [
        'applied_date', 'status_changed_at', 'status_changed_by', 
        'overall_score'
    ]
    list_editable = ['status']
    ordering = ['-applied_date']
    
    fieldsets = (
        ('Application Details', {
            'fields': ('candidate', 'job_posting', 'status', 'applied_date')
        }),
        ('Candidate Information', {
            'fields': ('expected_salary', 'notice_period', 'availability_date')
        }),
        ('Assessment Scores', {
            'fields': ('screening_score', 'technical_score', 'cultural_fit_score', 'overall_score')
        }),
        ('Notes', {
            'fields': ('internal_notes', 'candidate_notes')
        }),
        ('Status Tracking', {
            'fields': ('status_changed_at', 'status_changed_by')
        }),
    )
    
    def candidate_name(self, obj):
        return obj.candidate.full_name
    candidate_name.short_description = 'Candidate'
    
    def job_title(self, obj):
        return obj.job_posting.title
    job_title.short_description = 'Job Title'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'candidate', 'job_posting', 'status_changed_by'
        )


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = [
        'candidate_name', 'interview_type', 'status', 'scheduled_date', 
        'duration', 'overall_score', 'recommendation'
    ]
    list_filter = [
        'interview_type', 'status', 'scheduled_date', 'recommendation'
    ]
    search_fields = [
        'candidate__first_name', 'candidate__last_name', 
        'application__job_posting__title'
    ]
    readonly_fields = ['overall_score']
    list_editable = ['status', 'recommendation']
    ordering = ['-scheduled_date']
    
    fieldsets = (
        ('Interview Details', {
            'fields': ('application', 'candidate', 'interview_type', 'status')
        }),
        ('Scheduling', {
            'fields': ('scheduled_date', 'duration', 'location', 'meeting_link')
        }),
        ('Participants', {
            'fields': ('interviewers',)
        }),
        ('Feedback', {
            'fields': ('feedback_notes', 'technical_score', 'communication_score', 'cultural_fit_score', 'overall_score')
        }),
        ('Recommendation', {
            'fields': ('recommendation',)
        }),
        ('Reminders', {
            'fields': ('reminder_sent', 'reminder_sent_at')
        }),
    )
    
    def candidate_name(self, obj):
        return obj.candidate.full_name
    candidate_name.short_description = 'Candidate'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('candidate', 'application')


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = [
        'candidate_name', 'position_title', 'department', 'status', 
        'salary', 'currency', 'offer_date', 'expiry_date'
    ]
    list_filter = [
        'status', 'contract_type', 'offer_date', 'expiry_date', 'department'
    ]
    search_fields = [
        'application__candidate__first_name', 
        'application__candidate__last_name',
        'position_title', 'department'
    ]
    readonly_fields = ['offer_date']
    list_editable = ['status']
    ordering = ['-offer_date']
    
    fieldsets = (
        ('Offer Details', {
            'fields': ('application', 'status', 'position_title', 'department')
        }),
        ('Compensation', {
            'fields': ('salary', 'currency', 'benefits', 'initial_salary')
        }),
        ('Contract Terms', {
            'fields': ('contract_type', 'probation_period', 'notice_period')
        }),
        ('Timeline', {
            'fields': ('start_date', 'offer_date', 'expiry_date', 'response_date')
        }),
        ('Negotiation', {
            'fields': ('negotiation_notes',)
        }),
        ('Documents', {
            'fields': ('offer_letter',)
        }),
    )
    
    def candidate_name(self, obj):
        return obj.application.candidate.full_name
    candidate_name.short_description = 'Candidate'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('application__candidate')


@admin.register(Onboarding)
class OnboardingAdmin(admin.ModelAdmin):
    list_display = [
        'candidate_name', 'status', 'joining_date', 'orientation_date', 
        'buddy_assigned', 'checklist_completion'
    ]
    list_filter = [
        'status', 'joining_date', 'orientation_date', 'buddy_assigned'
    ]
    search_fields = [
        'offer__application__candidate__first_name',
        'offer__application__candidate__last_name',
        'offer__position_title'
    ]
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['status']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Onboarding Details', {
            'fields': ('offer', 'status', 'joining_date', 'orientation_date', 'buddy_assigned')
        }),
        ('Checklist', {
            'fields': (
                'documents_submitted', 'background_check_completed', 
                'medical_check_completed', 'equipment_issued', 
                'access_granted', 'training_completed'
            )
        }),
        ('Documents', {
            'fields': (
                'passport_copy', 'visa_copy', 'emirates_id', 
                'educational_certificates', 'experience_certificates'
            )
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )
    
    def candidate_name(self, obj):
        return obj.offer.application.candidate.full_name
    candidate_name.short_description = 'Candidate'
    
    def checklist_completion(self, obj):
        checklist_items = [
            obj.documents_submitted, obj.background_check_completed,
            obj.medical_check_completed, obj.equipment_issued,
            obj.access_granted, obj.training_completed
        ]
        completed = sum(checklist_items)
        total = len(checklist_items)
        percentage = (completed / total) * 100 if total > 0 else 0
        return format_html(
            '<span style="color: {};">{}% ({}/{})</span>',
            'green' if percentage == 100 else 'orange' if percentage >= 50 else 'red',
            int(percentage), completed, total
        )
    checklist_completion.short_description = 'Checklist Completion'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'offer__application__candidate', 'buddy_assigned'
        )


@admin.register(RecruitmentMetrics)
class RecruitmentMetricsAdmin(admin.ModelAdmin):
    list_display = [
        'period_display', 'total_applications', 'total_interviews', 
        'total_offers', 'avg_time_to_hire', 'total_cost_per_hire'
    ]
    list_filter = ['period_start', 'period_end']
    search_fields = ['period_start', 'period_end']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-period_start']
    
    fieldsets = (
        ('Period', {
            'fields': ('period_start', 'period_end')
        }),
        ('Application Metrics', {
            'fields': ('total_applications', 'applications_by_source')
        }),
        ('Interview Metrics', {
            'fields': ('total_interviews', 'interviews_completed', 'interviews_cancelled')
        }),
        ('Offer Metrics', {
            'fields': ('total_offers', 'offers_accepted', 'offers_rejected')
        }),
        ('Time Metrics', {
            'fields': ('avg_time_to_hire', 'avg_time_to_fill')
        }),
        ('Cost Metrics', {
            'fields': ('total_cost_per_hire', 'advertising_cost', 'agency_fees')
        }),
        ('Quality Metrics', {
            'fields': ('quality_of_hire_score', 'retention_rate')
        }),
    )
    
    def period_display(self, obj):
        return f"{obj.period_start} to {obj.period_end}"
    period_display.short_description = 'Period'
