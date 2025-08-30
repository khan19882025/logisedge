from django.urls import path
from . import views

app_name = 'bank_transfer'

urlpatterns = [
    # Main views
    path('', views.bank_transfer_list, name='list'),
    path('create/', views.bank_transfer_create, name='create'),
    path('quick/', views.quick_transfer, name='quick_transfer'),
    path('<int:pk>/', views.bank_transfer_detail, name='detail'),
    path('<int:pk>/edit/', views.bank_transfer_edit, name='edit'),
    path('<int:pk>/delete/', views.bank_transfer_delete, name='delete'),
    
    # Action views
    path('<int:pk>/complete/', views.bank_transfer_complete, name='complete'),
    path('<int:pk>/cancel/', views.bank_transfer_cancel, name='cancel'),
    
    # Template views
    path('templates/', views.template_list, name='template_list'),
    path('templates/create/', views.template_create, name='template_create'),
    path('templates/<int:pk>/edit/', views.template_edit, name='template_edit'),
    path('templates/<int:pk>/delete/', views.template_delete, name='template_delete'),
    
    # AJAX endpoints
    path('ajax/account-balance/', views.get_account_balance, name='account_balance'),
    path('ajax/account-currencies/', views.get_account_currencies, name='account_currencies'),
    path('ajax/summary/', views.bank_transfer_summary, name='summary'),
    path('ajax/load-template/<int:pk>/', views.load_template, name='load_template'),
] 