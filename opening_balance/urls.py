from django.urls import path
from . import views

app_name = 'opening_balance'

urlpatterns = [
    path('', views.opening_balance_list, name='opening_balance_list'),
    path('create/', views.opening_balance_create, name='opening_balance_create'),
    path('<int:pk>/', views.opening_balance_detail, name='opening_balance_detail'),
    path('<int:pk>/edit/', views.opening_balance_edit, name='opening_balance_edit'),
    path('<int:pk>/delete/', views.opening_balance_delete, name='opening_balance_delete'),
    path('ajax/account-search/', views.ajax_account_search, name='ajax_account_search'),
] 