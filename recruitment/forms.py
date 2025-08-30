from django import forms
from django.contrib.auth.models import User
from .models import (
    JobRequisition, JobPosting, Candidate, Application, 
    Interview, Offer, Onboarding, RecruitmentMetrics
)


class JobRequisitionForm(forms.ModelForm):
    """Form for creating and editing job requisitions"""
    
    class Meta:
        model = JobRequisition
        fields = [
            'title', 'department', 'location', 'position_type',
            'salary_range_min', 'salary_range_max', 'currency', 'headcount',
            'priority', 'job_description', 'required_skills', 'preferred_skills',
            'experience_required', 'education_required', 'benefits',
            'target_start_date', 'closing_date', 'status', 'requested_by',
            'internal_notes', 'external_notes'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter job title'}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter department'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter location'}),
            'position_type': forms.Select(attrs={'class': 'form-control'}),
            'salary_range_min': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Minimum salary'}),
            'salary_range_max': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Maximum salary'}),
            'currency': forms.TextInput(attrs={'class': 'form-control', 'value': 'AED', 'readonly': True}),
            'headcount': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'job_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Enter detailed job description'}),
            'required_skills': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter required skills'}),
            'preferred_skills': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter preferred skills (optional)'}),
            'experience_required': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': 'Years of experience'}),
            'education_required': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Required education level'}),
            'benefits': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe the benefits package, perks, and additional incentives'}),
            'target_start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'closing_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'requested_by': forms.Select(attrs={'class': 'form-control'}),
            'internal_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Internal notes for HR team'}),
            'external_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Notes for the requester'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set up the requested_by field
        if 'requested_by' in self.fields:
            self.fields['requested_by'].queryset = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
            if user and not self.instance.pk:  # Only for new instances
                self.fields['requested_by'].initial = user
        
        if user and not user.is_superuser:
            # Regular users can only edit certain fields
            readonly_fields = ['status', 'approved_by_hr', 'approved_by_director']
            for field in readonly_fields:
                if field in self.fields:
                    self.fields[field].widget.attrs['readonly'] = True
    
    def clean(self):
        cleaned_data = super().clean()
        salary_min = cleaned_data.get('salary_range_min')
        salary_max = cleaned_data.get('salary_range_max')
        
        if salary_min and salary_max and salary_min > salary_max:
            raise forms.ValidationError("Minimum salary cannot be greater than maximum salary")
        
        target_start = cleaned_data.get('target_start_date')
        closing_date = cleaned_data.get('closing_date')
        
        if target_start and closing_date and target_start <= closing_date:
            raise forms.ValidationError("Target start date must be after closing date")
        
        return cleaned_data


class JobPostingForm(forms.ModelForm):
    """Form for creating and editing job postings"""
    
    class Meta:
        model = JobPosting
        fields = [
            'title', 'description', 'requirements', 'benefits',
            'status', 'source', 'external_url', 'expiry_date'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter job posting title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Enter detailed job description for posting'}),
            'requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter job requirements'}),
            'benefits': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter company benefits (optional)'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'source': forms.Select(attrs={'class': 'form-control'}),
            'external_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'External job posting URL'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class CandidateForm(forms.ModelForm):
    """Form for creating and editing candidates"""
    
    class Meta:
        model = Candidate
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'gender',
            'date_of_birth', 'address', 'city', 'country',
            'current_position', 'current_company', 'years_of_experience',
            'education_level', 'skills', 'resume', 'cover_letter',
            'profile_picture', 'source', 'referred_by'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter first name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter last name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter city'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter country'}),
            'current_position': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Current job title'}),
            'current_company': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Current company'}),
            'years_of_experience': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': 'Years of experience'}),
            'education_level': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Highest education level'}),
            'skills': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter skills (comma separated)'}),
            'resume': forms.FileInput(attrs={'class': 'form-control'}),
            'cover_letter': forms.FileInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'source': forms.Select(attrs={'class': 'form-control'}),
            'referred_by': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter users for referral dropdown
        self.fields['referred_by'].queryset = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if Candidate.objects.filter(email=email).exclude(pk=self.instance.pk if self.instance.pk else None).exists():
            raise forms.ValidationError("A candidate with this email already exists.")
        return email


class ApplicationForm(forms.ModelForm):
    """Form for creating and editing applications"""
    
    class Meta:
        model = Application
        fields = [
            'candidate', 'job_posting', 'status', 'expected_salary',
            'notice_period', 'availability_date', 'screening_score',
            'technical_score', 'cultural_fit_score', 'internal_notes',
            'candidate_notes'
        ]
        widgets = {
            'candidate': forms.Select(attrs={'class': 'form-control'}),
            'job_posting': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'expected_salary': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Expected salary'}),
            'notice_period': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': 'Notice period in days'}),
            'availability_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'screening_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100, 'placeholder': 'Screening score (0-100)'}),
            'technical_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100, 'placeholder': 'Technical score (0-100)'}),
            'cultural_fit_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100, 'placeholder': 'Cultural fit score (0-100)'}),
            'internal_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Internal notes (HR only)'}),
            'candidate_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Notes from candidate'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter active candidates and job postings
        self.fields['candidate'].queryset = Candidate.objects.filter(is_active=True).order_by('first_name', 'last_name')
        self.fields['job_posting'].queryset = JobPosting.objects.filter(status='active').order_by('title')


