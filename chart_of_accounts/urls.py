from django.urls import path
from . import views

app_name = 'chart_of_accounts'

urlpatterns = [
    # Test views for debugging
    path('test/', views.test_view, name='test'),
    path('test-dashboard/', views.test_dashboard_view, name='test_dashboard'),
    path('test-list/', views.test_list_view, name='test_list'),
    
    # Dashboard
    path('', views.chart_of_accounts_dashboard, name='dashboard'),
    
    # Account Management
    path('accounts/', views.account_list, name='account_list'),
    path('parent-accounts/', views.parent_accounts_list, name='parent_accounts_list'),
    path('accounts/create/', views.account_create, name='account_create'),
    path('accounts/create-parent/', views.parent_account_create, name='parent_account_create'),
    path('accounts/<int:pk>/', views.account_detail, name='account_detail'),
    path('accounts/<int:pk>/edit/', views.account_update, name='account_update'),
    path('accounts/<int:pk>/delete/', views.account_delete, name='account_delete'),
    path('accounts/hierarchy/', views.account_hierarchy, name='account_hierarchy'),
    
    # Account Types
    path('account-types/', views.account_type_list, name='account_type_list'),
    path('account-types/create/', views.account_type_create, name='account_type_create'),
    path('account-types/<int:pk>/', views.account_type_detail, name='account_type_detail'),
    path('account-types/<int:pk>/edit/', views.account_type_edit, name='account_type_edit'),
    path('account-types/<int:pk>/delete/', views.account_type_delete, name='account_type_delete'),
    path('account-types/<int:pk>/toggle-status/', views.account_type_toggle_status, name='account_type_toggle_status'),
    path('account-types/export-excel/', views.export_account_types_excel, name='export_account_types_excel'),
    path('account-types/import-excel/', views.import_account_types_excel, name='import_account_types_excel'),
    
    # Chart of Accounts Excel Import/Export
    path('export-accounts-excel/', views.export_accounts_excel, name='export_accounts_excel'),
    path('import-accounts-excel/', views.import_accounts_excel, name='import_accounts_excel'),
    
    # Account Balances
    path('accounts/<int:account_pk>/balances/', views.account_balance_list, name='account_balance_list'),
    path('accounts/<int:account_pk>/balances/create/', views.account_balance_create, name='account_balance_create'),
    
    # Account Templates
    path('templates/', views.account_template_list, name='account_template_list'),
    path('templates/<int:pk>/', views.account_template_detail, name='account_template_detail'),
    path('templates/<int:template_pk>/apply/', views.apply_template, name='apply_template'),
    
    # Bulk Operations
    path('bulk-import/', views.bulk_import_accounts, name='bulk_import'),
    path('export-csv/', views.export_accounts_csv, name='export_csv'),
    
    # Parent Accounts Import/Export
    path('parent-accounts/export-excel/', views.export_parent_accounts_excel, name='export_parent_accounts_excel'),
    path('parent-accounts/import-excel/', views.import_parent_accounts_excel, name='import_parent_accounts_excel'),
    
    # AJAX Endpoints
    path('ajax/parent-accounts/', views.get_parent_accounts, name='ajax_parent_accounts'),
    path('ajax/account-details/<int:pk>/', views.get_account_details, name='ajax_account_details'),
    path('ajax/update-status/<int:pk>/', views.update_account_status, name='ajax_update_status'),
    path('ajax/generate-account-code/', views.generate_account_code, name='ajax_generate_account_code'),
]