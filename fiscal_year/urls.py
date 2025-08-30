from django.urls import path
from . import views

app_name = 'fiscal_year'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Fiscal Years
    path('fiscal-years/', views.fiscal_year_list, name='fiscal_year_list'),
    path('fiscal-years/create/', views.fiscal_year_create, name='fiscal_year_create'),
    path('fiscal-years/<int:pk>/', views.fiscal_year_detail, name='fiscal_year_detail'),
    path('fiscal-years/<int:pk>/edit/', views.fiscal_year_update, name='fiscal_year_update'),
    path('fiscal-years/<int:pk>/delete/', views.fiscal_year_delete, name='fiscal_year_delete'),
    path('fiscal-years/<int:pk>/toggle-status/', views.toggle_fiscal_year_status, name='toggle_fiscal_year_status'),
    
    # Fiscal Periods
    path('periods/', views.fiscal_period_list, name='fiscal_period_list'),
    path('periods/create/', views.fiscal_period_create, name='fiscal_period_create'),
    path('periods/<int:pk>/', views.fiscal_period_detail, name='fiscal_period_detail'),
    path('periods/<int:pk>/edit/', views.fiscal_period_update, name='fiscal_period_update'),
    path('periods/<int:pk>/delete/', views.fiscal_period_delete, name='fiscal_period_delete'),
    path('periods/<int:pk>/toggle-status/', views.toggle_period_status, name='toggle_period_status'),
    
    # Settings
    path('settings/', views.settings_view, name='settings'),
] 