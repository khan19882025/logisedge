from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta
import json

from .models import (
    JobRequisition, JobPosting, Candidate, Application, 
    Interview, Offer, Onboarding, RecruitmentMetrics
)
from .forms import (
    JobRequisitionForm, JobPostingForm, CandidateForm, ApplicationForm,
    InterviewForm, OfferForm, OnboardingForm, ApplicationSearchForm,
    InterviewScheduleForm, RecruitmentMetricsForm
)


@login_required
def dashboard(request):
    """Recruitment dashboard with key metrics and pipeline overview"""
    
    # Get current date
    today = timezone.now().date()
    
    # Dashboard metrics
    total_requisitions = JobRequisition.objects.filter(is_active=True).count()
    open_requisitions = JobRequisition.objects.filter(
        is_active=True, 
        status='approved',
        closing_date__gte=today
    ).count()
    
    total_applications = Application.objects.count()
    recent_applications = Application.objects.filter(
        applied_date__gte=today - timedelta(days=7)
    ).count()
    
    total_interviews = Interview.objects.count()
    upcoming_interviews = Interview.objects.filter(
        scheduled_date__gte=timezone.now(),
        status='scheduled'
    ).count()
    
    total_offers = Offer.objects.count()
    pending_offers = Offer.objects.filter(status='sent').count()
    
    # Pipeline data
    pipeline_data = {
        'applied': Application.objects.filter(status='applied').count(),
        'screening': Application.objects.filter(status='screening').count(),
        'shortlisted': Application.objects.filter(status='shortlisted').count(),
        'interview': Application.objects.filter(status='interview').count(),
        'offer': Application.objects.filter(status='offer').count(),
        'hired': Application.objects.filter(status='hired').count(),
    }
    
    # Recent activities
    recent_requisitions = JobRequisition.objects.filter(
        is_active=True
    ).order_by('-created_at')[:5]
    
    recent_applications_list = Application.objects.select_related(
        'candidate', 'job_posting'
    ).order_by('-applied_date')[:5]
    
    upcoming_interviews_list = Interview.objects.select_related(
        'candidate', 'application'
    ).filter(
        scheduled_date__gte=timezone.now(),
        status='scheduled'
    ).order_by('scheduled_date')[:5]
    
    # Source-wise applications
    source_stats = Application.objects.values(
        'job_posting__source'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    context = {
        'total_requisitions': total_requisitions,
        'open_requisitions': open_requisitions,
        'total_applications': total_applications,
        'recent_applications': recent_applications,
        'total_interviews': total_interviews,
        'upcoming_interviews': upcoming_interviews,
        'total_offers': total_offers,
        'pending_offers': pending_offers,
        'pipeline_data': pipeline_data,
        'recent_requisitions': recent_requisitions,
        'recent_applications_list': recent_applications_list,
        'upcoming_interviews_list': upcoming_interviews_list,
        'source_stats': source_stats,
    }
    
    return render(request, 'recruitment/dashboard.html', context)


# Job Requisition Views
@login_required
def requisition_list(request):
    """List all job requisitions"""
    requisitions = JobRequisition.objects.filter(is_active=True).order_by('-created_at')
    
    # Search and filter
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    department = request.GET.get('department', '')
    
    if search:
        requisitions = requisitions.filter(
            Q(title__icontains=search) |
            Q(department__icontains=search) |
            Q(location__icontains=search)
        )
    
    if status:
        requisitions = requisitions.filter(status=status)
    
    if department:
        requisitions = requisitions.filter(department__icontains=department)
    
    # Pagination
    paginator = Paginator(requisitions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'department': department,
    }
    
    return render(request, 'recruitment/requisition_list.html', context)


@login_required
def requisition_create(request):
    """Create a new job requisition"""
    if request.method == 'POST':
        form = JobRequisitionForm(request.POST, user=request.user)
        if form.is_valid():
            requisition = form.save(commit=False)
            requisition.requested_by = request.user
            requisition.save()
            messages.success(request, 'Job requisition created successfully!')
            return redirect('recruitment:requisition_list')
    else:
        form = JobRequisitionForm(user=request.user)
    
    context = {
        'form': form,
        'title': 'Create Job Requisition',
    }
    
    return render(request, 'recruitment/requisition_form.html', context)


@login_required
def requisition_update(request, pk):
    """Update a job requisition"""
    requisition = get_object_or_404(JobRequisition, pk=pk)
    
    if request.method == 'POST':
        form = JobRequisitionForm(request.POST, instance=requisition, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Job requisition updated successfully!')
            return redirect('recruitment:requisition_list')
    else:
        form = JobRequisitionForm(instance=requisition, user=request.user)
    
    context = {
        'form': form,
        'requisition': requisition,
        'title': 'Update Job Requisition',
    }
    
    return render(request, 'recruitment/requisition_form.html', context)


@login_required
def requisition_delete(request, pk):
    """Delete a job requisition"""
    requisition = get_object_or_404(JobRequisition, pk=pk)
    
    if request.method == 'POST':
        requisition.delete()
        messages.success(request, 'Job requisition deleted successfully!')
        return redirect('recruitment:requisition_list')
    
    context = {
        'requisition': requisition,
    }
    
    return render(request, 'recruitment/requisition_confirm_delete.html', context)


@login_required
def requisition_detail(request, pk):
    """View job requisition details"""
    requisition = get_object_or_404(JobRequisition, pk=pk)
    
    # Get related job postings
    job_postings = JobPosting.objects.filter(requisition=requisition)
    
    # Get applications for this requisition
    applications = Application.objects.filter(
        job_posting__requisition=requisition
    ).select_related('candidate', 'job_posting')
    
    context = {
        'requisition': requisition,
        'job_postings': job_postings,
        'applications': applications,
    }
    
    return render(request, 'recruitment/requisition_detail.html', context)


@login_required
@permission_required('recruitment.change_jobrequisition')
def requisition_approve(request, pk):
    """Approve a job requisition"""
    requisition = get_object_or_404(JobRequisition, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'hr_approve':
            requisition.status = 'pending_director'
            requisition.approved_by_hr = request.user
            requisition.hr_approval_date = timezone.now()
            messages.success(request, 'Requisition approved by HR!')
        elif action == 'director_approve':
            requisition.status = 'approved'
            requisition.approved_by_director = request.user
            requisition.director_approval_date = timezone.now()
            messages.success(request, 'Requisition approved by Director!')
        elif action == 'reject':
            requisition.status = 'rejected'
            messages.success(request, 'Requisition rejected!')
        
        requisition.save()
    
    return redirect('recruitment:requisition_detail', pk=pk)


# Job Posting Views
@login_required
def posting_list(request):
    """List all job postings"""
    postings = JobPosting.objects.all().order_by('-created_at')
    
    # Search and filter
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    source = request.GET.get('source', '')
    
    if search:
        postings = postings.filter(
            Q(title__icontains=search) |
            Q(requisition__department__icontains=search)
        )
    
    if status:
        postings = postings.filter(status=status)
    
    if source:
        postings = postings.filter(source=source)
    
    # Pagination
    paginator = Paginator(postings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'source': source,
    }
    
    return render(request, 'recruitment/posting_list.html', context)


@login_required
def posting_create(request):
    """Create a new job posting"""
    if request.method == 'POST':
        form = JobPostingForm(request.POST)
        if form.is_valid():
            posting = form.save()
            messages.success(request, 'Job posting created successfully!')
            return redirect('recruitment:posting_list')
    else:
        form = JobPostingForm()
    
    context = {
        'form': form,
        'title': 'Create Job Posting',
    }
    
    return render(request, 'recruitment/posting_form.html', context)


@login_required
def posting_update(request, pk):
    """Update a job posting"""
    posting = get_object_or_404(JobPosting, pk=pk)
    
    if request.method == 'POST':
        form = JobPostingForm(request.POST, instance=posting)
        if form.is_valid():
            form.save()
            messages.success(request, 'Job posting updated successfully!')
            return redirect('recruitment:posting_list')
    else:
        form = JobPostingForm(instance=posting)
    
    context = {
        'form': form,
        'posting': posting,
        'title': 'Update Job Posting',
    }
    
    return render(request, 'recruitment/posting_form.html', context)


# Candidate Views
@login_required
def candidate_list(request):
    """List all candidates"""
    candidates = Candidate.objects.filter(is_active=True).order_by('-created_at')
    
    # Search and filter
    search = request.GET.get('search', '')
    source = request.GET.get('source', '')
    experience_min = request.GET.get('experience_min', '')
    experience_max = request.GET.get('experience_max', '')
    
    if search:
        candidates = candidates.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search) |
            Q(current_position__icontains=search)
        )
    
    if source:
        candidates = candidates.filter(source=source)
    
    if experience_min:
        candidates = candidates.filter(years_of_experience__gte=experience_min)
    
    if experience_max:
        candidates = candidates.filter(years_of_experience__lte=experience_max)
    
    # Pagination
    paginator = Paginator(candidates, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'source': source,
        'experience_min': experience_min,
        'experience_max': experience_max,
    }
    
    return render(request, 'recruitment/candidate_list.html', context)


@login_required
def candidate_create(request):
    """Create a new candidate"""
    if request.method == 'POST':
        form = CandidateForm(request.POST, request.FILES)
        if form.is_valid():
            candidate = form.save()
            messages.success(request, 'Candidate created successfully!')
            return redirect('recruitment:candidate_list')
    else:
        form = CandidateForm()
    
    context = {
        'form': form,
        'title': 'Add New Candidate',
    }
    
    return render(request, 'recruitment/candidate_form.html', context)


@login_required
def candidate_update(request, pk):
    """Update a candidate"""
    candidate = get_object_or_404(Candidate, pk=pk)
    
    if request.method == 'POST':
        form = CandidateForm(request.POST, request.FILES, instance=candidate)
        if form.is_valid():
            form.save()
            messages.success(request, 'Candidate updated successfully!')
            return redirect('recruitment:candidate_list')
    else:
        form = CandidateForm(instance=candidate)
    
    context = {
        'form': form,
        'candidate': candidate,
        'title': 'Update Candidate',
    }
    
    return render(request, 'recruitment/candidate_form.html', context)


@login_required
def candidate_detail(request, pk):
    """View candidate details"""
    candidate = get_object_or_404(Candidate, pk=pk)
    
    # Get applications for this candidate
    applications = Application.objects.filter(
        candidate=candidate
    ).select_related('job_posting').order_by('-applied_date')
    
    # Get interviews for this candidate
    interviews = Interview.objects.filter(
        candidate=candidate
    ).select_related('application').order_by('-scheduled_date')
    
    context = {
        'candidate': candidate,
        'applications': applications,
        'interviews': interviews,
    }
    
    return render(request, 'recruitment/candidate_detail.html', context)


# Application Views
@login_required
def application_list(request):
    """List all applications with search and filter"""
    applications = Application.objects.select_related(
        'candidate', 'job_posting'
    ).order_by('-applied_date')
    
    # Search form
    search_form = ApplicationSearchForm(request.GET)
    if search_form.is_valid():
        keyword = search_form.cleaned_data.get('keyword')
        status = search_form.cleaned_data.get('status')
        source = search_form.cleaned_data.get('source')
        date_from = search_form.cleaned_data.get('date_from')
        date_to = search_form.cleaned_data.get('date_to')
        experience_min = search_form.cleaned_data.get('experience_min')
        experience_max = search_form.cleaned_data.get('experience_max')
        
        if keyword:
            applications = applications.filter(
                Q(candidate__first_name__icontains=keyword) |
                Q(candidate__last_name__icontains=keyword) |
                Q(job_posting__title__icontains=keyword) |
                Q(candidate__email__icontains=keyword)
            )
        
        if status:
            applications = applications.filter(status=status)
        
        if source:
            applications = applications.filter(job_posting__source=source)
        
        if date_from:
            applications = applications.filter(applied_date__date__gte=date_from)
        
        if date_to:
            applications = applications.filter(applied_date__date__lte=date_to)
        
        if experience_min:
            applications = applications.filter(candidate__years_of_experience__gte=experience_min)
        
        if experience_max:
            applications = applications.filter(candidate__years_of_experience__lte=experience_max)
    
    # Pagination
    paginator = Paginator(applications, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
    }
    
    return render(request, 'recruitment/application_list.html', context)


@login_required
def application_create(request):
    """Create a new application"""
    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            application = form.save()
            messages.success(request, 'Application created successfully!')
            return redirect('recruitment:application_list')
    else:
        form = ApplicationForm()
    
    context = {
        'form': form,
        'title': 'Create Application',
    }
    
    return render(request, 'recruitment/application_form.html', context)


@login_required
def application_update(request, pk):
    """Update an application"""
    application = get_object_or_404(Application, pk=pk)
    
    if request.method == 'POST':
        form = ApplicationForm(request.POST, instance=application)
        if form.is_valid():
            old_status = application.status
            application = form.save()
            
            # Update status changed info
            if old_status != application.status:
                application.status_changed_by = request.user
                application.save()
            
            messages.success(request, 'Application updated successfully!')
            return redirect('recruitment:application_list')
    else:
        form = ApplicationForm(instance=application)
    
    context = {
        'form': form,
        'application': application,
        'title': 'Update Application',
    }
    
    return render(request, 'recruitment/application_form.html', context)


@login_required
def application_detail(request, pk):
    """View application details"""
    application = get_object_or_404(Application, pk=pk)
    
    # Get interviews for this application
    interviews = Interview.objects.filter(
        application=application
    ).order_by('scheduled_date')
    
    # Get offer for this application
    try:
        offer = Offer.objects.get(application=application)
    except Offer.DoesNotExist:
        offer = None
    
    context = {
        'application': application,
        'interviews': interviews,
        'offer': offer,
    }
    
    return render(request, 'recruitment/application_detail.html', context)


# Interview Views
@login_required
def interview_list(request):
    """List all interviews"""
    interviews = Interview.objects.select_related(
        'candidate', 'application'
    ).order_by('-scheduled_date')
    
    # Filter by status
    status = request.GET.get('status', '')
    if status:
        interviews = interviews.filter(status=status)
    
    # Pagination
    paginator = Paginator(interviews, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status': status,
    }
    
    return render(request, 'recruitment/interview_list.html', context)


@login_required
def interview_create(request):
    """Create a new interview"""
    if request.method == 'POST':
        form = InterviewForm(request.POST)
        if form.is_valid():
            interview = form.save()
            messages.success(request, 'Interview scheduled successfully!')
            return redirect('recruitment:interview_list')
    else:
        form = InterviewForm()
    
    context = {
        'form': form,
        'title': 'Schedule Interview',
    }
    
    return render(request, 'recruitment/interview_form.html', context)


@login_required
def interview_update(request, pk):
    """Update an interview"""
    interview = get_object_or_404(Interview, pk=pk)
    
    if request.method == 'POST':
        form = InterviewForm(request.POST, instance=interview)
        if form.is_valid():
            interview = form.save()
            messages.success(request, 'Interview updated successfully!')
            return redirect('recruitment:interview_list')
    else:
        form = InterviewForm(instance=interview)
    
    context = {
        'form': form,
        'interview': interview,
        'title': 'Update Interview',
    }
    
    return render(request, 'recruitment/interview_form.html', context)


@login_required
def interview_detail(request, pk):
    """View interview details"""
    interview = get_object_or_404(Interview, pk=pk)
    
    context = {
        'interview': interview,
    }
    
    return render(request, 'recruitment/interview_detail.html', context)


# Offer Views
@login_required
def offer_list(request):
    """List all offers"""
    offers = Offer.objects.select_related(
        'application__candidate', 'application__job_posting'
    ).order_by('-offer_date')
    
    # Filter by status
    status = request.GET.get('status', '')
    if status:
        offers = offers.filter(status=status)
    
    # Pagination
    paginator = Paginator(offers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status': status,
    }
    
    return render(request, 'recruitment/offer_list.html', context)


@login_required
def offer_create(request):
    """Create a new offer"""
    if request.method == 'POST':
        form = OfferForm(request.POST, request.FILES)
        if form.is_valid():
            offer = form.save()
            messages.success(request, 'Offer created successfully!')
            return redirect('recruitment:offer_list')
    else:
        form = OfferForm()
    
    context = {
        'form': form,
        'title': 'Create Offer',
    }
    
    return render(request, 'recruitment/offer_form.html', context)


@login_required
def offer_update(request, pk):
    """Update an offer"""
    offer = get_object_or_404(Offer, pk=pk)
    
    if request.method == 'POST':
        form = OfferForm(request.POST, request.FILES, instance=offer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Offer updated successfully!')
            return redirect('recruitment:offer_list')
    else:
        form = OfferForm(instance=offer)
    
    context = {
        'form': form,
        'offer': offer,
        'title': 'Update Offer',
    }
    
    return render(request, 'recruitment/offer_form.html', context)


@login_required
def offer_detail(request, pk):
    """View offer details"""
    offer = get_object_or_404(Offer, pk=pk)
    
    # Get onboarding record if exists
    try:
        onboarding = Onboarding.objects.get(offer=offer)
    except Onboarding.DoesNotExist:
        onboarding = None
    
    context = {
        'offer': offer,
        'onboarding': onboarding,
    }
    
    return render(request, 'recruitment/offer_detail.html', context)


# Onboarding Views
@login_required
def onboarding_list(request):
    """List all onboarding records"""
    onboardings = Onboarding.objects.select_related(
        'offer__application__candidate'
    ).order_by('-created_at')
    
    # Filter by status
    status = request.GET.get('status', '')
    if status:
        onboardings = onboardings.filter(status=status)
    
    # Pagination
    paginator = Paginator(onboardings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status': status,
    }
    
    return render(request, 'recruitment/onboarding_list.html', context)


@login_required
def onboarding_create(request):
    """Create a new onboarding record"""
    if request.method == 'POST':
        form = OnboardingForm(request.POST, request.FILES)
        if form.is_valid():
            onboarding = form.save()
            messages.success(request, 'Onboarding record created successfully!')
            return redirect('recruitment:onboarding_list')
    else:
        form = OnboardingForm()
    
    context = {
        'form': form,
        'title': 'Create Onboarding Record',
    }
    
    return render(request, 'recruitment/onboarding_form.html', context)


@login_required
def onboarding_update(request, pk):
    """Update an onboarding record"""
    onboarding = get_object_or_404(Onboarding, pk=pk)
    
    if request.method == 'POST':
        form = OnboardingForm(request.POST, request.FILES, instance=onboarding)
        if form.is_valid():
            form.save()
            messages.success(request, 'Onboarding record updated successfully!')
            return redirect('recruitment:onboarding_list')
    else:
        form = OnboardingForm(instance=onboarding)
    
    context = {
        'form': form,
        'onboarding': onboarding,
        'title': 'Update Onboarding Record',
    }
    
    return render(request, 'recruitment/onboarding_form.html', context)


@login_required
def onboarding_detail(request, pk):
    """View onboarding details"""
    onboarding = get_object_or_404(Onboarding, pk=pk)
    
    context = {
        'onboarding': onboarding,
    }
    
    return render(request, 'recruitment/onboarding_detail.html', context)


# Pipeline Views
@login_required
def pipeline_view(request):
    """Kanban-style pipeline view"""
    # Get applications grouped by status
    pipeline_data = {}
    
    for status, label in Application.STATUS_CHOICES:
        applications = Application.objects.filter(
            status=status
        ).select_related('candidate', 'job_posting').order_by('-applied_date')
        pipeline_data[status] = {
            'label': label,
            'applications': applications,
            'count': applications.count()
        }
    
    context = {
        'pipeline_data': pipeline_data,
    }
    
    return render(request, 'recruitment/pipeline.html', context)


# Reports Views
@login_required
def reports_view(request):
    """Recruitment reports and analytics"""
    
    # Date range
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    if request.GET.get('start_date'):
        start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').date()
    if request.GET.get('end_date'):
        end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').date()
    
    # Applications by source
    source_stats = Application.objects.filter(
        applied_date__date__range=[start_date, end_date]
    ).values('job_posting__source').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Applications by status
    status_stats = Application.objects.filter(
        applied_date__date__range=[start_date, end_date]
    ).values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Time to hire metrics
    hired_applications = Application.objects.filter(
        status='hired',
        applied_date__date__range=[start_date, end_date]
    )
    
    avg_time_to_hire = 0
    if hired_applications.exists():
        total_days = 0
        for app in hired_applications:
            # Find the date when status changed to 'hired'
            # This is a simplified calculation
            days = (end_date - app.applied_date.date()).days
            total_days += days
        avg_time_to_hire = total_days / hired_applications.count()
    
    # Interview statistics
    interview_stats = Interview.objects.filter(
        scheduled_date__date__range=[start_date, end_date]
    ).aggregate(
        total=Count('id'),
        completed=Count('id', filter=Q(status='completed')),
        cancelled=Count('id', filter=Q(status='cancelled')),
        no_show=Count('id', filter=Q(status='no_show'))
    )
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'source_stats': source_stats,
        'status_stats': status_stats,
        'avg_time_to_hire': round(avg_time_to_hire, 1),
        'interview_stats': interview_stats,
        'hired_count': hired_applications.count(),
    }
    
    return render(request, 'recruitment/reports.html', context)


# AJAX Views
@login_required
@require_http_methods(["POST"])
def update_application_status(request, pk):
    """Update application status via AJAX"""
    application = get_object_or_404(Application, pk=pk)
    new_status = request.POST.get('status')
    
    if new_status in dict(Application.STATUS_CHOICES):
        old_status = application.status
        application.status = new_status
        application.status_changed_by = request.user
        application.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Status updated from {old_status} to {new_status}',
            'new_status': new_status
        })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid status'
    }, status=400)


