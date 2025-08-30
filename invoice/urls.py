from django.urls import path
from . import views

app_name = 'invoice'

urlpatterns = [
    # Invoice CRUD
    path('', views.invoice_list, name='invoice_list'),
    path('create/', views.invoice_create, name='invoice_create'),
    path('<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('<int:pk>/edit/', views.invoice_edit, name='invoice_edit'),
    path('<int:pk>/delete/', views.invoice_delete, name='invoice_delete'),
    
    # Print and Export
    path('<int:pk>/print/', views.invoice_print, name='invoice_print'),
    path('<int:pk>/print/cost-sale/', views.invoice_cost_sale_print, name='invoice_cost_sale_print'),
    path('<int:pk>/pdf/', views.invoice_pdf, name='invoice_pdf'),
    
    # AJAX endpoints
    path('ajax/get-customer-details/', views.get_customer_details, name='get_customer_details'),
    path('ajax/get-customer-jobs/', views.get_customer_jobs, name='get_customer_jobs'),
    path('ajax/get-job-details/', views.get_job_details, name='get_job_details'),
    path('ajax/get-services/', views.get_services_for_description, name='get_services_for_description'),
    path('ajax/get-vendors/', views.get_vendors, name='get_vendors'),
    path('ajax/calculate-totals/', views.calculate_totals, name='calculate_totals'),
    
    # Ledger Posting
    path('<int:invoice_id>/post-to-ledger/', views.post_invoice_to_ledger, name='post_invoice_to_ledger'),
] 