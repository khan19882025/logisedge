from django.urls import path
from . import views

app_name = 'container_management'

urlpatterns = [
    # Dashboard
    path('', views.container_dashboard, name='dashboard'),
    
    # Container Management
    path('containers/', views.ContainerListView.as_view(), name='container_list'),
    path('containers/create/', views.ContainerCreateView.as_view(), name='container_create'),
    path('containers/<int:pk>/', views.ContainerDetailView.as_view(), name='container_detail'),
    path('containers/<int:pk>/edit/', views.ContainerUpdateView.as_view(), name='container_update'),
    path('containers/<int:pk>/delete/', views.ContainerDeleteView.as_view(), name='container_delete'),
    
    # Container Booking
    path('bookings/', views.ContainerBookingListView.as_view(), name='booking_list'),
    path('bookings/create/', views.ContainerBookingCreateView.as_view(), name='booking_create'),
    path('bookings/<int:pk>/', views.ContainerBookingDetailView.as_view(), name='booking_detail'),
    path('bookings/<int:pk>/edit/', views.ContainerBookingUpdateView.as_view(), name='booking_update'),
    path('bookings/<int:pk>/delete/', views.ContainerBookingDeleteView.as_view(), name='booking_delete'),
    path('bookings/<int:pk>/status/', views.container_booking_status_update, name='booking_status_update'),
    
    # Container Tracking
    path('tracking/', views.ContainerTrackingListView.as_view(), name='tracking_list'),
    path('tracking/create/', views.ContainerTrackingCreateView.as_view(), name='tracking_create'),
    path('tracking/<int:pk>/', views.ContainerTrackingDetailView.as_view(), name='tracking_detail'),
    path('tracking/<int:pk>/edit/', views.ContainerTrackingUpdateView.as_view(), name='tracking_update'),
    path('tracking/<int:pk>/delete/', views.ContainerTrackingDeleteView.as_view(), name='tracking_delete'),
    
    # Container Inventory
    path('inventory/', views.ContainerInventoryListView.as_view(), name='inventory_list'),
    path('inventory/create/', views.ContainerInventoryCreateView.as_view(), name='inventory_create'),
    path('inventory/<int:pk>/', views.ContainerInventoryDetailView.as_view(), name='inventory_detail'),
    path('inventory/<int:pk>/edit/', views.ContainerInventoryUpdateView.as_view(), name='inventory_update'),
    path('inventory/<int:pk>/delete/', views.ContainerInventoryDeleteView.as_view(), name='inventory_delete'),
    path('inventory/export/', views.inventory_export, name='inventory_export'),
    
    # Reports
    path('reports/', views.container_report, name='reports'),
    
    # Bulk Upload
    path('bulk-upload/', views.container_bulk_upload, name='bulk_upload'),
    
    # Notifications
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/<int:pk>/', views.notification_detail, name='notification_detail'),
    path('notifications/send/', views.send_notification, name='send_notification'),
    
    # AJAX endpoints
    path('ajax/container-search/', views.container_search_ajax, name='container_search_ajax'),
    path('ajax/container/<int:pk>/status-update/', views.container_status_update_ajax, name='container_status_update_ajax'),
]
