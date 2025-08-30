from django.urls import path
from . import views

app_name = 'manual_journal_entry'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.journal_entry_dashboard, name='dashboard'),
    
    # CRUD operations
    path('', views.journal_entry_list, name='journal_entry_list'),
    path('create/', views.journal_entry_create, name='journal_entry_create'),
    path('<int:pk>/', views.journal_entry_detail, name='journal_entry_detail'),
    path('<int:pk>/edit/', views.journal_entry_edit, name='journal_entry_edit'),
    path('<int:pk>/delete/', views.journal_entry_delete, name='journal_entry_delete'),
    
    # Actions
    path('<int:pk>/post/', views.journal_entry_post, name='journal_entry_post'),
    path('<int:pk>/void/', views.journal_entry_void, name='journal_entry_void'),
    
    # AJAX endpoints
    path('ajax/account-search/', views.ajax_account_search, name='ajax_account_search'),
] 