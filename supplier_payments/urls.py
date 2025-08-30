from django.urls import path
from . import views

app_name = 'supplier_payments'

urlpatterns = [
    path('', views.supplier_payment_list, name='supplier_payment_list'),
    path('create/', views.supplier_payment_create, name='supplier_payment_create'),
    path('<uuid:pk>/', views.supplier_payment_detail, name='supplier_payment_detail'),
    path('<uuid:pk>/update/', views.supplier_payment_update, name='supplier_payment_update'),
    path('<uuid:pk>/delete/', views.supplier_payment_delete, name='supplier_payment_delete'),
    path('<uuid:pk>/print/', views.supplier_payment_print, name='supplier_payment_print'),
    path('<uuid:pk>/email/', views.supplier_payment_email, name='supplier_payment_email'),
    path('pending-bills/', views.pending_bills_list, name='pending_bills_list'),
    path('ajax/pending-invoices/', views.get_pending_invoices, name='ajax_pending_invoices'),
    path('get-pending-invoices/<int:supplier_id>/', views.get_pending_invoices, name='get_pending_invoices'),
    path('ajax/filter-ledger-accounts/', views.ajax_filter_ledger_accounts, name='ajax_filter_ledger_accounts'),
    path('ajax/all-ledger-accounts/', views.ajax_all_ledger_accounts, name='ajax_all_ledger_accounts'),

]