from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Set app name for namespace
app_name = 'auto_task_scheduler'

# Create router for API endpoints
router = DefaultRouter()
router.register(r'scheduled-tasks', views.ScheduledTaskViewSet, basename='scheduled-task')
router.register(r'task-logs', views.TaskLogViewSet, basename='task-log')

# URL patterns
urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    
    # Frontend views
    path('', views.task_scheduler_dashboard, name='task_scheduler_dashboard'),
    path('create/', views.task_scheduler_create, name='task_scheduler_create'),
    path('list/', views.task_scheduler_list, name='task_scheduler_list'),
    path('<uuid:task_id>/', views.task_scheduler_detail, name='task_scheduler_detail'),
    path('<uuid:task_id>/logs/', views.task_scheduler_logs, name='task_scheduler_logs'),
]
