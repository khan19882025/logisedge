from django.urls import path
from . import views

app_name = 'recruitment'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Job Requisitions
    path('requisitions/', views.requisition_list, name='requisition_list'),
    path('requisitions/create/', views.requisition_create, name='requisition_create'),
    path('requisitions/<uuid:pk>/', views.requisition_detail, name='requisition_detail'),
    path('requisitions/<uuid:pk>/update/', views.requisition_update, name='requisition_update'),
    path('requisitions/<uuid:pk>/delete/', views.requisition_delete, name='requisition_delete'),
    path('requisitions/<uuid:pk>/approve/', views.requisition_approve, name='requisition_approve'),
    
    # Job Postings
    path('postings/', views.posting_list, name='posting_list'),
    path('postings/create/', views.posting_create, name='posting_create'),
    path('postings/<uuid:pk>/update/', views.posting_update, name='posting_update'),
    
    # Candidates
    path('candidates/', views.candidate_list, name='candidate_list'),
    path('candidates/create/', views.candidate_create, name='candidate_create'),
    path('candidates/<uuid:pk>/', views.candidate_detail, name='candidate_detail'),
    path('candidates/<uuid:pk>/update/', views.candidate_update, name='candidate_update'),
    
    # Applications
    path('applications/', views.application_list, name='application_list'),
    path('applications/create/', views.application_create, name='application_create'),
    path('applications/<uuid:pk>/', views.application_detail, name='application_detail'),
    path('applications/<uuid:pk>/update/', views.application_update, name='application_update'),
    
    # Interviews
    path('interviews/', views.interview_list, name='interview_list'),
    path('interviews/create/', views.interview_create, name='interview_create'),
    path('interviews/<uuid:pk>/', views.interview_detail, name='interview_detail'),
    path('interviews/<uuid:pk>/update/', views.interview_update, name='interview_update'),
    
    # Offers
    path('offers/', views.offer_list, name='offer_list'),
    path('offers/create/', views.offer_create, name='offer_create'),
    path('offers/<uuid:pk>/', views.offer_detail, name='offer_detail'),
    path('offers/<uuid:pk>/update/', views.offer_update, name='offer_update'),
    
    # Onboarding
    path('onboarding/', views.onboarding_list, name='onboarding_list'),
    path('onboarding/create/', views.onboarding_create, name='onboarding_create'),
    path('onboarding/<uuid:pk>/', views.onboarding_detail, name='onboarding_detail'),
    path('onboarding/<uuid:pk>/update/', views.onboarding_update, name='onboarding_update'),
    
    # Pipeline
    path('pipeline/', views.pipeline_view, name='pipeline'),
    
    # Reports
    path('reports/', views.reports_view, name='reports'),
    
    # AJAX endpoints
    path('api/applications/<uuid:pk>/status/', views.update_application_status, name='update_application_status'),
    path('api/interviews/<uuid:pk>/status/', views.update_interview_status, name='update_interview_status'),
    path('api/candidates/<uuid:candidate_id>/applications/', views.get_candidate_applications, name='get_candidate_applications'),
    path('api/jobs/<uuid:job_id>/applications/', views.get_job_applications, name='get_job_applications'),
    path('api/status-counts/', views.get_status_counts, name='get_status_counts'),
] 