@login_required
@require_http_methods(["POST"])
def update_interview_status(request, pk):
    """Update interview status via AJAX"""
    interview = get_object_or_404(Interview, pk=pk)
    new_status = request.POST.get('status')
    
    if new_status in dict(Interview.STATUS_CHOICES):
        old_status = interview.status
        interview.status = new_status
        interview.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Interview status updated from {old_status} to {new_status}',
            'new_status': new_status
        })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid status'
    }, status=400)


@login_required
def get_candidate_applications(request, candidate_id):
    """Get applications for a specific candidate"""
    applications = Application.objects.filter(
        candidate_id=candidate_id
    ).select_related('job_posting').values(
        'id', 'job_posting__title', 'status', 'applied_date'
    )
    
    return JsonResponse({
        'applications': list(applications)
    })


@login_required
def get_job_applications(request, job_id):
    """Get applications for a specific job posting"""
    applications = Application.objects.filter(
        job_posting_id=job_id
    ).select_related('candidate').values(
        'id', 'candidate__first_name', 'candidate__last_name', 
        'candidate__email', 'status', 'applied_date'
    )
    
    return JsonResponse({
        'applications': list(applications)
    })


@login_required
def get_status_counts(request):
    """Get status counts for dashboard widgets"""
    from django.db.models import Count
    
    # Get counts for different statuses
    application_counts = Application.objects.values('status').annotate(
        count=Count('id')
    )
    
    requisition_counts = JobRequisition.objects.values('status').annotate(
        count=Count('id')
    )
    
    interview_counts = Interview.objects.values('status').annotate(
        count=Count('id')
    )
    
    # Convert to dictionary format
    application_status_counts = {item['status']: item['count'] for item in application_counts}
    requisition_status_counts = {item['status']: item['count'] for item in requisition_counts}
    interview_status_counts = {item['status']: item['count'] for item in interview_counts}
    
    return JsonResponse({
        'applications': application_status_counts,
        'requisitions': requisition_status_counts,
        'interviews': interview_status_counts,
    })
