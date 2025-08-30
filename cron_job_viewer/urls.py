from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Set app name for namespace
app_name = 'cron_job_viewer'

# Create router for API endpoints
router = DefaultRouter()
router.register(r'cron-jobs', views.CronJobViewSet, basename='cron-job')
router.register(r'cron-job-logs', views.CronJobLogViewSet, basename='cron-job-log')

# URL patterns
urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    
    # Frontend views
    path('', views.cron_job_dashboard, name='dashboard'),
    path('list/', views.cron_job_list, name='job_list'),
    path('<uuid:job_id>/', views.cron_job_detail, name='job_detail'),
    path('<uuid:job_id>/logs/', views.cron_job_logs, name='job_logs'),
    
    # AJAX endpoints
    path('<uuid:job_id>/ajax/update-status/', views.ajax_update_job_status, name='ajax_update_status'),
    path('<uuid:job_id>/ajax/run-now/', views.ajax_run_job_now, name='ajax_run_now'),
    path('ajax/statistics/', views.ajax_get_job_statistics, name='ajax_statistics'),
]
