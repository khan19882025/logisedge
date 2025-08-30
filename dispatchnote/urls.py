from django.urls import path
from . import views

app_name = 'dispatchnote'

urlpatterns = [
    # Main dispatch note URLs
    path('', views.dispatch_list, name='dispatch_list'),
    path('create/', views.dispatch_create, name='dispatch_create'),
    path('<int:pk>/', views.dispatch_detail, name='dispatch_detail'),
    path('<int:pk>/update/', views.dispatch_update, name='dispatch_update'),
    path('<int:pk>/delete/', views.dispatch_delete, name='dispatch_delete'),
    path('<int:pk>/print/', views.dispatch_print, name='dispatch_print'),
    path('<int:pk>/update-status/', views.update_dispatch_status, name='update_dispatch_status'),
    
    # Dispatch item URLs
    path('<int:dispatch_pk>/items/add/', views.dispatch_item_add, name='dispatch_item_add'),
    path('<int:dispatch_pk>/items/<int:item_pk>/update/', views.dispatch_item_update, name='dispatch_item_update'),
    path('<int:dispatch_pk>/items/<int:item_pk>/delete/', views.dispatch_item_delete, name='dispatch_item_delete'),
    
    # Status update via AJAX
    path('<int:pk>/status/', views.dispatch_status_update, name='dispatch_status_update'),
    
    # API endpoints for AJAX requests
    path('api/delivery-orders/<int:customer_id>/', views.api_delivery_orders_by_customer, name='api_delivery_orders_by_customer'),
    path('api/delivery-order/<int:delivery_order_id>/items/', views.api_delivery_order_items, name='api_delivery_order_items'),
] 