class InterviewForm(forms.ModelForm):
    """Form for creating and editing interviews"""
    
    class Meta:
        model = Interview
        fields = [
            'application', 'interview_type', 'status', 'scheduled_date',
            'duration', 'location', 'meeting_link', 'interviewers',
            'feedback_notes', 'technical_score', 'communication_score',
            'cultural_fit_score', 'recommendation'
        ]
        widgets = {
            'application': forms.Select(attrs={'class': 'form-control'}),
            'interview_type': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'scheduled_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control', 'min': 15, 'placeholder': 'Duration in minutes'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Interview location'}),
            'meeting_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Video call link'}),
            'interviewers': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'feedback_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Interview feedback and notes'}),
            'technical_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100, 'placeholder': 'Technical score (0-100)'}),
            'communication_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100, 'placeholder': 'Communication score (0-100)'}),
            'cultural_fit_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100, 'placeholder': 'Cultural fit score (0-100)'}),
            'recommendation': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter active applications and users
        self.fields['application'].queryset = Application.objects.filter(
            status__in=['shortlisted', 'interview']
        ).order_by('-applied_date')
        self.fields['interviewers'].queryset = User.objects.filter(is_active=True).order_by('first_name', 'last_name')


class OfferForm(forms.ModelForm):
    """Form for creating and editing job offers"""
    
    class Meta:
        model = Offer
        fields = [
            'application', 'status', 'position_title', 'department',
            'start_date', 'salary', 'currency', 'benefits',
            'contract_type', 'probation_period', 'notice_period',
            'expiry_date', 'initial_salary', 'negotiation_notes',
            'offer_letter'
        ]
        widgets = {
            'application': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'position_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Position title'}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Department'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Offered salary'}),
            'currency': forms.TextInput(attrs={'class': 'form-control', 'value': 'AED', 'readonly': True}),
            'benefits': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Benefits package'}),
            'contract_type': forms.Select(attrs={'class': 'form-control'}),
            'probation_period': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': 'Probation period in days'}),
            'notice_period': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': 'Notice period in days'}),
            'expiry_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'initial_salary': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Initial salary offer'}),
            'negotiation_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Salary negotiation notes'}),
            'offer_letter': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter applications that are ready for offer
        self.fields['application'].queryset = Application.objects.filter(
            status='offer'
        ).order_by('-applied_date')


class OnboardingForm(forms.ModelForm):
    """Form for creating and editing onboarding records"""
    
    class Meta:
        model = Onboarding
        fields = [
            'offer', 'status', 'joining_date', 'orientation_date',
            'buddy_assigned', 'documents_submitted', 'background_check_completed',
            'medical_check_completed', 'equipment_issued', 'access_granted',
            'training_completed', 'passport_copy', 'visa_copy', 'emirates_id',
            'educational_certificates', 'experience_certificates', 'notes'
        ]
        widgets = {
            'offer': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'joining_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'orientation_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'buddy_assigned': forms.Select(attrs={'class': 'form-control'}),
            'documents_submitted': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'background_check_completed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'medical_check_completed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'equipment_issued': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'access_granted': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'training_completed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'passport_copy': forms.FileInput(attrs={'class': 'form-control'}),
            'visa_copy': forms.FileInput(attrs={'class': 'form-control'}),
            'emirates_id': forms.FileInput(attrs={'class': 'form-control'}),
            'educational_certificates': forms.FileInput(attrs={'class': 'form-control'}),
            'experience_certificates': forms.FileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Onboarding notes'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter offers that are accepted
        self.fields['offer'].queryset = Offer.objects.filter(
            status='accepted'
        ).order_by('-offer_date')
        # Filter active users for buddy assignment
        self.fields['buddy_assigned'].queryset = User.objects.filter(is_active=True).order_by('first_name', 'last_name')


class ApplicationSearchForm(forms.Form):
    """Form for searching and filtering applications"""
    
    STATUS_CHOICES = [('', 'All Statuses')] + Application.STATUS_CHOICES
    SOURCE_CHOICES = [('', 'All Sources')] + JobPosting.SOURCE_CHOICES
    
    keyword = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by candidate name, job title...'
        })
    )
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    source = forms.ChoiceField(
        choices=SOURCE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    experience_min = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Min experience'})
    )
    experience_max = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Max experience'})
    )


class InterviewScheduleForm(forms.Form):
    """Form for scheduling interviews"""
    
    candidate = forms.ModelChoiceField(
        queryset=Candidate.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    application = forms.ModelChoiceField(
        queryset=Application.objects.filter(status__in=['shortlisted', 'interview']),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    interview_type = forms.ChoiceField(
        choices=Interview.TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    scheduled_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'})
    )
    duration = forms.IntegerField(
        min_value=15,
        initial=60,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Duration in minutes'})
    )
    location = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Interview location'})
    )
    meeting_link = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Video call link'})
    )
    interviewers = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'})
    )


class RecruitmentMetricsForm(forms.ModelForm):
    """Form for creating and editing recruitment metrics"""
    
    class Meta:
        model = RecruitmentMetrics
        fields = [
            'period_start', 'period_end', 'total_applications',
            'applications_by_source', 'total_interviews', 'interviews_completed',
            'interviews_cancelled', 'total_offers', 'offers_accepted',
            'offers_rejected', 'avg_time_to_hire', 'avg_time_to_fill',
            'total_cost_per_hire', 'advertising_cost', 'agency_fees',
            'quality_of_hire_score', 'retention_rate'
        ]
        widgets = {
            'period_start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'period_end': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'total_applications': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'applications_by_source': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'JSON format: {"source": count}'}),
            'total_interviews': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'interviews_completed': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'interviews_cancelled': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'total_offers': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'offers_accepted': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'offers_rejected': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'avg_time_to_hire': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': 'Average days to hire'}),
            'avg_time_to_fill': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': 'Average days to fill position'}),
            'total_cost_per_hire': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': 0.01}),
            'advertising_cost': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': 0.01}),
            'agency_fees': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': 0.01}),
            'quality_of_hire_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'retention_rate': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100, 'step': 0.01, 'placeholder': 'Percentage'}),
        } 