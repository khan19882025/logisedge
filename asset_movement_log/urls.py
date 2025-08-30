from django.urls import path
from . import views

app_name = 'asset_movement_log'

urlpatterns = [
    # Dashboard
    path('', views.asset_movement_dashboard, name='dashboard'),
    
    # Movement Log CRUD
    path('movements/', views.AssetMovementLogListView.as_view(), name='movement_list'),
    path('movements/create/', views.AssetMovementLogCreateView.as_view(), name='movement_create'),
    path('movements/<uuid:pk>/', views.AssetMovementLogDetailView.as_view(), name='movement_detail'),
    path('movements/<uuid:pk>/update/', views.AssetMovementLogUpdateView.as_view(), name='movement_update'),
    path('movements/<uuid:pk>/delete/', views.AssetMovementLogDeleteView.as_view(), name='movement_delete'),
    
    # Quick Movement
    path('movements/quick-create/', views.quick_movement_create, name='quick_movement_create'),
    
    # Export
    path('export/', views.asset_movement_export, name='export'),
    
    # API
    path('api/movements/', views.asset_movement_api, name='api_movements'),
    
    # Templates
    path('templates/', views.AssetMovementTemplateListView.as_view(), name='template_list'),
    path('templates/create/', views.AssetMovementTemplateCreateView.as_view(), name='template_create'),
    path('templates/<int:pk>/update/', views.AssetMovementTemplateUpdateView.as_view(), name='template_update'),
    path('templates/<int:pk>/delete/', views.AssetMovementTemplateDeleteView.as_view(), name='template_delete'),
    
    # Settings
    path('settings/', views.asset_movement_settings, name='settings'),
]
