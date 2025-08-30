from django.urls import path
from . import views

app_name = 'depreciation_schedule'

urlpatterns = [
    # Dashboard
    path('', views.depreciation_dashboard, name='dashboard'),
    
    # Schedules
    path('schedules/', views.DepreciationScheduleListView.as_view(), name='schedule_list'),
    path('schedules/create/', views.DepreciationScheduleCreateView.as_view(), name='schedule_create'),
    path('schedules/<uuid:pk>/', views.DepreciationScheduleDetailView.as_view(), name='schedule_detail'),
    path('schedules/<uuid:pk>/update/', views.DepreciationScheduleUpdateView.as_view(), name='schedule_update'),
    path('schedules/<uuid:pk>/delete/', views.DepreciationScheduleDeleteView.as_view(), name='schedule_delete'),
    path('schedules/<uuid:pk>/calculate/', views.calculate_depreciation, name='calculate_depreciation'),
    path('schedules/<uuid:pk>/post/', views.post_depreciation, name='post_depreciation'),
    path('schedules/<uuid:pk>/entries/', views.depreciation_entries, name='depreciation_entries'),
    path('schedules/<uuid:pk>/export/', views.export_depreciation, name='export_depreciation'),
    
    # Settings
    path('settings/', views.depreciation_settings, name='settings'),
    
    # Calculator
    path('calculator/', views.asset_depreciation_calculator, name='asset_calculator'),
    
    # API
    path('api/', views.depreciation_api, name='api'),
]
