from django.urls import path
from . import views

app_name = 'customer_payments'

urlpatterns = [
    path('', views.payment_list, name='payment_list'),
    path('create/', views.payment_create, name='payment_create'),
    path('<int:pk>/', views.payment_detail, name='payment_detail'),
    path('<int:pk>/delete/', views.payment_delete, name='payment_delete'),
    path('<int:pk>/print/', views.payment_print, name='payment_print'),
    path('<int:pk>/email/', views.payment_email, name='payment_email'),
    path('ajax/customer-invoices/', views.customer_invoices_ajax, name='customer_invoices_ajax'),
    path('ajax/filter-ledger-accounts/', views.filter_ledger_accounts, name='filter_ledger_accounts'),
]