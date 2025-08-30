from django.urls import path
from . import views

app_name = 'crossstuffing'

urlpatterns = [
    # List and search
    path('', views.crossstuffing_list, name='crossstuffing_list'),
    
    # CRUD operations
    path('create/', views.crossstuffing_create, name='crossstuffing_create'),
    path('<int:pk>/', views.crossstuffing_detail, name='crossstuffing_detail'),
    path('<int:pk>/edit/', views.crossstuffing_update, name='crossstuffing_update'),
    path('<int:pk>/delete/', views.crossstuffing_delete, name='crossstuffing_delete'),
    
    # Additional operations
    path('<int:pk>/quick-view/', views.crossstuffing_quick_view, name='crossstuffing_quick_view'),
    path('<int:pk>/duplicate/', views.crossstuffing_duplicate, name='crossstuffing_duplicate'),
    path('<int:pk>/status-update/', views.crossstuffing_status_update, name='crossstuffing_status_update'),
    path('get-customer-cargo-items/<int:customer_id>/', views.get_customer_cargo_items, name='get_customer_cargo_items'),
    
    # Print views
    path('<int:pk>/print/invoice/', views.crossstuffing_print_invoice, name='crossstuffing_print_invoice'),
    path('<int:pk>/print/packing-list/', views.crossstuffing_print_packing_list, name='crossstuffing_print_packing_list'),
    path('<int:pk>/print/da/', views.crossstuffing_print_da, name='crossstuffing_print_da'),
    path('<int:pk>/print/cs-summary/', views.crossstuffing_print_cs_summary, name='crossstuffing_print_cs_summary'),
    
    # Email views
    path('<int:pk>/email/invoice/', views.crossstuffing_email_invoice, name='crossstuffing_email_invoice'),
    path('<int:pk>/email/packing-list/', views.crossstuffing_email_packing_list, name='crossstuffing_email_packing_list'),
    path('<int:pk>/email/da/', views.crossstuffing_email_da, name='crossstuffing_email_da'),
    path('<int:pk>/email/cs-summary/', views.crossstuffing_email_cs_summary, name='crossstuffing_email_cs_summary'),
    
    # Test endpoint
    path('test-jobs/', views.test_crossstuffing_jobs, name='test_crossstuffing_jobs'),
] 