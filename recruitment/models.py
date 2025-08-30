from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid


class JobRequisition(models.Model):
    """Job requisition model for department managers to request new positions"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_hr', 'Pending HR Approval'),
        ('pending_director', 'Pending Director Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('closed', 'Closed'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    department = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    position_type = models.CharField(max_length=50, choices=[
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
    ])
    salary_range_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_range_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='AED')
    headcount = models.PositiveIntegerField(default=1)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Job details
    job_description = models.TextField()
    required_skills = models.TextField()
    preferred_skills = models.TextField(blank=True)
    experience_required = models.PositiveIntegerField(help_text="Years of experience required")
    education_required = models.CharField(max_length=100, blank=True)
    benefits = models.TextField(blank=True, help_text="Benefits package, perks, and additional incentives")
    
    # Approval workflow
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_requisitions_requested')
    approved_by_hr = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='job_requisitions_hr_approved')
    approved_by_director = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='job_requisitions_director_approved')
    
    # Timeline
    requested_date = models.DateTimeField(auto_now_add=True)
    hr_approval_date = models.DateTimeField(null=True, blank=True)
    director_approval_date = models.DateTimeField(null=True, blank=True)
    target_start_date = models.DateField()
    closing_date = models.DateField()
    
    # Additional info
    internal_notes = models.TextField(blank=True)
    external_notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Job Requisition'
        verbose_name_plural = 'Job Requisitions'
    
    def __str__(self):
        return f"{self.title} - {self.department}"
    
    @property
    def is_approved(self):
        return self.status == 'approved'
    
    @property
    def days_until_closing(self):
        return (self.closing_date - timezone.now().date()).days


class JobPosting(models.Model):
    """Job posting model for approved requisitions"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('closed', 'Closed'),
    ]
    
    SOURCE_CHOICES = [
        ('internal', 'Internal Portal'),
        ('linkedin', 'LinkedIn'),
        ('indeed', 'Indeed'),
        ('glassdoor', 'Glassdoor'),
        ('company_website', 'Company Website'),
        ('referral', 'Employee Referral'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requisition = models.OneToOneField(JobRequisition, on_delete=models.CASCADE, related_name='job_posting')
    title = models.CharField(max_length=200)
    description = models.TextField()
    requirements = models.TextField()
    benefits = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Posting details
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='internal')
    external_url = models.URLField(blank=True)
    posting_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateField()
    
    # Analytics
    views_count = models.PositiveIntegerField(default=0)
    applications_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Job Posting'
        verbose_name_plural = 'Job Postings'
    
    def __str__(self):
        return f"{self.title} - {self.source}"


class Candidate(models.Model):
    """Candidate model for storing candidate information"""
    
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Address
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    
    # Professional info
    current_position = models.CharField(max_length=100, blank=True)
    current_company = models.CharField(max_length=100, blank=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    education_level = models.CharField(max_length=100, blank=True)
    skills = models.TextField(blank=True)
    
    # Documents
    resume = models.FileField(upload_to='candidates/resumes/', blank=True)
    cover_letter = models.FileField(upload_to='candidates/cover_letters/', blank=True)
    profile_picture = models.ImageField(upload_to='candidates/photos/', blank=True)
    
    # Source tracking
    source = models.CharField(max_length=50, choices=JobPosting.SOURCE_CHOICES, default='other')
    referred_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='candidates_referred')
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Candidate'
        verbose_name_plural = 'Candidates'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        if self.date_of_birth:
            return (timezone.now().date() - self.date_of_birth).days // 365
        return None


class Application(models.Model):
    """Application model for candidate applications"""
    
    STATUS_CHOICES = [
        ('applied', 'Applied'),
        ('screening', 'Screening'),
        ('shortlisted', 'Shortlisted'),
        ('interview', 'Interview'),
        ('offer', 'Offer'),
        ('hired', 'Hired'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='applications')
    job_posting = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='applied')
    
    # Application details
    applied_date = models.DateTimeField(auto_now_add=True)
    expected_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notice_period = models.PositiveIntegerField(help_text="Days of notice period", default=30)
    availability_date = models.DateField(null=True, blank=True)
    
    # Assessment
    screening_score = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], null=True, blank=True)
    technical_score = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], null=True, blank=True)
    cultural_fit_score = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], null=True, blank=True)
    overall_score = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], null=True, blank=True)
    
    # Notes
    internal_notes = models.TextField(blank=True)
    candidate_notes = models.TextField(blank=True)
    
    # Timeline
    status_changed_at = models.DateTimeField(auto_now=True)
    status_changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='applications_status_changed')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-applied_date']
        unique_together = ['candidate', 'job_posting']
        verbose_name = 'Application'
        verbose_name_plural = 'Applications'
    
    def __str__(self):
        return f"{self.candidate.full_name} - {self.job_posting.title}"
    
    def save(self, *args, **kwargs):
        # Update overall score if individual scores are available
        scores = [self.screening_score, self.technical_score, self.cultural_fit_score]
        valid_scores = [score for score in scores if score is not None]
        if valid_scores:
            self.overall_score = sum(valid_scores) // len(valid_scores)
        super().save(*args, **kwargs)


