from django.urls import path
from . import views

app_name = 'multi_currency'

urlpatterns = [
    # Dashboard
    path('', views.currency_dashboard, name='dashboard'),
    
    # Currency management
    path('currencies/', views.currency_list, name='currency_list'),
    path('currencies/create/', views.currency_create, name='currency_create'),
    path('currencies/<int:pk>/', views.currency_detail, name='currency_detail'),
    path('currencies/<int:pk>/update/', views.currency_update, name='currency_update'),
    path('currencies/<int:pk>/delete/', views.currency_delete, name='currency_delete'),
    path('currencies/<int:pk>/toggle-status/', views.toggle_currency_status, name='toggle_currency_status'),
    
    # Exchange rate management
    path('exchange-rates/', views.exchange_rate_list, name='exchange_rate_list'),
    path('exchange-rates/create/', views.exchange_rate_create, name='exchange_rate_create'),
    path('exchange-rates/<int:pk>/', views.exchange_rate_detail, name='exchange_rate_detail'),
    path('exchange-rates/<int:pk>/update/', views.exchange_rate_update, name='exchange_rate_update'),
    path('exchange-rates/<int:pk>/delete/', views.exchange_rate_delete, name='exchange_rate_delete'),
    path('exchange-rates/<int:pk>/toggle-status/', views.toggle_exchange_rate_status, name='toggle_exchange_rate_status'),
    
    # Settings
    path('settings/', views.currency_settings, name='currency_settings'),
] 