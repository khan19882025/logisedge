from django.urls import path
from . import views

app_name = 'dispose_asset'

urlpatterns = [
    # Main disposal views
    path('', views.disposal_list, name='disposal_list'),
    path('create/', views.disposal_create, name='disposal_create'),
    path('<int:disposal_id>/', views.disposal_detail, name='disposal_detail'),
    path('<int:disposal_id>/edit/', views.disposal_edit, name='disposal_edit'),
    path('<int:disposal_id>/submit/', views.disposal_submit, name='disposal_submit'),
    path('<int:disposal_id>/approve/', views.disposal_approve, name='disposal_approve'),
    path('<int:disposal_id>/execute/', views.disposal_execute, name='disposal_execute'),
    path('<int:disposal_id>/reverse/', views.disposal_reverse, name='disposal_reverse'),
    
    # Asset selection and bulk disposal
    path('asset-selection/', views.asset_selection, name='asset_selection'),
    path('bulk-disposal/', views.bulk_disposal, name='bulk_disposal'),
    
    # AJAX endpoints
    path('ajax/asset-search/', views.asset_search_ajax, name='asset_search_ajax'),
    path('ajax/disposal-stats/', views.disposal_stats_ajax, name='disposal_stats_ajax'),
] 