class Interview(models.Model):
    """Interview model for scheduling and managing interviews"""
    
    TYPE_CHOICES = [
        ('phone', 'Phone Screen'),
        ('video', 'Video Call'),
        ('technical', 'Technical Interview'),
        ('hr', 'HR Interview'),
        ('managerial', 'Managerial Interview'),
        ('final', 'Final Interview'),
        ('assessment', 'Assessment'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='interviews')
    interview_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    # Scheduling
    scheduled_date = models.DateTimeField()
    duration = models.PositiveIntegerField(help_text="Duration in minutes", default=60)
    location = models.CharField(max_length=200, blank=True)
    meeting_link = models.URLField(blank=True)
    
    # Participants
    interviewers = models.ManyToManyField(User, related_name='interviews_conducting')
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='interviews')
    
    # Feedback
    feedback_notes = models.TextField(blank=True)
    technical_score = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], null=True, blank=True)
    communication_score = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], null=True, blank=True)
    cultural_fit_score = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], null=True, blank=True)
    overall_score = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], null=True, blank=True)
    
    # Recommendations
    recommendation = models.CharField(max_length=20, choices=[
        ('strong_hire', 'Strong Hire'),
        ('hire', 'Hire'),
        ('weak_hire', 'Weak Hire'),
        ('no_hire', 'No Hire'),
        ('strong_no_hire', 'Strong No Hire'),
    ], blank=True)
    
    # Reminders
    reminder_sent = models.BooleanField(default=False)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['scheduled_date']
        verbose_name = 'Interview'
        verbose_name_plural = 'Interviews'
    
    def __str__(self):
        return f"{self.candidate.full_name} - {self.interview_type} - {self.scheduled_date.strftime('%Y-%m-%d %H:%M')}"
    
    def save(self, *args, **kwargs):
        # Update overall score if individual scores are available
        scores = [self.technical_score, self.communication_score, self.cultural_fit_score]
        valid_scores = [score for score in scores if score is not None]
        if valid_scores:
            self.overall_score = sum(valid_scores) // len(valid_scores)
        super().save(*args, **kwargs)


class Offer(models.Model):
    """Offer model for job offers"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('negotiating', 'Negotiating'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
        ('withdrawn', 'Withdrawn'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='offer')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Offer details
    position_title = models.CharField(max_length=200)
    department = models.CharField(max_length=100)
    start_date = models.DateField()
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='AED')
    benefits = models.TextField(blank=True)
    
    # Contract details
    contract_type = models.CharField(max_length=20, choices=[
        ('permanent', 'Permanent'),
        ('contract', 'Contract'),
        ('probation', 'Probation'),
    ])
    probation_period = models.PositiveIntegerField(help_text="Days of probation period", default=90)
    notice_period = models.PositiveIntegerField(help_text="Days of notice period", default=30)
    
    # Timeline
    offer_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField()
    response_date = models.DateTimeField(null=True, blank=True)
    
    # Negotiation
    initial_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    negotiation_notes = models.TextField(blank=True)
    
    # Documents
    offer_letter = models.FileField(upload_to='offers/letters/', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-offer_date']
        verbose_name = 'Offer'
        verbose_name_plural = 'Offers'
    
    def __str__(self):
        return f"{self.application.candidate.full_name} - {self.position_title}"


class Onboarding(models.Model):
    """Onboarding model for new hires"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    offer = models.OneToOneField(Offer, on_delete=models.CASCADE, related_name='onboarding')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Onboarding details
    joining_date = models.DateField()
    orientation_date = models.DateField(null=True, blank=True)
    buddy_assigned = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='onboarding_buddy')
    
    # Checklist
    documents_submitted = models.BooleanField(default=False)
    background_check_completed = models.BooleanField(default=False)
    medical_check_completed = models.BooleanField(default=False)
    equipment_issued = models.BooleanField(default=False)
    access_granted = models.BooleanField(default=False)
    training_completed = models.BooleanField(default=False)
    
    # Documents
    passport_copy = models.FileField(upload_to='onboarding/documents/', blank=True)
    visa_copy = models.FileField(upload_to='onboarding/documents/', blank=True)
    emirates_id = models.FileField(upload_to='onboarding/documents/', blank=True)
    educational_certificates = models.FileField(upload_to='onboarding/documents/', blank=True)
    experience_certificates = models.FileField(upload_to='onboarding/documents/', blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Onboarding'
        verbose_name_plural = 'Onboarding'
    
    def __str__(self):
        return f"{self.offer.application.candidate.full_name} - Onboarding"


class RecruitmentMetrics(models.Model):
    """Model for tracking recruitment metrics and KPIs"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Application metrics
    total_applications = models.PositiveIntegerField(default=0)
    applications_by_source = models.JSONField(default=dict)
    
    # Interview metrics
    total_interviews = models.PositiveIntegerField(default=0)
    interviews_completed = models.PositiveIntegerField(default=0)
    interviews_cancelled = models.PositiveIntegerField(default=0)
    
    # Offer metrics
    total_offers = models.PositiveIntegerField(default=0)
    offers_accepted = models.PositiveIntegerField(default=0)
    offers_rejected = models.PositiveIntegerField(default=0)
    
    # Time metrics
    avg_time_to_hire = models.PositiveIntegerField(help_text="Average days to hire", default=0)
    avg_time_to_fill = models.PositiveIntegerField(help_text="Average days to fill position", default=0)
    
    # Cost metrics
    total_cost_per_hire = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    advertising_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    agency_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Quality metrics
    quality_of_hire_score = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], default=0)
    retention_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentage", default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-period_start']
        unique_together = ['period_start', 'period_end']
        verbose_name = 'Recruitment Metric'
        verbose_name_plural = 'Recruitment Metrics'
    
    def __str__(self):
        return f"Metrics {self.period_start} to {self.period_end}"
