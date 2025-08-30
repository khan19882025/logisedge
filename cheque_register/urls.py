from django.urls import path
from . import views

app_name = 'cheque_register'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # List and Filter
    path('list/', views.cheque_list, name='cheque_list'),
    
    # CRUD Operations
    path('create/', views.cheque_create, name='cheque_create'),
    path('<int:pk>/', views.cheque_detail, name='cheque_detail'),
    path('<int:pk>/edit/', views.cheque_edit, name='cheque_edit'),
    
    # Status Management
    path('<int:pk>/status/', views.cheque_status_change, name='cheque_status_change'),
    path('bulk-status-update/', views.bulk_status_update, name='bulk_status_update'),
    
    # Export
    path('export/', views.export_cheques, name='export_cheques'),
    
    # AJAX Endpoints
    path('ajax/party-suggestions/', views.ajax_get_party_suggestions, name='ajax_party_suggestions'),
] 