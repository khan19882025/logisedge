from django.urls import path
from . import views

app_name = 'general_journal'

urlpatterns = [
    # Main journal entry views
    path('', views.journal_list, name='journal_list'),
    path('create/', views.journal_create, name='journal_create'),
    path('<int:pk>/', views.journal_detail, name='journal_detail'),
    path('<int:pk>/update/', views.journal_update, name='journal_update'),
    path('<int:pk>/delete/', views.journal_delete, name='journal_delete'),
    
    # Journal entry actions
    path('<int:pk>/post/', views.journal_post, name='journal_post'),
    path('<int:pk>/cancel/', views.journal_cancel, name='journal_cancel'),
    path('<int:pk>/print/', views.journal_print, name='journal_print'),
]