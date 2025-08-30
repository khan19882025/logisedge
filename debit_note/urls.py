from django.urls import path
from . import views

app_name = 'debit_note'

urlpatterns = [
    path('', views.debit_note_list, name='list'),
    path('create/', views.debit_note_create, name='create'),
    path('<int:pk>/', views.debit_note_detail, name='detail'),
    path('<int:pk>/delete/', views.debit_note_delete, name='delete'),
    path('<int:pk>/print/', views.debit_note_print, name='print'),
    path('<int:pk>/email/', views.debit_note_email, name='email'),
    path('get-unpaid-invoices/', views.get_unpaid_invoices, name='get_unpaid_invoices'),
] 