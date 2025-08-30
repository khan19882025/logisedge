from django.urls import path
from . import views

app_name = 'stock_transfer'

urlpatterns = [
    # Stock Transfer Management
    path('', views.stock_transfer_list, name='stock_transfer_list'),
    path('create/', views.stock_transfer_create, name='stock_transfer_create'),
    path('<int:pk>/', views.stock_transfer_detail, name='stock_transfer_detail'),
    path('<int:pk>/edit/', views.stock_transfer_edit, name='stock_transfer_edit'),
    path('<int:pk>/approve/', views.stock_transfer_approve, name='stock_transfer_approve'),
    path('<int:pk>/process/', views.stock_transfer_process, name='stock_transfer_process'),
    path('<int:pk>/cancel/', views.stock_transfer_cancel, name='stock_transfer_cancel'),
    
    # Stock Ledger
    path('ledger/', views.stock_ledger_list, name='stock_ledger_list'),
    path('balance-report/', views.stock_balance_report, name='stock_balance_report'),
    
    # AJAX endpoints
    path('ajax/get-item-details/', views.get_item_details, name='get_item_details'),
    path('ajax/search-items/', views.search_items, name='search_items'),
] 