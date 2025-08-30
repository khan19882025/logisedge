from django.urls import path
from . import views

app_name = 'credit_note'

urlpatterns = [
    path('', views.credit_note_list, name='list'),
    path('create/', views.credit_note_create, name='create'),
    path('<int:pk>/', views.credit_note_detail, name='detail'),
    path('<int:pk>/delete/', views.credit_note_delete, name='delete'),
    path('<int:pk>/print/', views.credit_note_print, name='print'),
    path('<int:pk>/email/', views.credit_note_email, name='email'),
    path('get-unpaid-invoices/', views.get_unpaid_invoices, name='get_unpaid_invoices'),
] 