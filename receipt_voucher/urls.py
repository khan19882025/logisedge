from django.urls import path
from . import views

app_name = 'receipt_voucher'

urlpatterns = [
    # Main views
    path('', views.receipt_voucher_list, name='receipt_voucher_list'),
    path('dashboard/', views.receipt_voucher_dashboard, name='receipt_voucher_dashboard'),
    path('create/', views.receipt_voucher_create, name='receipt_voucher_create'),
    path('<int:pk>/', views.receipt_voucher_detail, name='receipt_voucher_detail'),
    path('<int:pk>/edit/', views.receipt_voucher_edit, name='receipt_voucher_edit'),
    path('<int:pk>/delete/', views.receipt_voucher_delete, name='receipt_voucher_delete'),
    
    # Status management
    path('<int:pk>/approve/', views.receipt_voucher_approve, name='receipt_voucher_approve'),
    path('<int:pk>/mark-received/', views.receipt_voucher_mark_received, name='receipt_voucher_mark_received'),
    path('<int:pk>/cancel/', views.receipt_voucher_cancel, name='receipt_voucher_cancel'),
    path('<int:pk>/print/', views.receipt_voucher_print, name='receipt_voucher_print'),
    
    # Attachment management
    path('<int:pk>/upload-attachment/', views.receipt_voucher_attachment_upload, name='receipt_voucher_attachment_upload'),
    path('<int:pk>/delete-attachment/<int:attachment_pk>/', views.receipt_voucher_attachment_delete, name='receipt_voucher_attachment_delete'),
    
    # AJAX endpoints
    path('ajax/payer-search/', views.ajax_payer_search, name='ajax_payer_search'),
    path('ajax/account-search/', views.ajax_account_search, name='ajax_account_search'),
    path('ajax/voucher-summary/', views.ajax_voucher_summary, name='ajax_voucher_summary'),
] 