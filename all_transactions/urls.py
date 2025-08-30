from django.urls import path
from . import views

app_name = 'all_transactions'

urlpatterns = [
    # Main transaction list view
    path('', views.transaction_list, name='transaction_list'),
    
    # Transaction detail view
    path('<str:pk>/', views.transaction_detail, name='transaction_detail'),
    
    # Dashboard view
    path('dashboard/', views.transaction_dashboard, name='transaction_dashboard'),
] 