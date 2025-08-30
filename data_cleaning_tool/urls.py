from django.urls import path, include
from . import views
from .merge_duplicates import views as merge_views

app_name = 'data_cleaning_tool'

urlpatterns = [
    # Dashboard and main views
    path('', views.dashboard, name='dashboard'),
    path('quick-clean/', views.quick_clean, name='quick_clean'),
    
    # Session management
    path('sessions/', views.session_list, name='session_list'),
    path('sessions/create/', views.session_create, name='session_create'),
    path('sessions/<int:pk>/', views.session_detail, name='session_detail'),
    path('sessions/<int:pk>/configure/', views.session_configure, name='session_configure'),
    path('sessions/<int:pk>/export/', views.session_export, name='session_export'),
    path('sessions/<int:pk>/rerun/', views.session_rerun, name='session_rerun'),
    
    # Rule management
    path('rules/', views.rule_list, name='rule_list'),
    path('rules/create/', views.rule_create, name='rule_create'),
    path('rules/<int:pk>/edit/', views.rule_edit, name='rule_edit'),
    path('rules/<int:pk>/delete/', views.rule_delete, name='rule_delete'),
    
    # Schedule management
    path('schedules/', views.schedule_list, name='schedule_list'),
    path('schedules/create/', views.schedule_create, name='schedule_create'),
    path('schedules/<int:pk>/edit/', views.schedule_edit, name='schedule_edit'),
    
    # Audit and reporting
    path('audit-logs/', views.audit_logs, name='audit_logs'),
    path('reports/', views.reports, name='reports'),
    path('reports/<int:pk>/', views.report_detail, name='report_detail'),
    
    # API endpoints
    path('api/sessions/<int:pk>/start/', views.api_start_cleaning, name='api_start_cleaning'),
    path('api/sessions/<int:pk>/progress/', views.api_cleaning_progress, name='api_cleaning_progress'),
    
    # Merge Duplicates functionality
    path('merge-duplicates/', merge_views.merge_duplicates_dashboard, name='merge_duplicates_dashboard'),
    path('merge-duplicates/sessions/', merge_views.session_list, name='merge_duplicates_session_list'),
    path('merge-duplicates/sessions/create/', merge_views.session_create, name='merge_duplicates_session_create'),
    path('merge-duplicates/sessions/<int:pk>/', merge_views.session_detail, name='merge_duplicates_session_detail'),
    path('merge-duplicates/sessions/<int:pk>/start/', merge_views.session_start, name='merge_duplicates_session_start'),
    path('merge-duplicates/groups/<int:pk>/', merge_views.duplicate_group_detail, name='merge_duplicates_group_detail'),
    path('merge-duplicates/groups/<int:pk>/review/', merge_views.duplicate_group_review, name='merge_duplicates_group_review'),
    path('merge-duplicates/rules/', merge_views.rules_list, name='merge_duplicates_rules_list'),
    path('merge-duplicates/rules/create/', merge_views.rule_create, name='merge_duplicates_rule_create'),
    path('merge-duplicates/rules/<int:pk>/edit/', merge_views.rule_edit, name='merge_duplicates_rule_edit'),
    path('merge-duplicates/scheduled-tasks/', merge_views.scheduled_tasks_list, name='merge_duplicates_scheduled_tasks_list'),
    path('merge-duplicates/scheduled-tasks/create/', merge_views.scheduled_task_create, name='merge_duplicates_scheduled_task_create'),
    path('merge-duplicates/bulk-merge/', merge_views.bulk_merge, name='merge_duplicates_bulk_merge'),
    path('merge-duplicates/analytics/', merge_views.merge_analytics, name='merge_duplicates_analytics'),
    path('merge-duplicates/api/start-session/', merge_views.api_start_session, name='merge_duplicates_api_start_session'),
    path('merge-duplicates/api/merge-records/', merge_views.api_merge_records, name='merge_duplicates_api_merge_records'),
]
