from django.urls import path
from . import views

app_name = 'recurring_journal_entry'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.recurring_entry_dashboard, name='dashboard'),
    
    # CRUD operations
    path('', views.recurring_entry_list, name='recurring_entry_list'),
    path('create/', views.recurring_entry_create, name='recurring_entry_create'),
    path('<int:pk>/', views.recurring_entry_detail, name='recurring_entry_detail'),
    path('<int:pk>/edit/', views.recurring_entry_edit, name='recurring_entry_edit'),
    path('<int:pk>/delete/', views.recurring_entry_delete, name='recurring_entry_delete'),
    
    # Actions
    path('<int:pk>/pause/', views.recurring_entry_pause, name='recurring_entry_pause'),
    path('<int:pk>/resume/', views.recurring_entry_resume, name='recurring_entry_resume'),
    path('<int:pk>/cancel/', views.recurring_entry_cancel, name='recurring_entry_cancel'),
    path('<int:pk>/generate/', views.generate_entry, name='generate_entry'),
    
    # Generated entries
    path('<int:pk>/generated-entries/', views.generated_entries_list, name='generated_entries_list'),
    
    # AJAX endpoints
    path('ajax/account-search/', views.ajax_account_search, name='ajax_account_search'),
] 