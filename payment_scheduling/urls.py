from django.urls import path
from . import views

app_name = 'payment_scheduling'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Schedule Management
    path('schedules/', views.schedule_list, name='schedule_list'),
    path('schedules/create/', views.schedule_create, name='schedule_create'),
    path('schedules/<int:schedule_id>/', views.schedule_detail, name='schedule_detail'),
    path('schedules/<int:schedule_id>/update/', views.schedule_update, name='schedule_update'),
    path('schedules/<int:schedule_id>/delete/', views.schedule_delete, name='schedule_delete'),
    path('schedules/<int:schedule_id>/status-change/', views.schedule_status_change, name='schedule_status_change'),
    
    # Calendar View
    path('calendar/', views.calendar_view, name='calendar_view'),
    
    # Reminders
    path('schedules/<int:schedule_id>/reminders/create/', views.reminder_create, name='reminder_create'),
    
    # Reports
    path('reports/', views.report_list, name='reports'),
    
    # Bulk Operations
    path('bulk-update/', views.bulk_update, name='bulk_update'),
    
    # API Endpoints
    path('api/schedule-data/', views.api_schedule_data, name='api_schedule_data'),
]
