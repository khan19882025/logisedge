from django.urls import path
from . import views

app_name = 'payment_voucher'

urlpatterns = [
    # Main views
    path('', views.payment_voucher_list, name='payment_voucher_list'),
    path('dashboard/', views.payment_voucher_dashboard, name='payment_voucher_dashboard'),
    path('create/', views.payment_voucher_create, name='payment_voucher_create'),
    path('<int:pk>/', views.payment_voucher_detail, name='payment_voucher_detail'),
    path('<int:pk>/edit/', views.payment_voucher_edit, name='payment_voucher_edit'),
    path('<int:pk>/delete/', views.payment_voucher_delete, name='payment_voucher_delete'),
    
    # Status management
    path('<int:pk>/approve/', views.payment_voucher_approve, name='payment_voucher_approve'),
    path('<int:pk>/mark-paid/', views.payment_voucher_mark_paid, name='payment_voucher_mark_paid'),
    path('<int:pk>/cancel/', views.payment_voucher_cancel, name='payment_voucher_cancel'),
    path('<int:pk>/print/', views.payment_voucher_print, name='payment_voucher_print'),
    
    # Attachment management
    path('<int:pk>/upload-attachment/', views.payment_voucher_attachment_upload, name='payment_voucher_attachment_upload'),
    path('<int:pk>/delete-attachment/<int:attachment_pk>/', views.payment_voucher_attachment_delete, name='payment_voucher_attachment_delete'),
    
    # AJAX endpoints
    path('ajax/payee-search/', views.ajax_payee_search, name='ajax_payee_search'),
    path('ajax/account-search/', views.ajax_account_search, name='ajax_account_search'),
    path('ajax/voucher-summary/', views.ajax_voucher_summary, name='ajax_voucher_summary'),
] 