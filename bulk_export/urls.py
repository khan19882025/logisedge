from django.urls import path
from . import views

app_name = 'bulk_export'

urlpatterns = [
    # Dashboard
    path('', views.BulkExportDashboardView.as_view(), name='dashboard'),
    
    # Export forms
    path('customers/', views.customer_export_view, name='customer_export'),
    path('items/', views.item_export_view, name='item_export'),
    path('transactions/', views.transaction_export_view, name='transaction_export'),
    
    # Export logs
    path('logs/', views.ExportLogListView.as_view(), name='export_logs'),
    path('logs/<uuid:pk>/', views.ExportLogDetailView.as_view(), name='export_log_detail'),
]
