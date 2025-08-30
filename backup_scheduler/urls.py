from django.urls import path
from . import views
from . import restore_views

app_name = 'backup_scheduler'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Backup Schedules
    path('schedules/', views.schedule_list, name='schedule_list'),
    path('schedules/create/', views.schedule_create, name='schedule_create'),
    path('schedules/<int:pk>/edit/', views.schedule_edit, name='schedule_edit'),
    path('schedules/<int:pk>/delete/', views.schedule_delete, name='schedule_delete'),
    
    # Manual Backups
    path('manual-backup/', views.manual_backup, name='manual_backup'),
    
    # Backup Executions
    path('executions/', views.execution_list, name='execution_list'),
    path('executions/<int:pk>/', views.execution_detail, name='execution_detail'),
    path('executions/<int:pk>/cancel/', views.execution_cancel, name='execution_cancel'),
    
    # Configuration
    path('backup-types/', views.backup_type_list, name='backup_type_list'),
    path('backup-scopes/', views.backup_scope_list, name='backup_scope_list'),
    path('storage-locations/', views.storage_location_list, name='storage_location_list'),
    path('retention-policies/', views.retention_policy_list, name='retention_policy_list'),
    path('alerts/', views.alert_list, name='alert_list'),
    path('disaster-recovery/', views.disaster_recovery_list, name='disaster_recovery_list'),
    
    # Logs
    path('logs/', views.logs_list, name='logs_list'),
    
    # API Endpoints
    path('api/backup-status/', views.api_backup_status, name='api_backup_status'),
    path('api/storage-usage/', views.api_storage_usage, name='api_storage_usage'),
    
    # Webhooks
    path('webhook/backup-status/', views.backup_status_webhook, name='backup_status_webhook'),
    
    # Restore Management
    path('restore/', restore_views.restore_dashboard, name='restore_dashboard'),
    path('restore/requests/', restore_views.restore_request_list, name='restore_request_list'),
    path('restore/requests/create/', restore_views.restore_request_create, name='restore_request_create'),
    path('restore/requests/<int:pk>/', restore_views.restore_request_detail, name='restore_request_detail'),
    path('restore/requests/<int:pk>/edit/', restore_views.restore_request_edit, name='restore_request_edit'),
    path('restore/requests/<int:pk>/delete/', restore_views.restore_request_delete, name='restore_request_delete'),
    path('restore/requests/<int:pk>/approve/', restore_views.restore_request_approve, name='restore_request_approve'),
    path('restore/requests/<int:pk>/execute/', restore_views.restore_request_execute, name='restore_request_execute'),
    
    # Restore Executions
    path('restore/executions/', restore_views.restore_execution_list, name='restore_execution_list'),
    path('restore/executions/<int:pk>/', restore_views.restore_execution_detail, name='restore_execution_detail'),
    path('restore/executions/<int:pk>/cancel/', restore_views.restore_execution_cancel, name='restore_execution_cancel'),
    
    # Restore Validation
    path('restore/validation/<int:pk>/', restore_views.restore_validation, name='restore_validation'),
    
    # Restore Webhooks
    path('webhook/restore-status/', restore_views.restore_status_webhook, name='restore_status_webhook'),
]
