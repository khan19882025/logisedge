from django.urls import path
from . import views

app_name = 'ledger'

urlpatterns = [
    # Main ledger views
    path('', views.ledger_list, name='ledger_list'),
    path('dashboard/', views.ledger_dashboard, name='ledger_dashboard'),
    path('create/', views.ledger_create, name='ledger_create'),
    path('<int:pk>/', views.ledger_detail, name='ledger_detail'),
    path('<int:pk>/update/', views.ledger_update, name='ledger_update'),
    path('<int:pk>/delete/', views.ledger_delete, name='ledger_delete'),
    path('<int:pk>/reconcile/', views.ledger_reconcile, name='ledger_reconcile'),
    
    # Batch views
    path('batches/', views.ledger_batch_list, name='batch_list'),
    path('batches/create/', views.ledger_batch_create, name='batch_create'),
    
    # Import/Export
    path('import/', views.ledger_import, name='ledger_import'),
    path('export/csv/', views.ledger_export_csv, name='ledger_export_csv'),
    
    # AJAX endpoints
    path('ajax/search/', views.ledger_ajax_search, name='ledger_ajax_search'),
] 