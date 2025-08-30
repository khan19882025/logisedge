from django.urls import path
from . import views

app_name = 'charges'

urlpatterns = [
    # Charge Management
    path('', views.charge_list, name='charge_list'),
    path('create/', views.charge_create, name='charge_create'),
    path('<int:pk>/', views.charge_detail, name='charge_detail'),
    path('<int:pk>/edit/', views.charge_edit, name='charge_edit'),
    path('<int:pk>/delete/', views.charge_delete, name='charge_delete'),
    path('<int:pk>/toggle-status/', views.charge_toggle_status, name='charge_toggle_status'),
    
    # Bulk Actions
    path('bulk-action/', views.bulk_action, name='bulk_action'),
    
    # AJAX endpoints
    path('ajax/get-charges/', views.ajax_get_charges, name='ajax_get_charges'),
] 