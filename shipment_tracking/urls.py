from django.urls import path
from . import views

app_name = 'shipment_tracking'

urlpatterns = [
    # Dashboard and Overview
    path('', views.dashboard_view, name='dashboard'),
    path('list/', views.ShipmentListView.as_view(), name='shipment_list'),
    
    # Shipment CRUD Operations
    path('create/', views.ShipmentCreateView.as_view(), name='shipment_create'),
    path('<int:pk>/', views.ShipmentDetailView.as_view(), name='shipment_detail'),
    path('<int:pk>/update/', views.ShipmentUpdateView.as_view(), name='shipment_update'),
    path('<int:pk>/delete/', views.ShipmentDeleteView.as_view(), name='shipment_delete'),
    
    # Search and Filter
    path('search/', views.shipment_search, name='shipment_search'),
    
    # Status Updates
    path('<int:pk>/status-update/', views.add_status_update, name='add_status_update'),
    path('<int:pk>/quick-update/', views.quick_status_update, name='quick_status_update'),
    
    # Attachments
    path('<int:pk>/upload-attachment/', views.upload_attachment, name='upload_attachment'),
    
    # Bulk Operations
    path('bulk-update/', views.bulk_update_view, name='bulk_update'),
    path('import/', views.shipment_import_view, name='shipment_import'),
    path('export/', views.export_shipments, name='export_shipments'),
    
    # API Endpoints
    path('api/<int:pk>/status/', views.api_shipment_status, name='api_shipment_status'),
]
