from django.urls import path
from . import views

app_name = 'delivery_order'

urlpatterns = [
    # Main CRUD operations
    path('', views.delivery_order_list, name='delivery_order_list'),
    path('create/', views.delivery_order_create, name='delivery_order_create'),
    path('<int:pk>/', views.delivery_order_detail, name='delivery_order_detail'),
    path('<int:pk>/edit/', views.delivery_order_edit, name='delivery_order_edit'),
    path('<int:pk>/delete/', views.delivery_order_delete, name='delivery_order_delete'),
    
    # Status updates
    path('<int:pk>/status-update/', views.delivery_order_status_update, name='delivery_order_status_update'),
    
    # AJAX endpoints
    path('ajax/customer/<int:customer_id>/', views.get_customer_info, name='get_customer_info'),
    path('ajax/grn-items/<int:grn_id>/', views.get_grn_items, name='get_grn_items'),
    path('get-customer-items/<int:customer_id>/', views.get_customer_items, name='get_customer_items'),
    path('get-customers-with-grns/', views.get_customers_with_grns, name='get_customers_with_grns'),
    
    # Email functionality
    path('<int:pk>/send-email/', views.send_delivery_order_email, name='send_email'),
    
    # Print functionality
    path('<int:pk>/print/', views.delivery_order_print, name='delivery_order_print'),
] 