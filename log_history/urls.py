from django.urls import path
from . import views

app_name = 'log_history'

urlpatterns = [
    # Dashboard and Overview
    path('', views.dashboard, name='dashboard'),
    
    # Log History Main Views
    path('logs/', views.LogHistoryListView.as_view(), name='log_history_list'),
    path('logs/<uuid:pk>/', views.LogHistoryDetailView.as_view(), name='log_history_detail'),
    path('search/', views.log_history_search, name='log_history_search'),
    path('export/', views.log_history_export, name='log_history_export'),
    
    # Bulk Actions
    path('bulk-action/', views.bulk_action, name='bulk_action'),
    
    # AJAX Endpoints
    path('ajax/chart-data/', views.log_history_chart_data, name='log_history_chart_data'),
    
    # Log Categories Management
    path('categories/', views.LogCategoryListView.as_view(), name='log_category_list'),
    path('categories/create/', views.LogCategoryCreateView.as_view(), name='log_category_create'),
    path('categories/<uuid:pk>/update/', views.LogCategoryUpdateView.as_view(), name='log_category_update'),
    path('categories/<uuid:pk>/delete/', views.LogCategoryDeleteView.as_view(), name='log_category_delete'),
    
    # Log Retention Policies Management
    path('retention-policies/', views.LogRetentionPolicyListView.as_view(), name='log_retention_policy_list'),
    path('retention-policies/create/', views.LogRetentionPolicyCreateView.as_view(), name='log_retention_policy_create'),
    path('retention-policies/<uuid:pk>/update/', views.LogRetentionPolicyUpdateView.as_view(), name='log_retention_policy_update'),
    path('retention-policies/<uuid:pk>/delete/', views.LogRetentionPolicyDeleteView.as_view(), name='log_retention_policy_delete'),
    path('retention-policies/cleanup/', views.log_retention_cleanup, name='log_retention_cleanup'),
]
