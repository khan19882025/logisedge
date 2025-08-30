from django.urls import path
from . import views

app_name = 'dunning_letters'

urlpatterns = [
    path('', views.dunning_letter_list, name='list'),
    path('dashboard/', views.dunning_letter_dashboard, name='dashboard'),
    path('create/', views.dunning_letter_create, name='create'),
    path('<int:pk>/', views.dunning_letter_detail, name='detail'),
    path('<int:pk>/update/', views.dunning_letter_update, name='update'),
    path('<int:pk>/delete/', views.dunning_letter_delete, name='delete'),
    path('<int:pk>/send-email/', views.dunning_letter_send_email, name='send_email'),
    path('<int:pk>/print/', views.dunning_letter_print, name='print'),
    path('<int:pk>/update-status/', views.update_letter_status, name='update_status'),
    path('ajax/overdue-invoices/', views.get_overdue_invoices, name='get_overdue_invoices'),
] 