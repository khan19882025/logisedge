from django.urls import path
from . import views

app_name = 'approval_workflow'

urlpatterns = [
    # Dashboard
    path('', views.approval_dashboard, name='dashboard'),
    
    # Workflow Types
    path('workflow-types/', views.WorkflowTypeListView.as_view(), name='workflow_type_list'),
    path('workflow-types/create/', views.WorkflowTypeCreateView.as_view(), name='workflow_type_create'),
    path('workflow-types/<int:pk>/update/', views.WorkflowTypeUpdateView.as_view(), name='workflow_type_update'),
    
    # Workflow Definitions
    path('workflow-definitions/', views.WorkflowDefinitionListView.as_view(), name='workflow_definition_list'),
    path('workflow-definitions/create/', views.WorkflowDefinitionCreateView.as_view(), name='workflow_definition_create'),
    path('workflow-definitions/<int:pk>/', views.WorkflowDefinitionDetailView.as_view(), name='workflow_definition_detail'),
    path('workflow-definitions/<int:pk>/update/', views.WorkflowDefinitionUpdateView.as_view(), name='workflow_definition_update'),
    path('workflow-definitions/<int:workflow_definition_id>/levels/', views.workflow_level_list, name='workflow_level_list'),
    path('workflow-definitions/<int:workflow_definition_id>/levels/create/', views.WorkflowLevelCreateView.as_view(), name='workflow_level_create'),
    
    # Approval Requests
    path('requests/', views.ApprovalRequestListView.as_view(), name='approval_request_list'),
    path('requests/create/', views.ApprovalRequestCreateView.as_view(), name='approval_request_create'),
    path('requests/<int:pk>/', views.ApprovalRequestDetailView.as_view(), name='approval_request_detail'),
    path('requests/<int:pk>/approve/', views.approve_request, name='approve_request'),
    path('requests/<int:pk>/comment/', views.add_comment, name='add_comment'),
    
    # My Approvals and Requests
    path('my-approvals/', views.my_approvals, name='my_approvals'),
    path('my-requests/', views.my_requests, name='my_requests'),
    
    # Workflow Templates
    path('templates/', views.workflow_templates, name='workflow_templates'),
    
    # Bulk Actions
    path('bulk-approve/', views.bulk_approve, name='bulk_approve'),
    
    # API Endpoints
    path('api/stats/', views.api_approval_stats, name='api_approval_stats'),
]
