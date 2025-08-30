from django.urls import path
from . import views

app_name = 'contra_entry'

urlpatterns = [
    # Main views
    path('', views.contra_entry_list, name='contra_entry_list'),
    path('create/', views.contra_entry_create, name='contra_entry_create'),
    path('<int:pk>/', views.contra_entry_detail, name='contra_entry_detail'),
    path('<int:pk>/edit/', views.contra_entry_edit, name='contra_entry_edit'),
    path('<int:pk>/delete/', views.contra_entry_delete, name='contra_entry_delete'),
    path('<int:pk>/print/', views.contra_entry_print, name='contra_entry_print'),
    
    # Action views
    path('<int:pk>/post/', views.contra_entry_post, name='contra_entry_post'),
    path('<int:pk>/cancel/', views.contra_entry_cancel, name='contra_entry_cancel'),
    
    # AJAX views
    path('ajax/account-search/', views.ajax_account_search, name='ajax_account_search'),
    path('ajax/summary/', views.ajax_contra_entry_summary, name='ajax_contra_entry_summary'),
    path('ajax/validate/', views.ajax_validate_contra_entry, name='ajax_validate_contra_entry'),
] 