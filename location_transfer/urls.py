from django.urls import path
from . import views

app_name = 'location_transfer'

urlpatterns = [
    # Dashboard
    path('', views.location_transfer_dashboard, name='location_transfer_dashboard'),
    
    # Location Transfer Management
    path('transfers/', views.location_transfer_list, name='location_transfer_list'),
    path('transfers/create/', views.location_transfer_create, name='location_transfer_create'),
    path('transfers/<int:pk>/', views.location_transfer_detail, name='location_transfer_detail'),
    path('transfers/<int:pk>/edit/', views.location_transfer_edit, name='location_transfer_edit'),
    path('transfers/<int:pk>/approve/', views.location_transfer_approve, name='location_transfer_approve'),
    path('transfers/<int:pk>/process/', views.location_transfer_process, name='location_transfer_process'),
    path('transfers/<int:pk>/cancel/', views.location_transfer_cancel, name='location_transfer_cancel'),
    
    # Pallet Management
    path('pallets/', views.pallet_list, name='pallet_list'),
    path('pallets/<int:pk>/', views.pallet_detail, name='pallet_detail'),
    
    # Quick Transfer
    path('quick-transfer/', views.quick_transfer, name='quick_transfer'),
    
    # AJAX endpoints
    path('ajax/get-pallet-details/', views.get_pallet_details, name='get_pallet_details'),
    path('ajax/search-pallets/', views.search_pallets, name='search_pallets'),
    path('ajax/get-available-locations/', views.get_available_locations, name='get_available_locations'),
] 