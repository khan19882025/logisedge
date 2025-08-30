from django.urls import path
from . import views

app_name = 'adjustment_entry'

urlpatterns = [
    # Main views
    path('', views.adjustment_entry_list, name='adjustment_entry_list'),
    path('create/', views.adjustment_entry_create, name='adjustment_entry_create'),
    path('<int:pk>/', views.adjustment_entry_detail, name='adjustment_entry_detail'),
    path('<int:pk>/edit/', views.adjustment_entry_edit, name='adjustment_entry_edit'),
    path('<int:pk>/delete/', views.adjustment_entry_delete, name='adjustment_entry_delete'),
    path('<int:pk>/print/', views.adjustment_entry_print, name='adjustment_entry_print'),
    
    # Action views
    path('<int:pk>/post/', views.adjustment_entry_post, name='adjustment_entry_post'),
    path('<int:pk>/cancel/', views.adjustment_entry_cancel, name='adjustment_entry_cancel'),
    
    # AJAX views
    path('ajax/account-search/', views.ajax_account_search, name='ajax_account_search'),
    path('ajax/summary/', views.ajax_adjustment_entry_summary, name='ajax_adjustment_entry_summary'),
    path('ajax/validate/', views.ajax_validate_adjustment_entry, name='ajax_validate_adjustment_entry'),
] 