from django.urls import path
from . import views

app_name = 'merge_duplicates'

urlpatterns = [
    # Dashboard
    path('', views.merge_duplicates_dashboard, name='merge_duplicates_dashboard'),
    
    # Sessions
    path('sessions/', views.session_list, name='session_list'),
    path('sessions/create/', views.session_create, name='session_create'),
    path('sessions/<int:pk>/', views.session_detail, name='session_detail'),
    path('sessions/<int:pk>/start/', views.session_start, name='session_start'),
    
    # Duplicate Groups
    path('groups/<int:pk>/', views.duplicate_group_detail, name='duplicate_group_detail'),
    path('groups/<int:pk>/review/', views.duplicate_group_review, name='duplicate_group_review'),
    
    # Rules
    path('rules/', views.rules_list, name='rules_list'),
    path('rules/create/', views.rule_create, name='rule_create'),
    path('rules/<int:pk>/edit/', views.rule_edit, name='rule_edit'),
    
    # Scheduled Tasks
    path('scheduled-tasks/', views.scheduled_tasks_list, name='scheduled_tasks_list'),
    path('scheduled-tasks/create/', views.scheduled_task_create, name='scheduled_task_create'),
    
    # Bulk Operations
    path('bulk-merge/', views.bulk_merge, name='bulk_merge'),
    
    # Analytics
    path('analytics/', views.merge_analytics, name='analytics'),
    
    # API Endpoints
    path('api/start-session/', views.api_start_session, name='api_start_session'),
    path('api/merge-records/', views.api_merge_records, name='api_merge_records'),
]
