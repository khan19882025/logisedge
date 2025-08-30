from django.urls import path
from . import views

app_name = 'cost_center_reports'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Reports
    path('reports/', views.report_list, name='report_list'),
    path('reports/create/', views.report_create, name='report_create'),
    path('reports/<uuid:pk>/', views.report_detail, name='report_detail'),
    path('reports/<uuid:pk>/edit/', views.report_edit, name='report_edit'),
    path('reports/<uuid:pk>/delete/', views.report_delete, name='report_delete'),
    path('reports/<uuid:pk>/export/', views.report_export, name='report_export'),
    
    # Schedules
    path('schedules/', views.report_schedule_list, name='schedule_list'),
    path('schedules/create/', views.report_schedule_create, name='schedule_create'),
]
