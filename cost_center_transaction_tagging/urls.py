from django.urls import path
from . import views

app_name = 'cost_center_transaction_tagging'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Transaction Tagging
    path('transactions/', views.transaction_tagging_list, name='transaction_tagging_list'),
    path('transactions/create/', views.transaction_tagging_create, name='transaction_tagging_create'),
    path('transactions/<uuid:pk>/', views.transaction_tagging_detail, name='transaction_tagging_detail'),
    path('transactions/<uuid:pk>/update/', views.transaction_tagging_update, name='transaction_tagging_update'),
    path('transactions/<uuid:pk>/delete/', views.transaction_tagging_delete, name='transaction_tagging_delete'),
    
    # Default Mappings
    path('default-mappings/', views.default_mapping_list, name='default_mapping_list'),
    path('default-mappings/create/', views.default_mapping_create, name='default_mapping_create'),
    path('default-mappings/<uuid:pk>/update/', views.default_mapping_update, name='default_mapping_update'),
    
    # Transaction Tagging Rules
    path('rules/', views.transaction_tagging_rule_list, name='transaction_tagging_rule_list'),
    path('rules/create/', views.transaction_tagging_rule_create, name='transaction_tagging_rule_create'),
    path('rules/<uuid:pk>/update/', views.transaction_tagging_rule_update, name='transaction_tagging_rule_update'),
    
    # Reports
    path('reports/', views.transaction_tagging_report_list, name='transaction_tagging_report_list'),
    path('reports/create/', views.transaction_tagging_report_create, name='transaction_tagging_report_create'),
    path('reports/<uuid:pk>/', views.transaction_tagging_report_detail, name='transaction_tagging_report_detail'),
    
    # Bulk Operations
    path('bulk-tagging/', views.bulk_transaction_tagging, name='bulk_transaction_tagging'),
    
    # API Endpoints
    path('api/get-default-cost-center/', views.get_default_cost_center, name='get_default_cost_center'),
]
