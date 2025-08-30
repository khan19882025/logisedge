from django.urls import path
from . import views

app_name = 'bank_accounts'

urlpatterns = [
    # Dashboard and List Views
    path('', views.bank_account_dashboard, name='bank_account_dashboard'),
    path('list/', views.bank_account_list, name='bank_account_list'),
    
    # CRUD Operations
    path('create/', views.bank_account_create, name='bank_account_create'),
    path('<int:pk>/', views.bank_account_detail, name='bank_account_detail'),
    path('<int:pk>/edit/', views.bank_account_edit, name='bank_account_edit'),
    path('<int:pk>/delete/', views.bank_account_delete, name='bank_account_delete'),
    path('<int:pk>/toggle-status/', views.bank_account_toggle_status, name='bank_account_toggle_status'),
    
    # Transactions
    path('<int:pk>/transactions/', views.bank_account_transactions, name='bank_account_transactions'),
    path('<int:pk>/add-transaction/', views.bank_account_add_transaction, name='bank_account_add_transaction'),
    
    # AJAX Endpoints
    path('ajax/account-search/', views.ajax_account_search, name='ajax_account_search'),
    
    # Export
    path('export/', views.export_bank_accounts, name='export_bank_accounts'),
] 