from django.urls import path
from . import views

app_name = 'system_logs'

urlpatterns = [
    # Dashboard and main views
    path('', views.dashboard, name='dashboard'),
    path('logs/', views.SystemLogListView.as_view(), name='system_log_list'),
    path('logs/<uuid:pk>/', views.SystemLogDetailView.as_view(), name='system_log_detail'),
    
    # Search and export
    path('search/', views.system_log_search, name='system_log_search'),
    path('export/', views.system_log_export, name='system_log_export'),
    path('chart-data/', views.system_log_chart_data, name='system_log_chart_data'),
    
    # Bulk actions
    path('bulk-action/', views.bulk_action, name='bulk_action'),
    
    # Error Patterns
    path('patterns/', views.ErrorPatternListView.as_view(), name='error_pattern_list'),
    path('patterns/<uuid:pk>/', views.ErrorPatternDetailView.as_view(), name='error_pattern_detail'),
    path('patterns/create/', views.ErrorPatternCreateView.as_view(), name='error_pattern_create'),
    path('patterns/<uuid:pk>/edit/', views.ErrorPatternUpdateView.as_view(), name='error_pattern_update'),
    path('patterns/<uuid:pk>/delete/', views.ErrorPatternDeleteView.as_view(), name='error_pattern_delete'),
    
    # Debug Sessions
    path('sessions/', views.DebugSessionListView.as_view(), name='debug_session_list'),
    path('sessions/<uuid:pk>/', views.DebugSessionDetailView.as_view(), name='debug_session_detail'),
    path('sessions/create/', views.DebugSessionCreateView.as_view(), name='debug_session_create'),
    path('sessions/<uuid:pk>/edit/', views.DebugSessionUpdateView.as_view(), name='debug_session_update'),
    path('sessions/<uuid:pk>/delete/', views.DebugSessionDeleteView.as_view(), name='debug_session_delete'),
    
    # Log Retention Policies
    path('retention-policies/', views.LogRetentionPolicyListView.as_view(), name='log_retention_policy_list'),
    path('retention-policies/create/', views.LogRetentionPolicyCreateView.as_view(), name='log_retention_policy_create'),
    path('retention-policies/<uuid:pk>/edit/', views.LogRetentionPolicyUpdateView.as_view(), name='log_retention_policy_update'),
    path('retention-policies/<uuid:pk>/delete/', views.LogRetentionPolicyDeleteView.as_view(), name='log_retention_policy_delete'),
    path('retention-cleanup/', views.log_retention_cleanup, name='log_retention_cleanup'),
]
