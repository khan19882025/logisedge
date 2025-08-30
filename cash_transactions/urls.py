from django.urls import path
from . import views

app_name = 'cash_transactions'

urlpatterns = [
    # Main views
    path('', views.cash_transaction_list, name='list'),
    path('create/', views.cash_transaction_create, name='create'),
    path('quick/', views.quick_transaction, name='quick'),
    path('<int:pk>/', views.cash_transaction_detail, name='detail'),
    path('<int:pk>/edit/', views.cash_transaction_edit, name='edit'),
    path('<int:pk>/delete/', views.cash_transaction_delete, name='delete'),
    
    # Action views
    path('<int:pk>/post/', views.cash_transaction_post, name='post'),
    path('<int:pk>/cancel/', views.cash_transaction_cancel, name='cancel'),
    
    # AJAX endpoints
    path('ajax/account-balance/', views.get_account_balance, name='account_balance'),
    path('ajax/cash-balance/', views.get_cash_balance, name='cash_balance'),
    path('ajax/summary/', views.cash_transaction_summary, name='summary'),
] 