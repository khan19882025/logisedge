from django.urls import path
from . import views

app_name = 'asset_register'

urlpatterns = [
    # Main asset views
    path('', views.asset_list, name='asset_list'),
    path('create/', views.asset_create, name='asset_create'),
    path('<int:asset_id>/', views.asset_detail, name='asset_detail'),
    path('<int:asset_id>/edit/', views.asset_edit, name='asset_edit'),
    path('<int:asset_id>/delete/', views.asset_delete, name='asset_delete'),
    path('<int:asset_id>/dispose/', views.asset_dispose, name='asset_dispose'),
    path('<int:asset_id>/movement/', views.asset_movement, name='asset_movement'),
    path('<int:asset_id>/maintenance/', views.asset_maintenance, name='asset_maintenance'),
    path('<int:asset_id>/qr-code/', views.asset_qr_code, name='asset_qr_code'),
    path('<int:asset_id>/barcode/', views.asset_barcode, name='asset_barcode'),
    path('<int:asset_id>/print/', views.asset_print, name='asset_print'),
    
    # Export functionality
    path('export/', views.asset_export, name='asset_export'),
    
    # AJAX endpoints
    path('ajax/search/', views.asset_search_ajax, name='asset_search_ajax'),
    path('ajax/stats/', views.asset_stats_ajax, name='asset_stats_ajax'),
    path('ajax/bulk-action/', views.asset_bulk_action, name='asset_bulk_action'),
    
    # Category management
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    
    # Location management
    path('locations/', views.location_list, name='location_list'),
    path('locations/create/', views.location_create, name='location_create'),
    
    # Status management
    path('statuses/', views.status_list, name='status_list'),
    path('statuses/create/', views.status_create, name='status_create'),
    
    # Depreciation method management
    path('depreciation/', views.depreciation_list, name='depreciation_list'),
    path('depreciation/create/', views.depreciation_create, name='depreciation_create'),
] 