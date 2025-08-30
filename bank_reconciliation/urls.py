from django.urls import path
from . import views

app_name = 'bank_reconciliation'

urlpatterns = [
    # Dashboard and Overview
    path('', views.reconciliation_dashboard, name='dashboard'),
    
    # Session Management
    path('sessions/', views.session_list, name='session_list'),
    path('sessions/create/', views.session_create, name='session_create'),
    path('sessions/<int:pk>/', views.session_detail, name='session_detail'),
    path('sessions/<int:pk>/edit/', views.session_edit, name='session_edit'),
    
    # Bank Statement Import and Management
    path('sessions/<int:session_pk>/import/', views.import_bank_statement, name='import_statement'),
    path('sessions/<int:session_pk>/add-entry/', views.add_bank_entry, name='add_bank_entry'),
    
    # Matching
    path('sessions/<int:session_pk>/manual-match/', views.manual_match, name='manual_match'),
    path('sessions/<int:session_pk>/bulk-match/', views.bulk_match, name='bulk_match'),
    
    # Reporting
    path('sessions/<int:session_pk>/report/', views.generate_report, name='generate_report'),
    
    # AJAX Endpoints
    path('ajax/unmatch/<str:entry_type>/<int:entry_id>/', views.ajax_unmatch_entry, name='ajax_unmatch_entry'),
    path('ajax/suggestions/<int:session_pk>/', views.ajax_get_matching_suggestions, name='ajax_suggestions'),
] 