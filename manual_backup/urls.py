from django.urls import path
from . import views

app_name = 'manual_backup'

urlpatterns = [
    # Dashboard and main views
    path('', views.dashboard, name='dashboard'),
    path('history/', views.backup_history, name='backup_history'),
    path('detail/<uuid:backup_id>/', views.backup_detail, name='backup_detail'),
    
    # Backup operations
    path('initiate/', views.initiate_backup, name='initiate_backup'),
    path('configurations/', views.backup_configurations, name='backup_configurations'),
    path('configurations/create/', views.create_configuration, name='create_configuration'),
    path('configurations/<int:config_id>/edit/', views.edit_configuration, name='edit_configuration'),
    
    # Storage management
    path('storage/', views.storage_locations, name='storage_locations'),
    path('storage/create/', views.create_storage_location, name='create_storage_location'),
    path('storage/<int:location_id>/edit/', views.edit_storage_location, name='edit_storage_location'),
    
    # Monitoring and logs
    path('audit-log/', views.audit_log, name='audit_log'),
    path('restore/', views.restore_options, name='restore_options'),
    
    # API endpoints
    path('api/start/<uuid:backup_id>/', views.start_backup_api, name='start_backup_api'),
    path('api/progress/<uuid:backup_id>/', views.backup_progress_api, name='backup_progress_api'),
    path('api/step-progress/<uuid:backup_id>/<int:step_id>/', views.update_step_progress_api, name='update_step_progress_api'),
    path('api/complete/<uuid:backup_id>/', views.complete_backup_api, name='complete_backup_api'),
    path('api/dashboard-stats/', views.dashboard_stats_api, name='dashboard_stats_api'),
    path('api/test-config/<int:config_id>/', views.test_configuration_api, name='test_configuration_api'),
    path('api/config/<int:config_id>/activate/', views.activate_configuration_api, name='activate_configuration_api'),
    path('api/config/<int:config_id>/deactivate/', views.deactivate_configuration_api, name='deactivate_configuration_api'),
    path('api/restore-details/<uuid:backup_id>/', views.restore_details_api, name='restore_details_api'),
    path('api/restore/<uuid:backup_id>/', views.start_restore_api, name='start_restore_api'),
]
